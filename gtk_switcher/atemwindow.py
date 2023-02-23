# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import ctypes
import json
import logging
import threading
import time
import traceback
from datetime import datetime

import gi

from gtk_switcher.debugger import DebuggerWindow
from gtk_switcher.videohubconnection import VideoHubConnection
from pyatem.hexdump import hexdump

from gtk_switcher.audio import AudioPage
from gtk_switcher.camera import CameraPage
from gtk_switcher.decorators import field, call_fields
from gtk_switcher.macroeditor import MacroEditorWindow
from gtk_switcher.media import MediaPage
from gtk_switcher.connectionwindow import ConnectionWindow
from gtk_switcher.switcher import SwitcherPage
from pyatem.command import ProgramInputCommand, PreviewInputCommand, AutoCommand, TransitionPositionCommand, \
    InputPropertiesCommand
from pyatem.protocol import AtemProtocol

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk

gi.require_version('Handy', '1')
from gi.repository import Handy


class AtemConnection(threading.Thread):
    def __init__(self, callback, disconnected, transfer_progress, download_done, connected, upload_done,
                 upload_progress):
        threading.Thread.__init__(self)
        self.name = 'Connection'
        self.callback = callback
        self.disconnected = disconnected
        self._connected = connected
        self.transfer_progress = transfer_progress
        self.download_done = download_done
        self.upload_done = upload_done
        self.upload_progress = upload_progress
        self.atem = None
        self.ip = None
        self.stop = False
        self.connected = False
        self.log = logging.getLogger('AtemConnection')

    def run(self):
        # Don't run if the ip isn't set yet
        if self.ip is None or self.ip == '0.0.0.0':
            if AtemProtocol.usb_exists():
                self.log.info(f'Connect to USB device')
                try:
                    self.mixer = AtemProtocol(usb="auto")
                except PermissionError:
                    self.log.error("Could not connect to USB device: permission denied")
                    self.log.error("The udev rules for this ATEM device might be missing on your system")
                    self.do_permission_error()
                    return
            else:
                self.log.error(f'Invalid connection parameter')
                return
        else:
            self.log.info(f'Connect to {self.ip}')
            self.mixer = AtemProtocol(self.ip)
        self.mixer.on('change', self.do_callback)
        self.mixer.on('connected', self.do_connected)
        self.mixer.on('disconnected', self.do_disconnected)
        self.mixer.on('transfer-progress', self.do_transfer_progress)
        self.mixer.on('download-done', self.do_download_done)
        self.mixer.on('upload-done', self.do_upload_done)
        self.mixer.on('upload-progress', self.do_upload_progress)
        try:
            self.mixer.connect()
        except ConnectionError as e:
            self.log.error(f"Could not connect to {self.ip}: {e}")
            return
        while not self.stop:
            try:
                self.mixer.loop()
            except Exception as e:
                traceback.print_exc()
                self.log.error(repr(e))

    def do_callback(self, *args, **kwargs):
        GLib.idle_add(self.callback, *args, **kwargs)

    def do_disconnected(self):
        self.connected = False
        GLib.idle_add(self.disconnected, "disconnected")

    def do_permission_error(self):
        self.connected = False
        GLib.idle_add(self.disconnected, "permission")

    def do_connected(self):
        self.connected = True
        GLib.idle_add(self._connected)

    def do_transfer_progress(self, store, slot, progress):
        GLib.idle_add(self.transfer_progress, store, slot, progress)

    def do_download_done(self, store, slot, data):
        GLib.idle_add(self.download_done, store, slot, data)

    def do_upload_progress(self, store, slot, percent, done, size):
        GLib.idle_add(self.upload_progress, store, slot, percent, done, size)

    def do_upload_done(self, store, slot):
        GLib.idle_add(self.upload_done, store, slot)

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
            self.log.error('Exception raise failure')


