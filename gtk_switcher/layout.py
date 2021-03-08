from gi.repository import Gtk, GObject, Gdk

from pyatem.command import KeyPropertiesDveCommand


class LayoutView(Gtk.Frame):
    __gtype_name__ = 'LayoutView'

    def __init__(self, index, connection):
        super(Gtk.Frame, self).__init__()
        self.index = index
        self.connection = connection
        self.set_size_request(640, 480)
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.get_style_context().add_class("view")

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

        self.area_width = 0
        self.area_height = 0
        self.area_top = 0
        self.area_left = 0

        self.da.connect("draw", self.on_draw)
        self.da.connect("configure-event", self.on_configure)
        self.da.connect("button-press-event", self.on_mouse_down)
        self.da.connect("button-release-event", self.on_mouse_up)
        self.da.connect("motion-notify-event", self.on_mouse_move)

        self.show_all()

        self.selected = None
        self.handle = None
        self.offset_x = None
        self.offset_y = None

        self.regions = {}
        self.tally = {}

    def update_region(self, label, x, y, w, h):
        self.regions[label] = [x, y, w, h]
        self.da.queue_draw()

    def region_onair(self, label, onair):
        self.tally[label] = onair
        self.da.queue_draw()

    def on_configure(self, widget, event, data=None):
        width, height = widget.get_allocated_width(), widget.get_allocated_height()

    def on_mouse_down(self, widget, event):
        # grr cairo coordinates
        event.y = self.area_height - event.y - self.area_top
        event.x = event.x - self.area_left

        if self.selected is None:
            for label in self.regions:
                region = self.regions[label]
                w = self._coord_w(region[2])
                h = self._coord_h(region[3])

                x = self._coord_x(region[0]) - (w / 2)
                y = self._coord_y(region[1]) - (h / 2)
                if x < event.x < (x + w):
                    if y < event.y < (y + h):
                        self.selected = label
                        self.da.queue_draw()
                        return
            return

        region = self.regions[self.selected]
        w = self._coord_w(region[2])
        h = self._coord_h(region[3])
        x = self._coord_x(region[0]) - (w / 2)
        y = self._coord_y(region[1]) - (h / 2)

        if (x - 5) < event.x < (x + 5):
            if (y - 5) < event.y < (y + 5):
                self.handle = 'bl'
                self.offset_x = x + w
                self.offset_y = y + h
                return

        if (x - 5) < event.x < (x + 5):
            if (y - 5 + h) < event.y < (y + 5 + h):
                self.handle = 'tl'
                self.offset_x = x + w
                self.offset_y = y
                return

        if (x - 5 + w) < event.x < (x + 5 + w):
            if (y - 5) < event.y < (y + 5):
                self.handle = 'br'
                self.offset_x = x
                self.offset_y = y + h
                return

        if (x - 5 + w) < event.x < (x + 5 + w):
            if (y - 5 + h) < event.y < (y + 5 + h):
                self.handle = 'tr'
                self.offset_x = x
                self.offset_y = y
                return

        if x < event.x < (x + w):
            if y < event.y < (y + h):
                self.handle = 'pos'
                self.offset_x = (x + (w / 2)) - event.x
                self.offset_y = (y + (h / 2)) - event.y
                return
        self.selected = None
        self.da.queue_draw()

    def on_mouse_up(self, widget, *args):
        self.handle = None
        self.da.queue_draw()

    def on_mouse_move(self, widget, event):

        if self.handle is None or self.selected is None:
            return

        # grr cairo coordinates
        event.y = self.area_height - event.y - self.area_top
        event.x = event.x - self.area_left

        if self.handle == 'pos':
            new_x = event.x + self.offset_x
            new_y = event.y + self.offset_y
            self.on_region_update(self.selected, pos_x=new_x, pos_y=new_y)
        else:
            new_x = (self.offset_x + event.x) / 2
            new_y = (self.offset_y + event.y) / 2
            new_w = max(self.offset_x, event.x) - min(self.offset_x, event.x)
            new_h = max(self.offset_y, event.y) - min(self.offset_y, event.y)
            self.on_region_update(self.selected, pos_x=new_x, pos_y=new_y, size_x=new_w, size_y=new_h)

    def on_region_update(self, label, pos_x=None, pos_y=None, size_x=None, size_y=None):
        if label.startswith("Upstream key"):
            keyer = int(label[13:]) - 1
            x, y = self._pos_to_atem(pos_x, pos_y)
            w = None
            h = None
            if size_x is not None and size_y is not None:
                w, h = self._size_to_atem(size_x, size_y)
                w = int(w * 100)
                h = int(h * 100)
            cmd = KeyPropertiesDveCommand(index=self.index, keyer=keyer, pos_x=int(x * 1000), pos_y=int(y * 1000),
                                          size_x=w, size_y=h)
            self.connection.mixer.send_commands([cmd])

    def _coord_x(self, input_coord):
        input_coord = (input_coord + 16) / 32.0
        return (self.area_width * input_coord)

    def _coord_y(self, input_coord):
        input_coord = (input_coord + 9) / 18.0
        return (self.area_height * input_coord)

    def _coord_w(self, input_coord):
        input_coord = input_coord / 16.0
        return (self.area_width * input_coord)

    def _coord_h(self, input_coord):
        input_coord = input_coord / 9
        return (self.area_height * input_coord)

    def _pos_to_atem(self, x, y):
        nx = x / self.area_width
        ny = y / self.area_height
        x = nx * 32 - 16
        y = ny * 18 - 9
        return x, y

    def _size_to_atem(self, x, y):
        nx = x / self.area_width
        ny = y / self.area_height
        x = nx * 10
        y = ny * 10
        return x, y

    def on_draw(self, widget, cr):

        # Calculate a 16:9 area inside the widget size
        width, height = widget.get_allocated_width(), widget.get_allocated_height()
        top = 0
        left = 0
        if width / height > 16 / 9:
            new_width = height * 16 // 9
            left = (width - new_width) // 2
            width = new_width
        else:
            new_height = width * 9 // 16
            top = (height - new_height)
            height = new_height

        self.area_width = width
        self.area_height = height
        self.area_top = top
        self.area_left = left

        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        cr.paint()

        # Draw frame
        cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.rectangle(left, top, width, height)
        cr.fill()

        for label in self.regions:
            region = self.regions[label]
            w = self._coord_w(region[2])
            h = self._coord_h(region[3])

            x = self._coord_x(region[0]) - (w / 2)
            y = self._coord_y(region[1]) - (h / 2)
            if label in self.tally and self.tally[label]:
                cr.set_source_rgb(1.0, 0, 0)
            else:
                cr.set_source_rgb(1.0, 1.0, 1.0)
            if self.selected == label:
                cr.set_dash([2.0, 1.0])
            cr.rectangle(x + left, height - (y + top + h), w, h)
            cr.stroke()
            if self.selected == label:
                cr.rectangle(x + left - 5, height - (y + top + h) - 5, 10, 10)
                cr.fill()
                cr.rectangle(x + left - 5 + w, height - (y + top + h) - 5, 10, 10)
                cr.fill()
                cr.rectangle(x + left - 5, height - (y + top) - 5, 10, 10)
                cr.fill()
                cr.rectangle(x + left - 5 + w, height - (y + top) - 5, 10, 10)
                cr.fill()
                cr.rectangle(x + left - 5 + (w / 2), height - (y + top + (h / 2)) - 5, 10, 10)
                cr.fill()

            cr.move_to(x + left + 10, height - (y + top + h) + 20)
            cr.show_text(label)
