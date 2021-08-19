import math

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk


class LogAdjustment(Gtk.Adjustment):
    __gtype_name__ = 'LogAdjustment'

    def __init__(self, value, lower, upper, step_increment, page_increment, page_size, range=60):
        super(Gtk.Adjustment, self).__init__()
        self.set_value(value)
        self.set_lower(lower)
        self.set_upper(upper)
        self.set_step_increment(step_increment)
        self.set_page_increment(page_increment)
        self.set_page_size(page_size)
        self.coeff = 10 ** (range / 20)

    def to_normalized(self, value):
        upper = self.get_upper() - self.get_page_size()
        adj_range = upper - self.get_lower()
        return (value - self.get_lower()) / adj_range

    def from_normalized(self, value):
        upper = self.get_upper() - self.get_page_size()
        lower = self.get_lower()
        adj_range = upper - lower
        val = (value * adj_range) + lower
        return val

    def set_value_log(self, value):
        oldval = value
        value = self.to_normalized(value)
        val = math.log((value * self.coeff) + 1) / math.log(self.coeff + 1)
        self.set_value(self.from_normalized(val))
        print("set_value_log", oldval, value, val, self.from_normalized(val))

    def get_value_log(self):
        value = self.get_value()
        oldval = value
        value = self.to_normalized(value)
        val = (math.exp((math.log(self.coeff + 1) * value)) - 1) / self.coeff
        print("get_value_log", oldval, value, val, self.from_normalized(val))
        return self.from_normalized(val)
