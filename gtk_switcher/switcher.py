# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import gettext
import logging
import re
from datetime import datetime, timedelta

from gtk_switcher.layout import LayoutView
from pyatem.command import CutCommand, AutoCommand, FadeToBlackCommand, TransitionSettingsCommand, WipeSettingsCommand, \
    TransitionPositionCommand, TransitionPreviewCommand, ColorGeneratorCommand, MixSettingsCommand, DipSettingsCommand, \
    DveSettingsCommand, AudioMasterPropertiesCommand, FairlightMasterPropertiesCommand, DkeyRateCommand, \
    DkeyAutoCommand, DkeyTieCommand, \
    DkeyOnairCommand, ProgramInputCommand, PreviewInputCommand, KeyOnAirCommand, KeyFillCommand, \
    FadeToBlackConfigCommand, RecorderStatusCommand, AuxSourceCommand, StreamingServiceSetCommand, \
    RecordingSettingsSetCommand, StreamingStatusSetCommand, MediaplayerSelectCommand, StreamingAudioBitrateCommand
from pyatem.field import TransitionSettingsField, InputPropertiesField, TopologyField
import gtk_switcher.stream_data

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

        self.log_sw = logging.getLogger('SwitcherPage')

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

        self.usks = {}
        self.dsks = {}
        self.has_models = []
        self.menu = None

        self.upstream_keyers = builder.get_object('upstream_keyers')
        self.downstream_keyers = builder.get_object('downstream_keyers')
        self.macro_flow = builder.get_object('macro_flow')

        self.usk1_dve_fill = builder.get_object('usk1_dve_fill')
        self.usk1_mask_en = builder.get_object('usk1_mask_en')
        self.usk1_mask_top = builder.get_object('usk1_mask_top')
        self.usk1_mask_bottom = builder.get_object('usk1_mask_bottom')
        self.usk1_mask_left = builder.get_object('usk1_mask_left')
        self.usk1_mask_right = builder.get_object('usk1_mask_right')

        self.expander_stream_recorder = builder.get_object('expander_stream_recorder')
        self.expander_livestream = builder.get_object('expander_livestream')
        self.expander_encoder = builder.get_object('expander_encoder')
        self.stream_recorder_filename = builder.get_object('stream_recorder_filename')
        self.stream_recorder_disk2 = builder.get_object('stream_recorder_disk2')
        self.stream_recorder_disk1 = builder.get_object('stream_recorder_disk1')
        self.stream_recorder_disk1_label = builder.get_object('stream_recorder_disk1_label')
        self.stream_recorder_disk2_label = builder.get_object('stream_recorder_disk2_label')
        self.stream_recorder_start = builder.get_object('stream_recorder_start')
        self.stream_recorder_stop = builder.get_object('stream_recorder_stop')
        self.stream_recorder_switch = builder.get_object('stream_recorder_switch')
        self.stream_recorder_clock = builder.get_object('stream_recorder_clock')
        self.stream_recorder_status = builder.get_object('stream_recorder_status')
        self.stream_recorder_disk = [None, None]
        self.stream_recorder_active = False
        self.stream_recorder_start_time = None

        self.audio_rate_min = builder.get_object('audio_rate_min')
        self.audio_rate_max = builder.get_object('audio_rate_max')
        self.video_rate_min = builder.get_object('video_rate_min')
        self.video_rate_max = builder.get_object('video_rate_max')

        self.stream_presets = builder.get_object('stream_presets')
        self.stream_live_clock = builder.get_object('stream_live_clock')
        self.stream_live_status = builder.get_object('stream_live_status')
        self.stream_live_platform = builder.get_object('stream_live_platform')
        self.stream_live_server = builder.get_object('stream_live_server')
        self.stream_live_key = builder.get_object('stream_live_key')
        self.stream_live_start = builder.get_object('stream_live_start')
        self.stream_live_stop = builder.get_object('stream_live_stop')
        self.live_stats = builder.get_object('live_stats')
        self.stream_live_active = False
        self.stream_live_start_time = None

        self.switcher_mediaplayers = builder.get_object('switcher_mediaplayers')
        self.mediaplayer_dropdowns = {}

        action_streampreset = Gio.SimpleAction.new("streampreset", GLib.VariantType.new("a{sv}"))
        action_streampreset.connect("activate", self.load_livestream_preset)
        self.application.add_action(action_streampreset)

        self.create_livestream_presets()

        self.disks = {}
        self.aux = {}

        self.grid_aux = builder.get_object('grid_aux')

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
        self.model_aux = builder.get_object('model_aux')
        self.model_disks = builder.get_object('model_disks')
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
        layout_exp = Gtk.Expander(label=_("Layout editor M/E {}").format(index + 1))
        layout_exp.set_margin_start(12)
        layout_exp.set_margin_end(12)
        layout_exp.add(layout)
        layout_exp.show_all()
        self.main_blocks.add(layout_exp)

    def on_cut_clicked(self, widget, index):
        cmd = CutCommand(index=index)
        self.connection.mixer.send_commands([cmd])

    def on_cut_shortcut(self, *args):
        if self.disable_shortcuts:
            return

        cmd = CutCommand(index=0)
        self.connection.mixer.send_commands([cmd])

    def on_auto_clicked(self, widget, index, *args):
        if self.disable_shortcuts and len(args) == 2:
            return

        cmd = AutoCommand(index=index)
        self.connection.mixer.send_commands([cmd])

    def on_auto_shortcut(self, *args):
        if self.disable_shortcuts:
            return

        cmd = AutoCommand(index=0)
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
        if self.model_changing:
            return
        cmd = WipeSettingsCommand(index=0, pattern=widget.pattern)
        self.connection.mixer.send_commands([cmd])

    def on_tbar_position_changed(self, widget, index, position):
        cmd = TransitionPositionCommand(index=index, position=position)
        self.connection.mixer.send_commands([cmd])

    def on_next_clicked(self, widget, index, current):
        self.log_sw.debug('next', index, current)
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
        if self.model_changing:
            return
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

    def on_aux_source_changed(self, widget):
        if hasattr(widget, 'ignore_change') and widget.ignore_change or self.model_changing:
            return
        cmd = AuxSourceCommand(widget.index, source=int(widget.get_active_id()))
        self.connection.mixer.send_commands([cmd])

    def on_wipe_symmetry_adj_value_changed(self, widget, *args):
        if self.model_changing:
            return
        cmd = WipeSettingsCommand(index=0, symmetry=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    def on_wipe_x_adj_value_changed(self, widget, *args):
        if self.model_changing:
            return
        cmd = WipeSettingsCommand(index=0, positionx=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    def on_wipe_y_adj_value_changed(self, widget, *args):
        if self.model_changing:
            return
        cmd = WipeSettingsCommand(index=0, positiony=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    def on_wipe_width_adj_value_changed(self, widget, *args):
        if self.model_changing:
            return
        cmd = WipeSettingsCommand(index=0, width=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    def on_wipe_softness_adj_value_changed(self, widget, *args):
        if self.model_changing:
            return
        cmd = WipeSettingsCommand(index=0, softness=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    def on_wipe_fill_changed(self, widget, *args):
        if hasattr(widget, 'ignore_change') and widget.ignore_change or self.model_changing:
            return
        cmd = WipeSettingsCommand(index=0, source=int(widget.get_active_id()))
        self.connection.mixer.send_commands([cmd])
        self.focus_dummy.grab_focus()

    def on_wipe_flipflop_clicked(self, widget, *args):
        if self.model_changing:
            return
        state = widget.get_style_context().has_class('active')
        cmd = WipeSettingsCommand(index=0, flipflop=not state)
        self.connection.mixer.send_commands([cmd])

    def on_wipe_reverse_clicked(self, widget, *args):
        if self.model_changing:
            return
        state = widget.get_style_context().has_class('active')
        cmd = WipeSettingsCommand(index=0, reverse=not state)
        self.connection.mixer.send_commands([cmd])

    def on_ftb_afv_clicked(self, widget, *args):
        if self.mixer == 'atem':
            cmd = AudioMasterPropertiesCommand(afv=not widget.get_style_context().has_class('active'))
        else:
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
        if data.index > len(self.me) - 1:
            self.log_sw.warning("Got FTB change for non-existing M/E {}".format(data.index + 1))
            return
        self.me[data.index].set_ftb_rate(data.rate)

    def on_transition_mix_change(self, data):
        if data.index > len(self.me) - 1:
            self.log_sw.warning("Got transition mix change for non-existing M/E {}".format(data.index + 1))
            return

        label = self.frames_to_time(data.rate)
        self.mix_rate.set_text(label)
        self.me[data.index].set_auto_rate('mix', data.rate)

    def on_transition_dip_change(self, data):
        if data.index > len(self.me) - 1:
            self.log_sw.warning("Got transition dip change for non-existing M/E {}".format(data.index + 1))
            return

        label = self.frames_to_time(data.rate)
        self.dip_rate.set_text(label)
        self.dip_source.ignore_change = True
        self.dip_source.set_active_id(str(data.source))
        self.dip_source.ignore_change = False
        self.me[data.index].set_auto_rate('dip', data.rate)

    def on_transition_wipe_change(self, data):
        if data.index > len(self.me) - 1:
            self.log_sw.warning("Got transition wipe change for non-existing M/E {}".format(data.index + 1))
            return

        label = self.frames_to_time(data.rate)
        self.wipe_rate.set_text(label)
        self.me[data.index].set_auto_rate('wipe', data.rate)

        for style, button in enumerate(self.wipe_style):
            self.set_class(button, 'stylebtn', True)
            self.set_class(button, 'active', style == data.pattern)

        if not self.slider_held:
            self.model_changing = True
            self.wipe_symmetry_adj.set_value(data.symmetry)
            self.wipe_x_adj.set_value(data.positionx)
            self.wipe_y_adj.set_value(data.positiony)
            self.wipe_width_adj.set_value(data.width)
            self.wipe_softness_adj.set_value(data.softness)
            self.model_changing = False

        self.model_changing = True
        self.wipe_fill.set_active_id(str(data.source))
        self.model_changing = False

        self.wipe_fill.set_sensitive(data.width > 0)
        self.set_class(self.wipe_reverse, 'active', data.reverse)
        self.set_class(self.wipe_flipflop, 'active', data.flipflop)

    def on_transition_dve_change(self, data):
        if data.index > len(self.me) - 1:
            self.log_sw.warning("Got transition dve change for non-existing M/E {}".format(data.index + 1))
            return

        label = self.frames_to_time(data.rate)
        self.dve_rate.set_text(label)
        self.me[data.index].set_auto_rate('dve', data.rate)

    def _remap(self, value, old_min, old_max, new_min, new_max):
        return ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min

    def on_dsk_change(self, data):
        self.me[0].set_dsk(data)
        if data.index in self.dsks:
            self.dsks[data.index].on_key_properties_change(data)

            top = 9000 - data.top
            bottom = data.bottom + 9000
            left = data.left + 16000
            right = 16000 - data.right

            region = self.layout[0].get(LayoutView.LAYER_DSK, data.index)
            region.set_mask(top, bottom, left, right)

    def on_dsk_state_change(self, data):
        self.me[0].set_dsk_state(data)
        region = self.layout[0].get(LayoutView.LAYER_DSK, data.index)
        region.set_tally(data.on_air)

    def on_topology_change(self, data: TopologyField):
        # Create the M/E units
        for i in range(0, data.me_units - len(self.me)):
            self.add_mixeffect()

        # Downstream keyer count, only available on M/E 1
        self.me[0].set_topology(data)
        self.apply_css(self.me[0], self.provider)

        from gtk_switcher.downstreamkey import DownstreamKeyer
        for widget in self.downstream_keyers:
            self.downstream_keyers.remove(widget)

        for i in range(0, data.downstream_keyers):
            exp = Gtk.Expander()
            exp.get_style_context().add_class('bmdgroup')
            label = _("Downstream keyer {}").format(i + 1)
            frame_label = Gtk.Label(label)
            frame_label.get_style_context().add_class("heading")
            exp.set_label_widget(frame_label)
            exp.set_expanded(True)
            dsk = DownstreamKeyer(index=i, connection=self.connection)
            self.dsks[dsk.index] = dsk
            self.has_models.append(dsk)
            exp.add(dsk)
            self.apply_css(dsk, self.provider)
            dsk.set_fill_model(self.model_me1_fill)
            dsk.set_key_model(self.model_key)
            self.downstream_keyers.pack_start(exp, False, True, 0)

            # Add the DSK to the layout editor of M/E 1
            region = self.layout[0].get(LayoutView.LAYER_DSK, i)
            region.set_region(0, 0, 16, 9)
            region.set_mask(0, 0, 0, 0)
        self.downstream_keyers.show_all()

        # Media players
        for i in range(0, data.mediaplayers):
            label = Gtk.Label(_("Media Player {}").format(i + 1), xalign=0.0)
            label.get_style_context().add_class('heading')
            expander = Gtk.Expander()
            expander.set_label_widget(label)
            expander.set_expanded(True)
            frame = Gtk.Frame()
            frame.set_margin_top(6)
            frame.get_style_context().add_class('view')
            expander.add(frame)

            grid = Gtk.Grid()
            grid.set_column_spacing(12)
            grid.set_row_spacing(12)
            grid.set_margin_top(12)
            grid.set_margin_bottom(12)
            grid.set_margin_start(12)
            grid.set_margin_end(12)
            frame.add(grid)

            label = Gtk.Label("Media", xalign=1.0)
            label.get_style_context().add_class('dim-label')
            grid.attach(label, 0, 0, 1, 1)

            dropdown = Gtk.ComboBox.new_with_model(self.model_media)
            grid.attach(dropdown, 1, 0, 1, 1)
            dropdown.set_entry_text_column(1)
            dropdown.set_id_column(0)
            self.mediaplayer_dropdowns[i] = dropdown

            if 'mediaplayer-selected' in self.connection.mixer.mixerstate:
                if i in self.connection.mixer.mixerstate['mediaplayer-selected']:
                    field = self.connection.mixer.mixerstate['mediaplayer-selected'][i]
                    if field.source_type == 1:
                        # Stills source
                        dropdown.set_active_id(str(field.slot))

            dropdown.mediaplayer = i
            dropdown.connect('changed', self.on_mediaplayer_change)
            renderer = Gtk.CellRendererText()
            dropdown.pack_start(renderer, True)
            dropdown.add_attribute(renderer, "text", 1)

            self.switcher_mediaplayers.add(expander)
        self.media_create_mediaplayers(data.mediaplayers)
        self.switcher_mediaplayers.show_all()

    def on_mediaplayer_switcher_source_change(self, data):
        if data.index not in self.mediaplayer_dropdowns:
            return
        self.model_changing = True
        if data.source_type == 1:
            self.mediaplayer_dropdowns[data.index].set_active_id(str(data.slot))
        self.model_changing = False

    def on_mediaplayer_change(self, widget, *args):
        if self.model_changing:
            return

        index = widget.get_active_id()
        if index == "":
            return

        index = int(index)
        cmd = MediaplayerSelectCommand(widget.mediaplayer, still=index)
        self.connection.mixer.send_commands([cmd])

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
        if data.index > len(self.me) - 1:
            self.log_sw.warning("Got _MeC for non-existing M/E {}".format(data.index + 1))
            return

        if data.index not in self.usks:
            self.usks[data.index] = {}

        self.me[data.index].set_config(data)

        from gtk_switcher.upstreamkey import UpstreamKeyer

        usk_count = len(self.usks[data.index])
        if data.keyers > usk_count:
            add = data.keyers - usk_count

            for i in range(0, add):
                exp = Gtk.Expander()
                exp.get_style_context().add_class('bmdgroup')
                label_text = _("Upstream keyer {}").format(len(self.usks[data.index]) + 1)
                if data.index != 0:
                    label_text += ' [M/E {}]'.format(data.index + 1)
                frame_label = Gtk.Label(label_text)
                frame_label.get_style_context().add_class("heading")
                exp.set_label_widget(frame_label)
                exp.set_expanded(True)
                usk = UpstreamKeyer(index=data.index, keyer=len(self.usks[data.index]), connection=self.connection)
                self.usks[data.index][usk.keyer] = usk
                self.has_models.append(usk)
                exp.add(usk)
                self.apply_css(usk, self.provider)
                usk.set_fill_model(self.model_me1_fill)
                usk.set_key_model(self.model_key)
                self.upstream_keyers.pack_start(exp, False, True, 0)

            self.upstream_keyers.show_all()

    def on_ftb_state_change(self, data):
        if data.index > len(self.me) - 1:
            self.log_sw.warning("Got FTB state change for non-existing M/E {}".format(data.index + 1))
            return

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
        if data.index > len(self.me) - 1:
            self.log_sw.warning("Got key-on-air for non-existant keyer {} M/E {}".format(data.keyer, data.index + 1))
            return
        self.me[data.index].set_key_on_air(data)
        self.layout[data.index].get(LayoutView.LAYER_USK, data.keyer).set_tally(data.enabled)

    def on_transition_preview_change(self, data):
        if data.index > len(self.me) - 1:
            self.log_sw.warning("Got transition preview change for non-existing M/E {}".format(data.index + 1))
            return
        self.me[data.index].set_preview_transition(data.enabled)

    def on_transition_settings_change(self, data):
        if data.index > len(self.me) - 1:
            self.log_sw.warning("Got transition settings change for non-existing M/E {}".format(data.index + 1))
            return
        self.me[data.index].set_transition_settings(data)

    def on_transition_position_change(self, data):
        if data.index > len(self.me) - 1:
            self.log_sw.warning("Got transition position change for non-existing M/E {}".format(data.index + 1))
            return
        self.me[data.index].set_transition_progress(data)

    def on_onair_clicked(self, widget, index, keyer, enabled):
        cmd = KeyOnAirCommand(index=index, keyer=keyer, enabled=enabled)
        self.connection.mixer.send_commands([cmd])

    def on_key_properties_base_change(self, data):
        if data.index not in self.usks:
            self.log_sw.warning(
                "Got key-properties-base for non-existant M/E {}".format(data.index + 1))
            return
        if data.keyer not in self.usks[data.index]:
            self.log_sw.warning(
                "Got key-properties-base for non-existant keyer {} M/E {}".format(data.keyer, data.index + 1))
            return
        self.usks[data.index][data.keyer].on_key_properties_base_change(data)

    def on_key_properties_luma_change(self, data):
        if data.index not in self.usks:
            self.log_sw.warning(
                "Got key-properties-luma for non-existant M/E {}".format(data.index + 1))
            return
        if data.keyer not in self.usks[data.index]:
            self.log_sw.warning(
                "Got key-properties-luma for non-existant keyer {} M/E {}".format(data.keyer, data.index + 1))
            return
        self.usks[data.index][data.keyer].on_key_properties_luma_change(data)

    def on_key_properties_dve_change(self, data):
        if data.index not in self.usks:
            self.log_sw.warning(
                "Got key-properties-dve for non-existant M/E {}".format(data.index + 1))
            return
        if data.keyer not in self.usks[data.index]:
            self.log_sw.warning(
                "Got key-properties-dve for non-existant keyer {} M/E {}".format(data.keyer, data.index + 1))
            return

        self.usks[data.index][data.keyer].on_key_properties_dve_change(data)
        width = 16.0 * data.size_x / 1000
        height = 9.0 * data.size_y / 1000

        region = self.layout[data.index].get(LayoutView.LAYER_USK, data.keyer)
        region.set_region(data.pos_x / 1000, data.pos_y / 1000, width, height)
        region.set_mask(data.mask_top, data.mask_bottom, data.mask_left, data.mask_right)

    def on_key_properties_advanced_chroma_change(self, data):
        if data.index not in self.usks:
            self.log_sw.warning(
                "Got KACk for non-existant M/E {}".format(data.index + 1))
            return
        if data.keyer not in self.usks[data.index]:
            self.log_sw.warning(
                "Got KACk for non-existant keyer {} M/E {}".format(data.keyer, data.index + 1))
            return
        self.usks[data.index][data.keyer].on_advanced_chroma_change(data)

    def on_key_properties_advanced_chroma_colorpicker_change(self, data):
        if data.index not in self.usks:
            self.log_sw.warning(
                "Got KACC for non-existant M/E {}".format(data.index + 1))
            return
        if data.keyer not in self.usks[data.index]:
            self.log_sw.warning(
                "Got KACC for non-existant keyer {} M/E {}".format(data.keyer, data.index + 1))
            return

        self.usks[data.index][data.keyer].on_chroma_picker_change(data)

        size = data.size / 1000

        region = self.layout[data.index].get(LayoutView.LAYER_ACK, data.keyer)
        region.set_region(data.x / 1000, data.y / 1000, size, size)
        region.set_tally(data.preview)
        region.set_visible(data.cursor)

    def on_program_input_change(self, data):
        if data.index > len(self.me) - 1:
            self.log_sw.warning("Got program input change for non-existing M/E {}".format(data.index + 1))
            return
        self.me[data.index].program_input_change(data)

    def on_preview_input_change(self, data):
        if data.index > len(self.me) - 1:
            self.log_sw.warning("Got preview input change for non-existing M/E {}".format(data.index + 1))
            return
        self.me[data.index].preview_input_change(data)

    def on_dkey_properties_base_change(self, data):
        if data.index not in self.dsks:
            self.log_sw.warning("Got dkey-properties-base for non-existant keyer {}".format(data.index))
            return
        self.dsks[data.index].on_key_properties_base_change(data)

    def on_me_program_changed(self, widget, index, source):
        cmd = ProgramInputCommand(index=index, source=source)
        self.connection.mixer.send_commands([cmd])

    def on_me_preview_changed(self, widget, index, source):
        cmd = PreviewInputCommand(index=index, source=source)
        self.connection.mixer.send_commands([cmd])

    def on_stream_recording_setting_change(self, data):
        self.expander_stream_recorder.show()
        self.model_changing = True
        self.stream_recorder_filename.set_text(data.filename)
        self.stream_recorder_disk = [data.disk1, data.disk2]

        self.stream_recorder_disk1.set_active_id(str(data.disk1))
        self.stream_recorder_disk2.set_active_id(str(data.disk2))
        self.on_update_recording_buttons()
        self.model_changing = False

    def on_stream_recording_disks_change(self, data):
        self.model_changing = True
        if data.is_deleted:
            del self.disks[data.index]
        else:
            self.disks[data.index] = data
            for i, row in enumerate(self.model_disks):
                if row[0] == str(data.index):
                    self.model_disks[i][1] = data.volumename
                    break
            else:
                self.model_disks.append([str(data.index), data.volumename])

        self.stream_recorder_disk1.set_active_id(str(self.stream_recorder_disk[0]))
        self.stream_recorder_disk2.set_active_id(str(self.stream_recorder_disk[1]))
        self.stream_recorder_disk1.set_sensitive(self.stream_recorder_disk[0] is not None)
        self.stream_recorder_disk2.set_sensitive(self.stream_recorder_disk[1] is not None)
        self.on_update_recording_buttons()
        self.model_changing = False

    def on_stream_recording_status_change(self, data):
        self.on_update_recording_buttons()

        status = 'STOP'
        active = False
        if data.has_dropped:
            status = 'DROP'
            active = True
        elif data.is_stopping:
            status = 'STOPPING'
        elif data.disk_full:
            status = 'DISK FULL'
        elif data.is_recording:
            status = 'REC'
            active = True

        if active != self.stream_recorder_active:
            if active:
                self.stream_recorder_start_time = datetime.now().timestamp()

        self.set_class(self.headerbar, 'recording', active)
        self.stream_recorder_active = active

        self.stream_recorder_status.set_text(status)
        self.set_class(self.stream_recorder_status, 'program', active)
        self.set_class(self.stream_recorder_clock, 'program', active)

    def on_stream_recording_duration_change(self, data):
        # This does not get called nearly often enough
        self.stream_recorder_clock.set_text(f'{data.hours}:{data.minutes}:{data.seconds}')
        seconds = data.seconds + (60 * data.minutes) + (60 * 60 * data.hours)
        self.stream_recorder_start_time = datetime.now().timestamp() - seconds

    def on_clock_stream_recorder(self):
        if self.stream_recorder_active:
            length = timedelta(seconds=int(datetime.now().timestamp() - self.stream_recorder_start_time))
            self.stream_recorder_clock.set_text(str(length))

    def on_clock_stream_live(self):
        if self.stream_live_active:
            length = timedelta(seconds=int(datetime.now().timestamp() - self.stream_live_start_time))
            self.stream_live_clock.set_text(str(length))

    def on_update_recording_buttons(self):
        has_usable_disks = False
        for index in self.disks:
            if self.disks[index].is_ready:
                has_usable_disks = True
        has_multi_ready_disks = self.stream_recorder_disk[0] is not None and self.stream_recorder_disk[1] is not None

        if 'recording-status' not in self.connection.mixer.mixerstate:
            return

        status = self.connection.mixer.mixerstate['recording-status']
        is_recording = status.is_recording

        self.stream_recorder_start.set_sensitive(has_usable_disks and not is_recording)
        self.stream_recorder_stop.set_sensitive(is_recording)
        self.stream_recorder_switch.set_sensitive(has_multi_ready_disks and is_recording)

        self.set_class(self.stream_recorder_disk1_label, 'program',
                       self.stream_recorder_disk[0] is not None
                       and self.stream_recorder_disk[0] in self.disks
                       and self.disks[self.stream_recorder_disk[0]].is_recording)
        self.set_class(self.stream_recorder_disk2_label, 'program',
                       self.stream_recorder_disk[1] is not None
                       and self.stream_recorder_disk[1] in self.disks
                       and self.disks[self.stream_recorder_disk[1]].is_recording)

    def on_stream_recorder_start_clicked(self, widget, *args):
        cmd = RecorderStatusCommand(recording=True)
        self.connection.mixer.send_commands([cmd])

    def on_stream_recorder_stop_clicked(self, widget, *args):
        cmd = RecorderStatusCommand(recording=False)
        self.connection.mixer.send_commands([cmd])

    def on_aux_output_source_change(self, source):
        if source.index not in self.aux:
            return

        self.aux[source.index].ignore_change = True
        self.aux[source.index].set_active_id(str(source.source))
        self.aux[source.index].ignore_change = False

        for me in self.me:
            if not hasattr(me, 'category'):
                continue
            if me.index == source.index:
                me.source_change(source.source)

    def on_input_layout_change(self, changed_input):
        inputs = self.connection.mixer.mixerstate['input-properties']
        external = []
        colors = []
        mp = []
        black = None
        bars = None
        extra1 = []
        extra2 = []

        extra1_me1 = []
        extra2_me1 = []
        extra1_me2 = []
        extra2_me2 = []

        # Clear the combobox models
        self.model_changing = True
        for i in self.has_models:
            i.model_changing = True
        self.model_me1_fill.clear()
        self.model_aux.clear()
        self.model_key.clear()

        for i in list(inputs.values()):
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
            if i.port_type == InputPropertiesField.PORT_SUPERSOURCE:
                extra2.append(i)
            if i.port_type == InputPropertiesField.PORT_ME_OUTPUT:
                if i.available_me1:
                    extra1_me1.append(i)
                if i.available_me2:
                    extra1_me2.append(i)

            if i.available_me1:
                self.model_me1_fill.append([str(i.index), i.name])
            if i.available_key_source:
                self.model_key.append([str(i.index), i.name])

            if i.available_aux:
                self.model_aux.append([str(i.index), i.name])

            if i.port_type == InputPropertiesField.PORT_AUX_OUTPUT:
                aux_id = i.index - 8001
                if aux_id not in self.aux:
                    self.aux[aux_id] = Gtk.ComboBox.new_with_model(self.model_aux)
                    self.aux[aux_id].set_entry_text_column(1)
                    self.aux[aux_id].set_id_column(0)
                    self.aux[aux_id].index = aux_id
                    self.aux[aux_id].connect('changed', self.on_aux_source_changed)
                    renderer = Gtk.CellRendererText()
                    self.aux[aux_id].pack_start(renderer, True)
                    self.aux[aux_id].add_attribute(renderer, "text", 1)
                    self.grid_aux.attach(self.aux[aux_id], 1, aux_id, 1, 1)

                    aux_me = Gtk.CheckButton.new_with_label(_("Show as bus"))
                    aux_me.index = i.index
                    aux_me.connect('toggled', self.on_aux_me_enable_toggled)

                    aux_follow_mon = Gtk.CheckButton.new_with_label(_("Follow audio monitor bus"))
                    aux_follow_mon.index = i.index
                    aux_follow_mon.connect('toggled', self.on_aux_me_follow_toggled)

                    aux_btn = Gtk.MenuButton()
                    hamburger = Gtk.Image.new_from_icon_name('open-menu-symbolic', Gtk.IconSize.BUTTON)
                    aux_btn.set_image(hamburger)

                    popover = Gtk.PopoverMenu()
                    aux_btn.set_popover(popover)
                    popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    popover_box.set_margin_top(8)
                    popover_box.set_margin_bottom(8)
                    popover_box.set_margin_start(8)
                    popover_box.set_margin_end(8)
                    popover_box.add(aux_me)
                    popover_box.add(aux_follow_mon)
                    popover.add(popover_box)
                    popover_box.show_all()
                    self.grid_aux.attach(aux_btn, 2, aux_id, 1, 1)

                    aux_label = Gtk.Label(label=i.name)
                    aux_label.get_style_context().add_class('dim-label')
                    self.grid_aux.attach(aux_label, 0, aux_id, 1, 1)
                    self.grid_aux.show_all()

        row1_ext = external
        row2_ext = [None] * len(external)
        if len(external) > 4:
            num = len(external) // 2
            row1_ext = external[0:num]
            row2_ext = external[num:] + [None] * ((2 * num) - len(external))

        row1 = row1_ext + [None, black, None] + colors + extra1
        row2 = row2_ext + [None, bars, None] + mp + extra2

        buttons = [row1, row2]

        for me in self.me:
            me_btns = [buttons[0][:], buttons[1][:]]
            if me.index == 0:
                me_btns[0] += extra1_me1
                me_btns[1] += extra2_me1
            elif me.index == 1:
                me_btns[0] += extra1_me2
                me_btns[1] += extra2_me2
            me.set_inputs(me_btns)
            self.apply_css(me, self.provider)

        self.model_changing = False
        for i in self.has_models:
            i.model_changing = False

    def on_aux_me_follow_toggled(self, widget):
        aux_id = widget.index - 8001
        if widget.get_active():
            self.aux_follow_audio.add(aux_id)
        else:
            self.aux_follow_audio.remove(aux_id)

    def on_aux_me_enable_toggled(self, widget):
        from gtk_switcher.mixeffect_aux import AuxMixEffectBlock
        if widget.get_active():
            inputs = self.connection.mixer.mixerstate['input-properties']
            auxsrcs = self.connection.mixer.mixerstate['aux-output-source']
            auxsrc = auxsrcs[widget.index - 8001]
            external = []
            output = []
            passthrough = []
            special = []
            black = []
            bars = []
            for i in inputs.values():
                if i.available_aux:
                    if i.port_type == InputPropertiesField.PORT_EXTERNAL:
                        external.append(i)
                    elif i.port_type == InputPropertiesField.PORT_ME_OUTPUT:
                        output.append(i)
                    elif i.port_type == InputPropertiesField.PORT_PASSTHROUGH:
                        passthrough.append(i)
                    elif i.port_type == InputPropertiesField.PORT_BLACK:
                        black.append(None)
                        black.append(i)
                    elif i.port_type == InputPropertiesField.PORT_BARS:
                        bars.append(None)
                        bars.append(i)
                    else:
                        special.append(i)

            row1_ext = external
            row2_ext = [None] * len(external)
            if len(external) > 6:
                num = len(external) // 2
                row1_ext = external[0:num]
                row2_ext = external[num:] + [None] * ((2 * num) - len(external))

                row1 = row1_ext + black + [None] + output + passthrough
                row2 = row2_ext + bars + [None] + special
            else:
                row1 = row1_ext + [None] + passthrough + black + bars + [None] + output + special
                row2 = row2_ext

            name = inputs[widget.index].name
            aux_me = AuxMixEffectBlock(widget.index, name)
            aux_me.set_inputs([row1, row2])
            aux_me.source_change(auxsrc.source)
            aux_me.connect('source-changed', self.on_aux_me_source_changed)
            aux_me.index = widget.index - 8001
            aux_me.category = 'aux'
            self.apply_css(aux_me, self.provider)
            self.me.append(aux_me)
            self.main_blocks.add(aux_me)
        else:
            for me in self.me:
                if not hasattr(me, 'category'):
                    continue
                if me.category != 'aux':
                    continue
                if me.index == widget.index - 8001:
                    self.me.remove(me)
                    me.destroy()

    def on_aux_me_source_changed(self, widget, aux, source):
        cmd = AuxSourceCommand(aux, source=source)
        self.connection.mixer.send_commands([cmd])

    def on_macro_properties_change(self, data):
        # Clear the macro flow container
        for widget in self.macro_flow:
            self.macro_flow.remove(widget)

        # Create new buttons
        macros = self.connection.mixer.mixerstate['macro-properties']
        for index in macros:
            macro = macros[index]
            if macro.is_used:
                button = Gtk.Button(macro.name.decode())
                button.index = index
                button.get_style_context().add_class('bmdbtn')
                button.get_style_context().add_class('macro')
                button.connect('button-press-event', self.on_macro_context)
                self.macro_flow.add(button)
        self.macro_flow.show_all()

    def on_macro_context(self, widget, event, *args):
        if event.button != 3:
            return

        self.menu = Gtk.Menu()
        run_item = Gtk.MenuItem(_("Run macro"))
        self.menu.append(run_item)
        edit_item = Gtk.MenuItem(_("Edit macro"))
        edit_item.index = widget.index
        edit_item.connect('activate', self.on_macro_edit)
        self.menu.append(edit_item)
        self.menu.show_all()
        self.menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())

    def on_macro_edit(self, widget):
        self.macro_edit = True
        self.connection.mixer.download(0xffff, widget.index)

    def bps_to_human(self, bps):
        if bps < 1000:
            return str(bps) + 'b'
        elif bps < 1000 * 1000:
            val = bps / 1000
            return f'{val:g}k'
        else:
            val = bps / 1000 / 1000
            return f'{val:g}M'

    def on_streaming_service_change(self, data):
        self.expander_livestream.show()
        self.expander_encoder.show()
        self.video_rate_min.set_text(self.bps_to_human(data.min))
        self.video_rate_max.set_text(self.bps_to_human(data.max))

        self.stream_live_platform.set_text(data.name)
        self.stream_live_server.set_text(data.url)
        self.stream_live_key.set_text(data.key)

    def on_streaming_audio_bitrate_change(self, data):
        self.expander_encoder.show()
        self.audio_rate_min.set_text(self.bps_to_human(data.min))
        self.audio_rate_max.set_text(self.bps_to_human(data.max))

    def on_streaming_status_change(self, data):
        starting = data.status == 2
        active = data.status == 4
        self.set_class(self.headerbar, 'streaming', active)
        if active:
            self.live_stats.show()
        else:
            self.live_stats.hide()

        self.stream_live_start.set_sensitive(not starting and not active)
        self.stream_live_stop.set_sensitive(starting or active)

        status = {
            1: (gettext.pgettext("livestream", "OFF"), False, False),
            2: (gettext.pgettext("livestream", "starting..."), True, False),
            4: (gettext.pgettext("livestream", "ON AIR"), False, True),
            34: (gettext.pgettext("livestream", "stopping..."), True, False),
            36: (gettext.pgettext("livestream", "stopping..."), True, False),
        }
        if data.status in status:
            self.stream_live_status.set_text(status[data.status][0])
            self.set_class(self.stream_live_status, 'active', status[data.status][1])
            self.set_class(self.stream_live_status, 'program', status[data.status][2])

        if active != self.stream_live_active:
            if active:
                self.stream_live_start_time = datetime.now().timestamp()

        self.stream_live_active = active

    def on_streaming_stats_change(self, data):
        self.live_stats.set_text('{:.2f} Mbps'.format(data.bitrate / 1000 / 1000))

    def create_livestream_presets(self):
        hardcoded = gtk_switcher.stream_data.services

        menu = Gio.Menu()
        for provider in hardcoded:
            section = Gio.Menu()
            for preset in hardcoded[provider]:
                item = Gio.MenuItem()
                item.set_label(preset.name)
                item.service = preset
                item.set_action_and_target_value('app.streampreset', preset.variant())
                section.append_item(item)

            menu.append_section(provider, section)
        self.stream_presets.set_menu_model(menu)

    def load_livestream_preset(self, action, data):
        data = dict(data)
        cmd = StreamingServiceSetCommand(name=data['name'], url=data['url'])
        self.connection.mixer.send_commands([cmd])

    def on_stream_live_platform_activate(self, widget, *args):
        cmd = StreamingServiceSetCommand(name=widget.get_text())
        self.connection.mixer.send_commands([cmd])

    def on_stream_live_server_activate(self, widget, *args):
        cmd = StreamingServiceSetCommand(url=widget.get_text())
        self.connection.mixer.send_commands([cmd])

    def on_stream_live_key_activate(self, widget, *args):
        cmd = StreamingServiceSetCommand(key=widget.get_text())
        self.connection.mixer.send_commands([cmd])

    def on_stream_live_start_clicked(self, *args):
        cmd = StreamingStatusSetCommand(True)
        self.connection.mixer.send_commands([cmd])

    def on_stream_live_stop_clicked(self, *args):
        cmd = StreamingStatusSetCommand(False)
        self.connection.mixer.send_commands([cmd])

    def on_stream_recorder_disk1_changed(self, widget, *args):
        if self.model_changing:
            return
        disk_id = int(widget.get_active_id())
        cmd = RecordingSettingsSetCommand(disk1=disk_id)
        self.connection.mixer.send_commands([cmd])

    def on_stream_recorder_disk2_changed(self, widget, *args):
        if self.model_changing:
            return
        disk_id = int(widget.get_active_id())
        cmd = RecordingSettingsSetCommand(disk2=disk_id)
        self.connection.mixer.send_commands([cmd])

    def on_stream_recorder_filename_activate(self, widget, *args):
        cmd = RecordingSettingsSetCommand(filename=widget.get_text())
        self.connection.mixer.send_commands([cmd])

    def human_to_bps(self, human):
        human = human.lower()
        human = human.replace('ps', '')

        if human.isnumeric():
            num = human
            unit = ''
        else:
            if not ' ' in human:
                human = re.sub(r'([a-z]+)', r' \1', human)
            num, unit = [string.strip() for string in human.split()]

        mult = 1
        if unit.startswith('k'):
            mult = 1000
        elif unit.startswith('m'):
            mult = 1000 * 1000
        return int(float(num) * mult)

    def on_audio_bitrate_activate(self, widget, *args):
        rate_min = self.human_to_bps(self.audio_rate_min.get_text())
        rate_max = self.human_to_bps(self.audio_rate_max.get_text())
        if rate_max < rate_min:
            rate_max = rate_min
        cmd = StreamingAudioBitrateCommand(rate_min, rate_max)
        self.connection.mixer.send_commands([cmd])

    def on_video_bitrate_activate(self, widget, *args):
        rate_min = self.human_to_bps(self.video_rate_min.get_text())
        rate_max = self.human_to_bps(self.video_rate_max.get_text())
        if rate_max < rate_min:
            rate_max = rate_min
        cmd = StreamingServiceSetCommand(bitrate_min=rate_min, bitrate_max=rate_max)
        self.connection.mixer.send_commands([cmd])
