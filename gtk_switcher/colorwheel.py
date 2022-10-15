# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import colorsys
import logging

import cairo
import io
import math
from gi.repository import Gtk, GObject, Gio


class ColorWheelWidget(Gtk.DrawingArea):
    _gtype_name__ = 'ColorWheelWidget'

    red = GObject.Property(type=float, nick='Red value', default=0.2)
    green = GObject.Property(type=float, nick='Green value', default=0.1)
    blue = GObject.Property(type=float, nick='Blue value', default=0.1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_size_request(100, 100)
        rainbow = Gio.resources_lookup_data('/nl/brixit/switcher/asset/rainbow.png', 0).get_data()
        rainbowpng = io.BytesIO(rainbow)
        self.rainbow = cairo.ImageSurface.create_from_png(rainbowpng)

    def get_coordinates(self):
        yiq = colorsys.rgb_to_yiq(self.red, self.green, self.blue)
        logging.debug(yiq)
        return yiq

    def set_coordinates(self, gain, x, y):
        rgb = colorsys.yiq_to_rgb(gain, x, y)
        self.red, self.green, self.blue = rgb

    def do_draw(self, cr):
        context = self.get_style_context()
        state = self.get_state_flags()
        context.set_state(state)

        size = self.get_allocation()

        # Draw background
        Gtk.render_background(context, cr, 0, 0, size.width, size.height)

        # Draw gain circle
        radius = (min(size.width, size.height) - 2) // 2
        cr.set_line_width(3.0)
        cr.arc(size.width // 2, size.height // 2, radius, 0, math.pi * 2)
        cr.stroke()

        # Draw center cross
        radius = radius * 0.9
        cr.set_line_width(1.0)
        cr.move_to((size.width // 2) - radius, size.height // 2)
        cr.line_to((size.width // 2) + radius, size.height // 2)
        cr.stroke()
        cr.move_to(size.width // 2, (size.height // 2) - radius)
        cr.line_to(size.width // 2, (size.height // 2) + radius)
        cr.stroke()

        # Draw color rainbow circle
        pattern_width = self.rainbow.get_width()
        if size.width > size.height:
            xoffset = (size.width - size.height) // 2
            yoffset = 0
            scale = size.height / pattern_width
        else:
            xoffset = 0
            yoffset = (size.height - size.width) // 2
            scale = size.width / pattern_width
        cr.set_source_surface(self.rainbow, xoffset / scale, yoffset / scale)
        source = cr.get_source()
        matrix = source.get_matrix()
        matrix.xx = 1 / scale
        matrix.yy = 1 / scale
        source.set_matrix(matrix)
        cr.set_line_width(16.0)
        cr.arc(size.width // 2, size.height // 2, radius, 0, math.pi * 2)
        cr.stroke()

        # Draw cursor
        gain, x, y = self.get_coordinates()
        cr.set_source_rgba(0, 0, 0, 1)
        cr.set_line_width(3)
        cr.arc((x * radius) + size.width // 2, (y * radius) + size.height // 2, 6, 0, math.pi * 2)
        cr.stroke()

        cr.save()
