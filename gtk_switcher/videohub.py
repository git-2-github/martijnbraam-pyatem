# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import json

from gi.repository import Gtk, GObject, Gdk

from gtk_switcher.template_i18n import TemplateLocale

import pyatem.videohub as videohubprotocol


@TemplateLocale(resource_path='/nl/brixit/switcher/ui/videohub.glade')
class VideoHub(Gtk.Grid):
    __gtype_name__ = 'VideoHub'

    ip_entry = Gtk.Template.Child()
    connectbtn = Gtk.Template.Child()
    status = Gtk.Template.Child()
    outputs = Gtk.Template.Child()

    def __init__(self):
        super(Gtk.Grid, self).__init__()
        self.init_template()

        self.probed = False
        self.input_model = None
        self.old_ip = None

        self.config = {
            'ip': None,
            'outputs': {}
        }

    def set_class(self, widget, classname, state):
        if state:
            widget.get_style_context().add_class(classname)
        else:
            widget.get_style_context().remove_class(classname)

    def set_input_model(self, model):
        self.input_model = model

    @GObject.Signal(name="config-changed", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(str,),
                    accumulator=GObject.signal_accumulator_true_handled)
    def settings_changed(self, *args):
        pass

    @GObject.Signal(name="ip-changed", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(str, str),
                    accumulator=GObject.signal_accumulator_true_handled)
    def ip_changed(self, *args):
        pass

    @GObject.Signal(name="deleted", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(str,),
                    accumulator=GObject.signal_accumulator_true_handled)
    def deleted(self, *args):
        pass

    def load(self, config):
        self.config = config
        self.ip_entry.set_text(config['ip'])
        self.old_ip = config['ip']
        self.on_connect_clicked(None, None)

    def save(self):
        self.emit('config-changed', json.dumps(self.config))

    @Gtk.Template.Callback()
    def on_delete_clicked(self, widget, *args):
        self.emit('deleted', self.old_ip)

    @Gtk.Template.Callback()
    def on_connect_clicked(self, widget, *args):
        ip = self.ip_entry.get_text()
        if ip.strip() == "":
            return

        if ip != self.old_ip:
            self.emit('ip-changed', self.old_ip, ip)
            self.old_ip = ip

        self.status.set_text(_("Connecting..."))

        self.probed = False
        probe = videohubprotocol.VideoHub(ip)
        probe.on('connect', self.on_connect)
        try:
            probe.connect()
        except OSError as e:
            self.status.set_text(str(e))
            return
        while not self.probed:
            probe.loop()

        self.status.set_text(_("Connected") + f" ({probe.model_display})")
        self.config['ip'] = ip
        for output in self.outputs:
            self.outputs.remove(output)

        for index in probe.output_label:
            output = probe.output_label[index]
            row = Gtk.Box(spacing=8)

            # Output label
            label = Gtk.Label(output)
            label.set_margin_start(8)
            row.add(label)

            # Show the videohub output as bus, checkbox
            checkbox = Gtk.CheckButton(_("Show as bus"))
            if str(index) in self.config['outputs']:
                checkbox.set_active(self.config['outputs'][str(index)]['bus'])
            checkbox.output = index
            checkbox.set_margin_end(8)
            checkbox.connect('toggled', self.on_bus_toggled)
            row.pack_end(checkbox, False, False, 0)

            # Source label checkbox
            checkbox = Gtk.CheckButton(_("Rename on change"))
            if str(index) in self.config['outputs']:
                checkbox.set_active(self.config['outputs'][str(index)]['rename'])
            checkbox.output = index
            checkbox.connect('toggled', self.on_rename_toggled)
            row.pack_end(checkbox, False, False, 0)

            # Atem input link
            input_select = Gtk.ComboBox.new_with_model(self.input_model)
            input_select.set_entry_text_column(1)
            input_select.set_id_column(0)
            if str(index) in self.config['outputs']:
                if self.config['outputs'][str(index)]['source'] is not None:
                    input_select.set_active_id(str(self.config['outputs'][str(index)]['source']))
            input_select.output = index
            input_select.connect('changed', self.on_source_change)
            renderer = Gtk.CellRendererText()
            input_select.pack_start(renderer, True)
            input_select.add_attribute(renderer, "text", 1)

            row.pack_end(input_select, False, False, 0)

            self.outputs.add(row)

            if str(index) not in self.config['outputs']:
                self.config['outputs'][str(index)] = {
                    'bus': False,
                    'rename': False,
                    'source': None,
                }

        self.outputs.show_all()
        self.save()

    def on_connect(self, *args):
        self.probed = True

    def on_source_change(self, widget, *args):
        output = widget.output
        index = widget.get_active_id()
        if index == "":
            index = None
        else:
            index = int(index)

        self.config["outputs"][str(output)]["source"] = index
        self.save()

    def on_bus_toggled(self, widget, *args):
        output = widget.output
        self.config["outputs"][str(output)]["bus"] = widget.get_active()
        self.save()

    def on_rename_toggled(self, widget, *args):
        output = widget.output
        self.config["outputs"][str(output)]["rename"] = widget.get_active()
        self.save()
