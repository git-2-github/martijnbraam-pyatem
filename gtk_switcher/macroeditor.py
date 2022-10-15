# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import gi

from pyatem.command import MultiviewInputCommand
from pyatem.field import InputPropertiesField
from pyatem.macro import decode_macro, encode_macro, encode_macroscript

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk

gi.require_version('Handy', '1')
from gi.repository import Handy


class MacroEditorWindow:
    def __init__(self, parent, application, connection, index, raw):
        self.application = application
        self.connection = connection

        self.index = index
        self.raw = raw

        builder = Gtk.Builder()
        builder.set_translation_domain("openswitcher")
        builder.add_from_resource('/nl/brixit/switcher/ui/macro-editor.glade')
        builder.connect_signals(self)
        css = Gio.resources_lookup_data("/nl/brixit/switcher/ui/style.css", 0)

        self.provider = Gtk.CssProvider()
        self.provider.load_from_data(css.get_data())

        self.window = builder.get_object("window")
        self.headerbar = builder.get_object("headerbar")
        self.main_stack = builder.get_object("main_stack")
        self.sourcecode = builder.get_object("sourcecode")
        self.sourcebuffer = builder.get_object("sourcebuffer")
        self.window.set_application(self.application)

        self.actions = builder.get_object("actions")

        self.apply_css(self.window, self.provider)

        self.window.set_transient_for(parent)
        self.window.set_modal(True)

        macro = self.connection.mixer.mixerstate['macro-properties'][index]
        self.headerbar.set_subtitle(macro.name.decode())

        ma = decode_macro(raw)
        source = encode_macroscript(ma)
        self.sourcebuffer.set_text(source)
        for action in ma:
            frame = Gtk.Frame()
            frame.get_style_context().add_class('view')
            grid = Gtk.Grid()
            grid.set_margin_top(8)
            grid.set_margin_bottom(8)
            grid.set_margin_start(8)
            grid.set_margin_end(8)
            grid.set_column_spacing(8)
            grid.set_row_spacing(8)
            frame.add(grid)
            name = Gtk.Label(action.__class__.NAME)
            name.set_xalign(0.0)
            grid.attach(name, 0, 0, 2, 1)

            top = 1
            for a in action.widgets:
                for attribute, datatype, label, properties in action.widgets[a]:
                    field_label = Gtk.Label(label)
                    field_label.get_style_context().add_class('dim-label')
                    field_label.set_xalign(1.0)
                    grid.attach(field_label, 0, top, 1, 1)

                    widget = None
                    if datatype == 'framecount':
                        widget = Gtk.SpinButton()
                        adjustment = Gtk.Adjustment(getattr(action, attribute), 0, 250, 1, 30, 1)
                        widget.adjustment = adjustment
                        widget.set_adjustment(adjustment)
                    elif datatype == 'number':
                        widget = Gtk.SpinButton()

                        value = getattr(action, attribute)
                        if 'offset' in properties:
                            value += properties['offset']

                        adjustment = Gtk.Adjustment(value, properties['min'], properties['max'], 1, 10, 1)
                        widget.adjustment = adjustment
                        widget.set_adjustment(adjustment)
                    elif datatype == 'source':
                        widget = Gtk.ComboBox()

                    if widget:
                        grid.attach(widget, 1, top, 1, 1)

                    top += 1

            self.actions.add(frame)

        self.window.show_all()

    def apply_css(self, widget, provider):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css, provider)

    def on_cancel_clicked(self, *args):
        self.window.close()

    def on_save_clicked(self, *args):
        self.window.close()

    def on_source_toggled(self, widget, *args):
        if widget.get_active():
            self.main_stack.set_visible_child_name("code")
        else:
            self.main_stack.set_visible_child_name("blocks")
