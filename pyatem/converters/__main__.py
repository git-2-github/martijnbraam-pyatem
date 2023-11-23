# Copyright 2022 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import argparse
import math
import os.path

import tqdm

import pyatem.converters.converter as conv
from pyatem.converters.protocol import Converter, WValueProtoConverter, Field

annotate = False


def enumerate_hardware():
    classes = []
    for name, cls in conv.__dict__.items():
        if isinstance(cls, type) and name not in ['Field', 'ValueField', 'Converter']:
            classes.append(cls)
    return classes


def dump_memory(device, target):
    if not isinstance(device, WValueProtoConverter):
        print("Operation not supported for this hardware")
        return

    memory = b''
    for offset in tqdm.tqdm(range(0x0000, 0xFFFF, 4)):
        chunk = bytes(device.handle.ctrl_transfer(bmRequestType=0xc1,
                                                  bRequest=83,
                                                  wValue=offset,
                                                  wIndex=0,
                                                  data_or_wLength=4))
        memory += chunk

    with open(target, 'wb') as handle:
        handle.write(memory)


def print_option(field, value):
    assert (isinstance(field, Field))
    if annotate and field.code is not None:
        print(f"{field.label}:  {value} (--{field.code})")
    else:
        print(f"{field.label}:  {value}")


def main():
    parser = argparse.ArgumentParser(description="Blackmagic Design Converter Setup")
    generic = parser.add_argument_group("Generic arguments")
    generic.add_argument('--factory-reset', action='store_true', help='Run the factory reset operation', dest='reset')
    generic.add_argument('--dump', help='Dump internal memory to file')
    generic.add_argument('--annotate', help='Show argument names', action='store_true')

    opt = parser.add_argument_group('Write converter setting')

    codes = set()
    codelut = {}
    for device in enumerate_hardware():
        for arg in device.FIELDS:
            if arg.code is not None:
                codes.add(arg.code)
                codelut[arg.code] = arg

    for item in sorted(codes):
        arg_type = None
        arg_choices = None
        field = codelut[item]
        if isinstance(field.mapping, dict):
            arg_type = str
            arg_choices = []
            for option in field.mapping.values():
                arg_choices.append(option[0])
        elif field.mapping == 'dB':
            arg_type = float
        opt.add_argument('--' + item, type=arg_type, choices=arg_choices)

    args = parser.parse_args()

    global annotate
    if args.annotate:
        annotate = True

    existing = []
    for device in enumerate_hardware():
        if device.is_plugged_in():
            existing.append(device)

    if len(existing) == 0:
        print("No supported hardware detected")
        exit(1)
    elif len(existing) > 1:
        print("Multiple converters found, not handled yet")
        for dev in existing:
            print(f" - {dev.NAME}")
        exit(1)

    deviceclass = existing[0]
    possible_codes = set()
    for item in deviceclass.FIELDS:
        if item.code is not None:
            possible_codes.add(item.code)

    print(f"Product:  {deviceclass.NAME}")

    to_write = []
    for code in codes:
        key = code.replace('-', '_')
        if getattr(args, key) is not None:
            if code not in possible_codes:
                print(f"Option --{code} is not valid for this device")
                exit(1)
            for item in deviceclass.FIELDS:
                if item.code == code:
                    to_write.append((item, getattr(args, key)))

    device = deviceclass()
    device.connect()
    if device.get_status() == Converter.STATUS_NEED_POWER:
        print("Converter needs power plugged in to be configured")
        exit(1)

    if args.dump:
        dump_memory(device, args.dump)
        exit(0)

    if len(to_write) > 0:
        print('===[ Write values ]===')
    lut_writes = []
    for field, value in to_write:
        if field.dtype == open:
            lut_writes.append((field, value))
            continue
        elif isinstance(field.mapping, dict):
            for raw_val in field.mapping:
                if field.mapping[raw_val][0] == value:
                    value = raw_val
                    break

        print_option(field, value)
        device.set_value(field, value)

    last_section = None
    device_state = device.get_state()
    for field_config in device.FIELDS:
        field = device_state[field_config.key]
        if field is None:
            continue
        if field.section != last_section:
            print(f"\n===[ {field.section} ]===")
            last_section = field.section
        value = field.value
        if field.dtype == open:
            continue
        if field.mapping is None:
            print_option(field, value)
        elif isinstance(field.mapping, dict):
            print(field.label + ':')
            got_check = False
            for key, display in field.mapping.items():
                x = 'x' if key == value else ' '
                if key == value:
                    got_check = True
                if annotate:
                    print(f'    [{x}] {display[1]} (--{field.code} {display[0]})')
                else:
                    print(f'    [{x}] {display[1]}')
            if not got_check:
                print(f"    Unknown value: {value}")
        elif isinstance(field.mapping, str):
            if field.mapping == 'dB':
                if value > float('-inf'):
                    print_option(field, f' {value:.2f} dB')
                else:
                    print_option(field, 'off')

    for field, value in lut_writes:
        title = os.path.basename(value)
        print(f"Uploading LUT '{title}'...")
        device.set_lut(field.key, value)
        print("done")

    if args.reset:
        print()
        print("Factory reset requested, press enter to reset all settings for this device or press ctrl+c to cancel")
        input()
        print("Executing factory reset")
        device.factory_reset()


if __name__ == '__main__':
    main()
