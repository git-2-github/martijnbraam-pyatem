import logging
import struct

from pyatem.transport import UdpProtocol, Packet, UsbProtocol, TcpProtocol
from pyatem.command import LockCommand, TransferDownloadRequestCommand, TransferAckCommand
from pyatem.media import rle_decode
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

        self.locks = {}
        self.mode = None
        self.transfer_queue = {}
        self.transfer_id = 42
        self.transfer_buffer = b''
        self.transfer_buffer2 = []
        self.transfer_store = None
        self.transfer_slot = None
        self.transfer_requested = False
        self.transfer_packets = 0

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
        try:
            for fieldname, data in self.decode_packet(packet.data):
                self.save_field_data(fieldname, data)
        except ConnectionError:
            print("Encountered protocol corruption, closing connection")
            self._raise('disconnected')
            self.mixerstate = {}
            self.connected = False

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

            # A zero length header is not possible, this occurs when the transport layer has corruption, mark the
            # connection closed to restart and recover state
            if datalen == 0:
                raise ConnectionError()

            raw = data[offset + 8:offset + datalen]
            yield (cmd, raw)
            offset += datalen

    def save_field_data(self, fieldname, contents):
        fieldname_to_pretty = {
            '_ver': 'firmware-version',
            '_pin': 'product-name',
            '_top': 'topology',
            'Time': 'time',
            'TCCc': 'time-config',
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
            'FMHP': 'fairlight-headphones',
            'FAMS': 'fairlight-solo',
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
            'SRSU': 'streaming-service',
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
            'LKOB': 'lock-obtained',
            'FTDa': 'file-transfer-data',
            'LKST': 'lock-state',
            'FTDE': 'file-transfer-error',
            'FTDC': 'file-transfer-data-complete',
            'AMLv': 'audio-meter-levels',
            'FMLv': 'fairlight-meter-levels',
            'FDLv': 'fairlight-master-levels',
            'CCdP': 'camera-control-data-packet',
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
            'camera-control-data-packet': '>BBB',
        }

        raw = contents
        key = fieldname.decode()
        if key in fieldname_to_pretty:
            key = fieldname_to_pretty[key]
            classname = key.title().replace('-', '') + "Field"
            if hasattr(fieldmodule, classname):
                contents = getattr(fieldmodule, classname)(contents)

        if key == 'CapA':
            return

        if key == 'lock-obtained':
            logging.debug('Got lock for {}'.format(contents.store))
            self.locks[contents.store] = True
            self._transfer_trigger(contents.store)
            return
        elif key == 'lock-state':
            logging.info(contents)
            return
        elif key == 'file-transfer-data':
            if contents.transfer == self.transfer_id:
                self.transfer_packets += 1
                self.transfer_buffer += contents.data
                if self.transfer_packets % 20 == 0:
                    total_size = self.mixerstate['video-mode'].get_pixels() * 4
                    transfer_progress = len(self.transfer_buffer) / total_size
                    self._raise('transfer-progress', self.transfer_store, self.transfer_slot, transfer_progress)
                # The 0 should be the transfer slot, but it seems it's always 0 in practice
                self.send_commands([TransferAckCommand(self.transfer_id, 0)])
            else:
                logging.error('Got file transfer data for wrong transfer id')
            return
        elif key == 'file-transfer-error':
            print("file-transfer-error", contents)
            self.transfer_requested = False
            if contents.status == 1:
                # Status is try-again
                logging.debug('Retrying transfer')
                self._transfer_trigger(self.transfer_store, retry=True)
            elif contents.status == 5:
                self.locks[self.transfer_store] = False
                self._transfer_trigger(self.transfer_store, retry=True)
            return
        elif key == 'file-transfer-data-complete':
            logging.debug('Transfer complete')
            if contents.transfer != self.transfer_id:
                return
            # Remove current item from the transfer queue
            queue = self.transfer_queue[self.transfer_store]
            self.transfer_queue[self.transfer_store] = queue[1:]

            # Assemble the buffer
            data = self.transfer_buffer
            self.transfer_buffer = b''
            self.transfer_requested = False

            # Decompress the buffer if needed
            if self.transfer_store == 0:
                data = rle_decode(data)

            self._raise('download-done', self.transfer_store, self.transfer_slot, data)

            # Start next transfer in the queue
            self._transfer_trigger(self.transfer_store)
            return

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

    def download(self, store, index):
        logging.info("Queue download of {}:{}".format(store, index))
        if store not in self.transfer_queue:
            self.transfer_queue[store] = []
        self.transfer_queue[store].append(index)
        self._transfer_trigger(store)

    def _transfer_trigger(self, store, retry=False):
        next = None

        # Try the preferred queue
        if store in self.transfer_queue:
            if len(self.transfer_queue[store]) > 0:
                next = (store, self.transfer_queue[store][0])

        # Try any queue
        if next is None:
            for store in self.transfer_queue:
                if len(self.transfer_queue[store]) > 0:
                    next = (store, self.transfer_queue[store][0])
                    break

        # All transfers done, clean locks
        if next is None:
            for lock in self.locks:
                if self.locks[lock]:
                    logging.info('Releasing lock {}'.format(lock))
                    cmd = LockCommand(lock, False)
                    self.send_commands([cmd])
            return

        # Request a lock if needed
        if next[0] != 0xffff and (next[0] not in self.locks or not self.locks[next[0]]):
            logging.info('Requesting lock for {}'.format(next[0]))
            cmd = LockCommand(next[0], True)
            self.send_commands([cmd])
            return

        # A transfer request is already running, don't start a new one
        if self.transfer_requested:
            logging.info('Request already submitted, do nothing')
            return

        # Assign a transfer id and start the transfer
        if not retry:
            self.transfer_id += 1
        self.transfer_store, self.transfer_slot = next
        cmd = TransferDownloadRequestCommand(self.transfer_id, next[0], next[1])
        logging.info('Requesting download of {}:{}'.format(*next))
        self.transfer_requested = True
        self.send_commands([cmd])


