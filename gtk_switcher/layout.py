from gi.repository import Gtk, GObject, Gdk

from pyatem.command import KeyPropertiesDveCommand, DkeyMaskCommand


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
        self.offset_alt_x = None
        self.offset_alt_y = None
        self.move_alt = False
        self.alt_x = None
        self.alt_y = None

        self.mask_top = 0
        self.mask_bottom = 0
        self.mask_left = 0
        self.mask_right = 0

        self.regions = {}
        self.masks = {}
        self.tally = {}
        self.types = {}

    def update_region(self, label, x, y, w, h):
        self.regions[label] = [x, y, w, h]
        self.da.queue_draw()

    def update_mask(self, label, top, bottom, left, right):
        top = (top) / 18000
        bottom = (bottom) / 18000
        left = (left) / 32000
        right = (right) / 32000
        self.masks[label] = [top, bottom, left, right]
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
        self.move_alt = event.state & Gdk.ModifierType.CONTROL_MASK > 0

        if self.selected is None:
            hits = []
            for label in self.regions:
                region = self.regions[label]
                w = self._coord_w(region[2])
                h = self._coord_h(region[3])

                x = self._coord_x(region[0]) - (w / 2)
                y = self._coord_y(region[1]) - (h / 2)
                if x < event.x < (x + w):
                    if y < event.y < (y + h):
                        hits.append((label, w * h))
            if len(hits) == 0:
                return
            sorted_hits = list(sorted(hits, key=lambda k: k[1]))
            self.selected = sorted_hits[0][0]
            self.da.queue_draw()
            return

        region = self.regions[self.selected]
        w = self._coord_w(region[2])
        h = self._coord_h(region[3])
        x = self._coord_x(region[0]) - (w / 2)
        y = self._coord_y(region[1]) - (h / 2)

        mtop = 0
        mbottom = 0
        mleft = 0
        mright = 0
        if self.selected in self.masks:
            mask = self.masks[self.selected]
            mtop = mask[0]
            mbottom = mask[1]
            mleft = mask[2]
            mright = mask[3]
            self.mask_top = mtop
            self.mask_bottom = mbottom
            self.mask_left = mleft
            self.mask_right = mright

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

        if (x - 5 + (mleft * w)) < event.x < (x + 5 + (mleft * w)):
            if (y - 15 + (h / 2)) < event.y < (y + 15 + (h / 2)):
                self.handle = 'ml'
                self.offset_x = x
                return

        if (x - 5 + w - (mright * w)) < event.x < (x + 5 + w - (mright * w)):
            if (y - 15 + (h / 2)) < event.y < (y + 15 + (h / 2)):
                self.handle = 'mr'
                self.offset_x = x + w
                return

        if (x - 15 + (w / 2)) < event.x < (x + 15 + (w / 2)):
            if (y - 5 + h - (mtop * h)) < event.y < (y + 5 + h - (mtop * h)):
                self.handle = 'mt'
                self.offset_y = y + h
                return

        if (x - 15 + (w / 2)) < event.x < (x + 15 + (w / 2)):
            if (y - 5 + (mbottom * h)) < event.y < (y + 5 + (mbottom * h)):
                self.handle = 'mb'
                self.offset_y = y
                return

        if x < event.x < (x + w):
            if y < event.y < (y + h):
                self.handle = 'pos'
                if self.move_alt:
                    self.offset_alt_x = event.x
                    self.offset_alt_y = event.y
                    self.alt_x = (x + (w / 2))
                    self.alt_y = (y + (h / 2))
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

        region = self.regions[self.selected]
        w = self._coord_w(region[2])
        h = self._coord_h(region[3])

        if self.handle == 'pos':
            if self.move_alt:
                # Alternate move moves the source inside the mask area instead of the key itself

                # Vertical axis first
                new_left = min(1.0, max(0, ((event.x - self.offset_alt_x) / w) + self.mask_left))
                new_right = min(1.0, max(0, self.mask_right + (self.mask_left - new_left)))

                # Horizontal axis
                new_bottom = min(1.0, max(0, ((event.y - self.offset_alt_y) / h) + self.mask_bottom))
                new_top = min(1.0, max(0, self.mask_top + (self.mask_bottom - new_bottom)))

                # Move the flying key in the opposite direction to compensate
                new_x = self.alt_x + (self.offset_alt_x - event.x)
                new_y = self.alt_y + (self.offset_alt_y - event.y)

                mask_cmd = self.on_mask_update(self.selected, left=new_left, right=new_right, top=new_top,
                                               bottom=new_bottom, exec=False)
                pos_cmd = self.on_region_update(self.selected, pos_x=new_x, pos_y=new_y, exec=False)
                self.connection.mixer.send_commands([pos_cmd, mask_cmd])
            else:
                new_x = event.x + self.offset_x
                new_y = event.y + self.offset_y
                self.on_region_update(self.selected, pos_x=new_x, pos_y=new_y)
        elif self.handle.startswith("m"):
            if self.handle == "ml":
                new_left = min(1.0, max(0, (event.x - self.offset_x) / w))
                self.on_mask_update(self.selected, left=new_left)
            elif self.handle == "mr":
                new_right = min(1.0, max(0, (self.offset_x - event.x) / w))
                self.on_mask_update(self.selected, right=new_right)
            elif self.handle == "mt":
                new_top = min(1.0, max(0, (self.offset_y - event.y) / h))
                self.on_mask_update(self.selected, top=new_top)
            elif self.handle == "mb":
                new_bottom = min(1.0, max(0, (event.y - self.offset_y) / h))
                self.on_mask_update(self.selected, bottom=new_bottom)
        else:
            new_x = (self.offset_x + event.x) / 2
            new_y = (self.offset_y + event.y) / 2
            new_w = max(self.offset_x, event.x) - min(self.offset_x, event.x)
            new_h = max(self.offset_y, event.y) - min(self.offset_y, event.y)
            self.on_region_update(self.selected, pos_x=new_x, pos_y=new_y, size_x=new_w, size_y=new_h)

    def on_region_update(self, label, pos_x=None, pos_y=None, size_x=None, size_y=None, exec=True):
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
            if exec:
                self.connection.mixer.send_commands([cmd])
            return cmd

    def on_mask_update(self, label, left=None, right=None, top=None, bottom=None, exec=True):
        ml = None
        mr = None
        mt = None
        mb = None
        if left is not None:
            ml = int(left * 32000)
        if right is not None:
            mr = int(right * 32000)
        if top is not None:
            mt = int(top * 18000)
        if bottom is not None:
            mb = int(bottom * 18000)

        if label.startswith("Upstream key"):
            keyer = int(label[13:]) - 1

            cmd = KeyPropertiesDveCommand(index=self.index, keyer=keyer, mask_top=mt, mask_bottom=mb, mask_left=ml,
                                          mask_right=mr)
        elif label.startswith("Downstream key"):
            keyer = int(label[17:]) - 1
            if ml is not None:
                ml = ml - 16000
            if mr is not None:
                mr = 16000 - mr
            if mt is not None:
                mt = 9000 - mt
            if mb is not None:
                mb = mb - 9000
            cmd = DkeyMaskCommand(index=keyer, top=mt, bottom=mb, left=ml, right=mr)

        if not cmd:
            return None
        if exec:
            self.connection.mixer.send_commands([cmd])
        return cmd

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

            mtop = 0
            mbottom = 0
            mleft = 0
            mright = 0
            if label in self.masks:
                mask = self.masks[label]
                mtop = mask[0]
                mbottom = mask[1]
                mleft = mask[2]
                mright = mask[3]

            if label in self.tally and self.tally[label]:
                cr.set_source_rgb(1.0, 0, 0)
            else:
                cr.set_source_rgb(1.0, 1.0, 1.0)
            if mleft != 0:
                cr.move_to(x + left + (w * mleft), height - (y + top + h))
                cr.line_to(x + left + (w * mleft), height - (y + top))
            if mtop != 0:
                cr.move_to(x + left, height - (y + top + h) + (mtop * h))
                cr.line_to(x + left + w, height - (y + top + h) + (mtop * h))
            if mbottom != 0:
                cr.move_to(x + left, height - (y + top + h) + h - (mbottom * h))
                cr.line_to(x + left + w, height - (y + top + h) + h - (mbottom * h))
            if mright != 0:
                cr.move_to(x + left + w - (w * mright), height - (y + top + h))
                cr.line_to(x + left + w - (w * mright), height - (y + top))

            if self.selected == label:
                cr.set_dash([2.0, 1.0])
            cr.rectangle(x + left, height - (y + top + h), w, h)
            cr.stroke()
            if self.selected == label:
                # Position/Size handles on the corners
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

                # Mask handles on the sides
                cr.rectangle(x + left - 4 + (w * mleft), height - (y + top + (h / 2)) - 15, 5, 30)
                cr.fill()
                cr.rectangle(x + left + w - (w * mright), height - (y + top + (h / 2)) - 15, 5, 30)
                cr.fill()
                cr.rectangle(x + left + (w / 2) - 15, height - (y + top + h - (mtop * h) + 4), 30, 5)
                cr.fill()
                cr.rectangle(x + left + (w / 2) - 15, height - (y + top + (mbottom * h)), 30, 5)
                cr.fill()

            cr.move_to(x + left + 10, height - (y + top + h) + 20)
            cr.show_text(label)
