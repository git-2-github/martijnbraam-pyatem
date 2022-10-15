# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk, GObject, Gdk

from pyatem.command import KeyPropertiesDveCommand, DkeyMaskCommand, KeyPropertiesAdvancedChromaColorpickerCommand


class Region:
    def __init__(self, rid, layout):
        self.rid = rid
        self.layout = layout

        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0

        self.has_mask = False
        self.mask_top = 0
        self.mask_bottom = 0
        self.mask_left = 0
        self.mask_right = 0

        self.tally = False
        self.visible = True

    def _queue_draw(self):
        self.layout.da.queue_draw()

    def set_tally(self, onair):
        if onair == self.tally:
            return
        self.tally = onair
        self._queue_draw()

    def set_visible(self, visible):
        if visible == self.visible:
            return
        self.visible = visible
        self._queue_draw()

    def set_region(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self._queue_draw()

    def set_mask(self, top, bottom, left, right):
        self.has_mask = True
        self.mask_top = top / 18000
        self.mask_bottom = bottom / 18000
        self.mask_left = left / 32000
        self.mask_right = right / 32000
        self._queue_draw()

    def get_label(self):
        return "Error"

    def __repr__(self):
        return '<Region {} {},{} {}x{}>'.format(self.get_label(), self.x, self.y, self.w, self.h)

    def get_region_cairo(self, width, height):
        w = self.w / 16
        h = self.h / 9
        x = ((self.x + 16) / 32.0) - (w / 2)
        y = ((self.y + 9) / 18.0) - (h / 2)

        return x * width, y * height, w * width, h * height

    def get_mask_cairo(self, width, height):
        return self.mask_top, self.mask_bottom, self.mask_left, self.mask_right

    def _update_region(self, index, pos_x=None, pos_y=None, size_x=None, size_y=None):
        return []

    def _update_mask(self, index, left=None, right=None, top=None, bottom=None):
        return []


class UpstreamKeyRegion(Region):
    def get_label(self):
        return _("Upstream key {}").format(self.rid[1] + 1)

    def _update_region(self, index, pos_x=None, pos_y=None, size_x=None, size_y=None):
        if pos_x is not None:
            x = int((pos_x * 32 - 16) * 1000)
        if pos_y is not None:
            y = int((pos_y * 18 - 9) * 1000)

        w = None
        h = None
        if size_x is not None and size_y is not None:
            w = int(size_x * 1000)
            h = int(size_y * 1000)
        cmd = KeyPropertiesDveCommand(index=index, keyer=self.rid[1], pos_x=x, pos_y=y,
                                      size_x=w, size_y=h)
        return [cmd]

    def _update_mask(self, index, left=None, right=None, top=None, bottom=None):
        ml, mr, mt, mb = None, None, None, None
        if left is not None:
            ml = int(left * 32000)
        if right is not None:
            mr = int(right * 32000)
        if top is not None:
            mt = int(top * 18000)
        if bottom is not None:
            mb = int(bottom * 18000)

        cmd = KeyPropertiesDveCommand(index=index, keyer=self.rid[1], mask_top=mt, mask_bottom=mb, mask_left=ml,
                                      mask_right=mr)
        return [cmd]


class DownstreamKeyRegion(Region):
    def get_label(self):
        return _("Downstream keyer {}").format(self.rid[1] + 1)

    def _update_mask(self, index, left=None, right=None, top=None, bottom=None):
        ml, mr, mt, mb = None, None, None, None
        if left is not None:
            ml = int(left * 32000) - 16000
        if right is not None:
            mr = 16000 - int(right * 32000)
        if top is not None:
            mt = 9000 - int(top * 18000)
        if bottom is not None:
            mb = int(bottom * 18000) - 9000

        cmd = DkeyMaskCommand(index=self.rid[1], top=mt, bottom=mb, left=ml, right=mr)
        return [cmd]


class ColorPickerRegion(Region):
    def get_label(self):
        return _("Chroma picker {}").format(self.rid[1] + 1)

    def _update_region(self, index, pos_x=None, pos_y=None, size_x=None, size_y=None):
        x = None
        y = None
        if pos_x is not None:
            x = int((pos_x * 32 - 16) * 1000)
        if pos_y is not None:
            y = int((pos_y * 18 - 9) * 1000)

        size = None
        if size_x is not None:
            size = int(size_x * 16000)

        cmd = KeyPropertiesAdvancedChromaColorpickerCommand(index=index, keyer=self.rid[1], x=x, y=y, size=size)
        return [cmd]


class LayoutView(Gtk.Frame):
    __gtype_name__ = 'LayoutView'
    LAYER_USK = 1
    LAYER_DSK = 2
    LAYER_ACK = 3

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

    def get(self, type, index):
        """
        Get a region by type and index, type is one of the LayoutView.LAYER_ constants.
        The region will be created internally if it did not exist yet.

        :rtype: Region
        """
        rid = (type, index)
        if rid not in self.regions:
            if type == LayoutView.LAYER_USK:
                region = UpstreamKeyRegion(rid, self)
            elif type == LayoutView.LAYER_DSK:
                region = DownstreamKeyRegion(rid, self)
            elif type == LayoutView.LAYER_ACK:
                region = ColorPickerRegion(rid, self)
            self.regions[rid] = region
        return self.regions[rid]

    def on_mouse_down(self, widget, event):
        # grr cairo coordinates
        event.y = self.area_height - event.y - self.area_top
        event.x = event.x - self.area_left
        self.move_alt = event.state & Gdk.ModifierType.CONTROL_MASK > 0

        if self.selected is None:
            hits = []
            for rid in self.regions:
                region = self.regions[rid]
                x, y, w, h = region.get_region_cairo(self.area_width, self.area_height)

                if x < event.x < (x + w):
                    if y < event.y < (y + h):
                        hits.append((rid, w * h))

            if len(hits) == 0:
                return

            # Sort all hits on area of the region, always pick the smallest one so it's possible to select overlapping
            # regions naturally
            sorted_hits = list(sorted(hits, key=lambda k: k[1]))
            self.selected = sorted_hits[0][0]
            self.da.queue_draw()
            return

        region = self.regions[self.selected]
        x, y, w, h = region.get_region_cairo(self.area_width, self.area_height)
        mtop, mbottom, mleft, mright = region.get_mask_cairo(self.area_width, self.area_height)

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
        x, y, w, h = region.get_region_cairo(self.area_width, self.area_height)

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

    def on_region_update(self, rid, pos_x=None, pos_y=None, size_x=None, size_y=None, exec=True):
        # Normalize the cairo coordinates again
        if pos_x is not None:
            pos_x = pos_x / self.area_width
        if pos_y is not None:
            pos_y = pos_y / self.area_height
        if size_x is not None:
            size_x = size_x / self.area_width
        if size_y is not None:
            size_y = size_y / self.area_height

        region = self.regions[rid]
        cmds = region._update_region(index=self.index, pos_x=pos_x, pos_y=pos_y, size_x=size_x, size_y=size_y)

        if exec:
            self.connection.mixer.send_commands(cmds)
        return cmds

    def on_mask_update(self, rid, left=None, right=None, top=None, bottom=None, exec=True):
        region = self.regions[rid]
        cmds = region._update_mask(index=self.index, left=left, right=right, top=top, bottom=bottom)
        if exec:
            self.connection.mixer.send_commands(cmds)
        return cmds

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

        # Clear
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        cr.paint()

        # Draw frame
        cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.rectangle(left, top, width, height)
        cr.fill()

        for rid in self.regions:
            region = self.regions[rid]
            if not region.visible:
                continue
            x, y, w, h = region.get_region_cairo(self.area_width, self.area_height)

            mtop, mbottom, mleft, mright = 0, 0, 0, 0
            if region.has_mask:
                mtop, mbottom, mleft, mright = region.get_mask_cairo(self.area_width, self.area_height)

            if region.tally:
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

            if self.selected == rid:
                cr.set_dash([2.0, 1.0])

            cr.rectangle(x + left, height - (y + top + h), w, h)
            cr.stroke()

            if self.selected == rid:
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
                if region.has_mask:
                    cr.rectangle(x + left - 4 + (w * mleft), height - (y + top + (h / 2)) - 15, 5, 30)
                    cr.fill()
                    cr.rectangle(x + left + w - (w * mright), height - (y + top + (h / 2)) - 15, 5, 30)
                    cr.fill()
                    cr.rectangle(x + left + (w / 2) - 15, height - (y + top + h - (mtop * h) + 4), 30, 5)
                    cr.fill()
                    cr.rectangle(x + left + (w / 2) - 15, height - (y + top + (mbottom * h)), 30, 5)
                    cr.fill()

            cr.move_to(x + left + 10, height - (y + top + h) + 20)
            cr.show_text(region.get_label())
