# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import gi

from gtk_switcher.colorwheel import ColorWheelWidget
from pyatem.field import InputPropertiesField

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk

gi.require_version('Handy', '1')
from gi.repository import Handy


class CameraPage:
    def __init__(self, builder):
        self.camera_box = builder.get_object('camera_box')

    def on_camera_layout_change(self, data):
        inputs = self.connection.mixer.mixerstate['input-properties']

        for child in self.camera_box:
            child.destroy()

        for i in inputs.values():
            if i.port_type == InputPropertiesField.PORT_EXTERNAL:
                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                box.set_spacing(8)
                label = Gtk.Label(i.name)
                label.get_style_context().add_class('heading')
                box.pack_start(label, False, True, 0)
                camera_frame = Gtk.Frame()
                camera_frame.get_style_context().add_class('view')
                box.pack_start(camera_frame, True, True, 0)
                self.camera_box.pack_start(box, True, True, 0)

                grid = Gtk.Grid()
                grid.set_row_spacing(8)
                grid.set_column_spacing(8)
                camera_frame.add(grid)

        self.camera_box.show_all()
