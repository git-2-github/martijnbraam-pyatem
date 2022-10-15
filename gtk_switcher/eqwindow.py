# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import time
from urllib.parse import urlparse, quote

import gi

from gtk_switcher.eqcurve import EqCurve
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

        for band_id in self.connection.mixer.mixerstate['atem-eq-band-properties'][self.strip_id]:
            band = self.connection.mixer.mixerstate['atem-eq-band-properties'][self.strip_id][band_id]
            self.curve.update_band(band)

            switch = Gtk.Switch()
            self.switch.append(switch)

        self.apply_css(window, self.provider)

        self.model_changing = False

        self.connection.mixer.on(f'change:atem-eq-band-properties:{self.strip_id}', self.on_band_change)
        self.connection.mixer.on(f'change:fairlight-strip-properties:{self.strip_id}', self.on_strip_change)
        window.show_all()

    def apply_css(self, widget, provider):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css, provider)

    def on_band_change(self, band):
        self.curve.update_band(band)

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
