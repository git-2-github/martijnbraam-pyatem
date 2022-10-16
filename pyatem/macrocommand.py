# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import shlex
import struct


class BaseMacroCommand:
    NAME = "Unknown action"
    TAG = "unknown-action"

    def __init__(self):
        self.actions = {}
        self.fields = {}
        self.lengths = {}
        self.widgets = {}

    def define_field(self, action, name, offset, packing):
        if action not in self.fields:
            self.fields[action] = []

        self.fields[action].append((offset, name, packing))

    def field_length(self, action, length):
        # Store action length without header
        self.lengths[action] = length - 4

    def add_action(self, action_id, raw):
        self.actions[action_id] = raw[4:]

    def add_widget(self, action_id, name, label, datatype, **kwargs):
        if action_id not in self.widgets:
            self.widgets[action_id] = []
        self.widgets[action_id].append((name, datatype, label, kwargs))

    def definition(self):
        pass

    def make_format(self, action):
        f = '<'
        current_offset = 0
        for offset, name, packing in sorted(self.fields[action]):
            if offset > current_offset:
                f += f'{offset - current_offset}x '
                current_offset = offset
            f += f'{packing} '
            current_offset += struct.calcsize(packing)
        if action in self.lengths:
            if current_offset < self.lengths[action]:
                f += '{}x'.format(self.lengths[action] - current_offset)
        return f

    def decode(self):
        self.definition()
        for action in self.fields:
            f = self.make_format(action)
            result = struct.unpack_from(f, self.actions[action], 0)
            for idx, field in enumerate(sorted(self.fields[action])):
                setattr(self, field[1], result[idx])

    def encode(self):
        result = b''
        for action in self.fields:
            f = self.make_format(action)
            fields = []
            for idx, field in enumerate(sorted(self.fields[action])):
                fields.append(getattr(self, field[1]))
            raw = struct.pack(f, *fields)
            header = struct.pack('<HH', self.lengths[action] + 4, action)
            result += header + raw
        return result

    def encode_script(self):
        result = self.__class__.TAG
        data = {}
        for action in self.fields:
            for offset, name, packing in self.fields[action]:
                data[name] = getattr(self, name)
        if len(data):
            parts = []
            for key in data:
                part = key + '='
                if isinstance(data[key], int) or isinstance(data[key], float) or isinstance(data[key], bool):
                    part += str(data[key])
                elif data[key] is None:
                    continue
                else:
                    part += '"' + str(data[key]).replace("\n", "\\n") + '"'
                parts.append(part)
            result += ' ' + ' '.join(parts)
        return result + "\n"

    def decode_script(self, raw_data):
        parts = shlex.split(raw_data, posix=False)
        for part in parts:
            key, value = part.split('=', maxsplit=1)
            if value.startswith('"'):
                value = value[1:-1]
            elif value == "False" or value == "True":
                value = value == "True"
            elif '.' in value:
                value = float(value)
            elif value.isnumeric():
                value = int(value)
            setattr(self, key, value)

    def __repr__(self):
        for a in self.actions:
            return '<action-unknown id={}>'.format(a)


class SleepMacroCommand(BaseMacroCommand):
    NAME = "Sleep"
    TAG = "sleep"

    def __init__(self):
        super().__init__()
        self.frames = None

    def definition(self):
        self.field_length(0x0007, 8)
        self.define_field(0x0007, 'frames', 0, 'H')
        self.add_widget(0x0007, 'frames', 'Duration', 'framecount')

    def __repr__(self):
        return '<sleep frames={}>'.format(self.frames)


class PreviewInputMacroCommand(BaseMacroCommand):
    NAME = "Preview input"
    TAG = "preview-input"

    def __init__(self):
        super().__init__()
        self.index = None
        self.source = None

    def definition(self):
        self.field_length(0x0003, 8)
        self.define_field(0x0003, 'index', 0, 'B')
        self.define_field(0x0003, 'source', 2, 'H')
        self.add_widget(0x0003, 'index', 'M/E unit', 'number', offset=1, min=1, max=4)
        self.add_widget(0x0003, 'source', 'Input', 'source', dataset='available_me')

    def __repr__(self):
        return '<preview-input me={} source={}>'.format(self.index, self.source)


class ProgramInputMacroCommand(BaseMacroCommand):
    NAME = "Program input"
    TAG = "program-input"

    def __repr__(self):
        return '<program-input>'


class TransitionWipeMacroCommand(BaseMacroCommand):
    NAME = "Transition wipe settings"
    TAG = "transition-wipe-settings"

    def __repr__(self):
        return '<transition-wipe>'
