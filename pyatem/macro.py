# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
from pyatem.macrocommand import *
import pyatem.macrocommand as macromodule

macro_command_map = {
    0x0002: ProgramInputMacroCommand,
    0x0003: PreviewInputMacroCommand,
    0x0007: SleepMacroCommand,
    0x0014: TransitionWipeMacroCommand,
    0x0015: TransitionWipeMacroCommand,
    0x0016: TransitionWipeMacroCommand
}


def decode_macro(raw):
    result = []
    offset = 0

    last_command = None
    while offset < len(raw):
        length, command_id = struct.unpack_from('<HH', raw, offset)
        command_raw = raw[offset:offset + length]
        if command_id in macro_command_map:
            command = macro_command_map[command_id]
            if command == last_command:
                result[-1].add_action(command_id, command_raw)
            else:
                decoder = command()
                decoder.add_action(command_id, command_raw)
                result.append(decoder)
        else:
            decoder = BaseMacroCommand()
            decoder.add_action(command_id, command_raw)
            result.append(decoder)
        offset += length

    for decoder in result:
        decoder.decode()

    return result


def encode_macro(actions):
    result = b''
    for action in actions:
        result += action.encode()
    return result


def encode_macroscript(actions):
    result = ''
    for action in actions:
        result += action.encode_script()
    return result


def decode_macroscript(script):
    classmap = {}
    for name, cls in macromodule.__dict__.items():
        if isinstance(cls, type) and name != "BaseMacroCommand":
            classmap[cls.TAG] = cls

    result = []
    for line in script.splitlines(keepends=False):
        name, data = line.split(' ', maxsplit=1)
        if name in classmap:
            inst = classmap[name]()
        else:
            inst = BaseMacroCommand()
        inst.decode_script(data)
        result.append(inst)
    return result


if __name__ == '__main__':

    with open('/workspace/usb-65535-0.bin', 'rb') as handle:
        raw_macro = handle.read()

    result = decode_macro(raw_macro)
    print(result)

    encoded = encode_macroscript(result)
    print(encoded)
    decoded = decode_macroscript(encoded)
    print(decoded)
