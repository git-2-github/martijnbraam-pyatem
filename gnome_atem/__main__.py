import os
import gi

from gnome_atem.atemwindow import AtemWindow

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

gi.require_version('Handy', '1')
from gi.repository import Handy


class AtemApplication(Gtk.Application):
    def __init__(self, application_id, flags):
        Gtk.Application.__init__(self, application_id=application_id, flags=flags)
        self.connect("activate", self.new_window)

    def new_window(self, *args):
        AtemWindow(self)


def main(version):
    Handy.init()
    if os.path.isfile('atem.gresource'):
        print("Using resources from cwd")
        resource = Gio.resource_load("atem.gresource")
        Gio.Resource._register(resource)

    app = AtemApplication("nl.brixit.Atem", Gio.ApplicationFlags.FLAGS_NONE)
    app.run()


if __name__ == '__main__':
    main('')