if __name__ == '__main__':
    from pyatem.command import CutCommand
    import pyatem.mediaconvert
    from pyatem.cameracontrol import CameraControlData

    logging.basicConfig(level=logging.INFO)

    testmixer = AtemProtocol('192.168.2.84')


    # testmixer = AtemProtocol(usb='auto')

    def changed(key, contents):
        if key == 'time':
            return
        if isinstance(contents, fieldmodule.CameraControlDataPacketField):
            parsed = CameraControlData.from_data(contents)
            if parsed:
                print(parsed)
                return
        if isinstance(contents, fieldmodule.FieldBase):
            print(contents)
        else:
            print(key)


    def connected():
        for mid in testmixer.mixerstate['macro-properties']:
            macro = testmixer.mixerstate['macro-properties'][mid]
            if macro.is_used:
                # testmixer.download(0xffff, macro.index)
                pass
        return
        for sid in testmixer.mixerstate['mediaplayer-file-info']:
            still = testmixer.mixerstate['mediaplayer-file-info'][sid]
            if not still.is_used:
                continue
            # print("Fetching {}".format(still.name))
            # testmixer.download(0, still.index)


    def downloaded(store, slot, data):
        logging.info('Downloaded {}:{}'.format(store, slot))
        with open(f'/workspace/usb-{store}-{slot}.bin', 'wb') as handle:
            handle.write(data)
        data = pyatem.mediaconvert.atem_to_rgb(data, 1920, 1080)
        with open(f'/workspace/usb-{store}-{slot}.data', 'wb') as handle:
            handle.write(data)


    def progress(store, slot, factor):
        print(factor * 100)


    testmixer.on('connected', connected)
    testmixer.on('download-done', downloaded)
    testmixer.on('transfer-progress', progress)
    testmixer.on('change', changed)

    testmixer.connect()
    while True:
        testmixer.loop()
