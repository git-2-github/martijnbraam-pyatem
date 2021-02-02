import ctypes
import threading
import time

import gi
from hexdump import hexdump

from gtk_switcher.preferenceswindow import PreferencesWindow
from pyatem.command import ProgramInputCommand, PreviewInputCommand, CutCommand, AutoCommand, TransitionSettingsCommand, \
    TransitionPreviewCommand, ColorGeneratorCommand, FadeToBlackCommand
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
    def __init__(self, application):
        self.application = application

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

        self.program_bus = builder.get_object('program')
        self.preview_bus = builder.get_object('preview')
        self.tbar_flip = False
        self.tbar = builder.get_object('tbar')
        self.tbar_adj = builder.get_object('tbar_adj')
        self.transition_progress = builder.get_object('transition_progress')
        self.last_transition_state = False
        self.auto = builder.get_object('auto')

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

        self.onair_key1 = builder.get_object('onair_key1')
        self.onair_key2 = builder.get_object('onair_key2')
        self.onair_key3 = builder.get_object('onair_key3')
        self.onair_key4 = builder.get_object('onair_key4')

        self.prev_trans = builder.get_object('prev_trans')

        self.color1 = builder.get_object('color1')
        self.color2 = builder.get_object('color2')

        self.ftb = builder.get_object('ftb')

        self.status_model = builder.get_object('status_model')
        self.status_mode = builder.get_object('status_mode')

        self.apply_css(self.window, self.provider)

        self.window.show_all()

        self.firmware_version = None

        self.connection = AtemConnection(self.on_change)

        if self.connection.ip == "0.0.0.0":
            PreferencesWindow(self.window)

        self.connection.ip = self.settings.get_string('switcher-ip')
        self.connection.daemon = True
        self.connection.start()

        Gtk.main()

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

    def on_cut_clicked(self, widget):
        cmd = CutCommand(index=0)
        self.connection.mixer.send_commands([cmd])

    def on_auto_clicked(self, widget):
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

    def on_change(self, field, data):
        if field == 'firmware-version':
            self.firmware_version = data
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
        elif field == 'fade-to-black-state':
            self.on_ftb_state_change(data)
        elif field == 'mixer-effect-config':
            self.on_mixer_effect_config_change(data)
        elif field == 'topology':
            print('---------------------------------')
            print("Got topology field:")
            hexdump(data)
            print('---------------------------------')
        elif field == 'product-name':
            self.status_model.set_text(data.name)
        elif field == 'video-mode':
            self.status_mode.set_text(data.get_label())
        else:
            print(field)

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

    def on_transition_position_change(self, data):
        if data.in_transition:
            self.auto.get_style_context().add_class('program')
        else:
            self.auto.get_style_context().remove_class('program')

        if data.in_transition != self.last_transition_state:
            self.last_transition_state = data.in_transition
            if not data.in_transition:
                # Transition just ended, perform the flip
                self.tbar_flip = not self.tbar_flip

        self.transition_progress.set_inverted(self.tbar_flip)
        self.transition_progress.set_fraction(data.position)

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

        row1_ext = external
        row2_ext = [None] * len(external)
        if len(external) > 8:
            row1_ext = external[0:8]
            row2_ext = external[8:] + [None] * (16 - len(external))

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
                    spacer.set_size_request(24, 24)
                    spacer.source_index = -1
                    pspacer = Gtk.Box()
                    pspacer.set_size_request(24, 24)
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
