# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import math

from gi.repository import Gtk, GObject, Gdk


class BiQuad:
    def __init__(self):
        self.b0 = 1
        self.b1 = 1
        self.b2 = 1
        self.a0 = 1
        self.a1 = 1
        self.a2 = 1

    def normalize(self):
        self.b0 /= self.a0
        self.b1 /= self.a0
        self.b2 /= self.a0
        self.a1 /= self.a0
        self.a2 /= self.a0
        self.a0 = 1.0

    def get_coeff(self):
        return ([self.b0, self.b1, self.b2], [self.a0, self.a1, self.a2])

    def calculate(self, f):
        # Don't worry about it
        phi = (math.sin(math.pi * f * 2 / (2 * 48000))) ** 2
        r = ((self.b0 + self.b1 + self.b2) ** 2 - \
             4 * (self.b0 * self.b1 + 4 * self.b0 * self.b2 + \
                  self.b1 * self.b2) * phi + 16 * self.b0 * self.b2 * phi * phi) / \
            ((1 + self.a1 + self.a2) ** 2 - 4 * (self.a1 + 4 * self.a2 + \
                                                 self.a1 * self.a2) * phi + 16 * self.a2 * phi * phi)
        if r < 0:
            r = 0
        r = r ** (.5)
        try:
            return 20 * math.log10(r)
        except:
            return -200


class HighPass(BiQuad):
    def __init__(self, frequency):
        w0 = (2 * math.pi * frequency) / 48000
        s0 = math.sin(w0)
        c0 = math.cos(w0)
        q = 0.7071
        alpha = s0 / (2 * q)
        self.b0 = (1 + c0) / 2
        self.b1 = -(1 + c0)
        self.b2 = (1 + c0) / 2
        self.a0 = 1 + alpha
        self.a1 = -2 * c0
        self.a2 = 1 - alpha
        self.normalize()


class LowPass(BiQuad):
    def __init__(self, frequency):
        w0 = (2 * math.pi * frequency) / 48000
        s0 = math.sin(w0)
        c0 = math.cos(w0)
        q = 0.7071
        alpha = s0 / (2 * q)
        self.b0 = (1 - c0) / 2
        self.b1 = 1 - c0
        self.b2 = (1 - c0) / 2
        self.a0 = 1 + alpha
        self.a1 = -2 * c0
        self.a2 = 1 - alpha
        self.normalize()


class Peaking(BiQuad):
    def __init__(self, frequency, gain, q):
        A = math.pow(10, gain / 40)
        w0 = (2 * math.pi * frequency) / 48000
        if q == 0:
            q = 1
        alpha = math.sin(w0) / (2 * q)
        self.b0 = 1 + alpha * A
        self.b1 = -2 * math.cos(w0)
        self.b2 = 1 - alpha * A
        self.a0 = 1 + alpha / A
        self.a1 = -2 * math.cos(w0)
        self.a2 = 1 - alpha / A
        self.normalize()


class Notch(BiQuad):
    def __init__(self, frequency):
        w0 = (2 * math.pi * frequency) / 48000
        q = 7
        alpha = math.sin(w0) / (2 * q)
        self.b0 = 1
        self.b1 = -2 * math.cos(w0)
        self.b2 = 1
        self.a0 = 1 + alpha
        self.a1 = -2 * math.cos(w0)
        self.a2 = 1 - alpha
        self.normalize()


class HighShelf(BiQuad):
    def __init__(self, frequency, gain):
        A = math.pow(10, gain / 40)
        w0 = (2 * math.pi * frequency) / 48000
        s0 = math.sin(w0)
        c0 = math.cos(w0)
        beta = math.sqrt(A + A)
        self.b0 = A * ((A + 1) + (A - 1) * c0 + beta * s0)
        self.b1 = -2 * A * ((A - 1) + (A + 1) * c0)
        self.b2 = A * ((A + 1) + (A - 1) * c0 - beta * s0)
        self.a0 = (A + 1) - (A - 1) * c0 + beta * s0
        self.a1 = 2 * ((A - 1) - (A + 1) * c0)
        self.a2 = (A + 1) - (A - 1) * c0 - beta * s0
        self.normalize()


class LowShelf(BiQuad):
    def __init__(self, frequency, gain):
        A = math.pow(10, gain / 40)
        w0 = (2 * math.pi * frequency) / 48000
        s0 = math.sin(w0)
        c0 = math.cos(w0)
        beta = math.sqrt(A + A)
        self.b0 = A * ((A + 1) - (A - 1) * c0 + beta * s0)
        self.b1 = 2 * A * ((A - 1) - (A + 1) * c0)
        self.b2 = A * ((A + 1) - (A - 1) * c0 - beta * s0)
        self.a0 = (A + 1) + (A - 1) * c0 + beta * s0
        self.a1 = -2 * ((A - 1) + (A + 1) * c0)
        self.a2 = (A + 1) + (A - 1) * c0 - beta * s0
        self.normalize()


