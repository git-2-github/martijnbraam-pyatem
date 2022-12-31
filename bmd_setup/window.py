# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import ipaddress
import os

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk, GLib, Pango

gi.require_version('Handy', '1')
from gi.repository import Handy

import pyatem.converters.converter as conv


class SetupWindow:
    def __init__(self, application):
        self.application = application

        Handy.init()

        self.window = None
        self.titlebar = None
        self.titleleaflet = None
        self.headerbar_side = None
        self.headerbar = None
        self.headergroup = None
        self.leaflet = None
        self.sidebar = None
        self.content = None
        self.listbox = None
        self.main = None
        self.back = None

        self.sg_sidebar = None
        self.sg_main = None

        self.create_window()

        self.create_pages()
        self.window.show_all()
        Gtk.main()

    def create_window(self):
        self.sg_sidebar = Gtk.SizeGroup()
        self.sg_sidebar.set_mode(Gtk.SizeGroupMode.HORIZONTAL)
        self.sg_main = Gtk.SizeGroup()
        self.sg_main.set_mode(Gtk.SizeGroupMode.HORIZONTAL)

        self.headergroup = Handy.HeaderGroup()

        self.window = Handy.Window()
        self.window.set_default_size(640, 480)
        self.window.set_title('Setup')
        self.window.connect('destroy', self.on_main_window_destroy)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.add(box)

        self.titlebar = Gtk.Box()
        self.titleleaflet = Handy.Leaflet()
        self.titlebar.add(self.titleleaflet)

        self.headerbar_side = Handy.HeaderBar()
        self.headerbar_side.set_show_close_button(True)
        self.titleleaflet.add(self.headerbar_side)
        self.titleleaflet.child_set(self.headerbar_side, name="sidebar")
        leaflet_sep = Gtk.Separator()
        leaflet_sep.get_style_context().add_class('sidebar')
        self.titleleaflet.add(leaflet_sep)

        self.headerbar = Handy.HeaderBar()
        self.titleleaflet.add(self.headerbar)
        self.titleleaflet.child_set(self.headerbar, name="content")
        self.headerbar.set_title("Setup")
        self.headerbar.set_show_close_button(True)
        self.headerbar.set_hexpand(True)

        self.headergroup.add_header_bar(self.headerbar_side)
        self.headergroup.add_header_bar(self.headerbar)

        self.back = Gtk.Button.new_from_icon_name("go-previous-symbolic", 1)
        self.back.connect("clicked", self.on_back_clicked)
        self.back.set_visible(False)
        self.back.set_no_show_all(True)
        self.headerbar.pack_start(self.back)

        self.leaflet = Handy.Leaflet()
        self.leaflet.set_transition_type(Handy.LeafletTransitionType.SLIDE)
        self.leaflet.connect("notify::folded", self.on_leaflet_change)
        self.leaflet.connect("notify::visible-child", self.on_leaflet_change)
        self.sidebar = Gtk.Box()
        self.sidebar.set_size_request(200, 0)
        self.content = Gtk.Box()
        self.content.props.hexpand = True
        self.leaflet.add(self.sidebar)
        self.leaflet.child_set(self.sidebar, name="sidebar")
        leaflet_sep = Gtk.Separator()
        leaflet_sep.get_style_context().add_class('sidebar')
        self.leaflet.add(leaflet_sep)
        self.leaflet.add(self.content)
        self.leaflet.child_set(self.content, name="content")
        self.leaflet.set_visible_child_name("sidebar")

        self.sg_sidebar.add_widget(self.headerbar_side)
        self.sg_sidebar.add_widget(self.sidebar)

        self.sg_main.add_widget(self.headerbar)
        self.sg_main.add_widget(self.content)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.sidebar.pack_start(sw, True, True, 0)
        self.listbox = Gtk.ListBox()
        self.listbox.connect('row-activated', self.on_select_page)
        sw.add(self.listbox)

        ms = Gtk.ScrolledWindow()
        ms.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.content.pack_start(ms, True, True, 0)
        self.main = ms

        box.pack_start(self.titlebar, False, True, 0)
        box.pack_start(self.leaflet, True, True, 0)

        self.actionbar = Gtk.ActionBar()
        self.action_revealer = Gtk.Revealer()
        box.pack_start(self.action_revealer, False, True, 0)
        self.action_revealer.add(self.actionbar)
        label = Gtk.Label(label="You have changed settings that need root permissions to save.", xalign=0.0)
        label.set_line_wrap(True)
        self.actionbar.pack_start(label)
        self.action_button = Gtk.Button.new_with_label("Apply")
        self.action_button.get_style_context().add_class('suggested-action')
        self.actionbar.pack_end(self.action_button)
        # self.action_button.connect('clicked', self.on_save_settings)

    def enumerate_hardware(self):
        classes = []
        for name, cls in conv.__dict__.items():
            if isinstance(cls, type) and name not in ['Field', 'ValueField', 'Converter']:
                classes.append(cls)
        return classes

    def create_pages(self):
        classes = self.enumerate_hardware()

        for device in classes:
            if device.is_plugged_in():
                instance = device()
                instance.connect()
                name = instance.get_name()
                label = Gtk.Label(label=name, xalign=0.0)
                label.set_margin_top(8)
                label.set_margin_left(10)
                label.set_margin_right(10)
                label.set_name('row')

                model = Gtk.Label(label=device.NAME.replace('Blackmagic design ', ''), xalign=0.0)
                model.get_style_context().add_class('dim-label')
                model.set_margin_bottom(8)
                model.set_margin_left(10)
                model.set_margin_right(10)

                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                box.add(label)
                box.add(model)

                row = Gtk.ListBoxRow()
                row.add(box)
                row.device = instance
                self.listbox.add(row)
            self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)

        return

    def make_page(self, device):
        for child in self.main:
            self.main.remove(child)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_left(12)
        box.set_margin_right(12)
        self.main.add(box)

        state = device.get_state()
        sections = {}
        for _, field in state.items():
            if field.section not in sections:
                sections[field.section] = []
            sections[field.section].append(field)

        for section, fields in sections.items():

            label = Gtk.Label(label=section, xalign=0.0)
            label.get_style_context().add_class('heading')
            label.set_margin_bottom(8)
            label.set_margin_top(16)
            box.pack_start(label, False, True, 0)
            frame = Gtk.ListBox()
            frame.set_selection_mode(Gtk.SelectionMode.NONE)
            frame.get_style_context().add_class('content')
            frame.set_margin_bottom(12)
            box.pack_start(frame, False, True, 0)

            for field in fields:
                sbox = Gtk.Box()
                sbox.set_margin_top(8)
                sbox.set_margin_bottom(8)
                sbox.set_margin_left(8)
                sbox.set_margin_right(8)
                lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                sbox.pack_start(lbox, True, True, 0)
                frame.add(sbox)
                wbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                sbox.pack_end(wbox, False, False, 0)

                label = Gtk.Label(label=field.label, xalign=0.0)
                lbox.pack_start(label, False, True, 0)

                value = field.value
                if field.dtype == str:
                    value = value.decode()
                elif field.dtype == int:
                    value = int.from_bytes(field.value, 'little')
                elif field.dtype == ipaddress.IPv4Address:
                    value = str(ipaddress.IPv4Address(value))
                if field.dtype == bool:
                    widget = Gtk.Switch()
                    widget.set_active(field.value)

                    # Make sure I leak some memory
                    widget.field = field
                    widget.device = device
                    field.widget = widget

                    widget.connect('notify::active', self.on_widget_changed)

                    wbox.pack_start(widget, False, False, 0)
                elif field.ro:
                    widget = Gtk.Label(value)
                    widget.set_xalign(0.0)
                    widget.get_style_context().add_class('dim-label')
                    widget.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
                    wbox.pack_start(widget, False, False, 0)
                elif field.mapping is not None:
                    widget = Gtk.ComboBoxText()
                    field.widget = widget
                    widget.device = device
                    widget.field = field

                    widget.set_entry_text_column(0)
                    i = 0
                    for key, display in field.mapping.items():
                        widget.append_text(display)
                        if key == value:
                            widget.set_active(i)
                        i += 1
                    widget.connect('changed', self.on_widget_changed)
                    wbox.pack_start(widget, False, False, 0)

                elif field.dtype == int:
                    w_min = 1
                    w_max = 255
                    w_step = 1
                    widget = Gtk.SpinButton.new_with_range(w_min, w_max, w_step)
                    field.widget = widget
                    widget.field = field
                    widget.device = device
                    widget.set_value(value)
                    widget.connect('value-changed', self.on_widget_changed)
                    wbox.pack_start(widget, False, False, 0)
                elif field.dtype == str or field.dtype == ipaddress.IPv4Address:
                    widget = Gtk.Entry()
                    field.widget = widget
                    widget.field = field
                    widget.device = device
                    widget.set_text(value)
                    widget.connect('activate', self.on_widget_changed)
                    wbox.pack_start(widget, False, False, 0)
                elif field.dtype == open:
                    widget = Gtk.FileChooserButton(title="Select LUT")
                    field.widget = widget
                    widget.field = field
                    widget.device = device
                    widget.connect('file-set', self.on_widget_changed)
                    wbox.pack_start(widget, False, False, 0)

        self.main.show_all()

    def encode_value(self, field, value):
        if field.dtype == str:
            return value.encode()
        elif field.dtype == int:
            value = int(value)
            return value.to_bytes(length=(8 + (value + (value < 0)).bit_length()), byteorder='little')
        return value

    def on_widget_changed(self, widget, *args):
        field = widget.field
        device = widget.device
        if field.dtype == bool:
            device.set_value(field, 0xff if widget.get_active else 0x00)
        elif field.dtype == open:
            device.set_lut(widget.get_filename())
            self.make_page(device)
        elif field.mapping is not None:
            display = widget.get_active_text()
            for value, d in field.mapping.items():
                if d == display:
                    break
            else:
                ValueError("Unknown mapping value")

            device.set_value(field, self.encode_value(field, value))
        elif field.dtype == str:
            value = widget.get_text()
            value = self.encode_value(field, value)
            device.set_value(field, value)
        elif field.dtype == int:
            value = widget.get_value()
            value = self.encode_value(field, value)
            device.set_value(field, value)
        elif field.dtype == ipaddress.IPv4Address:
            value = widget.get_text()
            addr = ipaddress.IPv4Address(value)
            device.set_value(field, addr.packed)

    def on_select_page(self, widget, row):
        if self.listbox.get_selection_mode() == Gtk.SelectionMode.NONE:
            self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
            self.listbox.select_row(row)

        self.make_page(row.device)

        self.headerbar.set_subtitle(row.device.NAME.replace('Blackmagic design ', ''))
        self.leaflet.set_visible_child_name('content')

        # In folded view unselect the row in the listbox
        # so it's possible to go back to the same page
        if self.leaflet.get_folded():
            self.listbox.unselect_row(row)

    def on_main_window_destroy(self, widget):
        Gtk.main_quit()

    def on_back_clicked(self, widget, *args):
        self.leaflet.set_visible_child_name('sidebar')
        self.headerbar.set_subtitle('')

    def on_leaflet_change(self, *args):
        self.titleleaflet.set_visible_child_name(self.leaflet.get_visible_child_name())
        self.back.set_visible(self.leaflet.get_folded())
        if self.leaflet.get_folded():
            self.headerbar_side.set_title("Setup")
        else:
            self.headerbar_side.set_title("")
