# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import argparse
import locale
import gettext
import logging
import os
import sys

import gi

from gtk_switcher.atemwindow import AtemWindow

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

gi.require_version('Handy', '1')
from gi.repository import Handy


class AtemLogFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    white = "\x1b[97;20m"
    blue = "\x1b[36;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = '[%(levelname)-8s %(threadName)-12s] %(name)-14s - %(message)s'

    FORMATS = {
        logging.DEBUG: blue + format + reset,
        logging.INFO: white + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class AtemApplication(Gtk.Application):
    def __init__(self, application_id, flags, args):
        Gtk.Application.__init__(self, application_id=application_id, flags=flags)
        self.connect("activate", self.new_window)
        self.args = args

        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)

    def new_window(self, *args):
        AtemWindow(self, self.args)


def main(version):
    Handy.init()

    parser = argparse.ArgumentParser(description="ATEM Control panel")
    parser.add_argument('ip', help='ip-address of the switcher to connect to', nargs='?')
    parser.add_argument('--persist', action='store_true', help='save the new ip address')
    parser.add_argument('--verbose', action='store_true', help='Show more log messages')
    parser.add_argument('--debug', action='store_true', help='Display a lot of debugging info')
    parser.add_argument('--dump', help='dump data for specific packets', nargs='*')
    parser.add_argument('--view', choices=['switcher', 'media', 'audio', 'camera'], default='switcher',
                        help='default view to open when launching')
    args = parser.parse_args()

    ch = logging.StreamHandler()
    ch.setFormatter(AtemLogFormatter())

    if args.verbose:
        logging.basicConfig(level=logging.INFO, handlers=[ch])
    elif args.debug:
        logging.basicConfig(level=logging.DEBUG, handlers=[ch])
    else:
        logging.basicConfig(handlers=[ch])

    log = logging.getLogger('Launcher')
    if os.path.isfile('atem.gresource'):
        log.info('using resources from cwd')
        resource = Gio.resource_load("atem.gresource")
        Gio.Resource._register(resource)

    app = AtemApplication("nl.brixit.Switcher", Gio.ApplicationFlags.FLAGS_NONE, args=args)
    app.run()


if __name__ == '__main__':
    locale.bindtextdomain("openswitcher", os.getenv('LOCALEDIR', '.'))
    gettext.install("openswitcher", os.getenv('LOCALEDIR', '.'))
    locale.textdomain("openswitcher")

    main('')
