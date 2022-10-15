# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import math

import gi

from gtk_switcher.template_i18n import TemplateLocale
from gtk_switcher.videohubconnection import VideoHubConnection

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject


@TemplateLocale(resource_path='/nl/brixit/switcher/ui/videohub-bus.glade')
class VideoHubBus(Gtk.Grid):
    __gtype_name__ = 'VideoHubBus'
    aux_name = Gtk.Template.Child()
    bus = Gtk.Template.Child()
    focus_dummy = Gtk.Template.Child()

    def __init__(self, provider, connection, output):
        super(Gtk.Grid, self).__init__()
        self.provider = provider
        if not isinstance(connection, VideoHubConnection):
            raise ValueError()

        self.init_template()
        self.connection = connection
        self.output = int(output)
        self.aux_name.set_label(connection.outputs[self.output]['label'])
        self.create_buttons()
        self.connection._route_change.append(self.on_route_change)

    def set_class(self, widget, classname, state):
        if state:
            widget.get_style_context().add_class(classname)
        else:
            widget.get_style_context().remove_class(classname)

    def apply_css(self, widget, provider):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css, provider)

    def create_buttons(self):
        shortnames = {
            'Black': 'BLK',
            'Color Bars': 'BARS',
            'Color 1': 'COL1',
            'Color 2': 'COL2',
            'Media Player 1': 'MP1',
            'Media Player 1 Key': 'MP1K',
            'Media Player 2': 'MP2',
            'Media Player 2 Key': 'MP2K',
            'Multi View': 'MVW',
            'Program': 'PGM',
            'Preview': 'PVW',
            'Computer Direct': 'DIR',
        }

        rows = len(self.connection.inputs) // 10
        cols = math.ceil(len(self.connection.inputs) / rows)

        left = 0
        top = 0
        for index in self.connection.inputs:
            name = self.connection.inputs[index]['label']
            if ':' in name:
                short_name, name = name.split(':', maxsplit=1)
                short_name = short_name.strip()
            elif name in shortnames:
                short_name = shortnames[name]
            else:
                short_name = str(index)

            label = Gtk.Label(label=short_name)
            btn = Gtk.Button()
            btn.add(label)
            btn.index = index
            btn.set_size_request(48, 48)
            btn.get_style_context().add_class('bmdbtn')
            if index == self.connection.outputs[self.output]['source']:
                btn.get_style_context().add_class('program')
            btn.connect('clicked', self.do_source_change)
            self.bus.attach(btn, left, top, 1, 1)
            left += 1
            if left > cols - 1:
                left = 0
                top += 1
        self.apply_css(self.bus, self.provider)
        self.bus.show_all()

    def on_route_change(self, hub_id, index, source):
        if int(index) == self.output:
            for btn in self.bus:
                if btn.index == int(source):
                    btn.get_style_context().add_class('program')
                else:
                    btn.get_style_context().remove_class('program')

    def do_source_change(self, widget):
        self.focus_dummy.grab_focus()
        self.connection.change_route(self.output, widget.index)
