from pyatem.command import CutCommand, AutoCommand, FadeToBlackCommand, TransitionSettingsCommand, WipeSettingsCommand, \
    TransitionPositionCommand, TransitionPreviewCommand, ColorGeneratorCommand, MixSettingsCommand, DipSettingsCommand, \
    DveSettingsCommand, FairlightMasterPropertiesCommand, DkeyRateCommand, DkeyAutoCommand, DkeyTieCommand, \
    DkeyOnairCommand, ProgramInputCommand, PreviewInputCommand
from pyatem.field import TransitionSettingsField, InputPropertiesField

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk

gi.require_version('Handy', '1')
from gi.repository import Handy


class SwitcherPage:
    def __init__(self, builder):
        self.program_bus = builder.get_object('program')
        self.preview_bus = builder.get_object('preview')

        self.dsks = builder.get_object('dsks')
        self.tbar = builder.get_object('tbar')
        self.tbar_adj = builder.get_object('tbar_adj')
        self.tbar.adj = self.tbar_adj
        self.tbar.is_tbar = True
        self.tbar_held = False
        self.transition_progress = builder.get_object('transition_progress')
        self.last_transition_state = False
        self.auto = builder.get_object('auto')
        self.auto_rate = builder.get_object('auto_rate')
        self.mix_rate = builder.get_object('mix_rate')
        self.dip_rate = builder.get_object('dip_rate')
        self.wipe_rate = builder.get_object('wipe_rate')
        self.dve_rate = builder.get_object('dve_rate')
        self.ftb_rate = builder.get_object('ftb_rate')
        self.dip_source = builder.get_object('dip_source')
        self.wipe_symmetry_adj = builder.get_object('wipe_symmetry_adj')
        self.wipe_x_adj = builder.get_object('wipe_x_adj')
        self.wipe_y_adj = builder.get_object('wipe_y_adj')
        self.wipe_width_adj = builder.get_object('wipe_width_adj')
        self.wipe_softness_adj = builder.get_object('wipe_softness_adj')
        self.wipe_fill = builder.get_object('wipe_fill')
        self.wipe_reverse = builder.get_object('wipe_reverse')
        self.wipe_flipflop = builder.get_object('wipe_flipflop')

        self.style_mix = builder.get_object('style_mix')
        self.style_dip = builder.get_object('style_dip')
        self.style_wipe = builder.get_object('style_wipe')
        self.style_sting = builder.get_object('style_sting')
        self.style_dve = builder.get_object('style_dve')
        self.next_bkgd = builder.get_object('next_bkgd')
        self.next_key1 = builder.get_object('next_key1')
        self.next_key2 = builder.get_object('next_key2')
        self.next_key3 = builder.get_object('next_key3')
        self.next_key4 = builder.get_object('next_key4')

        self.ftb_afv = builder.get_object('ftb_afv')

        self.onair_key1 = builder.get_object('onair_key1')
        self.onair_key2 = builder.get_object('onair_key2')
        self.onair_key3 = builder.get_object('onair_key3')
        self.onair_key4 = builder.get_object('onair_key4')

        self.focus_dummy = builder.get_object('focus_dummy')
        self.prev_trans = builder.get_object('prev_trans')
        self.wipe_style = [
            builder.get_object('wipestyle_h'),
            builder.get_object('wipestyle_v'),
            builder.get_object('wipestyle_mh'),
            builder.get_object('wipestyle_mv'),
            builder.get_object('wipestyle_cross'),
            builder.get_object('wipestyle_box'),
            builder.get_object('wipestyle_diamond'),
            builder.get_object('wipestyle_iris'),
            builder.get_object('wipestyle_box_tl'),
            builder.get_object('wipestyle_box_tr'),
            builder.get_object('wipestyle_box_br'),
            builder.get_object('wipestyle_box_bl'),
            builder.get_object('wipestyle_box_top'),
            builder.get_object('wipestyle_box_right'),
            builder.get_object('wipestyle_box_bottom'),
            builder.get_object('wipestyle_box_left'),
            builder.get_object('wipestyle_diag1'),
            builder.get_object('wipestyle_diag2'),
        ]

        for style, button in enumerate(self.wipe_style):
            button.pattern = style
            button.connect('pressed', self.on_wipe_pattern_clicked)

        self.color1 = builder.get_object('color1')
        self.color2 = builder.get_object('color2')

        self.ftb = builder.get_object('ftb')

        self.model_me1_fill = builder.get_object('model_me1_fill')
        self.model_key = builder.get_object('model_key')
        self.model_changing = False
        self.slider_held = False

        self.rate = {
            'mix': '0:00',
            'dip': '0:00',
            'wipe': '0:00',
            'sting': '0:00',
            'dve': '0:00'
        }

    def on_tbar_button_press_event(self, widget, *args):
        self.tbar_held = True

    def on_tbar_button_release_event(self, widget, *args):
        self.tbar_held = False

    def on_cut_clicked(self, widget, *args):
        print("CUT!")
        cmd = CutCommand(index=0)
        self.connection.mixer.send_commands([cmd])

    def on_auto_clicked(self, widget, *args):
        if len(args) > 0 and self.disable_shortcuts:
            return
        cmd = AutoCommand(index=0)
        self.connection.mixer.send_commands([cmd])

    def on_ftb_clicked(self, widget):
        cmd = FadeToBlackCommand(index=0)
        self.connection.mixer.send_commands([cmd])

    def on_style_mix_clicked(self, widget):
        cmd = TransitionSettingsCommand(index=0, style=TransitionSettingsField.STYLE_MIX)
        self.connection.mixer.send_commands([cmd])

    def on_style_dip_clicked(self, widget):
        cmd = TransitionSettingsCommand(index=0, style=TransitionSettingsField.STYLE_DIP)
        self.connection.mixer.send_commands([cmd])

    def on_style_wipe_clicked(self, widget):
        cmd = TransitionSettingsCommand(index=0, style=TransitionSettingsField.STYLE_WIPE)
        self.connection.mixer.send_commands([cmd])

    def on_style_sting_clicked(self, widget):
        cmd = TransitionSettingsCommand(index=0, style=TransitionSettingsField.STYLE_STING)
        self.connection.mixer.send_commands([cmd])

    def on_style_dve_clicked(self, widget):
        cmd = TransitionSettingsCommand(index=0, style=TransitionSettingsField.STYLE_DVE)
        self.connection.mixer.send_commands([cmd])

    def on_wipe_pattern_clicked(self, widget):
        cmd = WipeSettingsCommand(index=0, pattern=widget.pattern)
        self.connection.mixer.send_commands([cmd])

    def on_tbar_adj_value_changed(self, widget):
        # Ignore value changes if it's not from the user
        if not self.tbar_held:
            return

        val = widget.get_value() / 100.0
        if val == 1.0:
            # Transition done
            widget.set_value(0.0)
            self.tbar.set_inverted(not self.tbar.get_inverted())
            self.transition_progress.set_inverted(self.tbar.get_inverted())
            cmd = TransitionPositionCommand(index=0, position=0)
        else:
            cmd = TransitionPositionCommand(index=0, position=val)
        self.connection.mixer.send_commands([cmd])

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

        cmd = TransitionSettingsCommand(index=0, next_transition=current)
        self.connection.mixer.send_commands([cmd])

    def on_prev_trans_clicked(self, widget):
        current = widget.get_style_context().has_class('program')
        cmd = TransitionPreviewCommand(index=0, enabled=not current)
        self.connection.mixer.send_commands([cmd])

    def on_color1_color_set(self, widget):
        color = widget.get_rgba()
        cmd = ColorGeneratorCommand.from_rgb(index=0, red=color.red, green=color.green, blue=color.blue)
        self.connection.mixer.send_commands([cmd])

    def on_color2_color_set(self, widget):
        color = widget.get_rgba()
        cmd = ColorGeneratorCommand.from_rgb(index=1, red=color.red, green=color.green, blue=color.blue)
        self.connection.mixer.send_commands([cmd])

    def on_auto_rate_activate(self, widget, *args):
        cmd = None
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
            print(e)
            return

        # Send new rate to the mixer
        if style == 'mix':
            cmd = MixSettingsCommand(index=0, rate=frames)
        elif style == 'dip':
            cmd = DipSettingsCommand(index=0, rate=frames)
        elif style == 'wipe':
            cmd = WipeSettingsCommand(index=0, rate=frames)
        elif style == 'dve':
            cmd = DveSettingsCommand(index=0, rate=frames)
        if cmd is not None:
            self.connection.mixer.send_commands([cmd])

        # Remove focus from the entry so the keyboard shortcuts start working again
        self.focus_dummy.grab_focus()

    def on_dip_source_changed(self, widget):
        if hasattr(widget, 'ignore_change') and widget.ignore_change or self.model_changing:
            return
        cmd = DipSettingsCommand(index=0, source=int(self.dip_source.get_active_id()))
        self.connection.mixer.send_commands([cmd])

    def on_wipe_symmetry_adj_value_changed(self, widget, *args):
        cmd = WipeSettingsCommand(index=0, symmetry=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    def on_wipe_x_adj_value_changed(self, widget, *args):
        cmd = WipeSettingsCommand(index=0, positionx=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    def on_wipe_y_adj_value_changed(self, widget, *args):
        cmd = WipeSettingsCommand(index=0, positiony=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    def on_wipe_width_adj_value_changed(self, widget, *args):
        cmd = WipeSettingsCommand(index=0, width=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    def on_wipe_softness_adj_value_changed(self, widget, *args):
        cmd = WipeSettingsCommand(index=0, softness=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    def on_wipe_fill_changed(self, widget, *args):
        if hasattr(widget, 'ignore_change') and widget.ignore_change or self.model_changing:
            return
        cmd = WipeSettingsCommand(index=0, source=int(widget.get_active_id()))
        self.connection.mixer.send_commands([cmd])
        self.focus_dummy.grab_focus()

    def on_wipe_flipflop_clicked(self, widget, *args):
        state = widget.get_style_context().has_class('active')
        cmd = WipeSettingsCommand(index=0, flipflop=not state)
        self.connection.mixer.send_commands([cmd])

    def on_wipe_reverse_clicked(self, widget, *args):
        state = widget.get_style_context().has_class('active')
        cmd = WipeSettingsCommand(index=0, reverse=not state)
        self.connection.mixer.send_commands([cmd])

    def on_ftb_afv_clicked(self, widget, *args):
        cmd = FairlightMasterPropertiesCommand(afv=not widget.get_style_context().has_class('active'))
        self.connection.mixer.send_commands([cmd])

    def on_rate_focus(self, *args):
        self.disable_shortcuts = True

    def on_rate_unfocus(self, *args):
        self.disable_shortcuts = False

    def on_slider_held(self, *args):
        self.slider_held = True

    def on_slider_released(self, *args):
        self.slider_held = False

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

    def on_ftb_change(self, data):
        label = self.frames_to_time(data.rate)
        self.ftb_rate.set_text(label)

    def on_transition_mix_change(self, data):
        label = self.frames_to_time(data.rate)
        self.mix_rate.set_text(label)
        self.rate['mix'] = label
        if self.style_mix.get_style_context().has_class('active'):
            self.auto_rate.set_text(label)

    def on_transition_dip_change(self, data):
        label = self.frames_to_time(data.rate)
        self.dip_rate.set_text(label)
        self.dip_source.ignore_change = True
        self.dip_source.set_active_id(str(data.source))
        self.dip_source.ignore_change = False
        self.rate['dip'] = label
        if self.style_dip.get_style_context().has_class('active'):
            self.auto_rate.set_text(label)

    def on_transition_wipe_change(self, data):
        label = self.frames_to_time(data.rate)
        self.wipe_rate.set_text(label)
        self.rate['wipe'] = label
        if self.style_wipe.get_style_context().has_class('active'):
            self.auto_rate.set_text(label)

        for style, button in enumerate(self.wipe_style):
            self.set_class(button, 'stylebtn', True)
            self.set_class(button, 'active', style == data.pattern)

        if not self.slider_held:
            self.wipe_symmetry_adj.set_value(data.symmetry)
            self.wipe_x_adj.set_value(data.positionx)
            self.wipe_y_adj.set_value(data.positiony)
            self.wipe_width_adj.set_value(data.width)
            self.wipe_softness_adj.set_value(data.softness)

        self.model_changing = True
        self.wipe_fill.set_active_id(str(data.source))
        self.model_changing = False

        self.wipe_fill.set_sensitive(data.width > 0)
        self.set_class(self.wipe_reverse, 'active', data.reverse)
        self.set_class(self.wipe_flipflop, 'active', data.flipflop)

    def on_transition_dve_change(self, data):
        label = self.frames_to_time(data.rate)
        self.dve_rate.set_text(label)
        self.rate['dve'] = label
        if self.style_dve.get_style_context().has_class('active'):
            self.auto_rate.set_text(label)

    def on_mediaplayer_slots_change(self, data):
        for child in self.media_flow:
            child.destroy()

        for i in range(0, data.stills):
            slot = Gtk.Box()
            slot_label = Gtk.Label(label=str(i + 1))
            slot_label.get_style_context().add_class('dim-label')
            slot.pack_start(slot_label, False, False, False)

            slot_img = Gtk.Box()
            slot_img.get_style_context().add_class('mp-slot')
            slot_img.set_size_request(160, 120)
            slot.pack_start(slot_img, False, False, False)

            self.media_flow.add(slot)
        self.media_flow.show_all()

    def on_dsk_change(self, data):
        for child in self.dsks:
            if hasattr(child, 'dsk_tie') and child.dsk_tie == data.index:
                self.set_class(child, 'active', data.tie)
            if hasattr(child, 'dsk_rate_box') and child.dsk_rate_box == data.index:
                for bc in child:
                    if hasattr(bc, 'dsk_rate'):
                        label = self.frames_to_time(data.rate)
                        bc.set_text(label)

    def on_dsk_state_change(self, data):
        for child in self.dsks:
            if hasattr(child, 'dsk_onair') and child.dsk_onair == data.index:
                self.set_class(child, 'program', data.on_air)
            if hasattr(child, 'dsk_auto') and child.dsk_auto == data.index:
                self.set_class(child, 'active', data.is_autotransitioning)

    def on_topology_change(self, data):
        for child in self.dsks:
            child.destroy()

        for i in range(0, data.downstream_keyers):
            tie_label = Gtk.Label(label="TIE")
            tie = Gtk.Button()
            tie.add(tie_label)
            tie.dsk_tie = i
            tie.set_size_request(48, 48)
            tie.get_style_context().add_class('bmdbtn')
            tie.connect('clicked', self.do_dsk_tie_clicked)
            self.dsks.attach(tie, i, 0, 1, 1)

            rate_label = Gtk.Label(label="rate")
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

            air_label = Gtk.Label(label="ON\nAIR")
            air = Gtk.Button()
            air.add(air_label)
            air.dsk_onair = i
            air.set_size_request(48, 48)
            air.get_style_context().add_class('bmdbtn')
            air.connect('clicked', self.do_dsk_onair_clicked)
            self.dsks.attach(air, i, 2, 1, 1)

            auto_label = Gtk.Label(label="AUTO")
            auto = Gtk.Button()
            auto.add(auto_label)
            auto.dsk_auto = i
            auto.set_size_request(48, 48)
            auto.get_style_context().add_class('bmdbtn')
            auto.connect('clicked', self.do_dsk_auto_clicked)
            self.dsks.attach(auto, i, 3, 1, 1)
        self.apply_css(self.dsks, self.provider)
        self.dsks.show_all()

    def do_dsk_tie_clicked(self, widget):
        state = widget.get_style_context().has_class('active')
        cmd = DkeyTieCommand(index=widget.dsk_tie, tie=not state)
        self.connection.mixer.send_commands([cmd])

    def do_dsk_onair_clicked(self, widget):
        state = widget.get_style_context().has_class('program')
        cmd = DkeyOnairCommand(index=widget.dsk_onair, on_air=not state)
        self.connection.mixer.send_commands([cmd])

    def do_dsk_rate_activate(self, widget):
        # Try to parse the new rate
        try:
            frames = self.time_to_frames(widget.get_text())
        except Exception as e:
            print(e)
            return

        cmd = DkeyRateCommand(index=widget.dsk_rate, rate=frames)
        self.connection.mixer.send_commands([cmd])
        self.focus_dummy.grab_focus()

    def do_dsk_auto_clicked(self, widget):
        cmd = DkeyAutoCommand(index=widget.dsk_auto)
        self.connection.mixer.send_commands([cmd])

    def on_mixer_effect_config_change(self, data):
        # Only M/E 1 is supported
        if data.me != 0:
            return

        self.next_key1.set_sensitive(data.keyers > 0)
        self.next_key2.set_sensitive(data.keyers > 1)
        self.next_key3.set_sensitive(data.keyers > 2)
        self.next_key4.set_sensitive(data.keyers > 3)

        self.onair_key1.set_sensitive(data.keyers > 0)
        self.onair_key2.set_sensitive(data.keyers > 1)
        self.onair_key3.set_sensitive(data.keyers > 2)
        self.onair_key4.set_sensitive(data.keyers > 3)

    def on_ftb_state_change(self, data):
        self.set_class(self.ftb, 'program', data.done)
        self.set_class(self.ftb, 'active', data.transitioning)

    def on_color_change(self, data):
        r, g, b = data.get_rgb()
        color = Gdk.RGBA()
        color.red = r
        color.green = g
        color.blue = b
        color.alpha = 1.0

        if data.index == 0:
            self.color1.set_rgba(color)
        else:
            self.color2.set_rgba(color)

    def on_key_on_air_change(self, data):
        # support only M/E 1
        if data.index != 0:
            return

        if data.keyer == 0:
            self.set_class(self.onair_key1, 'program', data.enabled)
        elif data.keyer == 1:
            self.set_class(self.onair_key2, 'program', data.enabled)
        elif data.keyer == 2:
            self.set_class(self.onair_key3, 'program', data.enabled)
        elif data.keyer == 4:
            self.set_class(self.onair_key4, 'program', data.enabled)

    def on_transition_preview_change(self, data):
        # support only M/E 1
        if data.index != 0:
            return

        self.set_class(self.prev_trans, 'program', data.enabled)

    def on_transition_settings_change(self, data):
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

    def on_transition_position_change(self, data):
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

        self.transition_progress.set_fraction(data.position)
        if not self.tbar_held:
            self.tbar_adj.set_value(data.position * 100.0)

    def on_program_input_change(self, data):
        # support only M/E 1
        if data.index != 0:
            return

        for btn in self.program_bus:
            if btn.source_index == data.source:
                btn.get_style_context().add_class('program')
            else:
                btn.get_style_context().remove_class('program')

    def on_preview_input_change(self, data):
        # support only M/E 1
        if data.index != 0:
            return

        for btn in self.preview_bus:
            if btn.source_index == data.source:
                if data.in_program:
                    btn.get_style_context().add_class('program')
                else:
                    btn.get_style_context().add_class('preview')
            else:
                btn.get_style_context().remove_class('preview')
                btn.get_style_context().remove_class('program')

    def do_program_input_change(self, widget):
        cmd = ProgramInputCommand(index=0, source=widget.source_index)
        self.connection.mixer.send_commands([cmd])

    def do_preview_input_change(self, widget):
        cmd = PreviewInputCommand(index=0, source=widget.source_index)
        self.connection.mixer.send_commands([cmd])

    def on_input_layout_change(self, changed_input):
        inputs = self.connection.mixer.mixerstate['input-properties']
        external = []
        colors = []
        mp = []
        black = None
        bars = None

        # Clear the combobox models
        self.model_changing = True
        self.model_me1_fill.clear()
        self.model_key.clear()

        for i in inputs.values():
            if i.port_type == InputPropertiesField.PORT_EXTERNAL:
                external.append(i)
            if i.port_type == InputPropertiesField.PORT_COLOR:
                colors.append(i)
            if i.port_type == InputPropertiesField.PORT_MEDIAPLAYER and i.available_me1:
                mp.append(i)
            if i.port_type == InputPropertiesField.PORT_BLACK:
                black = i
            if i.port_type == InputPropertiesField.PORT_BARS:
                bars = i

            if i.available_me1:
                self.model_me1_fill.append([str(i.index), i.name])
            if i.available_key_source:
                self.model_key.append([str(i.index), i.name])

        row1_ext = external
        row2_ext = [None] * len(external)
        if len(external) > 4:
            num = len(external) // 2
            row1_ext = external[0:num]
            row2_ext = external[num:] + [None] * ((2 * num) - len(external))

        row1 = row1_ext + [None, black, None] + colors
        row2 = row2_ext + [None, bars, None] + mp

        buttons = [row1, row2]

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

                btn = Gtk.Button()
                btn.add(label)
                btn.source_index = button.index
                btn.set_sensitive(active)
                btn.set_size_request(48, 48)
                btn.get_style_context().add_class('bmdbtn')
                btn.connect('clicked', self.do_program_input_change)
                self.program_bus.attach(btn, left, top, 1, 1)

                plabel = Gtk.Label(label=button.short_name)
                pbtn = Gtk.Button()
                pbtn.add(plabel)
                pbtn.source_index = button.index
                pbtn.set_sensitive(active)
                pbtn.set_size_request(48, 48)
                pbtn.get_style_context().add_class('bmdbtn')
                pbtn.connect('clicked', self.do_preview_input_change)
                self.preview_bus.attach(pbtn, left, top, 1, 1)

        self.apply_css(self.program_bus, self.provider)
        self.apply_css(self.preview_bus, self.provider)

        self.program_bus.show_all()
        self.preview_bus.show_all()

        self.model_changing = False
