import threading
import time

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk

import rtmidi
from rtmidi.midiutil import open_midiinput

port = '20:0'


class MidiConnection(threading.Thread):
    def __init__(self, port, callback):
        threading.Thread.__init__(self)
        self.callback = callback
        self.port = port

    def run(self):
        def _midi_in(event, data=None):
            self._do_callback(*event[0])

        midiin, port_name = open_midiinput(self.port, client_name="Switcher")
        midiin.set_callback(_midi_in)

        while True:
            time.sleep(10)

    def _do_callback(self, *args, **kwargs):
        GLib.idle_add(self.callback, *args, **kwargs)


class MidiLink:
    def __init__(self, widget):
        self.type = None
        self.widget = widget
        self.adjustment = None
        self.min = None
        self.max = None
        self.is_tbar = False
        self.inverted = False

        if isinstance(widget, gi.repository.Gtk.Scale):
            self.type = 'scale'
            self.min = widget.adj.get_lower()
            self.max = widget.adj.get_upper()
            if hasattr(widget, 'is_tbar') and widget.is_tbar:
                self.is_tbar = True
                self.widget.connect("notify::inverted", self.on_tbar_inverted)
        if isinstance(widget, gi.repository.Gtk.Button):
            self.type = 'button'

    def new_value(self, value):
        if self.type == 'button':
            self.widget.emit("clicked")
        if self.type == 'scale':
            if self.inverted:
                self.widget.adj.set_value(self._remap(127, 0, self.min, self.max, value))
            else:
                self.widget.adj.set_value(self._remap(0, 127, self.min, self.max, value))

    def _remap(self, in_min, in_max, out_min, out_max, value):
        in_range = in_max - in_min
        out_range = out_max - out_min
        return (((value - in_min) * out_range) / in_range) + out_min

    def on_tbar_inverted(self, *args):
        self.inverted = not self.inverted


class MidiControl:
    def __init__(self, builder):
        self.midi = MidiConnection('20:0', self.on_midi)
        self.midi.daemon = True
        self.midi.start()

        self.midi_map = {}

        self.menu = None
        self.midi_learning = False
        self.midi_learning_widget = None

    def on_midi(self, event, channel, value):
        if event == 176:
            # CC

            print(event, channel, value)
            if channel in self.midi_map:
                self.midi_map[channel].new_value(value)

            if self.midi_learning:
                self.midi_learning = False
                self.midi_map[channel] = MidiLink(self.midi_learning_widget)
                self.midi_learning_widget = None

    def on_context_menu(self, widget, event, *args):
        if event.button != 3:
            return

        self.menu = Gtk.Menu()
        midi_item = Gtk.MenuItem("Midi learn")
        midi_item.connect('activate', self.on_start_midi_learn)
        self.menu.append(midi_item)
        self.menu.show_all()
        self.menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())
        self.midi_learning_widget = widget

    def on_start_midi_learn(self, *args):
        self.midi_learning = True
