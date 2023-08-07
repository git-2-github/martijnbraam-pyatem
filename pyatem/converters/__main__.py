# Copyright 2022 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import argparse
import ipaddress
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
        field = codelut[item]
        if isinstance(field.mapping, dict):
            arg_type = int
        elif field.mapping == 'dB':
            arg_type = float
        opt.add_argument('--' + item, type=arg_type)

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
        if isinstance(field.mapping, str):
            if field.mapping == 'dB':
                value = float(value)
                value = int(round(math.pow(10, value / 20) * 64))

        print_option(field, value)
        device.set_value(field, value)

    last_section = None
    for field in device.get_state().values():
        if field.section != last_section:
            print(f"\n===[ {field.section} ]===")
            last_section = field.section
        if field.dtype == str:
            value = field.value.split(b'\0')[0].decode()
        elif field.dtype == int:
            value = int.from_bytes(field.value, byteorder='little')
        elif field.dtype == bool:
            value = int.from_bytes(field.value, byteorder='little') > 0
        elif field.dtype == open:
            continue
        elif field.dtype == ipaddress.IPv4Address:
            value = ipaddress.IPv4Address(field.value)
        else:
            raise ValueError("Unknown type")

        if field.mapping is None:
            print_option(field, value)
        elif isinstance(field.mapping, dict):
            print(field.label + ':')
            for key, display in field.mapping.items():
                x = 'x' if key == value else ' '
                if annotate:
                    print(f'    [{x}] {display} (--{field.code} {key})')
                else:
                    print(f'    [{x}] {display}')
        elif isinstance(field.mapping, str):
            if field.mapping == 'dB':
                if value > 0:
                    value = 20 * math.log10(value / 64)
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
