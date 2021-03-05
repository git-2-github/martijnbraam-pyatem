import gi

from gtk_switcher.colorwheel import ColorWheelWidget
from pyatem.field import InputPropertiesField

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk

gi.require_version('Handy', '1')
from gi.repository import Handy


class MediaPage:
    def __init__(self, builder):
        self.media_flow = builder.get_object('media_flow')

    def on_mediaplayer_slots_change(self, data):
        for child in self.media_flow:
            child.destroy()

        for i in range(0, data.stills):
            slot = Gtk.Box()
            slot_label = Gtk.Label(label=str(i + 1))
            slot_label.get_style_context().add_class('dim-label')
            slot.pack_start(slot_label, False, False, False)

            slot_img = Gtk.Box()
            slot_img.get_style_context().add_class('mp-slot')
            slot_img.set_size_request(160, 120)
            slot.pack_start(slot_img, False, False, False)

            self.media_flow.add(slot)
        self.media_flow.show_all()
