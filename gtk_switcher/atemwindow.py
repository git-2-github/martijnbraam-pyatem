import ctypes
import threading

import gi
from hexdump import hexdump

from gtk_switcher.preferenceswindow import PreferencesWindow
from pyatem.command import ProgramInputCommand, PreviewInputCommand, CutCommand, AutoCommand, TransitionSettingsCommand, \
    TransitionPreviewCommand, ColorGeneratorCommand, FadeToBlackCommand, DkeyOnairCommand, DkeyAutoCommand, \
    DkeyTieCommand, TransitionPositionCommand, MixSettingsCommand, DipSettingsCommand, WipeSettingsCommand, \
    DveSettingsCommand, DkeyRateCommand, FairlightMasterPropertiesCommand, FairlightStripPropertiesCommand
from pyatem.field import InputPropertiesField, TransitionSettingsField
from pyatem.protocol import AtemProtocol

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk

gi.require_version('Handy', '1')
from gi.repository import Handy


class AtemConnection(threading.Thread):
    def __init__(self, callback):
        threading.Thread.__init__(self)
        self.callback = callback
        self.atem = None
        self.ip = None
        self.stop = False

    def run(self):
        # Don't run if the ip isn't set yet
        if self.ip is None or self.ip == '0.0.0.0':
            return

        self.mixer = AtemProtocol(self.ip)
        self.mixer.on('change', self.do_callback)
        self.mixer.connect()
        while not self.stop:
            self.mixer.loop()

    def do_callback(self, *args, **kwargs):
        GLib.idle_add(self.callback, *args, **kwargs)

    def get_id(self):

        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def die(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                         ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')


class AtemWindow:
    def __init__(self, application, args):
        self.application = application
        self.args = args

        self.debug = args.debug

        Handy.init()

        self.settings = Gio.Settings.new('nl.brixit.Switcher')
        self.settings.connect('changed::switcher-ip', self.on_switcher_ip_changed)

        builder = Gtk.Builder()
        builder.add_from_resource('/nl/brixit/switcher/ui/mixer.glade')
        builder.connect_signals(self)
        css = Gio.resources_lookup_data("/nl/brixit/switcher/ui/style.css", 0)

        self.provider = Gtk.CssProvider()
        self.provider.load_from_data(css.get_data())

        self.window = builder.get_object("main_window")
        self.window.set_application(self.application)

        # Load requested view
        self.mainstack = builder.get_object("mainstack")
        self.mainstack.set_visible_child_name(args.view)

        self.program_bus = builder.get_object('program')
        self.preview_bus = builder.get_object('preview')
        self.audio_channels = builder.get_object('audio_channels')
        self.dsks = builder.get_object('dsks')
        self.media_flow = builder.get_object('media_flow')
        self.tbar = builder.get_object('tbar')
        self.tbar_adj = builder.get_object('tbar_adj')
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

        self.status_model = builder.get_object('status_model')
        self.status_mode = builder.get_object('status_mode')
        self.disable_shortcuts = False
        self.model_changing = False
        self.slider_held = False

        self.mixer = 'atem'

        self.apply_css(self.window, self.provider)

        self.window.show_all()

        self.firmware_version = None
        self.mode = None
        self.rate = {
            'mix': '0:00',
            'dip': '0:00',
            'wipe': '0:00',
            'sting': '0:00',
            'dve': '0:00'
        }

        self.connection = AtemConnection(self.on_change)

        if args.ip:
            self.connection.ip = args.ip
            if args.persist:
                self.settings.set_string('switcher-ip', args.ip)
        else:
            if self.connection.ip == "0.0.0.0":
                PreferencesWindow(self.window)

            self.connection.ip = self.settings.get_string('switcher-ip')
        self.connection.daemon = True
        self.connection.start()

        accel = Gtk.AccelGroup()
        accel.connect(Gdk.keyval_from_name('space'), 0, 0, self.on_cut_clicked)
        accel.connect(Gdk.keyval_from_name('ISO_Enter'), 0, 0, self.on_auto_clicked)
        accel.connect(Gdk.keyval_from_name('Return'), 0, 0, self.on_auto_clicked)
        accel.connect(Gdk.keyval_from_name('KP_Enter'), 0, 0, self.on_auto_clicked)

        for i in range(0, 9):
            accel.connect(Gdk.keyval_from_name(str(i)), 0, 0, self.on_preview_keyboard_change)
            accel.connect(Gdk.keyval_from_name(str(i)), Gdk.ModifierType.CONTROL_MASK, 0,
                          self.on_program_keyboard_change)
            accel.connect(Gdk.keyval_from_name(str(i)), Gdk.ModifierType.MOD1_MASK, 0,
                          self.on_cutbus_keyboard_change)

        self.window.add_accel_group(accel)

        self.volume_level = {}
        self.input_gain = {}
        self.pan = {}
        self.delay = {}
        self.audio_tally = {}
        self.audio_strip = {}
        self.audio_on = {}
        self.audio_afv = {}
        self.audio_monitor = {}

        Gtk.main()

    def on_preview_keyboard_change(self, widget, window, key, modifier):
        if self.disable_shortcuts:
            return

        index = key - 49
        cmd = PreviewInputCommand(index=0, source=index + 1)
        self.connection.mixer.send_commands([cmd])

    def on_program_keyboard_change(self, widget, window, key, modifier):
        if self.disable_shortcuts:
            return

        index = key - 49
        cmd = ProgramInputCommand(index=0, source=index + 1)
        self.connection.mixer.send_commands([cmd])

    def on_cutbus_keyboard_change(self, widget, window, key, modifier):
        if self.disable_shortcuts:
            return

        index = key - 49
        cmd = PreviewInputCommand(index=0, source=index + 1)
        auto = AutoCommand(index=0)
        self.connection.mixer.send_commands([cmd, auto])

    def apply_css(self, widget, provider):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css, provider)

    def on_switcher_ip_changed(self, *args):
        print("Settings changed!")

        self.connection.die()
        self.connection.join(timeout=1)

        self.connection = AtemConnection(self.on_change)
        self.connection.daemon = True
        self.connection.ip = self.settings.get_string('switcher-ip')
        self.connection.start()

    def set_class(self, widget, classname, state):
        if state:
            widget.get_style_context().add_class(classname)
        else:
            widget.get_style_context().remove_class(classname)

    def on_main_window_destroy(self, widget):
        Gtk.main_quit()

    def on_preferences_button_clicked(self, widget):
        PreferencesWindow(self.window)

    def on_tbar_button_press_event(self, widget, *args):
        self.tbar_held = True

    def on_tbar_button_release_event(self, widget, *args):
        self.tbar_held = False

    def on_cut_clicked(self, widget, *args):
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

    def on_change(self, field, data):

        if self.args.dump is not None and field in self.args.dump:
            if isinstance(data, bytes):
                print('== {} ({} bytes)=='.format(field, len(data)))
                hexdump(data)
            else:
                print('== {} ({} bytes)=='.format(field, len(data.raw)))
                hexdump(data.raw)
                print(data)

        if field == 'firmware-version':
            self.firmware_version = data
            print("Firmware: {}".format(data.version))
        elif field == 'input-properties':
            self.on_input_layout_change(data)
        elif field == 'program-bus-input':
            self.on_program_input_change(data)
        elif field == 'preview-bus-input':
            self.on_preview_input_change(data)
        elif field == 'transition-position':
            self.on_transition_position_change(data)
        elif field == 'transition-settings':
            self.on_transition_settings_change(data)
        elif field == 'transition-preview':
            self.on_transition_preview_change(data)
        elif field == 'key-on-air':
            self.on_key_on_air_change(data)
        elif field == 'color-generator':
            self.on_color_change(data)
        elif field == 'fade-to-black':
            self.on_ftb_change(data)
        elif field == 'fade-to-black-state':
            self.on_ftb_state_change(data)
        elif field == 'mixer-effect-config':
            self.on_mixer_effect_config_change(data)
        elif field == 'topology':
            self.on_topology_change(data)
        elif field == 'product-name':
            self.status_model.set_text(data.name)
            print("Mixer model: {}".format(data.name))
        elif field == 'video-mode':
            self.mode = data
            self.status_mode.set_text(data.get_label())
        elif field == 'dkey-properties':
            self.on_dsk_change(data)
        elif field == 'dkey-state':
            self.on_dsk_state_change(data)
        elif field == 'mediaplayer-slots':
            self.on_mediaplayer_slots_change(data)
        elif field == 'transition-mix':
            self.on_transition_mix_change(data)
        elif field == 'transition-dip':
            self.on_transition_dip_change(data)
        elif field == 'transition-wipe':
            self.on_transition_wipe_change(data)
        elif field == 'transition-dve':
            self.on_transition_dve_change(data)
        elif field == 'fairlight-master-properties':
            self.on_fairlight_master_properties_change(data)
        elif field == 'fairlight-audio-input':
            self.on_fairlight_audio_input_change(data)
        elif field == 'audio-input':
            self.on_audio_input_change(data)
        elif field == 'fairlight-strip-properties':
            self.on_fairlight_strip_properties_change(data)
        elif field == 'fairlight-tally':
            self.on_fairlight_tally_change(data)
        else:
            if field == 'time':
                return
            if not self.debug and self.args.dump is not None and len(self.args.dump) > 0:
                return
            if isinstance(data, bytes):
                print(field)
            else:
                print(data)

    def on_fairlight_tally_change(self, data):
        for strip_id in data.tally:
            if strip_id in self.audio_tally:
                self.set_class(self.audio_tally[strip_id], 'program', data.tally[strip_id])

    def on_fairlight_strip_properties_change(self, data):
        """
        :type data: FairlightStripPropertiesField
        :return:
        """
        self.audio_strip[data.strip_id] = data
        if data.strip_id not in self.volume_level:
            self.volume_level[data.strip_id] = Gtk.Adjustment(0, -10000, 1000, 10, 10, 100)
            self.pan[data.strip_id] = Gtk.Adjustment(0, -10000, 10000, 10, 10, 100)
            self.input_gain[data.strip_id] = Gtk.Adjustment(0, -10000, 600, 10, 10, 100)
            self.delay[data.strip_id] = Gtk.Adjustment(0, 0, 8, 1, 1, 1)
            self.volume_level[data.strip_id].connect('value-changed', self.on_volume_changed)

        self.volume_level[data.strip_id].set_value(data.volume)
        self.pan[data.strip_id].set_value(data.pan)
        self.input_gain[data.strip_id].set_value(data.gain)
        self.delay[data.strip_id].set_value(data.delay)
        if data.strip_id in self.audio_tally:
            tally = self.audio_tally[data.strip_id]
            self.set_class(tally, 'afv', data.state == 4)
        if data.strip_id in self.audio_on:
            self.set_class(self.audio_on[data.strip_id], 'program', data.state & 2)
            self.set_class(self.audio_afv[data.strip_id], 'active', data.state & 4)

    def on_volume_changed(self, widget, *args):
        if self.mixer == 'fairlight':
            cmd = FairlightStripPropertiesCommand(source=widget.source, channel=widget.channel,
                                                  volume=int(widget.get_value()))
            self.connection.mixer.send_commands([cmd])

    def on_audio_input_change(self, data):
        self.mixer = 'atem'

        if data.strip_id not in self.volume_level:
            self.on_audio_input_list_change()
            return

        self.volume_level[data.strip_id].set_value(data.volume)

    def on_audio_input_list_change(self):
        inputs = self.connection.mixer.mixerstate['audio-input']
        # Clear the existing channels
        for child in self.audio_channels:
            child.destroy()

        # Create row of labels again
        label = Gtk.Label(label="dB")
        label.get_style_context().add_class('dim-label')
        label.set_halign(Gtk.Align.END)
        label.set_valign(Gtk.Align.START)
        self.audio_channels.attach(label, 0, 2, 1, 1)
        label = Gtk.Label(label="Pan")
        label.get_style_context().add_class('dim-label')
        label.set_halign(Gtk.Align.END)
        label.set_valign(Gtk.Align.START)
        self.audio_channels.attach(label, 0, 3, 1, 1)

        left = 1
        last_type = 0
        for input in inputs.values():
            self.audio_strip[input.strip_id] = input
            if last_type != input.type:
                last_type = input.type
                type_sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
                type_sep.get_style_context().add_class('dark')
                type_sep.set_margin_left(8)
                type_sep.set_margin_right(8)
                self.audio_channels.attach(type_sep, left, 0, 1, 5)
                left += 1

            if input.type == 0:
                label = self.connection.mixer.mixerstate['input-properties'][input.index].short_name
            elif input.type == 1:
                label = 'MP {}'.format(input.number + 1)
            else:
                label = 'Analog {}'.format(input.number + 1)
            label = Gtk.Label(label=label)
            self.audio_channels.attach(label, left, 0, 1, 1)
            strip_id = input.strip_id

            if strip_id not in self.volume_level:
                self.volume_level[strip_id] = Gtk.Adjustment(input.volume, 0, 65381, 10, 10, 100)
                self.pan[strip_id] = Gtk.Adjustment(input.balance, -10000, 10000, 10, 10, 100)
                self.volume_level[strip_id].connect('value-changed', self.on_volume_changed)
                self.volume_level[strip_id].source = input.index

                tally = Gtk.Box()
                tally.get_style_context().add_class('tally')
                if strip_id in self.audio_strip:
                    self.set_class(tally, 'afv', self.audio_strip[strip_id].state == 2)

                self.audio_tally[strip_id] = tally
                self.audio_channels.attach(tally, left, 1, 1, 1)

                volume_frame = Gtk.Frame()
                volume_frame.get_style_context().add_class('view')
                volume_frame.set_size_request(76, 0)
                volume_frame.set_vexpand(True)
                volume_box = Gtk.Box()
                volume_frame.add(volume_box)
                volume_slider = Gtk.Scale(orientation=Gtk.Orientation.VERTICAL, adjustment=self.volume_level[strip_id])
                volume_slider.set_inverted(True)
                volume_slider.set_draw_value(False)
                volume_slider.get_style_context().add_class('volume')
                volume_slider.connect('button-press-event', self.on_slider_held)
                volume_slider.connect('button-release-event', self.on_slider_released)
                volume_box.pack_start(volume_slider, True, True, 0)
                volume_box.set_margin_left(8)
                volume_box.set_margin_right(8)
                volume_box.set_margin_top(24)
                volume_box.set_margin_bottom(8)
                vu_left = Gtk.ProgressBar()
                vu_right = Gtk.ProgressBar()
                vu_left.set_orientation(Gtk.Orientation.VERTICAL)
                vu_right.set_orientation(Gtk.Orientation.VERTICAL)
                volume_box.pack_start(vu_left, False, True, 0)
                volume_box.pack_start(vu_right, False, True, 0)
                self.audio_channels.attach(volume_frame, left, 2, 1, 1)

                pan_frame = Gtk.Frame()
                pan_frame.get_style_context().add_class('view')
                pan_slider = Gtk.Scale(adjustment=self.pan[strip_id])
                pan_slider.set_draw_value(False)
                pan_slider.get_style_context().add_class('mini')
                pan_slider.get_style_context().add_class('pan')
                pan_frame.add(pan_slider)
                self.audio_channels.attach(pan_frame, left, 3, 1, 1)

                routing_grid = Gtk.Grid()
                routing_grid.set_row_homogeneous(True)
                routing_grid.set_column_homogeneous(True)
                routing_grid.set_row_spacing(8)
                routing_grid.set_column_spacing(8)
                on = Gtk.Button(label="ON")
                on.source = input.index
                # on.connect('clicked', self.do_audio_channel_on)
                on.get_style_context().add_class('bmdbtn')
                routing_grid.attach(on, 0, 0, 1, 1)
                afv = Gtk.Button(label="AFV")
                # afv.connect('clicked', self.do_audio_channel_afv)
                afv.get_style_context().add_class('bmdbtn')
                afv.source = input.index
                if input.type == 2:
                    afv.set_sensitive(False)
                routing_grid.attach(afv, 1, 0, 1, 1)
                self.audio_channels.attach(routing_grid, left, 4, 1, 1)
                self.audio_on[strip_id] = on
                self.audio_afv[strip_id] = afv
                if strip_id in self.audio_strip:
                    self.set_class(afv, 'active', self.audio_strip[strip_id].state == 2)
                    self.set_class(on, 'program', self.audio_strip[strip_id].state == 1)

            left += 1

        master_sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        master_sep.get_style_context().add_class('dark')
        master_sep.set_margin_left(8)
        master_sep.set_margin_right(8)
        self.audio_channels.attach(master_sep, left, 0, 1, 5)
        left += 1

        # Add master channel last
        for c in range(0, 1):
            label = Gtk.Label(label="Master")
            self.audio_channels.attach(label, left + c, 0, 1, 1)
            tally = Gtk.Box()
            tally.get_style_context().add_class('tally')
            tally.get_style_context().add_class('program')
            self.audio_channels.attach(tally, left + c, 1, 1, 1)

            volume_frame = Gtk.Frame()
            volume_frame.set_size_request(76, 0)
            volume_frame.get_style_context().add_class('view')
            volume_frame.set_vexpand(True)
            volume_box = Gtk.Box()
            volume_frame.add(volume_box)
            volume_slider = Gtk.Scale(orientation=Gtk.Orientation.VERTICAL)
            volume_box.pack_start(volume_slider, True, True, 0)
            volume_box.set_margin_left(8)
            volume_box.set_margin_right(8)
            volume_box.set_margin_top(8)
            volume_box.set_margin_bottom(8)
            vu_left = Gtk.ProgressBar()
            vu_right = Gtk.ProgressBar()
            vu_left.set_orientation(Gtk.Orientation.VERTICAL)
            vu_right.set_orientation(Gtk.Orientation.VERTICAL)
            volume_box.pack_start(vu_left, False, True, 0)
            volume_box.pack_start(vu_right, False, True, 0)
            self.audio_channels.attach(volume_frame, left + c, 2, 1, 1)

        self.apply_css(self.audio_channels, self.provider)
        self.audio_channels.show_all()

    def on_fairlight_audio_input_change(self, data):
        self.mixer = 'fairlight'
        inputs = self.connection.mixer.mixerstate['fairlight-audio-input']

        # Clear the existing channels
        for child in self.audio_channels:
            child.destroy()

        # Create row of labels again
        label = Gtk.Label(label="Input")
        label.get_style_context().add_class('dim-label')
        label.set_halign(Gtk.Align.END)
        label.set_valign(Gtk.Align.START)
        self.audio_channels.attach(label, 0, 2, 1, 1)
        label = Gtk.Label(label="Equalizer")
        label.get_style_context().add_class('dim-label')
        label.set_halign(Gtk.Align.END)
        label.set_valign(Gtk.Align.START)
        self.audio_channels.attach(label, 0, 3, 1, 1)
        label = Gtk.Label(label="Dynamics")
        label.get_style_context().add_class('dim-label')
        label.set_halign(Gtk.Align.END)
        label.set_valign(Gtk.Align.START)
        self.audio_channels.attach(label, 0, 4, 1, 1)
        label = Gtk.Label(label="dB")
        label.get_style_context().add_class('dim-label')
        label.set_halign(Gtk.Align.END)
        label.set_valign(Gtk.Align.START)
        self.audio_channels.attach(label, 0, 5, 1, 1)
        label = Gtk.Label(label="Pan")
        label.get_style_context().add_class('dim-label')
        label.set_halign(Gtk.Align.END)
        label.set_valign(Gtk.Align.START)
        self.audio_channels.attach(label, 0, 6, 1, 1)

        left = 1
        last_type = 0
        for input in inputs.values():
            num_subchannels = 1
            if input.split == 4:
                num_subchannels = 2

            if last_type != input.type:
                last_type = input.type
                type_sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
                type_sep.get_style_context().add_class('dark')
                type_sep.set_margin_left(8)
                type_sep.set_margin_right(8)
                self.audio_channels.attach(type_sep, left, 0, 1, 8)
                left += 1

            if input.type == 0:
                label = self.connection.mixer.mixerstate['input-properties'][input.index].short_name
            elif input.type == 1:
                label = 'MP {}'.format(input.number + 1)
            else:
                label = 'Analog {}'.format(input.number + 1)
            label = Gtk.Label(label=label)
            self.audio_channels.attach(label, left, 0, num_subchannels, 1)

            for c in range(0, num_subchannels):
                strip_id = str(input.index) + '.' + str(c)

                if strip_id not in self.volume_level:
                    self.volume_level[strip_id] = Gtk.Adjustment(0, -10000, 1000, 10, 10, 100)
                    self.pan[strip_id] = Gtk.Adjustment(0, -10000, 10000, 10, 10, 100)
                    self.input_gain[strip_id] = Gtk.Adjustment(0, -10000, 600, 10, 10, 100)
                    self.delay[strip_id] = Gtk.Adjustment(0, 0, 8, 1, 1, 1)
                    self.volume_level[strip_id].connect('value-changed', self.on_volume_changed)

                self.volume_level[strip_id].source = input.index
                self.volume_level[strip_id].channel = c if num_subchannels > 1 else -1

                tally = Gtk.Box()
                tally.get_style_context().add_class('tally')
                if strip_id in self.audio_strip:
                    self.set_class(tally, 'afv', self.audio_strip[strip_id].state & 4)

                self.audio_tally[strip_id] = tally
                self.audio_channels.attach(tally, left + c, 1, 1, 1)

                input_frame = Gtk.Frame()
                input_frame.get_style_context().add_class('view')
                self.audio_channels.attach(input_frame, left + c, 2, 1, 1)

                eq_frame = Gtk.Frame()
                eq_frame.get_style_context().add_class('view')
                eq_frame.set_size_request(0, 64)
                self.audio_channels.attach(eq_frame, left + c, 3, 1, 1)

                dynamics_frame = Gtk.Frame()
                dynamics_frame.get_style_context().add_class('view')
                dynamics_frame.set_size_request(0, 64)
                self.audio_channels.attach(dynamics_frame, left + c, 4, 1, 1)

                volume_frame = Gtk.Frame()
                volume_frame.get_style_context().add_class('view')
                volume_frame.set_size_request(76, 0)
                volume_frame.set_vexpand(True)
                volume_box = Gtk.Box()
                volume_frame.add(volume_box)
                volume_slider = Gtk.Scale(orientation=Gtk.Orientation.VERTICAL, adjustment=self.volume_level[strip_id])
                volume_slider.set_inverted(True)
                volume_slider.set_draw_value(False)
                volume_slider.get_style_context().add_class('volume')
                volume_slider.connect('button-press-event', self.on_slider_held)
                volume_slider.connect('button-release-event', self.on_slider_released)
                volume_box.pack_start(volume_slider, True, True, 0)
                volume_box.set_margin_left(8)
                volume_box.set_margin_right(8)
                volume_box.set_margin_top(24)
                volume_box.set_margin_bottom(8)
                vu_left = Gtk.ProgressBar()
                vu_right = Gtk.ProgressBar()
                vu_left.set_orientation(Gtk.Orientation.VERTICAL)
                vu_right.set_orientation(Gtk.Orientation.VERTICAL)
                volume_box.pack_start(vu_left, False, True, 0)
                volume_box.pack_start(vu_right, False, True, 0)
                self.audio_channels.attach(volume_frame, left + c, 5, 1, 1)

                pan_frame = Gtk.Frame()
                pan_frame.get_style_context().add_class('view')
                pan_slider = Gtk.Scale(adjustment=self.pan[strip_id])
                pan_slider.set_draw_value(False)
                pan_slider.get_style_context().add_class('mini')
                pan_slider.get_style_context().add_class('pan')
                pan_frame.add(pan_slider)
                self.audio_channels.attach(pan_frame, left + c, 6, 1, 1)

                routing_grid = Gtk.Grid()
                routing_grid.set_row_homogeneous(True)
                routing_grid.set_column_homogeneous(True)
                routing_grid.set_row_spacing(8)
                routing_grid.set_column_spacing(8)
                on = Gtk.Button(label="ON")
                on.source = input.index
                on.channel = c if num_subchannels > 1 else -1
                on.connect('clicked', self.do_fairlight_channel_on)
                on.get_style_context().add_class('bmdbtn')
                routing_grid.attach(on, 0, 0, 1, 1)
                afv = Gtk.Button(label="AFV")
                afv.connect('clicked', self.do_fairlight_channel_afv)
                afv.get_style_context().add_class('bmdbtn')
                afv.source = input.index
                afv.channel = c if num_subchannels > 1 else -1
                if input.type == 2:
                    afv.set_sensitive(False)
                routing_grid.attach(afv, 1, 0, 1, 1)
                mon = Gtk.Button(label="Monitor")
                mon.get_style_context().add_class('bmdbtn')
                routing_grid.attach(mon, 0, 1, 2, 1)
                self.audio_channels.attach(routing_grid, left + c, 7, 1, 1)
                self.audio_on[strip_id] = on
                self.audio_afv[strip_id] = afv
                self.audio_monitor[strip_id] = mon
                if strip_id in self.audio_strip:
                    self.set_class(afv, 'active', self.audio_strip[strip_id].state & 4)
                    self.set_class(on, 'program', self.audio_strip[strip_id].state & 2)

            left += num_subchannels

        master_sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        master_sep.get_style_context().add_class('dark')
        master_sep.set_margin_left(8)
        master_sep.set_margin_right(8)
        self.audio_channels.attach(master_sep, left, 0, 1, 8)
        left += 1

        # Add master channel last
        for c in range(0, 1):
            label = Gtk.Label(label="Master")
            self.audio_channels.attach(label, left + c, 0, 1, 1)
            tally = Gtk.Box()
            tally.get_style_context().add_class('tally')
            tally.get_style_context().add_class('program')
            self.audio_channels.attach(tally, left + c, 1, 1, 1)

            eq_frame = Gtk.Frame()
            eq_frame.get_style_context().add_class('view')
            eq_frame.set_size_request(0, 64)
            self.audio_channels.attach(eq_frame, left + c, 3, 1, 1)

            dynamics_frame = Gtk.Frame()
            dynamics_frame.get_style_context().add_class('view')
            dynamics_frame.set_size_request(0, 64)
            self.audio_channels.attach(dynamics_frame, left + c, 4, 1, 1)

            volume_frame = Gtk.Frame()
            volume_frame.set_size_request(76, 0)
            volume_frame.get_style_context().add_class('view')
            volume_frame.set_vexpand(True)
            volume_box = Gtk.Box()
            volume_frame.add(volume_box)
            volume_slider = Gtk.Scale(orientation=Gtk.Orientation.VERTICAL)
            volume_box.pack_start(volume_slider, True, True, 0)
            volume_box.set_margin_left(8)
            volume_box.set_margin_right(8)
            volume_box.set_margin_top(8)
            volume_box.set_margin_bottom(8)
            vu_left = Gtk.ProgressBar()
            vu_right = Gtk.ProgressBar()
            vu_left.set_orientation(Gtk.Orientation.VERTICAL)
            vu_right.set_orientation(Gtk.Orientation.VERTICAL)
            volume_box.pack_start(vu_left, False, True, 0)
            volume_box.pack_start(vu_right, False, True, 0)
            self.audio_channels.attach(volume_frame, left + c, 5, 1, 1)

            pan_frame = Gtk.Frame()
            pan_frame.get_style_context().add_class('view')
            self.audio_channels.attach(pan_frame, left + c, 6, 1, 1)

        self.apply_css(self.audio_channels, self.provider)
        self.audio_channels.show_all()

    def do_fairlight_channel_on(self, widget, *args):
        if widget.get_style_context().has_class('program'):
            state = 1
        else:
            state = 2
        cmd = FairlightStripPropertiesCommand(source=widget.source, channel=widget.channel, state=state)
        self.connection.mixer.send_commands([cmd])

    def do_fairlight_channel_afv(self, widget, *args):
        if widget.get_style_context().has_class('active'):
            state = 1
        else:
            state = 4
        cmd = FairlightStripPropertiesCommand(source=widget.source, channel=widget.channel, state=state)
        self.connection.mixer.send_commands([cmd])

    def on_fairlight_master_properties_change(self, data):
        self.set_class(self.ftb_afv, 'active', data.afv)

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
