import logging
import struct

from pyatem.transport import UdpProtocol, Packet, UsbProtocol, TcpProtocol
import pyatem.field as fieldmodule


class AtemProtocol:
    def __init__(self, ip=None, port=9910, usb=None):
        if ip is None and usb is None:
            raise ValueError("Need either an ip or usb port")
        if ip is not None:
            if ip.startswith('tcp://'):
                self.transport = TcpProtocol(url=ip)
            else:
                self.transport = UdpProtocol(ip, port)
        else:
            self.transport = UsbProtocol(usb)

        self.mixerstate = {}
        self.callbacks = {}
        self.inputs = {}
        self.callback_idx = 1
        self.connected = False

    @classmethod
    def usb_exists(cls):
        return UsbProtocol.device_exists()

    def connect(self):
        logging.debug('Starting connection')
        self.transport.connect()

    def loop(self):
        logging.debug('Waiting for data packet...')
        packet = self.transport.receive_packet()
        if packet is None:
            # Disconnected from hardware
            if self.connected:
                self._raise('disconnected')
                self.mixerstate = {}
            self.connected = False
            return
        self.connected = True
        for fieldname, data in self.decode_packet(packet.data):
            self.save_field_data(fieldname, data)

    def on(self, event, callback):
        if event not in self.callbacks:
            self.callbacks[event] = {}
        self.callbacks[event][self.callback_idx] = callback
        self.callback_idx += 1
        return self.callback_idx - 1

    def off(self, event, callback_id):
        if event not in self.callbacks:
            return
        del self.callbacks[event][callback_id]

    def _raise(self, event, *args, **kwargs):
        if event in self.callbacks:
            for cbidx in self.callbacks[event]:
                self.callbacks[event][cbidx](*args, **kwargs)

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
            'TrSS': 'transition-settings',
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
            'DskP': 'dkey-properties',
            'DskS': 'dkey-state',
            'FtbP': 'fade-to-black',
            'FtbS': 'fade-to-black-state',
            'ColV': 'color-generator',
            'AuxS': 'aux-output-source',
            'MPfe': 'mediaplayer-file-info',
            'MPCE': 'mediaplayer-selected',
            'AMMO': 'audio-mixer-master-properties',
            'AMmO': 'audio-mixer-monitor-properties',
            'AMTl': 'audio-mixer-tally',
            'FASP': 'fairlight-strip-properties',
            'FAMP': 'fairlight-master-properties',
            '_TlC': 'tally-config',
            'TlIn': 'tally-index',
            'TlSr': 'tally-source',
            'FMTl': 'fairlight-tally',
            'MPrp': 'macro-properties',
            'AiVM': 'auto-input-video-mode',
            'FASD': 'fairlight-strip-delete',
            'FAIP': 'fairlight-audio-input',
            'AMIP': 'audio-input',
            'RTMR': 'recording-duration',
            'RTMD': 'recording-disk',
            'RTMS': 'recording-status',
            'RMSu': 'recording-settings',
            'SRSU': 'streaming-services',
            'STAB': 'streaming-audio-bitrate',
            'StRS': 'streaming-status',
            'SRST': 'streaming-time',
            'SRSS': 'streaming-stats',
            'SAth': 'streaming-authentication',
            'AEBP': 'atem-eq-band-properties',
            'MvPr': 'multiviewer-properties',
            'MvIn': 'multiviewer-input',
            'VuMC': 'multiviewer-vu',
            'SaMw': 'multiviewer-safe-area',
        }

        fieldname_to_unique = {
            'mixer-effect-config': '>B',
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
            'fairlight-audio-input': '>H',
            'audio-input': '>H',
            'key-on-air': '>BB',
            'key-properties-base': '>BB',
            'key-properties-luma': '>BB',
            'key-properties-pattern': '>BB',
            'key-properties-dve': '>BB',
            'key-properties-fly': '>BB',
            'key-properties-fly-keyframe': '>BBB',
            'dkey-properties-base': '>B',
            'dkey-properties': '>B',
            'dkey-state': '>B',
            'fade-to-black': '>B',
            'fade-to-black-state': '>B',
            'color-generator': '>B',
            'aux-output-source': '>B',
            'mediaplayer-file-info': '>xxH',
            'mediaplayer-selected': '>B',
            'atem-eq-band-properties': '>H14xB',
            'multiviewer-properties': '>B',
            'multiviewer-input': '>BB',
            'multiviewer-vu': '>BB',
            'multiviewer-safe-area': '>BB',
        }

        raw = contents
        key = fieldname.decode()
        if key in fieldname_to_pretty:
            key = fieldname_to_pretty[key]
            classname = key.title().replace('-', '') + "Field"
            if hasattr(fieldmodule, classname):
                contents = getattr(fieldmodule, classname)(contents)

        if key in fieldname_to_unique:
            idxes = struct.unpack_from(fieldname_to_unique[key], raw, 0)
            if key not in self.mixerstate:
                self.mixerstate[key] = {}

            # Fairlight strips have weird numbering that's harder to parse here, read it back from the class
            if hasattr(contents, 'strip_id'):
                idxes = list(idxes)
                idxes[0] = contents.strip_id
                idxes = tuple(idxes)

            unique = self.make_unique_dict(contents, idxes)
            self.mixerstate[key] = self.recursive_merge(self.mixerstate[key], unique)
            self._raise('change:' + key + ':' + str(idxes[0]), contents)
            self._raise('change:' + key + ':*', contents)
        else:
            self.mixerstate[key] = contents
            self._raise('change:' + key, contents)
        if key == 'input-properties':
            self.inputs[contents.short_name] = contents.index

        if key == 'InCm':
            self._raise('connected')
        self._raise('change', key, contents)

    def make_unique_dict(self, content, path):
        result = {}
        if len(path) == 1:
            result[path[0]] = content
        else:
            result[path[0]] = self.make_unique_dict(content, path[1:])
        return result

    def recursive_merge(self, d1, d2):
        '''update first dict with second recursively'''
        if not isinstance(d2, dict):
            return d2
        for k, v in d1.items():
            if k in d2:
                d2[k] = self.recursive_merge(v, d2[k])
        d1.update(d2)
        return d1

    def send_commands(self, commands):
        data = b''
        for command in commands:
            data += command.get_command()

        if len(data) > 1300:
            raise ValueError("Command list too long for UDP packet")

        self.send_raw(data)

    def send_raw(self, data):
        packet = Packet()
        packet.flags = UdpProtocol.FLAG_RELIABLE
        packet.data = data
        self.transport.send_packet(packet)


if __name__ == '__main__':
    from pyatem.command import CutCommand

    logging.basicConfig(level=logging.INFO)

    # testmixer = AtemProtocol('192.168.2.17')
    testmixer = AtemProtocol(usb='auto')

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
