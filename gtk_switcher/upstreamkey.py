# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk, GObject, Gdk

from gtk_switcher.template_i18n import TemplateLocale
from pyatem.command import KeyFillCommand, KeyPropertiesDveCommand, KeyTypeCommand, KeyCutCommand, \
    KeyPropertiesLumaCommand, KeyerKeyframeSetCommand, KeyerKeyframeRunCommand, KeyPropertiesAdvancedChromaCommand, \
    KeyPropertiesAdvancedChromaColorpickerCommand
from pyatem.field import TransitionSettingsField, KeyPropertiesDveField, KeyPropertiesLumaField, \
    KeyPropertiesAdvancedChromaField


@TemplateLocale(resource_path='/nl/brixit/switcher/ui/upstream-keyer.glade')
class UpstreamKeyer(Gtk.Frame):
    __gtype_name__ = 'UpstreamKeyer'

    keyer_stack = Gtk.Template.Child()
    mask_top = Gtk.Template.Child()
    mask_bottom = Gtk.Template.Child()
    mask_left = Gtk.Template.Child()
    mask_right = Gtk.Template.Child()
    mask_en = Gtk.Template.Child()

    luma_fill = Gtk.Template.Child()
    luma_key = Gtk.Template.Child()
    luma_premultiplied = Gtk.Template.Child()
    luma_clip = Gtk.Template.Child()
    luma_clip_adj = Gtk.Template.Child()
    luma_gain = Gtk.Template.Child()
    luma_gain_adj = Gtk.Template.Child()
    luma_invert = Gtk.Template.Child()

    chroma_sample = Gtk.Template.Child()
    chroma_sample_pick = Gtk.Template.Child()
    chroma_sample_preview = Gtk.Template.Child()

    chroma_fill = Gtk.Template.Child()
    chroma_foreground_adj = Gtk.Template.Child()
    chroma_background_adj = Gtk.Template.Child()
    chroma_edge_adj = Gtk.Template.Child()
    chroma_spill_adj = Gtk.Template.Child()
    chroma_flare_adj = Gtk.Template.Child()
    chroma_brightness_adj = Gtk.Template.Child()
    chroma_contrast_adj = Gtk.Template.Child()
    chroma_saturation_adj = Gtk.Template.Child()
    chroma_red_adj = Gtk.Template.Child()
    chroma_green_adj = Gtk.Template.Child()
    chroma_blue_adj = Gtk.Template.Child()

    dve_fill = Gtk.Template.Child()
    dve_shadow_en = Gtk.Template.Child()

    dve_pos_x_adj = Gtk.Template.Child()
    dve_pos_y_adj = Gtk.Template.Child()
    dve_size_x_adj = Gtk.Template.Child()
    dve_size_y_adj = Gtk.Template.Child()
    dve_light_angle_adj = Gtk.Template.Child()
    dve_light_altitude_adj = Gtk.Template.Child()

    dve_border_en = Gtk.Template.Child()
    dve_border_color = Gtk.Template.Child()
    dve_border_opacity = Gtk.Template.Child()
    dve_border_outer_width_adj = Gtk.Template.Child()
    dve_border_inner_width_adj = Gtk.Template.Child()
    dve_border_outer_soften_adj = Gtk.Template.Child()
    dve_border_inner_soften_adj = Gtk.Template.Child()
    dve_border_bevel_position_adj = Gtk.Template.Child()
    dve_border_bevel_soften_adj = Gtk.Template.Child()

    dve_set_a = Gtk.Template.Child()
    dve_set_b = Gtk.Template.Child()

    def __init__(self, index, keyer, connection):
        self.index = index
        self.keyer = keyer
        self.connection = connection

        self.model_changing = False
        self.slider_held = False

        super(Gtk.Frame, self).__init__()
        self.init_template()

    def __repr__(self):
        return '<UpstreamKeyer me={} keyer={}>'.format(self.index, self.keyer)

    def set_class(self, widget, classname, state):
        if state:
            widget.get_style_context().add_class(classname)
        else:
            widget.get_style_context().remove_class(classname)

    def set_fill_model(self, model):
        self.model_changing = True
        self.dve_fill.set_model(model)
        self.luma_fill.set_model(model)
        self.chroma_fill.set_model(model)
        self.model_changing = False

    def set_key_model(self, model):
        self.model_changing = True
        self.luma_key.set_model(model)
        self.model_changing = False

    def on_key_properties_base_change(self, data):
        self.model_changing = True
        self.dve_fill.set_active_id(str(data.fill_source))
        self.luma_fill.set_active_id(str(data.fill_source))
        self.chroma_fill.set_active_id(str(data.fill_source))
        self.luma_key.set_active_id(str(data.key_source))

        if data.type == 0:
            self.keyer_stack.set_visible_child_name('key_luma')
        elif data.type == 1:
            self.keyer_stack.set_visible_child_name('key_chroma')
        elif data.type == 2:
            self.keyer_stack.set_visible_child_name('key_pattern')
        elif data.type == 3:
            self.keyer_stack.set_visible_child_name('key_dve')

        self.model_changing = False

        if data.type != 3:
            self.set_class(self.mask_en, 'active', data.mask_enabled)

            self.mask_top.set_text(str(data.mask_top / 1000))
            self.mask_bottom.set_text(str(data.mask_bottom / 1000))
            self.mask_left.set_text(str(data.mask_left / 1000))
            self.mask_right.set_text(str(data.mask_right / 1000))

    def on_key_properties_luma_change(self, data):
        if not isinstance(data, KeyPropertiesLumaField):
            return

        self.set_class(self.luma_premultiplied, 'active', data.premultiplied)
        self.set_class(self.luma_invert, 'active', data.key_inverted)

        self.luma_clip.set_sensitive(not data.premultiplied)
        self.luma_gain.set_sensitive(not data.premultiplied)

        self.luma_clip_adj.set_value(data.clip)
        self.luma_gain_adj.set_value(data.gain)

    def on_key_properties_dve_change(self, data):
        if not isinstance(data, KeyPropertiesDveField):
            return

        self.set_class(self.dve_shadow_en, 'active', data.shadow_enabled)
        self.set_class(self.dve_border_en, 'active', data.border_enabled)

        self.dve_pos_x_adj.set_value(data.pos_x)
        self.dve_pos_y_adj.set_value(data.pos_y)
        self.dve_size_x_adj.set_value(data.size_x)
        self.dve_size_y_adj.set_value(data.size_y)
        self.dve_light_angle_adj.set_value(data.light_angle)
        self.dve_light_altitude_adj.set_value(data.light_altitude)

        self.dve_border_opacity.set_value(data.border_opacity)
        self.dve_border_outer_width_adj.set_value(data.border_outer_width)
        self.dve_border_inner_width_adj.set_value(data.border_inner_width)
        self.dve_border_outer_soften_adj.set_value(data.border_outer_softness)
        self.dve_border_inner_soften_adj.set_value(data.border_inner_softness)
        self.dve_border_bevel_position_adj.set_value(data.border_bevel_position)
        self.dve_border_bevel_soften_adj.set_value(data.border_bevel_softness)

        r, g, b = data.get_border_color_rgb()
        color = Gdk.RGBA()
        color.red = r
        color.green = g
        color.blue = b
        color.alpha = 1.0
        self.dve_border_color.set_rgba(color)

        self.set_class(self.mask_en, 'active', data.mask_enabled)

        self.mask_top.set_text(str(data.mask_top / 1000))
        self.mask_bottom.set_text(str(data.mask_bottom / 1000))
        self.mask_left.set_text(str(data.mask_left / 1000))
        self.mask_right.set_text(str(data.mask_right / 1000))

    def on_advanced_chroma_change(self, data):
        if not isinstance(data, KeyPropertiesAdvancedChromaField):
            return

        self.model_changing = True
        self.chroma_foreground_adj.set_value(data.foreground)
        self.chroma_background_adj.set_value(data.background)
        self.chroma_edge_adj.set_value(data.key_edge)
        self.chroma_spill_adj.set_value(data.spill_suppress)
        self.chroma_flare_adj.set_value(data.flare_suppress)
        self.chroma_brightness_adj.set_value(data.brightness)
        self.chroma_contrast_adj.set_value(data.contrast)
        self.chroma_saturation_adj.set_value(data.saturation)
        self.chroma_red_adj.set_value(data.red)
        self.chroma_green_adj.set_value(data.green)
        self.chroma_blue_adj.set_value(data.blue)
        self.model_changing = False

    def on_chroma_picker_change(self, data):
        self.set_class(self.chroma_sample_pick, 'active', data.cursor)
        self.set_class(self.chroma_sample_preview, 'active', data.preview)

        r, g, b = data.get_rgb()
        color = Gdk.RGBA()
        color.red = r
        color.green = g
        color.blue = b
        color.alpha = 1.0

        self.chroma_sample.set_rgba(color)

    @Gtk.Template.Callback()
    def on_fill_changed(self, widget, *args):
        if self.model_changing:
            return
        source = int(widget.get_active_id())
        cmd = KeyFillCommand(index=self.index, keyer=self.keyer, source=source)
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_key_changed(self, widget, *args):
        if self.model_changing:
            return
        source = int(widget.get_active_id())
        cmd = KeyCutCommand(index=self.index, keyer=self.keyer, source=source)
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_slider_press(self, *args):
        self.slider_held = True

    @Gtk.Template.Callback()
    def on_slider_release(self, *args):
        self.slider_held = False

    @Gtk.Template.Callback()
    def on_dve_pos_x_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = KeyPropertiesDveCommand(index=self.index, keyer=self.keyer, pos_x=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_pos_y_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = KeyPropertiesDveCommand(index=self.index, keyer=self.keyer, pos_y=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_size_x_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = KeyPropertiesDveCommand(index=self.index, keyer=self.keyer, size_x=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_size_y_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = KeyPropertiesDveCommand(index=self.index, keyer=self.keyer, size_y=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_shadow_en_clicked(self, widget):
        state = widget.get_style_context().has_class('active')
        cmd = KeyPropertiesDveCommand(index=self.index, keyer=self.keyer, shadow_enabled=not state)
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_light_angle_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = KeyPropertiesDveCommand(index=self.index, keyer=self.keyer, angle=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_light_altitude_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = KeyPropertiesDveCommand(index=self.index, keyer=self.keyer, altitude=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_border_en_clicked(self, widget):
        state = widget.get_style_context().has_class('active')
        cmd = KeyPropertiesDveCommand(index=self.index, keyer=self.keyer, border_enabled=not state)
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_border_color_color_set(self, widget):
        color = widget.get_rgba()
        cmd = KeyPropertiesDveCommand(index=self.index, keyer=self.keyer)
        cmd.set_border_color_rgb(color.red, color.green, color.blue)
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_border_opacity_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = KeyPropertiesDveCommand(index=self.index, keyer=self.keyer, border_opacity=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_border_outer_width_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = KeyPropertiesDveCommand(index=self.index, keyer=self.keyer, outer_width=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_border_inner_width_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = KeyPropertiesDveCommand(index=self.index, keyer=self.keyer, inner_width=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_border_outer_soften_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = KeyPropertiesDveCommand(index=self.index, keyer=self.keyer, outer_softness=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_border_inner_soften_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = KeyPropertiesDveCommand(index=self.index, keyer=self.keyer, inner_softness=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_border_bevel_soften_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = KeyPropertiesDveCommand(index=self.index, keyer=self.keyer, bevel_softness=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_border_bevel_position_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = KeyPropertiesDveCommand(index=self.index, keyer=self.keyer, bevel_position=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_keyer_stack_visible_child_notify(self, widget, *args):
        if self.model_changing:
            return
        state = widget.get_visible_child_name()
        if state == 'key_luma':
            cmd = KeyTypeCommand(index=self.index, keyer=self.keyer, type=KeyTypeCommand.LUMA)
        elif state == 'key_chroma':
            cmd = KeyTypeCommand(index=self.index, keyer=self.keyer, type=KeyTypeCommand.CHROMA)
        elif state == 'key_pattern':
            cmd = KeyTypeCommand(index=self.index, keyer=self.keyer, type=KeyTypeCommand.PATTERN)
        elif state == 'key_dve':
            cmd = KeyTypeCommand(index=self.index, keyer=self.keyer, type=KeyTypeCommand.DVE)

        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_luma_premultiplied_clicked(self, widget, *args):
        state = widget.get_style_context().has_class('active')
        cmd = KeyPropertiesLumaCommand(index=self.index, keyer=self.keyer, premultiplied=not state)
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_luma_invert_clicked(self, widget, *args):
        state = widget.get_style_context().has_class('active')
        cmd = KeyPropertiesLumaCommand(index=self.index, keyer=self.keyer, invert_key=not state)
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_luma_clip_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = KeyPropertiesLumaCommand(index=self.index, keyer=self.keyer, clip=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_luma_gain_adj_value_changed(self, widget):
        if not self.slider_held:
            return

        cmd = KeyPropertiesLumaCommand(index=self.index, keyer=self.keyer, gain=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_lock_toggled(self, widget):
        self.set_class(widget, 'program', not widget.get_active)
        self.dve_set_a.set_sensitive(not widget.get_active())
        self.dve_set_b.set_sensitive(not widget.get_active())

    @Gtk.Template.Callback()
    def on_dve_set_a_clicked(self, widget):
        cmd = KeyerKeyframeSetCommand(index=self.index, keyer=self.keyer, keyframe='A')
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_set_b_clicked(self, widget):
        cmd = KeyerKeyframeSetCommand(index=self.index, keyer=self.keyer, keyframe='B')
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_run_full_clicked(self, widget):
        cmd = KeyerKeyframeRunCommand(index=self.index, keyer=self.keyer, run_to='Full')
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_run_a_clicked(self, widget):
        cmd = KeyerKeyframeRunCommand(index=self.index, keyer=self.keyer, run_to='A')
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_dve_run_b_clicked(self, widget):
        cmd = KeyerKeyframeRunCommand(index=self.index, keyer=self.keyer, run_to='B')
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_chroma_pick_clicked(self, widget):
        state = widget.get_style_context().has_class('active')
        cmd = KeyPropertiesAdvancedChromaColorpickerCommand(index=self.index, keyer=self.keyer, cursor=not state)
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_chroma_preview_clicked(self, widget):
        state = widget.get_style_context().has_class('active')
        cmd = KeyPropertiesAdvancedChromaColorpickerCommand(index=self.index, keyer=self.keyer, preview=not state)
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_chroma_foreground_adj_value_changed(self, widget):
        if not self.slider_held:
            return
        cmd = KeyPropertiesAdvancedChromaCommand(index=self.index, keyer=self.keyer, foreground=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_chroma_background_adj_value_changed(self, widget):
        if not self.slider_held:
            return
        cmd = KeyPropertiesAdvancedChromaCommand(index=self.index, keyer=self.keyer, background=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_chroma_edge_adj_value_changed(self, widget):
        if not self.slider_held:
            return
        cmd = KeyPropertiesAdvancedChromaCommand(index=self.index, keyer=self.keyer, key_edge=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_chroma_spill_adj_value_changed(self, widget):
        if not self.slider_held:
            return
        cmd = KeyPropertiesAdvancedChromaCommand(index=self.index, keyer=self.keyer, spill=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_chroma_flare_adj_value_changed(self, widget):
        if not self.slider_held:
            return
        cmd = KeyPropertiesAdvancedChromaCommand(index=self.index, keyer=self.keyer, flare=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_chroma_brightness_adj_value_changed(self, widget):
        if not self.slider_held:
            return
        cmd = KeyPropertiesAdvancedChromaCommand(index=self.index, keyer=self.keyer, brightness=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_chroma_contrast_adj_value_changed(self, widget):
        if not self.slider_held:
            return
        cmd = KeyPropertiesAdvancedChromaCommand(index=self.index, keyer=self.keyer, contrast=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_chroma_saturation_adj_value_changed(self, widget):
        if not self.slider_held:
            return
        cmd = KeyPropertiesAdvancedChromaCommand(index=self.index, keyer=self.keyer, saturation=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_chroma_red_adj_value_changed(self, widget):
        if not self.slider_held:
            return
        cmd = KeyPropertiesAdvancedChromaCommand(index=self.index, keyer=self.keyer, red=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_chroma_green_adj_value_changed(self, widget):
        if not self.slider_held:
            return
        cmd = KeyPropertiesAdvancedChromaCommand(index=self.index, keyer=self.keyer, green=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])

    @Gtk.Template.Callback()
    def on_chroma_blue_adj_value_changed(self, widget):
        if not self.slider_held:
            return
        cmd = KeyPropertiesAdvancedChromaCommand(index=self.index, keyer=self.keyer, blue=int(widget.get_value()))
        self.connection.mixer.send_commands([cmd])
