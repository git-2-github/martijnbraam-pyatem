# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import collections

import gi

from pyatem.field import InputPropertiesField
from pyatem.hexdump import hexdump

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk, Pango

gi.require_version('Handy', '1')
from gi.repository import Handy


class DebuggerWindow:
    def __init__(self, parent, connection, application):
        self.application = application
        self.connection = connection

        builder = Gtk.Builder()
        builder.set_translation_domain("openswitcher")
        builder.add_from_resource('/nl/brixit/switcher/ui/debugger.glade')
        builder.connect_signals(self)
        css = Gio.resources_lookup_data("/nl/brixit/switcher/ui/style.css", 0)

        self.provider = Gtk.CssProvider()
        self.provider.load_from_data(css.get_data())

        self.window = builder.get_object("window")

        self.statemodel = builder.get_object("statemodel")
        self.state_tree = builder.get_object("state_tree")
        self.state_box = builder.get_object("state_box")
        self.events = builder.get_object("events")

        self.load_initial_state()

        self.apply_css(self.window, self.provider)
        self.connection.mixer.on('change', self.on_change)
        self.window.show_all()

    def apply_css(self, widget, provider):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css, provider)

    def flatten(self, d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def load_initial_state(self):
        known = self.statemodel.append(None, ("Known",))
        unknown = self.statemodel.append(None, ("Unknown",))

        col_name = Gtk.TreeViewColumn("Field")
        render_name = Gtk.CellRendererText()
        col_name.pack_start(render_name, True)
        col_name.add_attribute(render_name, 'text', 0)

        self.state_tree.append_column(col_name)

        for fieldname in self.connection.mixer.mixerstate:
            field = self.connection.mixer.mixerstate[fieldname]
            if isinstance(field, bytes):
                parent = unknown
            else:
                parent = known
            self.statemodel.append(parent, (fieldname,))

    def on_state_selection_changed(self, widget, *args):
        model, model_iter = widget.get_selected()
        fieldname = model.get(model_iter, 0)[0]
        if fieldname == "Known" or fieldname == "Unknown":
            return

        for widget in self.state_box:
            self.state_box.remove(widget)

        field = self.connection.mixer.mixerstate[fieldname]
        if not isinstance(field, dict):
            field = {"0": field}

        flat = self.flatten(field)

        for key in flat:
            row = flat[key]
            self.state_box.add(self.make_field_widget(fieldname, row))
        self.apply_css(self.state_box, self.provider)
        self.state_box.show_all()

    def make_field_widget(self, name, field):
        frame = Gtk.Frame()
        frame.get_style_context().add_class('view')
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add(box)

        heading = Gtk.Label(name)
        heading.get_style_context().add_class("heading")
        heading.set_margin_start(10)
        heading.set_margin_end(10)
        heading.set_margin_top(10)
        heading.set_margin_bottom(10)

        box.add(heading)

        if isinstance(field, bytes):
            label = Gtk.Label(hexdump(field, result='return'))
            label.get_style_context().add_class('hexdump')
            label.set_margin_start(10)
            label.set_margin_end(10)
            label.set_margin_top(10)
            label.set_margin_bottom(10)
            box.add(label)
        else:
            grid = Gtk.Grid(column_spacing=10, row_spacing=3)
            grid.set_margin_bottom(10)
            i = 0
            for key in field.__dict__:
                if key == "raw":
                    continue
                keylabel = Gtk.Label(key, xalign=1.0)
                keylabel.set_hexpand(True)
                valuelabel = Gtk.Label(str(getattr(field, key)), xalign=0.0)
                valuelabel.set_line_wrap(True)
                valuelabel.set_hexpand(True)
                keylabel.get_style_context().add_class('dim-label')
                grid.attach(keylabel, 0, i, 1, 1)
                grid.attach(valuelabel, 1, i, 1, 1)
                i += 1

            box.add(grid)

        return frame

    def on_change(self, fieldname, field):
        if fieldname == 'time':
            return

        GLib.idle_add(self.on_change_uithread, fieldname, field)

    def on_change_uithread(self, fieldname, field):
        widget = self.make_field_widget(fieldname, field)
        widget.get_style_context().add_class('pulsein')
        self.apply_css(widget, self.provider)
        self.events.pack_end(widget, False, False, 0)
        self.events.show_all()
