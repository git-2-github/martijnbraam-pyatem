import ctypes
import threading

import gi
from hexdump import hexdump

from gtk_switcher.audio import AudioPage
from gtk_switcher.camera import CameraPage
from gtk_switcher.decorators import field, call_fields
from gtk_switcher.media import MediaPage
from gtk_switcher.midi import MidiConnection, MidiControl
from gtk_switcher.switcher import SwitcherPage
from pyatem.command import ProgramInputCommand, PreviewInputCommand, AutoCommand, TransitionPositionCommand
from pyatem.protocol import AtemProtocol

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk

gi.require_version('Handy', '1')
from gi.repository import Handy


class PreferencesWindow:
    def __init__(self, parent, application, connection):
        self.application = application
        self.connection = connection
        self.settings = Gio.Settings.new('nl.brixit.Switcher')

        builder = Gtk.Builder()
        builder.add_from_resource('/nl/brixit/switcher/ui/preferences.glade')
        builder.connect_signals(self)
        css = Gio.resources_lookup_data("/nl/brixit/switcher/ui/style.css", 0)

        self.provider = Gtk.CssProvider()
        self.provider.load_from_data(css.get_data())

        self.window = builder.get_object("window")
        self.window.set_application(self.application)

        # Load requested view
        self.mainstack = builder.get_object("mainstack")
        self.settingsstack = builder.get_object("settingsstack")
        self.apply_css(self.window, self.provider)

        self.window.set_transient_for(parent)
        self.window.set_modal(True)

        self.window.show_all()

    def apply_css(self, widget, provider):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css, provider)
