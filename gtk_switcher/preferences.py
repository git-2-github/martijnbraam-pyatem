# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import json

import gi

from pyatem.command import MultiviewInputCommand, VideoModeCommand, AutoInputVideoModeCommand
from pyatem.field import InputPropertiesField

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk

gi.require_version('Handy', '1')
from gi.repository import Handy


class PreferencesWindow:
    def __init__(self, parent, application, connection):
        self.application = application
        self.connection = connection
        self.settings = Gio.Settings.new('nl.brixit.Switcher')
        self.model_changing = False
        self.config = {}

        builder = Gtk.Builder()
        builder.set_translation_domain("openswitcher")
        builder.add_from_resource('/nl/brixit/switcher/ui/preferences.glade')
        builder.connect_signals(self)
        css = Gio.resources_lookup_data("/nl/brixit/switcher/ui/style.css", 0)

        self.provider = Gtk.CssProvider()
        self.provider.load_from_data(css.get_data())

        self.window = builder.get_object("window")
        self.window.set_application(self.application)

        self.multiview_window = []

        self.model_me1 = builder.get_object("model_me1")
        self.model_aux = builder.get_object("model_aux")
        self.model_route_inputs = Gtk.ListStore(str, str)

        # Load requested view
        self.mainstack = builder.get_object("mainstack")
        self.settingsstack = builder.get_object("settingsstack")

        self.video_mode = builder.get_object('video_mode')
        self.current_video_mode = builder.get_object('current_video_mode')
        self.model_video_mode = builder.get_object('model_video_mode')
        self.multiview_mode = builder.get_object('multiview_mode')
        self.current_multiview_mode = builder.get_object('current_multiview_mode')
        self.model_multiview_mode = builder.get_object('model_multiview_mode')
        self.downconvert_mode = builder.get_object('downconvert_mode')
        self.current_downconvert_mode = builder.get_object('current_downconvert_mode')
        self.model_downconvert_mode = builder.get_object('model_downconvert_mode')

        self.multiview_layout = builder.get_object("multiview_layout")
        self.multiview_tl = builder.get_object("multiview_tl")
        self.multiview_tr = builder.get_object("multiview_tr")
        self.multiview_bl = builder.get_object("multiview_bl")
        self.multiview_br = builder.get_object("multiview_br")
        self.multiview_swap = builder.get_object("multiview_swap")
        self.multiview_layout = builder.get_object("multiview_layout")

        self.videohubs = builder.get_object("videohubs")

        self.apply_css(self.window, self.provider)

        self.window.set_transient_for(parent)
        self.window.set_modal(True)
        self.load_models()
        self.load_preferences()
        self.load_config()
        self.connection.mixer.on('change:multiviewer-properties:*', self.make_multiviewer)
        self.connection.mixer.on('change:multiviewer-input:*', self.update_multiviewer_input)
        self.connection.mixer.on('change:video-mode', self.update_mode_models)
        self.window.show_all()

    def load_config(self):
        from gtk_switcher.videohub import VideoHub

        connections = self.settings.get_string('connections')
        connections = json.loads(connections)
        if self.connection.ip in connections:
            self.config = connections[self.connection.ip]
        else:
            self.config = {
                'videohubs': {}
            }

        for ip in self.config['videohubs']:
            config = self.config['videohubs'][ip]
            hub = VideoHub()
            hub.set_input_model(self.model_route_inputs)
            hub.connect('config-changed', self.on_videohub_config_changed)
            hub.connect('ip-changed', self.on_videohub_ip_changed)
            hub.connect('deleted', self.on_videohub_deleted)
            hub.load(config)
            self.videohubs.add(hub)
        self.videohubs.show_all()

    def on_videohub_config_changed(self, widget, config):
        config = json.loads(config)
        self.config['videohubs'][config['ip']] = config
        self.save_config()

    def on_videohub_ip_changed(self, widget, old_ip, new_ip):
        if old_ip is None:
            return

        hub_config = self.config['videohubs'][old_ip]
        del self.config['videohubs'][old_ip]
        self.config['videohubs'][new_ip] = hub_config
        self.save_config()

    def on_videohub_deleted(self, widget, ip):
        del self.config['videohubs'][ip]
        self.videohubs.remove(widget)
        self.save_config()

    def save_config(self):
        connections = self.settings.get_string('connections')
        connections = json.loads(connections)
        connections[self.connection.ip] = self.config
        connections = json.dumps(connections)
        self.settings.set_string('connections', connections)

    def load_models(self):
        inputs = self.connection.mixer.mixerstate['input-properties']
        self.model_changing = True
        self.model_route_inputs.clear()
        self.model_route_inputs.append(["", ""])
        for i in inputs.values():
            if i.available_me1:
                self.model_me1.append([str(i.index), i.name])

            if i.available_aux:
                self.model_aux.append([str(i.index), i.name])

            if i.port_type == InputPropertiesField.PORT_EXTERNAL:
                self.model_route_inputs.append([str(i.index), f"{i.index}: {i.name}"])

        self.model_changing = False

        self.update_mode_models(None, update_active=True)

    def update_mode_models(self, arg, update_active=False):
        current_mode = self.connection.mixer.mixerstate['video-mode']
        if 'auto-input-video-mode' in self.connection.mixer.mixerstate:
            am = self.connection.mixer.mixerstate['auto-input-video-mode']
            has_auto = True
            automode = am.enabled
        else:
            has_auto = False
            automode = False

        old_video_mode = self.video_mode.get_active_id()
        old_multiview_mode = self.multiview_mode.get_active_id()
        old_downscale_mode = self.downconvert_mode.get_active_id()

        self.current_video_mode.set_text(current_mode.get_label())
        self.model_video_mode.clear()
        self.model_multiview_mode.clear()
        self.model_downconvert_mode.clear()

        if has_auto:
            self.model_video_mode.append(['auto', 'Auto'])

        cmi = {'multiview': [], 'downscale': []}
        for mode in self.connection.mixer.mixerstate['video-mode-capability'].modes:
            self.model_video_mode.append([str(mode['modenum']), mode['mode'].get_label()])
            if mode['modenum'] == current_mode.mode:
                cmi = mode
                for mv_mode in mode['multiview']:
                    self.model_multiview_mode.append([str(mv_mode.mode), mv_mode.get_label()])
                for dc_mode in mode['downscale']:
                    self.model_downconvert_mode.append([str(dc_mode.mode), dc_mode.get_label()])

        if update_active:
            if automode:
                self.video_mode.set_active_id('auto')
            else:
                self.video_mode.set_active_id(str(current_mode.mode))

            if len(cmi['multiview']) == 1:
                self.multiview_mode.set_active_id(str(cmi['multiview'][0].mode))

            if len(cmi['downscale']) == 1:
                self.downconvert_mode.set_active_id(str(cmi['downscale'][0].mode))

        else:
            self.video_mode.set_active_id(old_video_mode)
            self.multiview_mode.set_active_id(old_multiview_mode)
            self.downconvert_mode.set_active_id(old_downscale_mode)

    def on_video_mode_selection_changed(self, widget):
        self.model_multiview_mode.clear()
        self.model_downconvert_mode.clear()
        current_mode = None
        for mode in self.connection.mixer.mixerstate['video-mode-capability'].modes:
            if str(mode['modenum']) == self.video_mode.get_active_id():
                current_mode = mode
                for mv_mode in mode['multiview']:
                    self.model_multiview_mode.append([str(mv_mode.mode), mv_mode.get_label()])
                for dc_mode in mode['downscale']:
                    self.model_downconvert_mode.append([str(dc_mode.mode), dc_mode.get_label()])

        if current_mode:
            if len(current_mode['multiview']) == 1:
                self.multiview_mode.set_active_id(str(current_mode['multiview'][0].mode))
            if len(current_mode['downscale']) == 1:
                self.downconvert_mode.set_active_id(str(current_mode['downscale'][0].mode))

    def load_preferences(self):
        state = self.connection.mixer.mixerstate

        if 'multiviewer-properties' in state and 'multiviewer-input' in state:
            self.make_multiviewer()

    def update_multiviewer_input(self, input):
        state = self.connection.mixer.mixerstate

        if 'multiviewer-properties' in state and 'multiviewer-input' in state:
            self.make_multiviewer()

    def make_multiviewer(self, *args):
        state = self.connection.mixer.mixerstate
        multiviewer = state['multiviewer-properties'][0]
        self.multiview_window = []
        for widget in self.multiview_layout:
            self.multiview_layout.remove(widget)

        sideways = multiviewer.layout == 5 or multiviewer.layout == 10

        if sideways:
            if not multiviewer.top_left_small:
                self.make_multiview_window(0, 0)
            if not multiviewer.bottom_left_small:
                self.make_multiview_window(0, 1)
            if not multiviewer.top_right_small:
                self.make_multiview_window(1, 0)
            if not multiviewer.bottom_right_small:
                self.make_multiview_window(1, 1)
        else:
            if not multiviewer.top_left_small:
                self.make_multiview_window(0, 0)
            if not multiviewer.top_right_small:
                self.make_multiview_window(1, 0)
            if not multiviewer.bottom_left_small:
                self.make_multiview_window(0, 1)
            if not multiviewer.bottom_right_small:
                self.make_multiview_window(1, 1)

        if multiviewer.top_left_small:
            self.make_split_multiview_window(0, 0, False)
        if multiviewer.top_right_small:
            self.make_split_multiview_window(1, 0, False)
        if multiviewer.top_left_small:
            self.make_split_multiview_window(0, 0, True)
        if multiviewer.top_right_small:
            self.make_split_multiview_window(1, 0, True)

        if multiviewer.bottom_left_small:
            self.make_split_multiview_window(0, 1, False)
        if multiviewer.bottom_right_small:
            self.make_split_multiview_window(1, 1, False)
        if multiviewer.bottom_left_small:
            self.make_split_multiview_window(0, 1, True)
        if multiviewer.bottom_right_small:
            self.make_split_multiview_window(1, 1, True)

        for index, window in enumerate(self.multiview_window):
            window.index = index

        self.multiview_tl.set_active(not multiviewer.top_left_small)
        self.multiview_tr.set_active(not multiviewer.top_right_small)
        self.multiview_bl.set_active(not multiviewer.bottom_left_small)
        self.multiview_br.set_active(not multiviewer.bottom_right_small)
        self.multiview_swap.set_active(multiviewer.flip)
        self.multiview_layout.show_all()

    def make_split_multiview_window(self, x, y, second=False):
        x *= 2
        y *= 2
        if not second:
            self.make_multiview_window(x, y, 1, 1)
            self.make_multiview_window(x + 1, y, 1, 1)
        else:
            self.make_multiview_window(x, y + 1, 1, 1)
            self.make_multiview_window(x + 1, y + 1, 1, 1)

    def make_multiview_window(self, x, y, w=2, h=2):
        x *= w
        y *= h
        routable = self.connection.mixer.mixerstate['topology'].multiviewer_routable
        frame = Gtk.Frame()
        frame.get_style_context().add_class('view')

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add(box)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_left(8)
        box.set_margin_right(8)

        index = len(self.multiview_window)
        if index in self.connection.mixer.mixerstate['multiviewer-input'][0]:
            input = self.connection.mixer.mixerstate['multiviewer-input'][0][index]
            ip = self.connection.mixer.mixerstate['input-properties'][input.source]

            if routable:
                input_select = Gtk.ComboBox.new_with_model(self.model_aux)
                input_select.set_entry_text_column(1)
                input_select.set_id_column(0)
                input_select.window = index
                renderer = Gtk.CellRendererText()
                input_select.pack_start(renderer, True)
                input_select.add_attribute(renderer, "text", 1)
                input_select.set_active_id(str(input.source))
                input_select.set_margin_bottom(16)
                input_select.connect('changed', self.on_multiview_window_changed)
                box.add(input_select)
            else:
                input_label = Gtk.Label(ip.name)
                input_label.set_margin_bottom(16)
                box.add(input_label)

            buttonbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            box.pack_end(buttonbox, False, False, 0)
            if input.vu:
                vu = self.connection.mixer.mixerstate['multiviewer-vu'][0][index]
                icon = Gtk.Image.new_from_resource("/nl/brixit/switcher/icons/multiview-vu.svg")
                vubutton = Gtk.ToggleButton(image=icon)
                vubutton.set_active(vu.enabled)
                buttonbox.add(vubutton)
            if input.safearea:
                sa = self.connection.mixer.mixerstate['multiviewer-safe-area'][0][index]
                icon = Gtk.Image.new_from_resource("/nl/brixit/switcher/icons/multiview-safearea.svg")
                sabutton = Gtk.ToggleButton(image=icon)
                sabutton.set_active(sa.enabled)
                buttonbox.add(sabutton)

        self.multiview_layout.attach(frame, x, y, w, h)
        self.multiview_window.append(frame)

    def on_multiview_window_changed(self, widget):
        if self.model_changing:
            return
        cmd = MultiviewInputCommand(index=0, window=widget.window, source=int(widget.get_active_id()))
        self.connection.mixer.send_commands([cmd])

    def apply_css(self, widget, provider):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css, provider)

    def on_set_video_mode_clicked(self, widget):
        cmds = []
        if 'auto-input-video-mode' in self.connection.mixer.mixerstate:
            am = self.connection.mixer.mixerstate['auto-input-video-mode']
            if am.enabled and self.video_mode.get_active_id() != 'auto':
                cmds.append(AutoInputVideoModeCommand(False))
            if not am.enabled and self.video_mode.get_active_id() == 'auto':
                cmd = AutoInputVideoModeCommand(True)
                self.connection.mixer.send_commands([cmd])
                return

        cmds.append(VideoModeCommand(int(self.video_mode.get_active_id())))
        self.connection.mixer.send_commands(cmds)

    def on_add_videohub_clicked(self, widget, *args):
        from gtk_switcher.videohub import VideoHub

        hub = VideoHub()
        hub.set_input_model(self.model_route_inputs)
        hub.connect('config-changed', self.on_videohub_config_changed)
        hub.connect('ip-changed', self.on_videohub_ip_changed)
        hub.connect('deleted', self.on_videohub_deleted)
        self.videohubs.add(hub)
        self.videohubs.show_all()
