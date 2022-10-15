# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk, GObject, Gdk

from gtk_switcher.template_i18n import TemplateLocale
from pyatem.command import KeyFillCommand, KeyPropertiesDveCommand, KeyTypeCommand, KeyCutCommand, \
    KeyPropertiesLumaCommand, KeyerKeyframeSetCommand, KeyerKeyframeRunCommand, DkeySetFillCommand, DkeySetKeyCommand, \
    DkeyGainCommand
from pyatem.field import TransitionSettingsField, KeyPropertiesDveField, KeyPropertiesLumaField, DkeyPropertiesField


@TemplateLocale(resource_path='/nl/brixit/switcher/ui/downstream-keyer.glade')
class DownstreamKeyer(Gtk.Frame):
    __gtype_name__ = 'DownstreamKeyer'

    luma_fill = Gtk.Template.Child()
    luma_key = Gtk.Template.Child()
    luma_premultiplied = Gtk.Template.Child()
    luma_clip = Gtk.Template.Child()
    luma_clip_adj = Gtk.Template.Child()
    luma_gain = Gtk.Template.Child()
    luma_gain_adj = Gtk.Template.Child()
    luma_invert = Gtk.Template.Child()

    mask_top = Gtk.Template.Child()
    mask_bottom = Gtk.Template.Child()
    mask_left = Gtk.Template.Child()
    mask_right = Gtk.Template.Child()
    mask_en = Gtk.Template.Child()

    def __init__(self, index, connection):
        self.index = index
        self.connection = connection

        self.model_changing = False
        self.slider_held = False

        super(Gtk.Frame, self).__init__()
        self.init_template()

    def set_class(self, widget, classname, state):
        if state:
            widget.get_style_context().add_class(classname)
        else:
            widget.get_style_context().remove_class(classname)

    def set_fill_model(self, model):
        self.model_changing = True
        self.luma_fill.set_model(model)
        self.model_changing = False

    def set_key_model(self, model):
        self.model_changing = True
        self.luma_key.set_model(model)
        self.model_changing = False

    def on_key_properties_base_change(self, data):
        self.model_changing = True
        self.luma_fill.set_active_id(str(data.fill_source))
        self.luma_key.set_active_id(str(data.key_source))
        self.model_changing = False

    def on_key_properties_change(self, data):
        if not isinstance(data, DkeyPropertiesField):
            return

        self.set_class(self.luma_premultiplied, 'active', data.premultiplied)
        self.set_class(self.luma_invert, 'active', data.invert_key)
        self.set_class(self.mask_en, 'active', data.masked)

        self.luma_clip.set_sensitive(not data.premultiplied)
        self.luma_gain.set_sensitive(not data.premultiplied)

        self.luma_clip_adj.set_value(data.clip)
        self.luma_gain_adj.set_value(data.gain)

        self.mask_top.set_text(str(data.top / 1000))
        self.mask_bottom.set_text(str(data.bottom / 1000))
        self.mask_left.set_text(str(data.left / 1000))
        self.mask_right.set_text(str(data.right / 1000))

    @Gtk.Template.Callback()
    def on_fill_changed(self, widget, *args):
        if self.model_changing:
            return
        source = int(widget.get_active_id())
        cmd = DkeySetFillCommand(index=self.index, source=source)
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_key_changed(self, widget, *args):
        if self.model_changing:
            return
        source = int(widget.get_active_id())
        cmd = DkeySetKeyCommand(index=self.index, source=source)
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_slider_press(self, *args):
        self.slider_held = True

    @Gtk.Template.Callback()
    def on_slider_release(self, *args):
        self.slider_held = False

    @Gtk.Template.Callback()
    def on_luma_premultiplied_clicked(self, widget, *args):
        state = widget.get_style_context().has_class('active')
        cmd = DkeyGainCommand(index=self.index, premultiplied=not state)
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_luma_invert_clicked(self, widget, *args):
        state = widget.get_style_context().has_class('active')
        cmd = DkeyGainCommand(index=self.index, invert=not state)
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_luma_clip_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = DkeyGainCommand(index=self.index, clip=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_luma_gain_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = DkeyGainCommand(index=self.index, gain=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])
