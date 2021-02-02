import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, GdkPixbuf

gi.require_version('Handy', '1')
from gi.repository import Handy


class PreferencesWindow:
    def __init__(self, parent):
        builder = Gtk.Builder()
        builder.add_from_resource('/nl/brixit/switcher/ui/connection.glade')
        builder.connect_signals(Handler(builder, self))

        window = builder.get_object("preferences_window")

        window.set_transient_for(parent)
        window.set_modal(True)

        window.show_all()


class Item(GObject.GObject):
    text = GObject.property(type=str)

    def __init__(self, text):
        GObject.GObject.__init__(self)
        self.text = text


class Handler:
    def __init__(self, builder, application):
        self.builder = builder
        self.application = application
        self.window = builder.get_object('preferences_window')

        self.ipaddress = builder.get_object('ipaddress')

        self.settings = Gio.Settings.new('nl.brixit.Switcher')
        self.settings.connect('changed::switcher-ip', self.on_switcher_ip_changed, self.ipaddress)

        self.on_switcher_ip_changed(self.settings, 'switcher-ip', self.ipaddress)

    def on_save_clicked(self, widget):
        self.settings.set_string('switcher-ip', self.ipaddress.get_text())
        self.window.close()

    def on_switcher_ip_changed(self, settings, key, widget):
        if key == 'switcher-ip':
            widget.set_text(self.settings.get_string('switcher-ip'))
