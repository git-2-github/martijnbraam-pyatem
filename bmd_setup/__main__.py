# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import argparse
import os
import gi

from bmd_setup.window import SetupWindow

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib

gi.require_version('Handy', '1')
from gi.repository import Handy


class SetupApplication(Gtk.Application):
    def __init__(self, application_id, flags):
        Gtk.Application.__init__(self, application_id=application_id, flags=flags)
        GLib.set_prgname(application_id)
        self.connect("activate", self.new_window)

    def new_window(self, *args):
        SetupWindow(self)


def main(version):
    Handy.init()
    app = SetupApplication("nl.brixit.Setup", Gio.ApplicationFlags.FLAGS_NONE)
    app.run()


if __name__ == '__main__':
    main('')
