import logging
import struct

from pyatem.transport import UdpProtocol, Packet
import pyatem.field as fieldmodule


class AtemProtocol:
    def __init__(self, ip, port=9910):
        self.transport = UdpProtocol(ip, port)

        self.mixerstate = {}
        self.callbacks = {}

    def connect(self):
        logging.debug('Starting connection')
        self.transport.connect()

    def loop(self):
        logging.debug('Waiting for data packet...')
        packet = self.transport.receive_packet()

        for fieldname, data in self.decode_packet(packet.data):
            self.save_field_data(fieldname, data)

    def on(self, event, callback):
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)

    def _raise(self, event, *args, **kwargs):
        if event in self.callbacks:
            for cb in self.callbacks[event]:
                cb(*args, **kwargs)

    def decode_packet(self, data):
        offset = 0
        while offset < len(data):
            datalen, cmd = struct.unpack_from('!H2x 4s', data, offset)
            raw = data[offset + 8:offset + datalen]
            yield (cmd, raw)
            offset += datalen

    def save_field_data(self, fieldname, contents):
        fieldname_to_pretty = {
            '_ver': 'firmware-version',
            '_pin': 'product-name',
            '_top': 'topology',
            'Time': 'time',
            '_MeC': 'mixer-effect-config',
            '_mpl': 'mediaplayer-slots',
            'VidM': 'video-mode',
            'InPr': 'input-properties',
            'PrgI': 'program-bus-input',
            'PrvI': 'preview-bus-input',
            'TrPr': 'transition-preview',
            'TrPs': 'transition-position',
            'TMxP': 'transition-mix',
            'TDpP': 'transition-dip',
            'TWpP': 'transition-wipe',
            'TDvP': 'transition-dve',
            'TStP': 'transition-stinger',
            'KeOn': 'key-on-air',
            'KeBP': 'key-properties-base',
            'KeLm': 'key-properties-luma',
            'KePt': 'key-properties-pattern',
            'KeDV': 'key-properties-dve',
            'KeFS': 'key-properties-fly',
            'KKFP': 'key-properties-fly-keyframe',
            'DskB': 'dkey-properties-base',
            'DskP': 'dkey-properties-mask',
            'DskS': 'dkey-properties-transition',
            'FtbP': 'fade-to-black',
            'FtbS': 'fade-to-black-state',
            'ColV': 'color-generator',
            'AuxS': 'aux-output-source',
            'MPfe': 'mediaplayer-file-info',
            'MPCE': 'mediaplayer-selected',
            'FASP': 'fairlight-strip-properties',
            'FAMP': 'fairlight-master-properties',
            '_TlC': 'tally-config',
            'TlIn': 'tally-index',
            'TlSr': 'tally-source',
            'FMTl': 'fairlight-tally',
            'MPrp': 'macro-properties',
            'AiVM': 'auto-input-video-mode',
        }

        fieldname_to_unique = {
            'mixer-effect-config': '>H',
            'input-properties': '>H',
            'program-bus-input': '>B',
            'preview-bus-input': '>B',
            'transition-preview': '>B',
            'transition-position': '>B',
            'transition-mix': '>B',
            'transition-dip': '>B',
            'transition-wipe': '>B',
            'transition-dve': '>B',
            'transition-stinger': '>B',
            'fairlight-strip-properties': '>H',
            'macro-properties': '>H',
        }

        if fieldname == b'InCm':
            print("done")
        raw = contents
        key = fieldname.decode()
        if key in fieldname_to_pretty:
            key = fieldname_to_pretty[key]
            classname = key.title().replace('-', '') + "Field"
            if hasattr(fieldmodule, classname):
                contents = getattr(fieldmodule, classname)(contents)

        if key in fieldname_to_unique:
            idx, = struct.unpack_from(fieldname_to_unique[key], raw, 0)
            if key not in self.mixerstate:
                self.mixerstate[key] = {}
            self.mixerstate[key][idx] = contents
            self._raise('change:' + key + ':' + str(idx), contents)
            self._raise('change:' + key + ':*', contents)
        else:
            self.mixerstate[key] = contents
            self._raise('change:' + key, contents)
        self._raise('change', key, contents)

    def send_commands(self, commands):
        data = b''
        for command in commands:
            data += command.get_command()

        if len(data) > 1300:
            raise ValueError("Command list too long for UDP packet")

        packet = Packet()
        packet.flags = UdpProtocol.FLAG_RELIABLE
        packet.data = data
        self.transport.send_packet(packet)


if __name__ == '__main__':
    from pyatem.command import CutCommand

    logging.basicConfig(level=logging.INFO)

    testmixer = AtemProtocol('192.168.2.17')

    waiter = 5
    waiting = False
    done = False


    def changed(key, contents):
        global waiter
        global waiting
        global done

        if waiting and not done:
            waiter -= 1
            if waiter == 0:
                logging.debug('SENDING CUT')
                done = True
                cmd = CutCommand(index=0)
                testmixer.send_commands([cmd])

        if key == 'InCm':
            waiting = True

        if key == 'time':
            return
        if isinstance(contents, fieldmodule.FieldBase):
            print(contents)
        else:
            print(key)


    testmixer.on('change', changed)

    testmixer.connect()
    while True:
        testmixer.loop()
