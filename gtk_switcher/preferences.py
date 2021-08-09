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

        self.multiview_window = []

        # Load requested view
        self.mainstack = builder.get_object("mainstack")
        self.settingsstack = builder.get_object("settingsstack")
        self.multiview_layout = builder.get_object("multiview_layout")
        self.multiview_tl = builder.get_object("multiview_tl")
        self.multiview_tr = builder.get_object("multiview_tr")
        self.multiview_bl = builder.get_object("multiview_bl")
        self.multiview_br = builder.get_object("multiview_br")
        self.multiview_swap = builder.get_object("multiview_swap")
        self.multiview_layout = builder.get_object("multiview_layout")
        self.apply_css(self.window, self.provider)

        self.window.set_transient_for(parent)
        self.window.set_modal(True)
        self.load_preferences()
        self.connection.mixer.on('change:multiviewer-properties:*', self.make_multiviewer)
        self.connection.mixer.on('change:multiviewer-input:*', self.update_multiviewer_input)
        self.window.show_all()

    def load_preferences(self):
        state = self.connection.mixer.mixerstate

        if 'multiviewer-properties' in state:
            self.make_multiviewer()

    def update_multiviewer_input(self, input):
        pass

    def make_multiviewer(self, *args):
        state = self.connection.mixer.mixerstate
        multiviewer = state['multiviewer-properties'][0]
        self.multiview_window = []
        for widget in self.multiview_layout:
            self.multiview_layout.remove(widget)

        sideways = multiviewer.layout == 5 or multiviewer.layout == 10

        if sideways:
            if not multiviewer.top_left_small:
                self.make_multiview_window(0, 0)
            if not multiviewer.bottom_left_small:
                self.make_multiview_window(0, 1)
            if not multiviewer.top_right_small:
                self.make_multiview_window(1, 0)
            if not multiviewer.bottom_right_small:
                self.make_multiview_window(1, 1)
        else:
            if not multiviewer.top_left_small:
                self.make_multiview_window(0, 0)
            if not multiviewer.top_right_small:
                self.make_multiview_window(1, 0)
            if not multiviewer.bottom_left_small:
                self.make_multiview_window(0, 1)
            if not multiviewer.bottom_right_small:
                self.make_multiview_window(1, 1)

        if sideways:
            if multiviewer.top_left_small:
                self.make_split_multiview_window(0, 0, sideways)
            if multiviewer.bottom_left_small:
                self.make_split_multiview_window(0, 1, sideways)
            if multiviewer.top_right_small:
                self.make_split_multiview_window(1, 0, sideways)
            if multiviewer.bottom_right_small:
                self.make_split_multiview_window(1, 1, sideways)
        else:
            if multiviewer.top_left_small:
                self.make_split_multiview_window(0, 0, sideways, False)
            if multiviewer.top_right_small:
                self.make_split_multiview_window(1, 0, sideways, False)
            if multiviewer.top_left_small:
                self.make_split_multiview_window(0, 0, sideways, True)
            if multiviewer.top_right_small:
                self.make_split_multiview_window(1, 0, sideways, True)
            if multiviewer.bottom_left_small:
                self.make_split_multiview_window(0, 1, sideways, False)
            if multiviewer.bottom_right_small:
                self.make_split_multiview_window(1, 1, sideways, False)
            if multiviewer.bottom_left_small:
                self.make_split_multiview_window(0, 1, sideways, True)
            if multiviewer.bottom_right_small:
                self.make_split_multiview_window(1, 1, sideways, True)

        for index, window in enumerate(self.multiview_window):
            window.index = index

        self.multiview_tl.set_active(not multiviewer.top_left_small)
        self.multiview_tr.set_active(not multiviewer.top_right_small)
        self.multiview_bl.set_active(not multiviewer.bottom_left_small)
        self.multiview_br.set_active(not multiviewer.bottom_right_small)
        self.multiview_swap.set_active(multiviewer.flip)
        self.multiview_layout.show_all()

    def make_split_multiview_window(self, x, y, sideways, second):
        x *= 2
        y *= 2
        if sideways:
            if not second:
                self.make_multiview_window(x, y, 1, 1)
                self.make_multiview_window(x, y + 1, 1, 1)
            else:
                self.make_multiview_window(x + 1, y, 1, 1)
                self.make_multiview_window(x + 1, y + 1, 1, 1)
        else:
            if not second:
                self.make_multiview_window(x, y, 1, 1)
                self.make_multiview_window(x + 1, y, 1, 1)
            else:
                self.make_multiview_window(x, y + 1, 1, 1)
                self.make_multiview_window(x + 1, y + 1, 1, 1)

    def make_multiview_window(self, x, y, w=2, h=2):
        x *= w
        y *= h
        frame = Gtk.Frame()
        frame.get_style_context().add_class('view')

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add(box)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_left(8)
        box.set_margin_right(8)

        index = len(self.multiview_window)
        if index in self.connection.mixer.mixerstate['multiviewer-input'][0]:
            input = self.connection.mixer.mixerstate['multiviewer-input'][0][index]
            ip = self.connection.mixer.mixerstate['input-properties'][input.source]
            input_label = Gtk.Label(ip.name)
            input_label.set_margin_bottom(16)
            box.add(input_label)

            buttonbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            box.pack_end(buttonbox, False, False, 0)
            if input.vu:
                icon = Gtk.Image.new_from_resource("/nl/brixit/switcher/icons/multiview-vu.svg")
                vubutton = Gtk.Button(image=icon)
                buttonbox.add(vubutton)
            if input.safearea:
                icon = Gtk.Image.new_from_resource("/nl/brixit/switcher/icons/multiview-safearea.svg")
                sabutton = Gtk.Button(image=icon)
                buttonbox.add(sabutton)

        self.multiview_layout.attach(frame, x, y, w, h)
        self.multiview_window.append(frame)

    def apply_css(self, widget, provider):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css, provider)
