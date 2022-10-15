# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import math

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk


class Dial(Gtk.Range):
    __gtype_name__ = 'Dial'

    def __init__(self):
        super(Gtk.Range, self).__init__()
        self.set_size_request(48, 48)
        self.editing = False
        self.start_x = None
        self.position = None
        self.connect('button-press-event', self.on_mouse_down)
        self.connect('button-release-event', self.on_mouse_up)
        self.connect('motion-notify-event', self.on_mouse_move)

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
        if self.editing:
            context.add_class('active')

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

    def on_mouse_down(self, widget, event):
        self.editing = True
        self.start_x = event.x
        adj = self.get_adjustment()
        value = adj.get_value()
        self.position = self._remap(value, adj.get_lower(), adj.get_upper(), -100, 100)

    def on_mouse_up(self, widget, *args):
        self.editing = False
        self.invalidate()

    def on_mouse_move(self, widget, event):
        if self.editing:
            new_x = event.x

            change = new_x - self.start_x
            change += self.position
            new_val = self._remap(change, -100, 100, self.get_adjustment().get_lower(),
                                  self.get_adjustment().get_upper())
            self.get_adjustment().set_value(new_val)

    def _remap(self, value, old_min, old_max, new_min, new_max):
        return ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min

    def invalidate(self):
        # TODO: Make functional
        return
        rect = self.get_allocation()
        parent = self.get_parent()
        if parent:
            offset = parent.get_allocation()
            rect.x -= offset.x
            rect.y -= offset.y

        self.window.invalidate_rect(rect, False)