class AtemWindow(SwitcherPage, MediaPage, AudioPage, CameraPage):
    def __init__(self, application, args):
        self.application = application
        self.args = args

        self.debug = args.debug
        self.log_aw = logging.getLogger('AtemWindow')

        Handy.init()

        self.settings = Gio.Settings.new('nl.brixit.Switcher')
        self.settings.connect('changed::switcher-ip', self.on_switcher_ip_changed)
        self.settings.connect('changed::connections', self.on_connection_settings_changed)

        builder = Gtk.Builder()
        builder.set_translation_domain("openswitcher")
        builder.add_from_resource('/nl/brixit/switcher/ui/mixer.glade')
        builder.connect_signals(self)
        css = Gio.resources_lookup_data("/nl/brixit/switcher/ui/style.css", 0)

        self.provider = Gtk.CssProvider()
        self.provider.load_from_data(css.get_data())

        self.window = builder.get_object("main_window")
        self.window.set_application(self.application)
        self.headerbar = builder.get_object("headerbar")

        # Load requested view
        self.mainstack = builder.get_object("mainstack")
        self.connectionstack = builder.get_object("connectionstack")
        self.mainstack.set_visible_child_name(args.view)
        self.connectionstack.set_visible_child_name("disconnected")

        self.mainstack.connect('notify::visible-child', self.on_page_changed)

        SwitcherPage.__init__(self, builder)
        MediaPage.__init__(self, builder)
        AudioPage.__init__(self, builder)
        CameraPage.__init__(self, builder)

        self.status_model = builder.get_object('status_model')
        self.status_mode = builder.get_object('status_mode')
        self.focus_dummy = builder.get_object('focus_dummy')
        self.disable_shortcuts = False
        self.macro_edit = False

        self.timecode_mode = 0
        self.timecode_offset = 0

        self.aux_follow_audio = set()

        self.hardware_threads = {}
        self.connection_settings = {}
        self.inpr_latch = 0

        self.apply_css(self.window, self.provider)

        self.window.show_all()

        self.firmware_version = None
        self.mode = None

        self.connection = AtemConnection(self.on_change, self.on_disconnect, self.on_transfer_progress,
                                         self.on_download_done, self.on_connect, self.on_upload_done,
                                         self.on_upload_progress)

        if args.ip:
            self.connection.ip = args.ip
            if args.persist:
                self.settings.set_string('switcher-ip', args.ip)
        else:
            if self.connection.ip == "0.0.0.0":
                ConnectionWindow(self.window, self.connection, self.application)

            self.connection.ip = self.settings.get_string('switcher-ip')
        self.connection.daemon = True
        self.connection.start()

        accel = Gtk.AccelGroup()
        accel.connect(Gdk.keyval_from_name('space'), 0, 0, self.on_cut_shortcut)
        accel.connect(Gdk.keyval_from_name('ISO_Enter'), 0, 0, self.on_auto_shortcut)
        accel.connect(Gdk.keyval_from_name('Return'), 0, 0, self.on_auto_shortcut)
        accel.connect(Gdk.keyval_from_name('KP_Enter'), 0, 0, self.on_auto_shortcut)
        accel.connect(Gdk.keyval_from_name('F12'), 0, 0, self.on_debugger_shortcut)
        ctrl = Gdk.ModifierType.CONTROL_MASK
        accel.connect(Gdk.keyval_from_name('question'), ctrl, 0, self.on_help_shortcut)

        for i in range(0, 9):
            accel.connect(Gdk.keyval_from_name(str(i)), 0, 0, self.on_preview_keyboard_change)
            accel.connect(Gdk.keyval_from_name(str(i)), Gdk.ModifierType.CONTROL_MASK, 0,
                          self.on_program_keyboard_change)
            accel.connect(Gdk.keyval_from_name(str(i)), Gdk.ModifierType.MOD1_MASK, 0,
                          self.on_cutbus_keyboard_change)

        self.window.add_accel_group(accel)

        GLib.timeout_add_seconds(1, self.on_clock)

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

    def on_entry_focus(self, *args):
        self.disable_shortcuts = True

    def on_entry_unfocus(self, *args):
        self.disable_shortcuts = False
        self.focus_dummy.grab_focus()

    def on_context_menu(self, *args):
        pass

    def on_entry_activate(self, *args):
        self.focus_dummy.grab_focus()

    def hook_up_focus(self, widget):
        widget.connect("focus-in-event", self.on_entry_focus)
        widget.connect("focus-out-event", self.on_entry_unfocus)
        widget.connect("activate", self.on_entry_activate)

    def apply_css(self, widget, provider):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css, provider)

    def on_switcher_ip_changed(self, *args):
        self.log_aw.info("Connection settings changed")
        self.log_aw.info("Closing old connection...")
        self.connection.die()
        self.connection.join(timeout=1)
        for tid in self.hardware_threads:
            self.hardware_threads[tid].die()
        for me in self.me:
            self.me.remove(me)
        for widget in self.main_blocks:
            self.main_blocks.remove(widget)
        time.sleep(0.1)
        self.clear_audio_state()
        self.log_aw.info("Starting new connection to {}".format(self.settings.get_string('switcher-ip')))
        self.connection = AtemConnection(self.on_change, self.on_disconnect, self.on_transfer_progress,
                                         self.on_download_done, self.on_connect, self.on_upload_done,
                                         self.on_upload_progress)
        self.connection.daemon = True
        self.connection.ip = self.settings.get_string('switcher-ip')
        self.connection.start()

    def on_reconnect_clicked(self, widget, *args):
        self.log_aw.info("Reconnect clicked")
        self.on_switcher_ip_changed()

    def on_connection_settings_changed(self, *args):
        self.log_aw.info("Connection stored config changed")

    def set_class(self, widget, classname, state):
        if state:
            widget.get_style_context().add_class(classname)
        else:
            widget.get_style_context().remove_class(classname)

    def on_main_window_destroy(self, widget):
        Gtk.main_quit()

    def on_preferences_button_clicked(self, widget):
        ConnectionWindow(self.window, self.connection, self.application)

    def on_disconnect(self, reason):
        self.connectionstack.set_visible_child_name(reason)
        for tid in self.hardware_threads:
            self.hardware_threads[tid].die()
        self.log_aw.warning("Disconnected from mixer")

    def on_connect(self):
        self.inpr_latch = 0
        self.audio_latch = 0
        # Load stored connection-specific settings if available
        settings = self.settings.get_string('connections')
        settings = json.loads(settings)
        if self.connection.ip in settings:
            self.connection_settings = settings[self.connection.ip]
        else:
            self.connection_settings = {
                "videohubs": []
            }

        # Connect to stored videohubs
        if 'videohubs' in self.connection_settings:
            hubs = self.connection_settings['videohubs']
            for ip in hubs:
                hub = hubs[ip]
                thread = VideoHubConnection(ip, self.on_videohub_connect, self.on_videohub_disconnect,
                                            self.on_videohub_input_change, self.on_videohub_output_change,
                                            self.on_videohub_route_change)
                thread.daemon = True
                thread.id = f'hub-{ip}'
                thread.start()
                self.hardware_threads[thread.id] = thread

    def on_debugger_shortcut(self, *args):
        if self.disable_shortcuts:
            return

        DebuggerWindow(self.window, self.connection, self.application)

    def on_help_shortcut(self, *args):
        if self.disable_shortcuts:
            return

        builder = Gtk.Builder()
        builder.set_translation_domain("openswitcher")
        builder.add_from_resource('/nl/brixit/switcher/ui/shortcuts.ui')
        window = builder.get_object('shortcuts')
        window.set_transient_for(self.window)
        window.present()

    def on_videohub_connect(self, hub_id):
        self.log_aw.info(f"Connected to {hub_id}")
        from gtk_switcher.videohubbus import VideoHubBus
        for hubid in self.connection_settings['videohubs']:
            ip = self.connection_settings['videohubs'][hubid]['ip']
            for outputid in self.connection_settings['videohubs'][hubid]['outputs']:
                output = self.connection_settings['videohubs'][hubid]['outputs'][outputid]
                if output['bus']:
                    bus = VideoHubBus(self.provider, self.hardware_threads[f'hub-{ip}'], outputid)
                    self.main_blocks.add(bus)

            for me in self.me:
                if hasattr(me, 'add_router'):
                    me.add_router(self.hardware_threads[f'hub-{ip}'], self.connection_settings['videohubs'][hubid])

        self.main_blocks.show_all()

    def on_videohub_disconnect(self, hub_id):
        self.log_aw.warning(f"Disconnected from {hub_id}")

    def on_videohub_input_change(self, hub_id, index, inputs):
        pass

    def on_videohub_output_change(self, hub_id, index, outputs):
        pass

    def on_videohub_route_change(self, hub_id, index, source):
        hub = self.hardware_threads[hub_id]
        ip = hub.ip
        if 'videohubs' not in self.connection_settings:
            return

        if ip not in self.connection_settings['videohubs']:
            return

        if self.connection_settings['videohubs'][ip]['outputs'][str(index)]['rename']:
            atem_input = self.connection_settings['videohubs'][ip]['outputs'][str(index)]['source']
            new_name = hub.inputs[source]['label']
            if ':' in new_name:
                button, new_name = new_name.split(':', maxsplit=1)
                new_name = new_name.strip()
                button = button.strip()
            else:
                button = None

            cmd = InputPropertiesCommand(source_index=atem_input, label=new_name, short_label=button)
            self.connection.mixer.send_commands([cmd])

    def on_bypass_firmware_clicked(self, widget, *args):
        self.connectionstack.set_visible_child_name("connected")

    def on_change(self, field, data):
        global _callbacks
        if self.args.dump is not None and field in self.args.dump:
            if isinstance(data, bytes):
                print('== {} ({} bytes)=='.format(field, len(data)))
                hexdump(data)
            else:
                print('== {} ({} bytes)=='.format(field, len(data.raw)))
                hexdump(data.raw)
                print(data)

        # Call all the registered decorators
        call_fields(field, self, data)

        try:
            if self.inpr_latch == 1 and field != 'input-properties':
                # Run the input change event after the events on start have run
                self.inpr_latch = 2
                self.on_input_layout_change(None)
                self.on_camera_layout_change(None)

            if field == 'firmware-version':
                self.firmware_version = data
                if data.major < 2:
                    self.connectionstack.set_visible_child_name("firmware")
                elif data.minor < 28:
                    self.connectionstack.set_visible_child_name("firmware")
                else:
                    self.connectionstack.set_visible_child_name("connected")
                self.log_aw.info("Firmware: {}".format(data.version))
            elif field == 'time':
                self.on_time_sync(data)
            elif field == 'time-config':
                self.on_timecode_config_change(data)
            elif field == 'input-properties':
                # Ignore input-properties fields in the initial connection
                if self.inpr_latch == 0:
                    self.inpr_latch = 1
                elif self.inpr_latch == 1:
                    return
                else:
                    self.on_input_layout_change(data)
                    self.on_camera_layout_change(data)
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
                self.log_aw.info("Mixer model: {}".format(data.name))
            elif field == 'video-mode':
                self.mode = data
                for me in self.me:
                    me.set_mode(data)
                self.status_mode.set_text(data.get_label())
            elif field == 'dkey-properties':
                self.on_dsk_change(data)
            elif field == 'dkey-state':
                self.on_dsk_state_change(data)
            elif field == 'mediaplayer-slots':
                self.on_mediaplayer_slots_change(data)
            elif field == 'mediaplayer-file-info':
                self.on_mediaplayer_file_info_change(data)
            elif field == 'mediaplayer-selected':
                self.on_mediaplayer_switcher_source_change(data)
                self.on_mediaplayer_media_source_change(data)
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
            elif field == 'atem-eq-band-properties':
                self.on_fairlight_eq_band_change(data)
            elif field == 'audio-input':
                self.on_audio_input_change(data)
            elif field == 'fairlight-strip-properties':
                self.on_fairlight_strip_properties_change(data)
            elif field == 'fairlight-tally':
                self.on_fairlight_tally_change(data)
            elif field == 'audio-mixer-tally':
                self.on_audio_mixer_tally_change(data)
            elif field == 'audio-mixer-master-properties':
                self.on_audio_mixer_master_properties_change(data)
            elif field == 'audio-mixer-monitor-properties':
                self.on_audio_monitor_properties_change(data)
            elif field == 'key-properties-base':
                self.on_key_properties_base_change(data)
            elif field == 'key-properties-luma':
                self.on_key_properties_luma_change(data)
            elif field == 'key-properties-dve':
                self.on_key_properties_dve_change(data)
            elif field == 'key-properties-advanced-chroma':
                self.on_key_properties_advanced_chroma_change(data)
            elif field == 'key-properties-advanced-chroma-colorpicker':
                self.on_key_properties_advanced_chroma_colorpicker_change(data)
            elif field == 'recording-settings':
                self.on_stream_recording_setting_change(data)
            elif field == 'recording-disk':
                self.on_stream_recording_disks_change(data)
            elif field == 'recording-status':
                self.on_stream_recording_status_change(data)
            elif field == 'recording-duration':
                self.on_stream_recording_duration_change(data)
            elif field == 'aux-output-source':
                self.on_aux_output_source_change(data)
                if data.index in self.aux_follow_audio:
                    self.on_aux_monitor_source_change(data)
            elif field == 'dkey-properties-base':
                self.on_dkey_properties_base_change(data)
            elif field == 'macro-properties':
                self.on_macro_properties_change(data)
            elif field == 'audio-meter-levels':
                self.on_audio_meter_levels_change(data)
            elif field == 'fairlight-meter-levels':
                self.on_fairlight_meter_levels_change(data)
            elif field == 'fairlight-master-levels':
                self.on_fairlight_master_levels_change(data)
            elif field == 'streaming-service':
                self.on_streaming_service_change(data)
            elif field == 'streaming-audio-bitrate':
                self.on_streaming_audio_bitrate_change(data)
            elif field == 'streaming-stats':
                self.on_streaming_stats_change(data)
            elif field == 'streaming-status':
                self.on_streaming_status_change(data)

            else:
                if field == 'time':
                    return
                if not self.debug and self.args.dump is not None and len(self.args.dump) > 0:
                    return
                if isinstance(data, bytes):
                    self.log_aw.debug(field)
                else:
                    self.log_aw.debug(data)
        except Exception as e:
            # When the connection breaks on initial sync the UI events are queued but no mixer state is present
            # catch the exceptions and bring the software into the disconnected state cleanly
            if self.connection.connected:
                raise
            self.log_aw.error(f"Exception while disconnected: {e}")

    def on_time_sync(self, data):
        seconds = data.total_seconds()
        if self.timecode_mode == 0:
            self.timecode_offset = seconds - datetime.now().timestamp()
        else:
            t = time.localtime()
            tod = 3600 * t.tm_hour + 60 * t.tm_min + t.tm_sec
            self.timecode_offset = tod - seconds

    def on_timecode_config_change(self, data):
        self.timecode_mode = data.mode

    def on_clock(self):
        self.on_clock_stream_recorder()
        self.on_clock_stream_live()
        return True

    def on_transfer_progress(self, store, slot, progress):
        if store == 0:
            # Media transfer
            self.on_media_transfer_progress(slot, progress)

    def on_download_done(self, store, slot, data):
        if store == 0:
            # Media transfer
            self.on_media_download_done(slot, data)
        if store == 0xffff:
            # Macro fetch
            if self.macro_edit:
                self.macro_edit = False

                MacroEditorWindow(self.window, self.application, self.connection, slot, data)

    def on_upload_done(self, store, slot):
        if store == 0:
            self.on_media_upload_done(store, slot)

    def on_upload_progress(self, store, slot, percent, done, size):
        if store == 0:
            self.on_media_upload_progress(store, slot, percent, done, size)

    def on_page_changed(self, widget, *args):
        page = widget.get_visible_child_name()
        if page == 'media':
            self.on_page_media_open()
        if page == 'audio':
            self.enable_levels()
        else:
            self.disable_levels()

#    @field('input-properties')
#    def on_input_properties_changed(self, data):
#        print(data)
