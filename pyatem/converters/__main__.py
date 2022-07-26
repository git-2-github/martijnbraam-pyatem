import argparse
import pyatem.converters.converter as conv


def enumerate_hardware():
    classes = []
    for name, cls in conv.__dict__.items():
        if isinstance(cls, type) and name not in ['Field', 'Converter']:
            classes.append(cls)
    return classes


def main():
    parser = argparse.ArgumentParser(description="Blackmagic Design Converter Setup")
    parser.add_argument('--factory-reset', action='store_true', help='Run the factory reset operation', dest='reset')
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
            value = field.value.decode()
        if field.dtype == int:
            value = int.from_bytes(field.value, byteorder='little')

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


if __name__ == '__main__':
    main()
