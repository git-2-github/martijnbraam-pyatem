# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import ctypes
import logging
import sys
import threading
import traceback

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GLib

from pyatem.videohub import VideoHub


class VideoHubConnection(threading.Thread):
    def __init__(self, ip, connected, disconnected, input_change, output_change, route_change):
        threading.Thread.__init__(self)

        self.log = logging.getLogger('VideoHubConnection')

        self.id = None

        self._connected = [connected]
        self._disconnected = [disconnected]
        self._input_change = [input_change]
        self._output_change = [output_change]
        self._route_change = [route_change]

        self.ip = ip

        self.hub = None

        self.stop = False
        self.connected = False

        self.inputs = {}
        self.outputs = {}

    def run(self):
        self.hub = VideoHub(self.ip)
        self.hub.on('connect', self.do_connected)
        self.hub.on('disconnect', self.do_disconnected)
        self.hub.on('input-label-change', self.do_input_label_change)
        self.hub.on('input-status-change', self.do_input_status_change)
        self.hub.on('output-label-change', self.do_output_label_change)
        self.hub.on('route-change', self.do_route_change)

        try:
            self.hub.connect()
        except ConnectionError as e:
            self.log.error(f"Could not connect to VideoHub at {self.ip}: {e}")
            return
        except OSError as e:
            self.log.error(f"Could not connect to VideoHub at {self.ip}: {e}")
            return
        while not self.stop:
            try:
                self.hub.loop()
            except Exception as e:
                traceback.print_exc()
                self.log.error(repr(e))

    def do_disconnected(self, hub):
        self.connected = False
        for handler in self._disconnected:
            GLib.idle_add(handler, self.id)

    def do_connected(self, hub):
        for handler in self._connected:
            GLib.idle_add(handler, self.id)

    def do_input_label_change(self, hub, index, label):
        if index not in self.inputs:
            self.inputs[index] = {
                'status': None,
                'label': None
            }
        self.inputs[index]['label'] = label

        for handler in self._input_change:
            GLib.idle_add(handler, self.id, index, self.inputs)

    def do_input_status_change(self, hub, index, status):
        if index not in self.inputs:
            self.inputs[index] = {
                'status': None,
                'label': None
            }
        self.inputs[index]['status'] = status
        for handler in self._input_change:
            GLib.idle_add(handler, self.id, index, self.inputs)

    def do_output_label_change(self, hub, index, label):
        if index not in self.outputs:
            self.outputs[index] = {
                'source': None,
                'label': None
            }
        self.outputs[index]['label'] = label
        for handler in self._output_change:
            GLib.idle_add(handler, self.id, index, self.outputs)

    def do_route_change(self, hub, index, source):
        if index not in self.outputs:
            self.outputs[index] = {
                'source': None,
                'label': None
            }
        self.outputs[index]['source'] = source
        for handler in self._route_change:
            GLib.idle_add(handler, self.id, index, source)

    def change_route(self, index, source):
        self.hub.set_source(index, source)

    def get_id(self):
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def die(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                         ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            self.log.error('Exception raise failure')
