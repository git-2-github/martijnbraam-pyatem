import argparse
import signal

import tabulate

from pyatem.protocol import AtemProtocol
from pyatem.hexdump import hexdump

switcher = None
result = {}


def on_change(key, contents):
    global switcher
    global result
    if isinstance(contents, bytes):
        if key not in result:
            result[key] = set()
        result[key].add(contents)

    if key == 'multiviewer-input' or key == 'time':
        return
    
    print(key)
    if isinstance(contents, bytes):
        print('    ' + hexdump(contents, 'return').replace('\n', '\n    '))
    else:
        print('    ' + repr(contents))


def sigint_handler(signal, frame):
    print('--- [ Report ] ---')
    rows = []

    for field in result:
        d = ''
        for r in result[field]:
            d += repr(r) + '\n'
        rows.append((
            field,
            len(result[field]),
            d
        ))

    print(tabulate.tabulate(rows, headers=['field', 'count', 'data']))
    exit(0)


def on_connected():
    global switcher
    global testqueue
    global prepqueue
    global stats_start

    signal.signal(signal.SIGINT, sigint_handler)

    print("Connection successful")
    model = switcher.mixerstate['product-name']
    print(f"Detected hardware: {model.name}")


def on_disconnected():
    print("Hardware has disconnected")


def run(device):
    global switcher
    print(f"Connecting to {device}...")
    switcher = AtemProtocol(device)
    switcher.on('connected', on_connected)
    switcher.on('disconnected', on_disconnected)
    switcher.on('change', on_change)
    switcher.connect()
    while True:
        switcher.loop()


def main():
    parser = argparse.ArgumentParser(description="Find non-implemented fields in the connected hardware")
    parser.add_argument('device', help="Device ip address or 'usb'")
    args = parser.parse_args()
    run(args.device)


if __name__ == '__main__':
    main()