class EqCurve(Gtk.Frame):
    __gtype_name__ = 'EqCurve'

    def __init__(self):
        super(Gtk.Frame, self).__init__()
        self.connection = None
        self.set_size_request(900, 240)

        self.da = Gtk.DrawingArea()
        self.add(self.da)

        self.da.set_events(
            self.da.get_events()
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.POINTER_MOTION_HINT_MASK
        )

        self.da.connect("draw", self.on_draw)
        # self.da.connect("button-press-event", self.on_mouse_down)
        self.da.connect("button-release-event", self.on_mouse_up)
        # self.da.connect("motion-notify-event", self.on_mouse_move)
        self.show_all()
        self.bands = {}
        self.mini = True
        self.enabled = True

    def update_band(self, bandupdate):
        self.bands[bandupdate.band_index] = bandupdate
        self.da.queue_draw()

    def set_enabled(self, enabled):
        self.enabled = enabled
        self.da.queue_draw()

    def _x_to_f(self, width, x):
        frac = (x + 1) / (width + 1)

        log_min = math.log(19, 2)
        log_max = math.log(19000, 2)
        log_delta = log_max - log_min
        return 2 ** (log_min + (log_delta * frac))

    def _f_to_x(self, width, f):
        start = 0
        end = width
        while True:
            middle = start + ((end - start) / 2)
            pf = self._x_to_f(width, middle)
            distance = abs(pf - f)
            if distance < 3 or abs(end - start) < 2:
                break
            if pf < f:
                start = middle
            else:
                end = middle
        return middle

    def _x_to_f_aligned(self, width, x):
        """
        This is hack to shift the sampling frequency slightly so it corresponds to the peak of the nearest filter
        if there is a filter in the exact range covered by the pixel. This fixes aliasing in the display for very
        steep filters and is a lot more efficient than oversampling the whole frequency range.
        """
        lower = self._x_to_f(width, max(0, x - 1))
        upper = self._x_to_f(width, min(width, x + 1))
        for band_idx in self.bands:
            if not self.bands[band_idx].band_enabled:
                continue
            if self.bands[band_idx].band_filter not in [0x04, 0x08]:
                continue
            if self.bands[band_idx].band_gain == 0:
                continue
            bf = self.bands[band_idx].band_frequency
            if lower <= bf <= upper:
                return bf
        return self._x_to_f(width, x)

    def _y_to_db(self, height, y):
        fract = (y / height) * 2 - 1
        return height - (fract * 20)

    def _db_to_y(self, height, db):
        fract = db / 20
        return height - (fract * (height / 2) + height / 2)

    def calculate_filter(self, f):
        biquads = []
        for band_index in self.bands:
            band = self.bands[band_index]
            if not band.band_enabled:
                continue

            if band.band_filter == 0x01:
                # Low shelf
                biquads.append(LowShelf(band.band_frequency, band.band_gain / 100))
            elif band.band_filter == 0x02:
                # Low pass
                biquads.append(LowPass(band.band_frequency))
            elif band.band_filter == 0x04:
                # Bell
                biquads.append(Peaking(band.band_frequency, band.band_gain / 100, band.band_q / 100))
            elif band.band_filter == 0x08:
                # Notch
                biquads.append(Notch(band.band_frequency))
            elif band.band_filter == 0x10:
                # High pass band
                biquads.append(HighPass(band.band_frequency))
            elif band.band_filter == 0x20:
                # High shelf
                biquads.append(HighShelf(band.band_frequency, band.band_gain / 100))

        db = 0.0
        for band in biquads:
            db += band.calculate(f)
        return db

    def on_draw(self, widget, cr):
        width, height = widget.get_allocated_width(), widget.get_allocated_height()
        context = self.get_style_context()

        context.save()
        context.add_class('eq-window')
        if self.mini:
            context.add_class('mini')
        Gtk.render_background(context, cr, 0, 0, width, height)

        context.restore()
        context.save()
        context.add_class('eq-window-lines')
        context.add_class('zero')
        Gtk.render_line(context, cr, 0, height / 2, width, height / 2)

        if not self.mini:
            context.remove_class('zero')
            for dB in [15, 10, 5, -5, -10, -15]:
                Gtk.render_line(context, cr, 0, self._db_to_y(height, dB), width, self._db_to_y(height, dB))
            for Hz in [31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]:
                x = self._f_to_x(width, Hz)
                Gtk.render_line(context, cr, x, 0, x, height)

        context.restore()
        context.save()
        context.add_class('eq-window-curve')
        if not self.enabled:
            context.add_class('disabled')

        step = 1 if self.mini else 3

        last = self._db_to_y(height, self.calculate_filter(19))
        for i in range(0, width, step):
            f = self._x_to_f_aligned(width, i)
            gain = self.calculate_filter(f)
            y = self._db_to_y(height, gain)
            Gtk.render_line(context, cr, i - step, last, i, y)
            last = y

        if not self.mini:
            context.restore()
            context.save()
            context.add_class('eq-window-handle')
            if not self.enabled:
                context.add_class('disabled')
            for band_index in self.bands:
                band = self.bands[band_index]
                if band.band_enabled:
                    context.add_class('active')
                else:
                    context.remove_class('active')
                x = self._f_to_x(width, band.band_frequency)
                y = self._db_to_y(height, band.band_gain / 100)
                Gtk.render_background(context, cr, x - 8, y - 8, 16, 16)
                Gtk.render_frame(context, cr, x - 8, y - 8, 16, 16)
                cr.move_to(x - 3, y + 4)
                color = context.get_color(Gtk.StateFlags.NORMAL)
                cr.set_source_rgba(color.red, color.green, color.blue, color.alpha)
                cr.show_text(f"{band_index + 1}")

        context.restore()

    def on_mouse_up(self, widget, *args):
        if self.mini:
            pass
