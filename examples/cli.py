import argparse
from pyatem.command import CutCommand, PreviewInputCommand
from pyatem.protocol import AtemProtocol

switcher = None
_inputs = {}
_switch_to = None
looping = True


def input_changed(inputproperties):
    global _inputs
    _inputs[inputproperties.short_name] = inputproperties.index


def connection_ready(*args):
    global looping
    select = PreviewInputCommand(index=0, source=_inputs[_switch_to])
    switch = CutCommand(index=0)
    switcher.send_commands([select, switch])
    looping = False


def main():
    global switcher, _switch_to
    parser = argparse.ArgumentParser(description="Atem CLI")
    parser.add_argument('ip', help='Atem ip or "usb" for usb')
    parser.add_argument('command', help='Command to execute')
    args = parser.parse_args()

    _switch_to = args.command

    if args.ip == 'usb':
        switcher = AtemProtocol(usb='auto')
    else:
        switcher = AtemProtocol(ip=args.ip)

    switcher.on('change:input-properties:*', input_changed)
    switcher.on('connected', connection_ready)

    switcher.connect()
    while looping:
        switcher.loop()


if __name__ == '__main__':
    main()
