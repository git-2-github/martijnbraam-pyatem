# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import gi

from gtk_switcher.template_i18n import TemplateLocale

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject


@TemplateLocale(resource_path='/nl/brixit/switcher/ui/mixeffect-aux.glade')
class AuxMixEffectBlock(Gtk.Grid):
    __gtype_name__ = 'AuxMixEffectBlock'

    dsk_box = Gtk.Template.Child()

    aux_name = Gtk.Template.Child()
    bus = Gtk.Template.Child()
    focus_dummy = Gtk.Template.Child()

    def __init__(self, index, name):
        super(Gtk.Grid, self).__init__()
        self.init_template()
        self.index = index
        self.aux_name.set_label(name)

    def set_class(self, widget, classname, state):
        if state:
            widget.get_style_context().add_class(classname)
        else:
            widget.get_style_context().remove_class(classname)

    def set_inputs(self, buttons):
        # Clear the existing buttons
        for child in self.bus:
            child.destroy()

        for top, row in enumerate(buttons):
            for left, button in enumerate(row):
                if button is None:
                    spacer = Gtk.Box()
                    spacer.set_size_request(4, 4)
                    spacer.source_index = -1
                    pspacer = Gtk.Box()
                    pspacer.set_size_request(4, 4)
                    pspacer.source_index = -1

                    self.bus.attach(spacer, left, top, 1, 1)
                    continue
                active = button.short_name != ""

                label = Gtk.Label(label=button.short_name)

                btn = Gtk.Button()
                btn.add(label)
                btn.source_index = button.index
                btn.set_sensitive(active)
                btn.set_size_request(48, 48)
                btn.get_style_context().add_class('bmdbtn')
                btn.connect('clicked', self.do_program_input_change)
                self.bus.attach(btn, left, top, 1, 1)

        self.bus.show_all()

    def source_change(self, source):
        for btn in self.bus:
            if btn.source_index == source:
                btn.get_style_context().add_class('program')
            else:
                btn.get_style_context().remove_class('program')

    @GObject.Signal(name="source-changed", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int, int),
                    accumulator=GObject.signal_accumulator_true_handled)
    def source_changed(self, *args):
        pass

    def do_program_input_change(self, widget):
        self.focus_dummy.grab_focus()
        self.emit("source-changed", self.index, widget.source_index)
