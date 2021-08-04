import math

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk


class Dial(Gtk.Range):
    __gtype_name__ = 'Dial'

    def __init__(self):
        super(Gtk.Range, self).__init__()
        self.set_size_request(64, 64)

    def _polar(self, dist, angle):
        x = dist * math.cos(math.radians(angle))
        y = dist * math.sin(math.radians(angle))
        return x, y

    def do_draw(self, cr):
        allocation = self.get_allocation()
        context = self.get_style_context()

        context.save()
        context.add_class('dial-frame')
        Gtk.render_background(context, cr, 0, 0, allocation.width, allocation.height)
        Gtk.render_frame(context, cr, 0, 0, allocation.width, allocation.height)
        context.restore()
        context.save()
        context.add_class('dial')

        padding = 16
        top = padding / 2
        left = padding / 2
        diameter = min(allocation.width - padding, allocation.height - padding)
        if allocation.width - padding > diameter:
            left = (allocation.width - diameter) // 2

        cx = allocation.width / 2
        cy = allocation.height / 2

        Gtk.render_background(context, cr, left, top, diameter, diameter)
        Gtk.render_frame(context, cr, left, top, diameter, diameter)
        context.restore()

        context.save()
        context.add_class('dial-mark')

        value = self.get_value()
        range_min = self.get_adjustment().get_lower()
        range_max = self.get_adjustment().get_upper()
        value = ((value - range_min) / (range_max - range_min))
        inner = self._polar(diameter * 0.2, (value * 270) + 45 + 90)
        outer = self._polar(diameter * 0.4, (value * 270) + 45 + 90)
        cr.set_line_width(2)
        cr.move_to(cx + inner[0] + 0.5, cy + inner[1] + 0.5)
        cr.line_to(cx + outer[0] + 0.5, cy + outer[1] + 0.5)
        cr.set_source_rgba(255, 255, 255, 1)
        cr.stroke()
        context.restore()
