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


class PresetWindow:
    def __init__(self, parent, provider):
        self.provider = provider
        self.model_changing = True
        builder = Gtk.Builder()
        builder.set_translation_domain("openswitcher")
        builder.add_from_resource('/nl/brixit/switcher/ui/preset.glade')
        builder.connect_signals(self)

        self.window = builder.get_object("dialog")
        self.window.set_transient_for(parent)
        self.window.set_modal(True)

        self.name = builder.get_object('name')

    def run(self):
        return self.window.run()

    def get_name(self):
        return self.name.get_text()

    def destroy(self):
        self.window.destroy()
