from gi.repository import Gtk, GObject, Gdk

from pyatem.command import KeyFillCommand, KeyPropertiesDveCommand
from pyatem.field import TransitionSettingsField, KeyPropertiesDveField


@Gtk.Template(resource_path='/nl/brixit/switcher/ui/upstream-keyer.glade')
class UpstreamKeyer(Gtk.Frame):
    __gtype_name__ = 'UpstreamKeyer'

    keyer_stack = Gtk.Template.Child()
    mask_top = Gtk.Template.Child()
    mask_bottom = Gtk.Template.Child()
    mask_left = Gtk.Template.Child()
    mask_right = Gtk.Template.Child()
    mask_en = Gtk.Template.Child()

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

    def __init__(self, index, keyer, connection):
        self.index = index
        self.keyer = keyer
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
        self.dve_fill.set_model(model)
        self.model_changing = False

    def on_key_properties_base_change(self, data):
        self.model_changing = True
        self.dve_fill.set_active_id(str(data.fill_source))
        self.model_changing = False

        if data.type == 0:
            self.keyer_stack.set_visible_child_name('key_luma')
        elif data.type == 1:
            self.keyer_stack.set_visible_child_name('key_chroma')
        elif data.type == 2:
            self.keyer_stack.set_visible_child_name('key_pattern')
        elif data.type == 3:
            self.keyer_stack.set_visible_child_name('key_dve')

        if data.type != 3:
            self.set_class(self.mask_en, 'active', data.mask_enabled)

            self.mask_top.set_text(str(data.mask_top / 1000))
            self.mask_bottom.set_text(str(data.mask_bottom / 1000))
            self.mask_left.set_text(str(data.mask_left / 1000))
            self.mask_right.set_text(str(data.mask_right / 1000))

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

    @Gtk.Template.Callback()
    def on_dve_fill_changed(self, widget, *args):
        if self.model_changing:
            return
        source = int(widget.get_active_id())
        cmd = KeyFillCommand(index=self.index, keyer=self.keyer, source=source)
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
