# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import socket


class VideoHub:
    _SECTION_UNKNOWN = 0
    _SECTION_PREAMBLE = 1
    _SECTION_DEVICE = 2
    _SECTION_INPUTLABEL = 3
    _SECTION_INPUTSTATUS = 4
    _SECTION_OUTPUTLABEL = 5
    _SECTION_CONFIGURATION = 6
    _SECTION_ROUTING = 7
    _SECTION_END = 8

    def __init__(self, ip, port=9990):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.version = None

        self._section = VideoHub._SECTION_PREAMBLE
        self._sections = {
            'PROTOCOL PREAMBLE:': VideoHub._SECTION_PREAMBLE,
            'VIDEOHUB DEVICE:': VideoHub._SECTION_DEVICE,
            'INPUT LABELS:': VideoHub._SECTION_INPUTLABEL,
            'VIDEO INPUT STATUS:': VideoHub._SECTION_INPUTSTATUS,
            'OUTPUT LABELS:': VideoHub._SECTION_OUTPUTLABEL,
            'CONFIGURATION:': VideoHub._SECTION_CONFIGURATION,
            'VIDEO OUTPUT ROUTING:': VideoHub._SECTION_ROUTING,
            'END PRELUDE:': VideoHub._SECTION_END,
        }

        self.model = 'Unknown'
        self.model_display = 'Unknown'
        self.uuid = ''
        self.mode = None
        self.input_count = 0
        self.output_count = 0
        self.input_label = {}
        self.input_status = {}
        self.output_label = {}
        self.output_source = {}

        self._handler = {
            'connect': set(),
            'disconnect': set(),
            'route-change': set(),
            'input-label-change': set(),
            'output-label-change': set(),
            'input-status-change': set(),
        }

    def connect(self):
        self.sock.connect((self.ip, self.port))
        self.sock.settimeout(15)
        line = self._readline()
        if line != 'PROTOCOL PREAMBLE:':
            raise ValueError("Not a videohub")
        version = self._readline()
        _, self.version = version.split(': ', maxsplit=1)

    def _readline(self):
        buffer = b''
        while True:
            char = self.sock.recv(1)
            if char == b'\n':
                return buffer.decode()
            buffer += char

    def on(self, event, handler):
        if event not in self._handler:
            raise ValueError("Unknown event")
        self._handler[event].add(handler)

    def _raise(self, event, **kwargs):
        for handler in self._handler[event]:
            handler(self, **kwargs)

    def _parse_device(self, line):
        key, value = line.split(': ', maxsplit=1)
        if key == 'Model name':
            self.model = value
        elif key == 'Friendly name':
            self.model_display = value
        elif key == 'Unique ID':
            self.uuid = value
        elif key == 'Video inputs':
            self.input_count = int(value)
        elif key == 'Video outputs':
            self.output_count = int(value)

    def _parse_configuration(self, line):
        key, value = line.split(': ', maxsplit=1)
        if key == 'Video Mode':
            self.mode = value

    def _parse_inputlabel(self, line):
        key, value = line.split(' ', maxsplit=1)
        index = int(key)
        self.input_label[index] = value
        self._raise('input-label-change', index=index, label=value)

    def _parse_inputstatus(self, line):
        key, value = line.split(' ', maxsplit=1)
        index = int(key)
        self.input_status[index] = value
        self._raise('input-status-change', index=index, status=value)

    def _parse_outputlabel(self, line):
        key, value = line.split(' ', maxsplit=1)
        index = int(key)
        self.output_label[index] = value
        self._raise('output-label-change', index=index, label=value)

    def _parse_routing(self, line):
        if line == 'ACK':
            return
        key, value = line.split(' ', maxsplit=1)
        index = int(key)
        source = int(value)
        self.output_source[index] = source
        self._raise('route-change', index=index, source=source)

    def _ping(self):
        self.sock.send(b'PING:\n\n')

    def loop(self):
        try:
            line = self._readline()
        except TimeoutError:
            # No traffic for 15 seconds, try to send a ping
            self._ping()
            return

        if line == '' or line == 'ACK':
            return

        if line in self._sections:
            self._section = self._sections[line]
            if self._section == VideoHub._SECTION_END:
                self._raise('connect')
            return
        elif line.endswith(':'):
            self._section = VideoHub._SECTION_UNKNOWN
            return

        if self._section == VideoHub._SECTION_DEVICE:
            return self._parse_device(line)
        elif self._section == VideoHub._SECTION_INPUTLABEL:
            return self._parse_inputlabel(line)
        elif self._section == VideoHub._SECTION_INPUTSTATUS:
            return self._parse_inputstatus(line)
        elif self._section == VideoHub._SECTION_OUTPUTLABEL:
            return self._parse_outputlabel(line)
        elif self._section == VideoHub._SECTION_CONFIGURATION:
            return self._parse_configuration(line)
        elif self._section == VideoHub._SECTION_ROUTING:
            return self._parse_routing(line)

    def set_source(self, index, source):
        cmd = f'VIDEO OUTPUT ROUTING:\n{index} {source}\n\n'
        self.sock.send(cmd.encode())


if __name__ == '__main__':
    test = VideoHub('192.168.2.84')
    test.connect()


    def on_connect(device):
        print(device.model)
        device.set_source(1, 4)


    def on_route(device, index, source):
        print(f"Route: {device.input_label[source]} -> {device.output_label[index]}")


    test.on('connect', on_connect)
    test.on('route-change', on_route)
    while True:
        test.loop()
