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
        self.b0 = s0
        self.b1 = 0
        self.b2 = -s0
        self.a0 = 1 - c0 + s0
        self.a1 = 2 * (1 - c0)
        self.a2 = 1 - c0 - s0
        self.normalize()


class LowPass(BiQuad):
    def __init__(self, frequency):
        w0 = (2 * math.pi * frequency) / 48000
        s0 = math.sin(w0)
        c0 = math.cos(w0)
        self.b0 = 1 - c0
        self.b1 = (1 - c0) * 2
        self.b2 = 1 - c0
        self.a0 = 1 - c0 + s0
        self.a1 = 2 * (1 - c0)
        self.a2 = 1 - c0 - s0
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
        self.set_size_request(640, 480)

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
        # self.da.connect("button-release-event", self.on_mouse_up)
        # self.da.connect("motion-notify-event", self.on_mouse_move)
        self.show_all()
        self.bands = {}

    def update_band(self, bandupdate):
        self.bands[bandupdate.band_index] = bandupdate
        self.da.queue_draw()

    def _x_to_f(self, width, x):
        frac = x / width + 0.00001

        return 10 * (2400 ** frac)

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
        Gtk.render_background(context, cr, 0, 0, width, height)

        context.restore()
        context.save()
        context.add_class('eq-window-lines')

        Gtk.render_line(context, cr, 0, height / 2, width, height / 2)
        context.restore()
        context.save()
        context.add_class('eq-window-curve')

        last = self._db_to_y(height, self.calculate_filter(5))
        for i in range(0, width):
            f = self._x_to_f(width, i)
            gain = self.calculate_filter(f)
            y = self._db_to_y(height, gain)
            Gtk.render_line(context, cr, i - 1, last, i, y)
            last = y
        context.restore()
