import gi

from gtk_switcher.adjustmententry import AdjustmentEntry
from gtk_switcher.dial import Dial
from pyatem.command import FairlightStripPropertiesCommand

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk

gi.require_version('Handy', '1')
from gi.repository import Handy


class AudioPage:
    def __init__(self, builder):
        self.audio_channels = builder.get_object('audio_channels')

        self.mixer = 'atem'

        self.volume_level = {}
        self.input_gain = {}
        self.pan = {}
        self.delay = {}
        self.audio_tally = {}
        self.audio_strip = {}
        self.audio_on = {}
        self.audio_afv = {}
        self.audio_monitor = {}

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

        self.model_changing = True
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
        self.model_changing = False

    def on_volume_changed(self, widget, *args):
        if self.model_changing:
            return
        if self.mixer == 'fairlight':
            cmd = FairlightStripPropertiesCommand(source=widget.source, channel=widget.channel,
                                                  volume=int(widget.get_value()))
            self.connection.mixer.send_commands([cmd])

    def on_input_gain_changed(self, widget, *args):
        if self.model_changing:
            return
        if self.mixer == 'fairlight':
            print("NEW GAIN", int(widget.get_value()))
            cmd = FairlightStripPropertiesCommand(source=widget.source, channel=widget.channel,
                                                  gain=int(widget.get_value()))
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
                alabel = 'Analog'
                if input.index > 1300 and input.index < 1400:
                    alabel = 'Mic'

                label = '{} {}'.format(alabel, input.number + 1)
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
                alabel = 'Analog'
                if input.index > 1300 and input.index < 1400:
                    alabel = 'Mic'

                label = '{} {}'.format(alabel, input.number + 1)
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
                    self.input_gain[strip_id].connect('value-changed', self.on_input_gain_changed)

                self.volume_level[strip_id].source = input.index
                self.volume_level[strip_id].channel = c if num_subchannels > 1 else -1
                self.input_gain[strip_id].source = input.index
                self.input_gain[strip_id].channel = c if num_subchannels > 1 else -1

                tally = Gtk.Box()
                tally.get_style_context().add_class('tally')
                if strip_id in self.audio_strip:
                    self.set_class(tally, 'afv', self.audio_strip[strip_id].state & 4)

                self.audio_tally[strip_id] = tally
                self.audio_channels.attach(tally, left + c, 1, 1, 1)

                input_frame = Gtk.Frame()
                input_frame.get_style_context().add_class('view')
                dial = Dial()
                dial.set_adjustment(self.input_gain[strip_id])
                gain_input = AdjustmentEntry(self.input_gain[strip_id], -100, 6)
                gain_input.get_style_context().add_class('mini')
                gain_input.set_margin_left(16)
                gain_input.set_margin_right(16)
                gain_input.set_margin_end(8)
                gain_input.set_max_width_chars(6)
                gain_input.set_width_chars(6)
                gain_input.set_alignment(xalign=0.5)
                self.hook_up_focus(gain_input)
                gain_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                gain_box.add(dial)
                gain_box.add(gain_input)
                input_frame.add(gain_box)
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
        return
        self.set_class(self.ftb_afv, 'active', data.afv)
