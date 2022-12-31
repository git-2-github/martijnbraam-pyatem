# Copyright 2022 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import argparse
import ipaddress

import pyatem.converters.converter as conv


def enumerate_hardware():
    classes = []
    for name, cls in conv.__dict__.items():
        if isinstance(cls, type) and name not in ['Field', 'ValueField', 'Converter']:
            classes.append(cls)
    return classes


def main():
    parser = argparse.ArgumentParser(description="Blackmagic Design Converter Setup")
    parser.add_argument('--factory-reset', action='store_true', help='Run the factory reset operation', dest='reset')
    parser.add_argument('--lut', help='Set new lut from a .cube file')
    args = parser.parse_args()

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

    print(f"Product:  {deviceclass.NAME}")

    device = deviceclass()
    device.connect()
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
            print(f'{field.label}:  {value}')
        else:
            print(field.label + ':')
            for key, display in field.mapping.items():
                x = 'x' if key == value else ' '
                print(f'    [{x}] {display}')

    if args.reset:
        print()
        print("Factory reset requested, press enter to reset all settings for this device or press ctrl+c to cancel")
        input()
        print("Executing factory reset")
        device.factory_reset()

    if args.lut is not None:
        print("Uploading new LUT to the converter...")
        device.set_lut(args.lut)
        print("done")


if __name__ == '__main__':
    main()
