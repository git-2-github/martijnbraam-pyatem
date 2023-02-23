# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import logging

from gi.repository import Gtk, GObject

from gtk_switcher.template_i18n import TemplateLocale
from pyatem.field import TransitionSettingsField


@TemplateLocale(resource_path='/nl/brixit/switcher/ui/mixeffect.glade')
class MixEffectBlock(Gtk.Grid):
    __gtype_name__ = 'MixEffectBlock'

    dsk_box = Gtk.Template.Child()

    program_bus = Gtk.Template.Child()
    preview_bus = Gtk.Template.Child()
    ftb = Gtk.Template.Child()
    ftb_rate = Gtk.Template.Child()
    auto = Gtk.Template.Child()
    cut = Gtk.Template.Child()
    auto_rate = Gtk.Template.Child()
    prev_trans = Gtk.Template.Child()
    dsks = Gtk.Template.Child()
    focus_dummy = Gtk.Template.Child()

    style_mix = Gtk.Template.Child()
    style_dip = Gtk.Template.Child()
    style_wipe = Gtk.Template.Child()
    style_sting = Gtk.Template.Child()
    style_dve = Gtk.Template.Child()

    next_bkgd = Gtk.Template.Child()
    next_key1 = Gtk.Template.Child()
    next_key2 = Gtk.Template.Child()
    next_key3 = Gtk.Template.Child()
    next_key4 = Gtk.Template.Child()

    onair_key1 = Gtk.Template.Child()
    onair_key2 = Gtk.Template.Child()
    onair_key3 = Gtk.Template.Child()
    onair_key4 = Gtk.Template.Child()

    tbar = Gtk.Template.Child()
    transition_progress = Gtk.Template.Child()
    tbar_adj = Gtk.Template.Child()

    def __init__(self, index):
        super(Gtk.Grid, self).__init__()
        self.init_template()
        self.index = index
        self.mode = None

        self.log = logging.getLogger('MixEffectBlock')

        self.tbar_held = False
        self.last_transition_state = False

        self.rate = {
            'mix': '0:00',
            'dip': '0:00',
            'wipe': '0:00',
            'sting': '0:00',
            'dve': '0:00'
        }

        self.menu = None
        self.routers = []
        self.last_program = None
        self.last_preview = None
        self.last_preview_in_program = False

    def __repr__(self):
        return '<MixEffectBlock index={}>'.format(self.index)

    def set_mode(self, mode):
        self.mode = mode

    def frames_to_time(self, frames):
        # WTF BMD
        if self.mode.rate < 29:
            transition_rate = 25
        elif self.mode.rate < 49:
            transition_rate = 30
        elif self.mode.rate < 59:
            transition_rate = 25
        else:
            transition_rate = 30

        if self.mode is None:
            return '00:00'

        seconds = frames // transition_rate
        frames = frames % transition_rate
        return '{:02d}:{:02d}'.format(int(seconds), int(frames))

    def time_to_frames(self, timestr):
        if self.mode.rate < 29:
            transition_rate = 25
        elif self.mode.rate < 49:
            transition_rate = 30
        elif self.mode.rate < 59:
            transition_rate = 25
        else:
            transition_rate = 30

        if self.mode is None:
            return 0

        part = timestr.split(':')
        if len(part) == 1:
            return int(part[0]) * transition_rate
        elif len(part) == 2:
            return (int(part[0]) * transition_rate) + int(part[1])

    def set_class(self, widget, classname, state):
        if state:
            widget.get_style_context().add_class(classname)
        else:
            widget.get_style_context().remove_class(classname)

    def set_dsk(self, enabled):
        if enabled:
            self.dsk_box.get_style_context().remove_class('hidden')
        else:
            self.dsk_box.get_style_context().add_class('hidden')

    def set_inputs(self, buttons):
        # Clear the existing buttons
        for child in self.program_bus:
            child.destroy()
        for child in self.preview_bus:
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

                    self.program_bus.attach(spacer, left, top, 1, 1)
                    self.preview_bus.attach(pspacer, left, top, 1, 1)
                    continue
                active = button.short_name != ""

                label = Gtk.Label(label=button.short_name)
                link = None
                hwthread = None
                for hwthread, config in self.routers:
                    link = None
                    for output_idx in config['outputs']:
                        output = config['outputs'][output_idx]
                        if output['source'] == button.index:
                            link = output_idx
                    if link is not None:
                        break

                btn = Gtk.Button()
                btn.add(label)
                btn.source_index = button.index
                btn.set_sensitive(active)
                btn.set_size_request(48, 48)
                btn.get_style_context().add_class('bmdbtn')
                btn.router_output = link
                if link is not None:
                    btn.router = hwthread
                    btn.get_style_context().add_class('routable')
                if button.index == self.last_program:
                    btn.get_style_context().add_class('program')
                btn.connect('clicked', self.do_program_input_change)
                btn.connect('button-release-event', self.on_mouse_release)
                self.program_bus.attach(btn, left, top, 1, 1)

                plabel = Gtk.Label(label=button.short_name)
                pbtn = Gtk.Button()
                pbtn.add(plabel)
                pbtn.source_index = button.index
                pbtn.set_sensitive(active)
                pbtn.set_size_request(48, 48)
                pbtn.get_style_context().add_class('bmdbtn')
                pbtn.router_output = link
                if link is not None:
                    pbtn.router = hwthread
                    pbtn.get_style_context().add_class('routable')
                if button.index == self.last_preview:
                    if self.last_preview_in_program:
                        pbtn.get_style_context().add_class('program')
                    else:
                        pbtn.get_style_context().add_class('preview')
                pbtn.connect('clicked', self.do_preview_input_change)
                pbtn.connect('button-release-event', self.on_mouse_release)
                self.preview_bus.attach(pbtn, left, top, 1, 1)

        self.program_bus.show_all()
        self.preview_bus.show_all()

    def on_mouse_release(self, widget, event):
        # Only respond on right click
        if event.button != 3:
            return

        if not hasattr(widget, 'router_output') or widget.router_output is None:
            return

        self.menu = Gtk.Menu()
        for index in widget.router.inputs:
            source = widget.router.inputs[index]
            item = Gtk.MenuItem(source['label'])
            item.router = widget.router
            item.router_output = widget.router_output
            item.router_input = int(index)
            item.connect('activate', self.on_route_change)
            self.menu.append(item)
        self.menu.show_all()
        self.menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())

    def on_route_change(self, widget, *args):
        widget.router.change_route(widget.router_output, widget.router_input)

    def program_input_change(self, data):
        self.last_program = data.source
        for btn in self.program_bus:
            if btn.source_index == data.source:
                btn.get_style_context().add_class('program')
            else:
                btn.get_style_context().remove_class('program')

    def preview_input_change(self, data):
        self.last_preview = data.source
        self.last_preview_in_program = data.in_program
        for btn in self.preview_bus:
            if btn.source_index == data.source:
                if data.in_program:
                    btn.get_style_context().add_class('program')
                else:
                    btn.get_style_context().add_class('preview')
            else:
                btn.get_style_context().remove_class('preview')
                btn.get_style_context().remove_class('program')

    @GObject.Signal(name="program-changed", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int, int),
                    accumulator=GObject.signal_accumulator_true_handled)
    def program_changed(self, *args):
        pass

    @GObject.Signal(name="preview-changed", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int, int),
                    accumulator=GObject.signal_accumulator_true_handled)
    def preview_changed(self, *args):
        pass

    def do_program_input_change(self, widget):
        self.focus_dummy.grab_focus()
        self.emit("program-changed", self.index, widget.source_index)

    def do_preview_input_change(self, widget):
        self.focus_dummy.grab_focus()
        self.emit("preview-changed", self.index, widget.source_index)

    @Gtk.Template.Callback()
    def on_rate_focus(self, *args):
        self.emit('rate-focus')

    @Gtk.Template.Callback()
    def on_rate_unfocus(self, *args):
        self.emit('rate-unfocus')

    @GObject.Signal(name="rate-focus")
    def rate_focus(self, *args):
        self.disable_shortcuts = True

    @GObject.Signal(name="rate-unfocus")
    def rate_unfocus(self, *args):
        self.disable_shortcuts = False
        self.focus_dummy.grab_focus()

    @Gtk.Template.Callback()
    def on_context_menu(self, *args):
        self.log.debug("CONTEXT!")

    @Gtk.Template.Callback()
    def on_ftb_clicked(self, *args):
        self.focus_dummy.grab_focus()
        self.emit('ftb-clicked', self.index)

    @GObject.Signal(name="ftb-clicked", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int,),
                    accumulator=GObject.signal_accumulator_true_handled)
    def ftb_clicked(self, *args):
        pass

    def set_ftb_state(self, done, transitioning):
        self.set_class(self.ftb, 'program', done)
        self.set_class(self.ftb, 'active', transitioning)

    @Gtk.Template.Callback()
    def on_tbar_button_press_event(self, *args):
        self.tbar_held = True

    @Gtk.Template.Callback()
    def on_tbar_button_release_event(self, *args):
        self.tbar_held = False

    @GObject.Signal(name="tbar-position-changed", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int, int),
                    accumulator=GObject.signal_accumulator_true_handled)
    def tbar_position_changed(self, *args):
        pass

    @Gtk.Template.Callback()
    def on_tbar_adj_value_changed(self, widget):
        # Ignore value changes if it's not from the user
        if not self.tbar_held:
            return

        val = widget.get_value()
        if val == 9999.0:
            # Transition done
            widget.set_value(0.0)
            self.tbar.set_inverted(not self.tbar.get_inverted())
            self.transition_progress.set_inverted(self.tbar.get_inverted())
            self.emit("tbar-position-changed", self.index, 0)
        else:
            self.emit("tbar-position-changed", self.index, int(val))

    def set_transition_progress(self, data):
        if data.in_transition:
            self.auto.get_style_context().add_class('program')
        else:
            self.auto.get_style_context().remove_class('program')

        if data.in_transition != self.last_transition_state:
            self.last_transition_state = data.in_transition
            if not data.in_transition:
                # Transition just ended, perform the flip
                self.tbar.set_inverted(not self.tbar.get_inverted())
                self.transition_progress.set_inverted(self.tbar.get_inverted())
                self.tbar_adj.set_value(0.0)

        self.transition_progress.set_fraction(data.position / 9999)
        if not self.tbar_held:
            self.tbar_adj.set_value(data.position)

    @GObject.Signal(name="auto-rate-changed", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int, str, int),
                    accumulator=GObject.signal_accumulator_true_handled)
    def auto_rate_changed(self, *args):
        pass

    @Gtk.Template.Callback()
    def on_auto_rate_activate(self, *args):
        style = None

        # Get current transition style
        if self.style_mix.get_style_context().has_class('active'):
            style = 'mix'
        elif self.style_dip.get_style_context().has_class('active'):
            style = 'dip'
        elif self.style_wipe.get_style_context().has_class('active'):
            style = 'wipe'
        elif self.style_sting.get_style_context().has_class('active'):
            style = 'sting'
        elif self.style_dve.get_style_context().has_class('active'):
            style = 'dve'

        # Try to parse the new rate, on failure restore last rate
        try:
            frames = self.time_to_frames(self.auto_rate.get_text())
        except Exception as e:
            if style is not None:
                self.auto_rate.set_text(self.rate[style])
            self.log.error(e)
            return

        # Send new rate
        self.emit('auto-rate-changed', self.index, style, frames)

        # Remove focus from the entry so the keyboard shortcuts start working again
        self.focus_dummy.grab_focus()

    def set_auto_rate(self, style, rate):
        label = self.frames_to_time(rate)
        self.rate[style] = label
        active = False
        if style == 'mix' and self.style_mix.get_style_context().has_class('active'):
            active = True
        elif style == 'dip' and self.style_dip.get_style_context().has_class('active'):
            active = True
        elif style == 'wipe' and self.style_wipe.get_style_context().has_class('active'):
            active = True
        elif style == 'sting' and self.style_sting.get_style_context().has_class('active'):
            active = True
        elif style == 'dve' and self.style_dve.get_style_context().has_class('active'):
            active = True

        if active:
            self.auto_rate.set_text(label)

    def set_transition_settings(self, data):
        self.set_class(self.style_mix, 'active', data.style == TransitionSettingsField.STYLE_MIX)
        self.set_class(self.style_dip, 'active', data.style == TransitionSettingsField.STYLE_DIP)
        self.set_class(self.style_wipe, 'active', data.style == TransitionSettingsField.STYLE_WIPE)
        self.set_class(self.style_sting, 'active', data.style == TransitionSettingsField.STYLE_STING)
        self.set_class(self.style_dve, 'active', data.style == TransitionSettingsField.STYLE_DVE)

        self.set_class(self.next_bkgd, 'active', data.next_transition_bkgd)
        self.set_class(self.next_key1, 'active', data.next_transition_key1)
        self.set_class(self.next_key2, 'active', data.next_transition_key2)
        self.set_class(self.next_key3, 'active', data.next_transition_key3)
        self.set_class(self.next_key4, 'active', data.next_transition_key4)

        if data.style == TransitionSettingsField.STYLE_MIX:
            self.auto_rate.set_text(self.rate['mix'])
        elif data.style == TransitionSettingsField.STYLE_DIP:
            self.auto_rate.set_text(self.rate['dip'])
        elif data.style == TransitionSettingsField.STYLE_WIPE:
            self.auto_rate.set_text(self.rate['wipe'])
        elif data.style == TransitionSettingsField.STYLE_STING:
            self.auto_rate.set_text(self.rate['sting'])
        elif data.style == TransitionSettingsField.STYLE_DVE:
            self.auto_rate.set_text(self.rate['dve'])

    @GObject.Signal(name="auto-clicked", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int,),
                    accumulator=GObject.signal_accumulator_true_handled)
    def auto_clicked(self, *args):
        pass

    @Gtk.Template.Callback()
    def on_auto_clicked(self, *args):
        self.emit('auto-clicked', self.index)
        self.focus_dummy.grab_focus()

    @GObject.Signal(name="cut-clicked", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int,),
                    accumulator=GObject.signal_accumulator_true_handled)
    def cut_clicked(self, *args):
        pass

    @Gtk.Template.Callback()
    def on_cut_clicked(self, *args):
        self.emit('cut-clicked', self.index)
        self.focus_dummy.grab_focus()

    @GObject.Signal(name="preview-transition-clicked", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int, bool),
                    accumulator=GObject.signal_accumulator_true_handled)
    def prev_trans_clicked(self, *args):
        pass

    @Gtk.Template.Callback()
    def on_prev_trans_clicked(self, widget):
        current = widget.get_style_context().has_class('program')
        self.emit('preview-transition-clicked', self.index, not current)
        self.focus_dummy.grab_focus()

    def set_preview_transition(self, enabled):
        self.set_class(self.prev_trans, 'program', enabled)

    @GObject.Signal(name="style-changed", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int, str),
                    accumulator=GObject.signal_accumulator_true_handled)
    def style_changed(self, *args):
        pass

    @Gtk.Template.Callback()
    def on_style_mix_clicked(self, *args):
        self.emit('style-changed', self.index, 'mix')
        self.focus_dummy.grab_focus()

    @Gtk.Template.Callback()
    def on_style_dip_clicked(self, *args):
        self.emit('style-changed', self.index, 'dip')
        self.focus_dummy.grab_focus()

    @Gtk.Template.Callback()
    def on_style_wipe_clicked(self, *args):
        self.emit('style-changed', self.index, 'wipe')
        self.focus_dummy.grab_focus()

    @Gtk.Template.Callback()
    def on_style_sting_clicked(self, *args):
        self.emit('style-changed', self.index, 'sting')
        self.focus_dummy.grab_focus()

    @Gtk.Template.Callback()
    def on_style_dve_clicked(self, *args):
        self.emit('style-changed', self.index, 'dve')
        self.focus_dummy.grab_focus()

    def set_key_on_air(self, data):
        if data.keyer == 0:
            self.set_class(self.onair_key1, 'program', data.enabled)
        elif data.keyer == 1:
            self.set_class(self.onair_key2, 'program', data.enabled)
        elif data.keyer == 2:
            self.set_class(self.onair_key3, 'program', data.enabled)
        elif data.keyer == 4:
            self.set_class(self.onair_key4, 'program', data.enabled)

    @GObject.Signal(name="onair-clicked", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int, int, bool),
                    accumulator=GObject.signal_accumulator_true_handled)
    def onair_clicked(self, *args):
        pass

    @Gtk.Template.Callback()
    def on_onair_key1_clicked(self, widget):
        enabled = not widget.get_style_context().has_class('program')
        self.emit('onair-clicked', self.index, 0, enabled)
        self.focus_dummy.grab_focus()

    @Gtk.Template.Callback()
    def on_onair_key2_clicked(self, widget):
        enabled = not widget.get_style_context().has_class('program')
        self.emit('onair-clicked', self.index, 1, enabled)
        self.focus_dummy.grab_focus()

    @Gtk.Template.Callback()
    def on_onair_key3_clicked(self, widget):
        enabled = not widget.get_style_context().has_class('program')
        self.emit('onair-clicked', self.index, 2, enabled)
        self.focus_dummy.grab_focus()

    @Gtk.Template.Callback()
    def on_onair_key4_clicked(self, widget):
        enabled = not widget.get_style_context().has_class('program')
        self.emit('onair-clicked', self.index, 3, enabled)
        self.focus_dummy.grab_focus()

    @GObject.Signal(name="next-clicked", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int, int),
                    accumulator=GObject.signal_accumulator_true_handled)
    def next_clicked(self, *args):
        pass

    @Gtk.Template.Callback()
    def on_next_clicked(self, widget):
        if widget.get_style_context().has_class('active'):
            widget.get_style_context().remove_class('active')
        else:
            widget.get_style_context().add_class('active')

        current = 0
        if self.next_bkgd.get_style_context().has_class('active'):
            current |= (1 << 0)
        if self.next_key1.get_style_context().has_class('active'):
            current |= (1 << 1)
        if self.next_key2.get_style_context().has_class('active'):
            current |= (1 << 2)
        if self.next_key3.get_style_context().has_class('active'):
            current |= (1 << 3)
        if self.next_key4.get_style_context().has_class('active'):
            current |= (1 << 4)

        self.emit('next-clicked', self.index, current)
        self.focus_dummy.grab_focus()

    def set_topology(self, data):
        for child in self.dsks:
            child.destroy()

        for i in range(0, data.downstream_keyers):
            tie_label = Gtk.Label(label=_("TIE"))
            tie = Gtk.Button()
            tie.add(tie_label)
            tie.dsk_tie = i
            tie.set_size_request(48, 48)
            tie.get_style_context().add_class('bmdbtn')
            tie.connect('clicked', self.do_dsk_tie_clicked)
            self.dsks.attach(tie, i, 0, 1, 1)

            rate_label = Gtk.Label(label=_("rate"))
            rate_label.get_style_context().add_class('dim-label')
            rate_label.get_style_context().add_class('rate')
            rate_entry = Gtk.Entry()
            rate_entry.get_style_context().add_class('rate')
            rate_entry.set_size_request(48, 0)
            rate_entry.set_width_chars(5)
            rate_entry.set_max_width_chars(5)
            rate_entry.set_alignment(0.5)
            rate_entry.connect('focus-in-event', self.on_rate_focus)
            rate_entry.connect('focus-out-event', self.on_rate_unfocus)
            rate_entry.connect('activate', self.do_dsk_rate_activate)
            rate_entry.dsk_rate = i
            rate_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            rate_box.pack_start(rate_label, 1, 1, 1)
            rate_box.dsk_rate_box = i
            rate_box.pack_start(rate_entry, 1, 1, 1)
            self.dsks.attach(rate_box, i, 1, 1, 1)

            air_label = Gtk.Label(label=_("ON\nAIR"))
            air = Gtk.Button()
            air.add(air_label)
            air.dsk_onair = i
            air.set_size_request(48, 48)
            air.get_style_context().add_class('bmdbtn')
            air.connect('clicked', self.do_dsk_onair_clicked)
            self.dsks.attach(air, i, 2, 1, 1)

            auto_label = Gtk.Label(label=_("AUTO"))
            auto = Gtk.Button()
            auto.add(auto_label)
            auto.dsk_auto = i
            auto.set_size_request(48, 48)
            auto.get_style_context().add_class('bmdbtn')
            auto.connect('clicked', self.do_dsk_auto_clicked)
            self.dsks.attach(auto, i, 3, 1, 1)
        self.dsks.show_all()

    def set_dsk(self, data):
        for child in self.dsks:
            if hasattr(child, 'dsk_tie') and child.dsk_tie == data.index:
                self.set_class(child, 'active', data.tie)
            if hasattr(child, 'dsk_rate_box') and child.dsk_rate_box == data.index:
                for bc in child:
                    if hasattr(bc, 'dsk_rate'):
                        label = self.frames_to_time(data.rate)
                        bc.set_text(label)

    def set_dsk_state(self, data):
        for child in self.dsks:
            if hasattr(child, 'dsk_onair') and child.dsk_onair == data.index:
                self.set_class(child, 'program', data.on_air)
            if hasattr(child, 'dsk_auto') and child.dsk_auto == data.index:
                self.set_class(child, 'active', data.is_autotransitioning)

    @GObject.Signal(name="dsk-tie", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int, int, bool),
                    accumulator=GObject.signal_accumulator_true_handled)
    def dsk_tie_clicked(self, *args):
        pass

    def do_dsk_tie_clicked(self, widget, *args):
        state = not widget.get_style_context().has_class('active')
        self.emit('dsk-tie', self.index, widget.dsk_tie, state)
        self.focus_dummy.grab_focus()

    @GObject.Signal(name="dsk-onair", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int, int, bool),
                    accumulator=GObject.signal_accumulator_true_handled)
    def dsk_onair_clicked(self, *args):
        pass

    def do_dsk_onair_clicked(self, widget):
        state = not widget.get_style_context().has_class('program')
        self.focus_dummy.grab_focus()
        self.emit('dsk-onair', self.index, widget.dsk_onair, state)

    @GObject.Signal(name="dsk-auto", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int, int),
                    accumulator=GObject.signal_accumulator_true_handled)
    def dsk_auto_clicked(self, *args):
        pass

    def do_dsk_auto_clicked(self, widget):
        self.focus_dummy.grab_focus()
        self.emit('dsk-auto', self.index, widget.dsk_auto)

    @GObject.Signal(name="dsk-rate", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int, int, int),
                    accumulator=GObject.signal_accumulator_true_handled)
    def dsk_rate_changed(self, *args):
        pass

    def do_dsk_rate_activate(self, widget, *args):
        # Try to parse the new rate
        try:
            frames = self.time_to_frames(widget.get_text())
        except Exception as e:
            self.log.error(e)
            return
        self.emit('dsk-rate', self.index, widget.dsk_rate, frames)
        self.focus_dummy.grab_focus()

    @GObject.Signal(name="ftb-rate", flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(int, int),
                    accumulator=GObject.signal_accumulator_true_handled)
    def ftb_rate_changed(self, *args):
        pass

    @Gtk.Template.Callback()
    def on_ftb_rate_activate(self, widget, *args):
        # Try to parse the new rate
        try:
            frames = self.time_to_frames(widget.get_text())
        except Exception as e:
            self.log.error(e)
            return
        self.emit('ftb-rate', self.index, frames)
        self.focus_dummy.grab_focus()

    def set_ftb_rate(self, frames):
        label = self.frames_to_time(frames)
        self.ftb_rate.set_text(label)

    def set_config(self, data):
        self.next_key1.set_sensitive(data.keyers > 0)
        self.next_key2.set_sensitive(data.keyers > 1)
        self.next_key3.set_sensitive(data.keyers > 2)
        self.next_key4.set_sensitive(data.keyers > 3)

        self.onair_key1.set_sensitive(data.keyers > 0)
        self.onair_key2.set_sensitive(data.keyers > 1)
        self.onair_key3.set_sensitive(data.keyers > 2)
        self.onair_key4.set_sensitive(data.keyers > 3)

    def add_router(self, hwthread, config):
        self.routers.append((hwthread, config))
        for btn in list(self.program_bus) + list(self.preview_bus):
            link = None
            for output_idx in config['outputs']:
                output = config['outputs'][output_idx]
                if output['source'] == btn.source_index:
                    link = output_idx
            btn.router_output = link
            if link is not None:
                btn.router = hwthread
                btn.get_style_context().add_class('routable')
            else:
                btn.get_style_context().remove_class('routable')
