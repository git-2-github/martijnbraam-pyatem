import os
import urllib.request
from pathlib import Path

import gi
import pyatem

from gtk_switcher.colorwheel import ColorWheelWidget
from pyatem.field import InputPropertiesField
from pyatem.media import atem_to_rgb

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, Gdk, GdkPixbuf

gi.require_version('Handy', '1')
from gi.repository import Handy


class MediaPage:
    def __init__(self, builder):
        self.media_flow = builder.get_object('media_flow')
        self.model_media = builder.get_object('model_media')
        self.media_slot = {}
        self.media_slot_name = {}
        self.media_slot_box = {}
        self.media_slot_progress = {}
        self.media_pixbuf = {}
        self.media_queue = []
        self.media_last_upload = None

        self.media_context = None

    def on_mediaplayer_slots_change(self, data):
        for child in self.media_flow:
            child.destroy()
        self.model_changing = True
        self.model_media.clear()

        for i in range(0, data.stills):
            self.model_media.append([f"{i}", f"{i + 1}: "])

            slot = Gtk.Frame()
            slot.index = i
            slot.drag_dest_set(Gtk.DestDefaults.MOTION |
                               Gtk.DestDefaults.HIGHLIGHT | Gtk.DestDefaults.DROP,
                               [Gtk.TargetEntry.new("text/uri-list", 0, 80)], Gdk.DragAction.COPY)
            slot.connect('drag_data_received', self.on_media_file_dropped)
            slot.get_style_context().add_class('view')
            grid = Gtk.Grid()
            grid.set_column_spacing(8)
            grid.set_row_spacing(4)
            grid.set_margin_top(6)
            grid.set_margin_bottom(6)
            grid.set_margin_start(6)
            grid.set_margin_end(6)
            slot.add(grid)
            slot.get_style_context().add_class('media-slot')

            slot_number = Gtk.Label(label=str(i + 1))
            slot_number.get_style_context().add_class('dim-label')
            grid.attach(slot_number, 0, 0, 1, 1)

            slot_label = Gtk.Label("")
            slot_label.set_hexpand(True)
            slot_label.set_xalign(0.0)
            grid.attach(slot_label, 1, 0, 1, 1)

            slot_img = Gtk.Box()
            slot_img.get_style_context().add_class('mp-slot')
            slot_img.set_size_request(160, 120)
            grid.attach(slot_img, 0, 1, 2, 1)

            progress = Gtk.ProgressBar()
            progress.set_no_show_all(True)
            grid.attach(progress, 0, 2, 2, 1)

            self.media_slot[i] = slot
            self.media_slot_name[i] = slot_label
            self.media_slot_box[i] = slot_img
            self.media_slot_progress[i] = progress

            self.media_flow.add(slot)
        self.model_changing = False
        self.media_flow.show_all()

    def on_mediaplayer_file_info_change(self, data):
        if data.index not in self.media_slot_name:
            return
        self.set_class(self.media_slot[data.index], 'used', data.is_used)
        self.set_class(self.media_slot[data.index], 'empty', data.is_used)

        self.model_changing = True
        self.model_media[data.index][1] = f'{data.index + 1}: {data.name.decode()}'
        self.model_changing = False

        if self.media_last_upload is not None and data.index == self.media_last_upload:
            # Don't download the frame that was just uploaded
            self.media_last_upload = None
            return
        if data.is_used:
            self.media_slot_name[data.index].set_label(data.name.decode())
            if self.mainstack.get_visible_child_name() == 'media':
                self.connection.mixer.download(0, data.index)
            else:
                self.media_queue.append(data.index)
        else:
            if data.index in self.media_queue:
                self.media_queue.remove(data.index)
            self.media_slot_name[data.index].set_label("")
            for child in self.media_slot_box[data.index]:
                self.media_slot_box[data.index].remove(child)

    def on_media_transfer_progress(self, index, progress):
        if index not in self.media_slot_progress:
            return

        self.media_slot_progress[index].show()
        self.media_slot_progress[index].set_fraction(progress)

    def on_media_save(self, widget, target):
        frame = target.frame

        dialog = Gtk.FileChooserDialog(title="Saving frame", action=Gtk.FileChooserAction.SAVE)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE,
            Gtk.ResponseType.OK,
        )

        for fmt in GdkPixbuf.Pixbuf.get_formats():
            if fmt.is_writable():
                f = Gtk.FileFilter()
                f.set_name(fmt.description)
                f.fname = fmt.name
                for ext in fmt.get_extensions():
                    f.add_pattern(f"*.{ext}")
                dialog.add_filter(f)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filter = dialog.get_filter()
            frame.savev(dialog.get_filename(), filter.fname)
        dialog.destroy()

    def on_media_context_menu(self, widget, event):
        print("Button", event.button)
        if event.button != 3:
            return
        self.media_context = Gtk.Menu.new()

        item = Gtk.MenuItem.new_with_label("Save image")
        item.connect('activate', self.on_media_save, widget)
        self.media_context.append(item)
        self.media_context.show_all()
        self.media_context.popup_at_pointer()

    def on_media_download_done(self, index, data):
        if index not in self.media_slot:
            return

        if len(data) == 0:
            return

        width, height = self.connection.mixer.mixerstate['video-mode'].get_resolution()
        raw = atem_to_rgb(data, width, height)

        # Pad the frame to the right size instead of failing hard when the transfer is corrupted
        if len(raw) != (width * 4 * height):
            missing = (width * 4 * height) - len(raw)
            raw += b'\0' * missing

        gdk_raw = GLib.Bytes.new(raw)
        pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(gdk_raw, GdkPixbuf.Colorspace.RGB, True, 8, width, height,
                                                 width * 4)
        aw = 184
        thumb = pixbuf.scale_simple(aw, int(aw * height / width), GdkPixbuf.InterpType.BILINEAR)
        thumb_img = Gtk.Image.new_from_pixbuf(thumb)
        eventbox = Gtk.EventBox()
        eventbox.add(thumb_img)
        eventbox.frame = pixbuf
        eventbox.connect('button-press-event', self.on_media_context_menu)

        self.media_slot_box[index].add(eventbox)
        self.media_slot_box[index].show_all()
        self.media_slot_progress[index].hide()

    def on_page_media_open(self):
        for index in self.media_queue:
            self.media_slot_progress[index].show()
            self.connection.mixer.download(0, index)
        self.media_queue = []

    def dnd_uri_to_path(self, uri):
        # Strip the various schemes from dropped uris
        path = ""
        if uri.startswith('file:\\\\\\'):
            path = uri[8:]
        elif uri.startswith('file://'):
            path = uri[7:]
        elif uri.startswith('file:'):
            path = uri[5:]

        path = urllib.request.url2pathname(path)
        path = path.strip('\r\n\x00')
        return path

    def on_media_file_dropped(self, widget, context, x, y, selection, target_type, timestamp):
        index = widget.index

        # URI List
        if target_type == 80:
            data = selection.get_data().decode().strip('\r\n\0')
            for uri in data.split('\r\n'):
                path = self.dnd_uri_to_path(uri)
                if not os.path.isfile(path):
                    print(f"File does not exist: {path}")
                    continue
                self.media_slot_upload_file(index, path)
                index += 1

    def on_media_upload_done(self, store, slot):
        self.media_slot_progress[slot].hide()

        width, height = self.connection.mixer.mixerstate['video-mode'].get_resolution()
        pixbuf = self.media_pixbuf[slot]
        aw = 184
        thumb = pixbuf.scale_simple(aw, int(aw * height / width), GdkPixbuf.InterpType.BILINEAR)
        thumb_img = Gtk.Image.new_from_pixbuf(thumb)
        eventbox = Gtk.EventBox()
        eventbox.add(thumb_img)
        eventbox.frame = pixbuf
        eventbox.connect('button-press-event', self.on_media_context_menu)

        self.media_slot_box[slot].add(eventbox)
        self.media_slot_box[slot].show_all()

    def on_media_upload_progress(self, store, slot, percent, done, size):
        self.media_slot_progress[slot].set_fraction(percent / 100)

    def media_slot_upload_file(self, index, path):
        mode = self.connection.mixer.mixerstate['video-mode']
        width, height = mode.get_resolution()

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, width, height, preserve_aspect_ratio=True)

        name = Path(path).stem

        self.media_slot_upload_pixbuf(index, pixbuf, name=name)

    def media_slot_upload_pixbuf(self, index, pixbuf, name=None):
        print(f"Uploading pixbuf to media slot {index}")
        mode = self.connection.mixer.mixerstate['video-mode']
        width, height = mode.get_resolution()
        aspect = width / height
        swidth = pixbuf.get_width()
        sheight = pixbuf.get_height()
        saspect = swidth / sheight

        if saspect < aspect:
            scale = sheight / height
            dest_y = 0
            dest_x = (width - (swidth * scale)) / 2
        else:
            scale = swidth / width
            dest_x = 0
            dest_y = (height - (sheight * scale)) / 2

        dest_w = swidth * scale
        dest_h = sheight * scale

        dest = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height)
        pixbuf.scale(dest, dest_x, dest_y, dest_w, dest_h, dest_x, dest_y, scale, scale, GdkPixbuf.InterpType.BILINEAR)

        self.media_pixbuf[index] = pixbuf

        pixels = dest.get_pixels()
        frame = pyatem.media.rgb_to_atem(pixels, width, height)
        self.media_slot_progress[index].show()
        self.media_slot[index].get_style_context().add_class('uploading')
        self.connection.mixer.upload(0, index, frame, name=name)
        self.media_last_upload = index
