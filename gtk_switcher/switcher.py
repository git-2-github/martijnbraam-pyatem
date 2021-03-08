from gtk_switcher.layout import LayoutView
from pyatem.command import CutCommand, AutoCommand, FadeToBlackCommand, TransitionSettingsCommand, WipeSettingsCommand, \
    TransitionPositionCommand, TransitionPreviewCommand, ColorGeneratorCommand, MixSettingsCommand, DipSettingsCommand, \
    DveSettingsCommand, FairlightMasterPropertiesCommand, DkeyRateCommand, DkeyAutoCommand, DkeyTieCommand, \
    DkeyOnairCommand, ProgramInputCommand, PreviewInputCommand, KeyOnAirCommand, KeyFillCommand, \
    FadeToBlackConfigCommand
from pyatem.field import TransitionSettingsField, InputPropertiesField

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk

gi.require_version('Handy', '1')
from gi.repository import Handy


class SwitcherPage:
    def __init__(self, builder):
        self.main_blocks = builder.get_object('main_blocks')
        self.me = []
        self.layout = {}

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

        self.ftb_afv = builder.get_object('ftb_afv')

        self.keyer_stack = builder.get_object('keyer_stack')

        self.usk_count = 0
        self.usks = {}
        self.has_models = []

        self.upstream_keyers = builder.get_object('upstream_keyers')
        self.downstream_keyers = builder.get_object('downstream_keyers')

        self.usk1_dve_fill = builder.get_object('usk1_dve_fill')
        self.usk1_mask_en = builder.get_object('usk1_mask_en')
        self.usk1_mask_top = builder.get_object('usk1_mask_top')
        self.usk1_mask_bottom = builder.get_object('usk1_mask_bottom')
        self.usk1_mask_left = builder.get_object('usk1_mask_left')
        self.usk1_mask_right = builder.get_object('usk1_mask_right')

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

        self.model_me1_fill = builder.get_object('model_me1_fill')
        self.model_key = builder.get_object('model_key')
        self.model_changing = False
        self.slider_held = False

    def add_mixeffect(self):
        from gtk_switcher.mixeffect import MixEffectBlock
        index = len(self.me)
        me = MixEffectBlock(index)
        self.me.append(me)
        me.set_dsk(False)
        self.main_blocks.add(me)

        me.connect('program-changed', self.on_me_program_changed)
        me.connect('preview-changed', self.on_me_preview_changed)
        me.connect('rate-focus', self.on_rate_focus)
        me.connect('rate-unfocus', self.on_rate_unfocus)
        me.connect('ftb-clicked', self.on_ftb_clicked)
        me.connect('ftb-rate', self.on_ftb_rate_changed)
        me.connect('tbar-position-changed', self.on_tbar_position_changed)
        me.connect('auto-rate-changed', self.on_auto_rate_changed)
        me.connect('auto-clicked', self.on_auto_clicked)
        me.connect('cut-clicked', self.on_cut_clicked)
        me.connect('preview-transition-clicked', self.on_prev_trans_clicked)
        me.connect('style-changed', self.on_style_clicked)
        me.connect('onair-clicked', self.on_onair_clicked)
        me.connect('next-clicked', self.on_next_clicked)
        me.connect('dsk-tie', self.on_dsk_tie_clicked)
        me.connect('dsk-onair', self.on_dsk_onair_clicked)
        me.connect('dsk-auto', self.on_dsk_auto_clicked)
        me.connect('dsk-rate', self.on_dsk_rate_activate)

        layout = LayoutView(index, self.connection)
        self.layout[index] = layout
        self.main_blocks.add(layout)

    def on_cut_clicked(self, widget, index):
        cmd = CutCommand(index=index)
        self.connection.mixer.send_commands([cmd])

    def on_auto_clicked(self, widget, index, *args):
        if self.disable_shortcuts and len(args) == 2:
            return

        # When triggered by keyboard shortcut, control M/E 1
        if len(args) != 0:
            index = 0

        cmd = AutoCommand(index=index)
        self.connection.mixer.send_commands([cmd])

    def on_ftb_clicked(self, widget, index):
        cmd = FadeToBlackCommand(index=index)
        self.connection.mixer.send_commands([cmd])

    def on_ftb_rate_changed(self, widget, index, frames):
        cmd = FadeToBlackConfigCommand(index=index, frames=frames)
        self.connection.mixer.send_commands([cmd])

    def on_style_clicked(self, widget, index, style):
        s = None
        if style == 'mix':
            s = TransitionSettingsField.STYLE_MIX
        elif style == 'dip':
            s = TransitionSettingsField.STYLE_DIP
        elif style == 'wipe':
            s = TransitionSettingsField.STYLE_WIPE
        elif style == 'sting':
            s = TransitionSettingsField.STYLE_STING
        elif style == 'dve':
            s = TransitionSettingsField.STYLE_DVE
        cmd = TransitionSettingsCommand(index=index, style=s)
        self.connection.mixer.send_commands([cmd])

    def on_wipe_pattern_clicked(self, widget):
        cmd = WipeSettingsCommand(index=0, pattern=widget.pattern)
        self.connection.mixer.send_commands([cmd])

    def on_tbar_position_changed(self, widget, index, position):
        cmd = TransitionPositionCommand(index=index, position=position)
        self.connection.mixer.send_commands([cmd])

    def on_next_clicked(self, widget, index, current):
        print('next', index, current)
        cmd = TransitionSettingsCommand(index=index, next_transition=current)
        self.connection.mixer.send_commands([cmd])

    def on_prev_trans_clicked(self, widget, index, enabled):
        cmd = TransitionPreviewCommand(index=index, enabled=enabled)
        self.connection.mixer.send_commands([cmd])

    def on_color1_color_set(self, widget):
        color = widget.get_rgba()
        cmd = ColorGeneratorCommand.from_rgb(index=0, red=color.red, green=color.green, blue=color.blue)
        self.connection.mixer.send_commands([cmd])

    def on_color2_color_set(self, widget):
        color = widget.get_rgba()
        cmd = ColorGeneratorCommand.from_rgb(index=1, red=color.red, green=color.green, blue=color.blue)
        self.connection.mixer.send_commands([cmd])

    def on_auto_rate_changed(self, widget, index, style, frames):
        cmd = None
        # Send new rate to the mixer
        if style == 'mix':
            cmd = MixSettingsCommand(index=index, rate=frames)
        elif style == 'dip':
            cmd = DipSettingsCommand(index=index, rate=frames)
        elif style == 'wipe':
            cmd = WipeSettingsCommand(index=index, rate=frames)
        elif style == 'dve':
            cmd = DveSettingsCommand(index=index, rate=frames)
        if cmd is not None:
            self.connection.mixer.send_commands([cmd])

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
        self.me[data.index].set_ftb_rate(data.rate)

    def on_transition_mix_change(self, data):
        label = self.frames_to_time(data.rate)
        self.mix_rate.set_text(label)
        self.me[data.index].set_auto_rate('mix', data.rate)

    def on_transition_dip_change(self, data):
        label = self.frames_to_time(data.rate)
        self.dip_rate.set_text(label)
        self.dip_source.ignore_change = True
        self.dip_source.set_active_id(str(data.source))
        self.dip_source.ignore_change = False
        self.me[data.index].set_auto_rate('dip', data.rate)

    def on_transition_wipe_change(self, data):
        label = self.frames_to_time(data.rate)
        self.wipe_rate.set_text(label)
        self.me[data.index].set_auto_rate('wipe', data.rate)

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
        self.me[data.index].set_auto_rate('dve', data.rate)

    def on_dsk_change(self, data):
        self.me[0].set_dsk(data)

    def on_dsk_state_change(self, data):
        self.me[0].set_dsk_state(data)

    def on_topology_change(self, data):
        for i in range(0, data.me_units - len(self.me)):
            self.add_mixeffect()

        # Topology is only used for downstream keyer count, only available on M/E 1
        self.me[0].set_topology(data)
        self.apply_css(self.me[0], self.provider)

    def on_dsk_tie_clicked(self, widget, index, dsk, enabled):
        cmd = DkeyTieCommand(index=dsk, tie=enabled)
        self.connection.mixer.send_commands([cmd])

    def on_dsk_onair_clicked(self, widget, index, dsk, enabled):
        cmd = DkeyOnairCommand(index=dsk, on_air=enabled)
        self.connection.mixer.send_commands([cmd])

    def on_dsk_rate_activate(self, widget, index, dsk, frames):
        cmd = DkeyRateCommand(index=dsk, rate=frames)
        self.connection.mixer.send_commands([cmd])

    def on_dsk_auto_clicked(self, widget, index, dsk):
        cmd = DkeyAutoCommand(index=dsk)
        self.connection.mixer.send_commands([cmd])

    def on_mixer_effect_config_change(self, data):
        self.me[data.index].set_config(data)

        from gtk_switcher.upstreamkey import UpstreamKeyer

        if data.keyers > self.usk_count:
            add = data.keyers - self.usk_count

            for i in range(0, add):
                self.usk_count += 1
                exp = Gtk.Expander()
                exp.get_style_context().add_class('bmdgroup')
                frame_label = Gtk.Label("Upstream keyer {}".format(self.usk_count))
                frame_label.get_style_context().add_class("heading")
                exp.set_label_widget(frame_label)
                exp.set_expanded(True)
                usk = UpstreamKeyer(index=0, keyer=self.usk_count - 1, connection=self.connection)
                self.usks[usk.index] = usk
                self.has_models.append(usk)
                exp.add(usk)
                self.apply_css(usk, self.provider)
                usk.set_fill_model(self.model_me1_fill)
                usk.set_key_model(self.model_key)
                self.upstream_keyers.pack_start(exp, False, True, 0)

            self.upstream_keyers.show_all()

    def on_ftb_state_change(self, data):
        self.me[data.index].set_ftb_state(data.done, data.transitioning)

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
        self.me[data.index].set_key_on_air(data)
        self.layout[data.index].region_onair('Upstream key {}'.format(data.keyer + 1), data.enabled)

    def on_transition_preview_change(self, data):
        self.me[data.index].set_preview_transition(data.enabled)

    def on_transition_settings_change(self, data):
        self.me[data.index].set_transition_settings(data)

    def on_transition_position_change(self, data):
        self.me[data.index].set_transition_progress(data)

    def on_onair_clicked(self, widget, index, keyer, enabled):
        cmd = KeyOnAirCommand(index=index, keyer=keyer, enabled=enabled)
        self.connection.mixer.send_commands([cmd])

    def on_key_properties_base_change(self, data):
        self.usks[data.index].on_key_properties_base_change(data)

    def on_key_properties_luma_change(self, data):
        self.usks[data.index].on_key_properties_luma_change(data)

    def on_key_properties_dve_change(self, data):
        self.usks[data.keyer].on_key_properties_dve_change(data)
        width = 16.0 * data.size_x / 1000
        height = 9.0 * data.size_y / 1000
        self.layout[data.index].update_region('Upstream key {}'.format(data.keyer + 1),
                                              data.pos_x / 1000, data.pos_y / 1000, width, height)

    def on_program_input_change(self, data):
        self.me[data.index].program_input_change(data)

    def on_preview_input_change(self, data):
        self.me[data.index].preview_input_change(data)

    def on_me_program_changed(self, widget, index, source):
        cmd = ProgramInputCommand(index=index, source=source)
        self.connection.mixer.send_commands([cmd])

    def on_me_preview_changed(self, widget, index, source):
        cmd = PreviewInputCommand(index=index, source=source)
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
        for i in self.has_models:
            i.model_changing = True
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

        for me in self.me:
            me.set_inputs(buttons)
            self.apply_css(me, self.provider)

        self.model_changing = False
        for i in self.has_models:
            i.model_changing = False
