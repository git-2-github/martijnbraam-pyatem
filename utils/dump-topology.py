import argparse
from pyatem.protocol import AtemProtocol
from pyatem.hexdump import hexdump

switcher = None
result = {}


def on_connected():
    global switcher
    global testqueue
    global prepqueue
    global stats_start

    print("Connection successful")
    model = switcher.mixerstate['product-name']
    print(f"Detected hardware: {model.name}")
    fw = switcher.mixerstate['firmware-version']
    print(f"Firmware: {fw}")
    print()
    print("Topology:")
    top = switcher.mixerstate['topology']
    print(top)
    print(hexdump(top.raw))
    exit(0)


def on_disconnected():
    print("Hardware has disconnected")


def run(device):
    global switcher
    print(f"Connecting to {device}...")
    switcher = AtemProtocol(device)
    switcher.on('connected', on_connected)
    switcher.on('disconnected', on_disconnected)
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
