import logging
import struct

from pyatem.transport import UdpProtocol, Packet
import pyatem.field as fieldmodule


class AtemProtocol:
    def __init__(self, ip, port=9910):
        self.transport = UdpProtocol(ip, port)

        self.mixerstate = {}
        self.callbacks = {}
        self.locks = {}
        self.mode = None
        self.transfer_queue = {}
        self.transfer_id = 42
        self.transfer_buffer = b''
        self.transfer_store = None
        self.transfer_slot = None
        self.transfer_requested = False

    def connect(self):
        logging.debug('Starting connection')
        self.transport.connect()

    def loop(self):
        logging.debug('Waiting for data packet...')
        packet = self.transport.receive_packet()

        for fieldname, data in self.decode_packet(packet.data):
            self.save_field_data(fieldname, data)

    def download(self, store, index):
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
                    logging.debug('Releasing lock {}'.format(lock))
                    cmd = LockCommand(lock, False)
                    self.send_commands([cmd])
            return

        # Request a lock if needed
        if next[0] not in self.locks or not self.locks[next[0]]:
            logging.debug('Requesting lock for {}'.format(next[0]))
            cmd = LockCommand(next[0], True)
            self.send_commands([cmd])
            return

        # A transfer request is already running, don't start a new one
        if self.transfer_requested:
            logging.debug('Request already submitted, do nothing')
            return

        # Assign a transfer id and start the transfer
        if not retry:
            self.transfer_id += 1
        self.transfer_store, self.transfer_slot = next
        cmd = TransferDownloadRequestCommand(self.transfer_id, next[0], next[1])
        logging.debug('Requesting download of {}:{}'.format(*next))
        self.transfer_requested = True
        self.send_commands([cmd])

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
            'FASP': 'fairlight-strip-properties',
            'FAMP': 'fairlight-master-properties',
            '_TlC': 'tally-config',
            'TlIn': 'tally-index',
            'TlSr': 'tally-source',
            'FMTl': 'fairlight-tally',
            'MPrp': 'macro-properties',
            'AiVM': 'auto-input-video-mode',
            'FASD': 'fairlight-strip-ding',
            'FAIP': 'fairlight-audio-input',
            'AMIP': 'audio-input',
            'LKOB': 'lock-obtained',
            'FTDa': 'file-transfer-data',
            'LKST': 'lock-state',
            'FTDE': 'file-transfer-error',
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
            'fairlight-audio-input': '>H',
            'audio-input': '>H',
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

        if key == 'lock-obtained':
            logging.debug('Got lock for {}'.format(contents.store))
            self.locks[contents.store] = True
            self._transfer_trigger(contents.store)
            return
        elif key == 'lock-state':
            logging.debug('Lock state changed')
        elif key == 'file-transfer-data':
            if contents.transfer == self.transfer_id:
                self.transfer_buffer += contents.data
                self.send_commands([TransferAckCommand(self.transfer_id, 0)])
            return
        elif key == 'file-transfer-error':
            if contents.status == 1:
                # Status is try-again
                logging.debug("Retrying transfer")
                self._transfer_trigger(self.transfer_store, retry=True)
                return
        elif key == 'FTDC':
            logging.debug('Transfer complete')
            queue = self.transfer_queue[self.transfer_store]
            self.transfer_queue[self.transfer_store] = queue[1:]
            self._transfer_trigger(self.transfer_store)
            self._raise('download-done', self.transfer_store, self.transfer_slot, self.transfer_buffer)
            return
        elif key == 'video-mode':
            # Store the current video mode for image processing
            self.mode = contents

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
    from pyatem.command import CutCommand, TransferDownloadRequestCommand, LockCommand, TransferAckCommand

    logging.basicConfig(level=logging.INFO)

    testmixer = AtemProtocol('192.168.2.84')

    waiter = 5
    waiting = False
    done = False


    def changed(key, contents):
        global waiter
        global waiting
        global done

        if key == 'InCm':
            waiting = True
            testmixer.download(0, 0)

        if key == 'time':
            return
        if isinstance(contents, fieldmodule.FieldBase):
            print(contents)
        else:
            print(key)


    def downloaded(store, slot, data):
        filename = 'download-{}-{}.bin'.format(store, slot)
        print("Saving data to {}".format(filename))
        with open(filename, 'wb') as handle:
            handle.write(data)
        exit(0)


    testmixer.on('change', changed)
    testmixer.on('download-done', downloaded)

    testmixer.connect()
    while True:
        testmixer.loop()
