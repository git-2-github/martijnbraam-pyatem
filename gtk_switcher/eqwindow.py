# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import time
from urllib.parse import urlparse, quote

import gi

from gtk_switcher.adjustmententry import AdjustmentEntry
from gtk_switcher.dial import Dial
from gtk_switcher.eqcurve import EqCurve
from gtk_switcher.gtklogadjustment import LogAdjustment
from gtk_switcher.preferences import PreferencesWindow
from pyatem import locate
from pyatem.command import FairlightStripPropertiesCommand
from pyatem.field import FairlightStripPropertiesField

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, GdkPixbuf

gi.require_version('Handy', '1')
from gi.repository import Handy


class EqWindow:
    def __init__(self, strip_id, parent, connection, provider):
        self.strip_id = strip_id
        self.connection = connection
        self.provider = provider
        self.model_changing = True
        builder = Gtk.Builder()
        builder.set_translation_domain("openswitcher")
        builder.add_from_resource('/nl/brixit/switcher/ui/eq.glade')
        builder.connect_signals(self)

        window = builder.get_object("window")
        curvebox = builder.get_object("curvebox")
        self.eq_enable = builder.get_object('eq_enable')

        window.set_transient_for(parent)
        window.set_modal(True)

        self.curve = EqCurve()
        self.curve.mini = False
        curvebox.add(self.curve)

        strip = self.connection.mixer.mixerstate['fairlight-strip-properties'][self.strip_id]
        self.source = strip.index
        self.channel = strip.subchannel

        self.eq_enable.set_state(strip.eq_enable)
        self.curve.set_enabled(strip.eq_enable)

        self.box = []
        self.switch = []
        for i in range(0, 6):
            self.box.append(builder.get_object(f"controls_band{i + 1}"))

        self.adj_frequency = []
        self.adj_gain = []
        self.adj_q = []

        for i in range(0, 6):
            blocks = self.create_band(i, i == 0, i == 5)
            container = builder.get_object(f'controls_band{i + 1}')
            for b in blocks:
                container.add(b)

        for band_id in self.connection.mixer.mixerstate['atem-eq-band-properties'][self.strip_id]:
            band = self.connection.mixer.mixerstate['atem-eq-band-properties'][self.strip_id][band_id]
            self.on_band_change(band)

            switch = Gtk.Switch()
            self.switch.append(switch)

        self.model_changing = False

        self.apply_css(window, self.provider)

        self.connection.mixer.on(f'change:atem-eq-band-properties:{self.strip_id}', self.on_band_change)
        self.connection.mixer.on(f'change:fairlight-strip-properties:{self.strip_id}', self.on_strip_change)
        window.show_all()

    def create_control(self, name, adjustment, min, max):
        result = Gtk.Grid()
        label = Gtk.Label(label=name)
        label.get_style_context().add_class('dim-label')
        result.attach(label, 0, 0, 1, 1)

        entry = AdjustmentEntry(adjustment, min, max)
        entry.get_style_context().add_class('mini')
        entry.set_margin_left(16)
        entry.set_margin_right(16)
        entry.set_margin_end(8)
        entry.set_max_width_chars(6)
        entry.set_width_chars(6)
        entry.set_alignment(xalign=0.5)

        result.attach(entry, 0, 1, 1, 1)

        dial = Dial()
        dial.set_adjustment(adjustment)
        result.attach(dial, 1, 0, 1, 2)
        s = Gtk.Separator()
        result.attach(s, 0, 2, 2, 1)
        return result

    def create_band(self, index, first=False, last=False):
        lower = 30
        upper = 21700
        if first:
            upper = 395
        elif last:
            lower = 1400
        adj_frequency = Gtk.Adjustment(0, lower, upper, 10, 10, 0)
        adj_frequency.index = index
        adj_frequency.connect('value-changed', self.on_frequency_change)
        self.adj_frequency.append(adj_frequency)

        adj_gain = Gtk.Adjustment(0, -2000, 2000, 10, 10, 0)
        adj_gain.index = index
        self.adj_gain.append(adj_gain)

        adj_q = Gtk.Adjustment(0, 30, 1030, 10, 10, 0)
        adj_q.index = index
        self.adj_q.append(adj_q)

        blocks = []

        blocks.append(self.create_control('Frequency', adj_frequency, lower, upper))
        blocks.append(self.create_control('Gain', adj_gain, -20, 20))
        blocks.append(self.create_control('Q', adj_q, 0.3, 10.3))
        return blocks

    def apply_css(self, widget, provider):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css, provider)

    def on_band_change(self, band):
        self.model_changing = True
        self.curve.update_band(band)

        self.adj_frequency[band.band_index].set_value(band.band_frequency)
        self.adj_gain[band.band_index].set_value(band.band_gain)
        self.adj_q[band.band_index].set_value(band.band_q)
        self.model_changing = False

    def on_strip_change(self, strip):
        if not isinstance(strip, FairlightStripPropertiesField):
            return
        self.eq_enable.set_state(strip.eq_enable)
        self.curve.set_enabled(strip.eq_enable)

    def on_eq_enable_state_set(self, widget, enabled):
        if self.model_changing:
            return
        cmd = FairlightStripPropertiesCommand(source=self.source, channel=self.channel, eq_enable=enabled)
        self.connection.mixer.send_commands([cmd])

    def on_frequency_change(self, widget):
        if self.model_changing:
            return

        cmd = FairlightStripPropertiesCommand(source=self.source, channel=self.channel, eq_enable=enabled)
        print("WHA!")
