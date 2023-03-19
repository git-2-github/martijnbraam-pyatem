# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import logging
import struct

from pyatem.transfer import TransferTask, TransferQueueFlushed
from pyatem.transport import UdpProtocol, Packet, UsbProtocol, TcpProtocol, ConnectionReady
from pyatem.command import LockCommand, TransferDownloadRequestCommand, TransferAckCommand, \
    TransferUploadRequestCommand, TransferDataCommand, TransferFileDataCommand, PartialLockCommand, TimeRequestCommand
from pyatem.media import rle_decode
import pyatem.field as fieldmodule


class AtemProtocol:
    STRUCT_FIELD = struct.Struct('!H2x 4s')

    FIELDNAME_PRETTY = {
        '_ver': 'firmware-version',
        '_pin': 'product-name',
        '_top': 'topology',
        'Time': 'time',
        'TCCc': 'time-config',
        'TcLk': 'timecode-lock',
        '_MeC': 'mixer-effect-config',
        '_MvC': 'multiviewer-config',
        '_FAC': 'fairlight-audio-config',
        '_VMC': 'video-mode-capability',
        'MvVM': 'multiview-video-mode-capability',
        '_MAC': 'macro-config',
        '_DVE': 'dve-capabilities',
        'Powr': 'power-status',
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
        'KACk': 'key-properties-advanced-chroma',
        'KACC': 'key-properties-advanced-chroma-colorpicker',
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
        'MPSp': 'mediaplayer-space',
        'MPCS': 'mediaplayer-clip-source',
        'MPAS': 'mediaplayer-audio-source',
        'RCPS': 'mediaplayer-clip-status',
        'AMMO': 'audio-mixer-master-properties',
        'AMmO': 'audio-mixer-monitor-properties',
        'AMTl': 'audio-mixer-tally',
        'FASP': 'fairlight-strip-properties',
        'FAMP': 'fairlight-master-properties',
        'FMPP': 'fairlight-properties',
        'FMHP': 'fairlight-headphones',
        'FAMS': 'fairlight-solo',
        'AIXP': 'fairlight-expander-properties',
        'AICP': 'fairlight-compressor-properties',
        'AILP': 'fairlight-limiter-properties',
        'MOCP': 'fairlight-master-compressor-properties',
        'AMLP': 'fairlight-master-limiter-properties',
        'ATMP': 'talkback-mixer-properties',
        'TMIP': 'talkback-mixer-input-properties',
        'MMOP': 'mix-minus-output-properties',
        '_TlC': 'tally-config',
        'TlIn': 'tally-index',
        'TlSr': 'tally-source',
        'FMTl': 'fairlight-tally',
        'MPrp': 'macro-properties',
        'MRPr': 'macro-play-status',
        'MRcS': 'macro-record-status',
        'CCst': 'camera-control-settings',
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
        'AMBP': 'atem-master-eq-band-properties',
        'MvPr': 'multiviewer-properties',
        'MvIn': 'multiviewer-input',
        'VuMC': 'multiviewer-vu',
        'VuMo': 'multiviewer-vu-opacity',
        'SaMw': 'multiviewer-safe-area',
        'LKOB': 'lock-obtained',
        'FTDa': 'file-transfer-data',
        'LKST': 'lock-state',
        'FTDE': 'file-transfer-error',
        'FTDC': 'file-transfer-data-complete',
        'FTCD': 'file-transfer-continue-data',
        'AMLv': 'audio-meter-levels',
        'FMLv': 'fairlight-meter-levels',
        'FDLv': 'fairlight-master-levels',
        'CCdP': 'camera-control-data-packet',
        '*XFC': 'transfer-complete',
        '_SSC': 'supersource-config',
        'SSrc': 'supersource-properties',
        'SSBP': 'supersource-box-properties',
        'V3sl': 'sdi-3g-level',
        'RXMS': 'hyperdeck-settings',
        'RXCP': 'hyperdeck-status',
        'RXSS': 'hyperdeck-storage',
        'RXCC': 'hyperdeck-clip-count',
        'DCPV': 'displayclock-properties',
        'DSTV': 'displayclock-set-time',
    }

    FIELDNAME_UNIQUE = {
        'mixer-effect-config': struct.Struct('>B'),
        'input-properties': struct.Struct('>H'),
        'program-bus-input': struct.Struct('>B'),
        'preview-bus-input': struct.Struct('>B'),
        'transition-preview': struct.Struct('>B'),
        'transition-position': struct.Struct('>B'),
        'transition-mix': struct.Struct('>B'),
        'transition-dip': struct.Struct('>B'),
        'transition-wipe': struct.Struct('>B'),
        'transition-dve': struct.Struct('>B'),
        'transition-stinger': struct.Struct('>B'),
        'fairlight-strip-properties': struct.Struct('>H'),
        'macro-properties': struct.Struct('>H'),
        'fairlight-audio-input': struct.Struct('>H'),
        'audio-input': struct.Struct('>H'),
        'key-on-air': struct.Struct('>BB'),
        'key-properties-base': struct.Struct('>BB'),
        'key-properties-luma': struct.Struct('>BB'),
        'key-properties-pattern': struct.Struct('>BB'),
        'key-properties-dve': struct.Struct('>BB'),
        'key-properties-fly': struct.Struct('>BB'),
        'key-properties-fly-keyframe': struct.Struct('>BBB'),
        'dkey-properties-base': struct.Struct('>B'),
        'dkey-properties': struct.Struct('>B'),
        'dkey-state': struct.Struct('>B'),
        'fade-to-black': struct.Struct('>B'),
        'fade-to-black-state': struct.Struct('>B'),
        'color-generator': struct.Struct('>B'),
        'aux-output-source': struct.Struct('>B'),
        'mediaplayer-file-info': struct.Struct('>xxH'),
        'mediaplayer-selected': struct.Struct('>B'),
        'atem-eq-band-properties': struct.Struct('>H14xB'),
        'multiviewer-properties': struct.Struct('>B'),
        'multiviewer-input': struct.Struct('>BB'),
        'multiviewer-vu': struct.Struct('>BB'),
        'multiviewer-safe-area': struct.Struct('>BB'),
        'camera-control-data-packet': struct.Struct('>BBB'),
    }

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

        self.log = logging.getLogger('AtemProtocol')
        self.transport.queue_callback = self.queue_callback
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
        self.transfer = None
        self.transfer_requested = False
        self.transfer_packets = 0
        self.transfer_budget = []

    @classmethod
    def usb_exists(cls):
        return UsbProtocol.device_exists()

    def connect(self):
        self.log.debug('Starting connection')
        self.transport.connect()

    def loop(self):
        self.log.debug('Waiting for data packet...')
        packet = self.transport.receive_packet()
        if packet is None:
            # Disconnected from hardware
            if self.connected:
                self._raise('disconnected')
                self.mixerstate = {}
            self.connected = False
            return
        if isinstance(packet, ConnectionReady):
            self.connected = True
            self.send_commands([TimeRequestCommand()])
            self._raise('connected')
            return
        self.connected = True
        if isinstance(packet, TransferQueueFlushed):
            self._queue_flushed()
            return
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

    def get_link_quality(self):
        return self.transport.get_link_quality()

    def _raise(self, event, *args, **kwargs):
        if event in self.callbacks:
            for cbidx in self.callbacks[event]:
                self.callbacks[event][cbidx](*args, **kwargs)

    def decode_packet(self, data):
        offset = 0
        while offset < len(data):
            datalen, cmd = self.STRUCT_FIELD.unpack_from(data, offset)

            # A zero length header is not possible, this occurs when the transport layer has corruption, mark the
            # connection closed to restart and recover state
            if datalen == 0:
                raise ConnectionError()

            raw = data[offset + 8:offset + datalen]
            yield (cmd, raw)
            offset += datalen

    def save_field_data(self, fieldname, contents):
        raw = contents
        key = fieldname.decode()
        if key in self.FIELDNAME_PRETTY:
            key = self.FIELDNAME_PRETTY[key]
            classname = key.title().replace('-', '') + "Field"
            if hasattr(fieldmodule, classname):
                contents = getattr(fieldmodule, classname)(contents)

        if key == 'CapA':
            return

        if key == 'lock-obtained':
            self.log.info('Got lock for {}'.format(contents.store))
            self.locks[contents.store] = True
            self._transfer_trigger(contents.store)
            return
        elif key == 'lock-state':
            if contents.state:
                # Ignore lock aquired messages from other clients
                return
            if contents.store in self.locks and self.locks[contents.store]:
                # Remove the lock if we held it
                del self.locks[contents.store]
            self.log.debug(contents)
            return
        elif key == 'file-transfer-continue-data':
            self.transfer_budget = contents
            old = self.transfer_budget.size
            self.transfer_budget.size = self.transfer_budget.size // 8 * 8
            if old != self.transfer_budget.size:
                self.log.debug(f"Adjusted transfer chunk size from {old} to {self.transfer_budget.size}")
            self._queue_chunks()
            return
        elif key == 'file-transfer-data':
            if contents.transfer == self.transfer.tid:
                self.transfer_packets += 1
                self.transfer_buffer += contents.data
                if self.transfer_packets % 20 == 0:
                    total_size = self.mixerstate['video-mode'].get_pixels() * 4
                    transfer_progress = len(self.transfer_buffer) / total_size
                    self._raise('transfer-progress', self.transfer.store, self.transfer.slot, transfer_progress)
                # The 0 should be the transfer slot, but it seems it's always 0 in practice
                self.send_commands([TransferAckCommand(self.transfer.tid, 0)])
            else:
                self.log.error('Got file transfer data for wrong transfer id')
            return
        elif key == 'file-transfer-error':
            self.log.error(f"file-transfer-error: {str(contents)}")
            self.transfer_requested = False
            if contents.status == 1:
                # Status is try-again
                self.log.debug('Retrying transfer')
                self._transfer_trigger(self.transfer.store, retry=True)
            elif contents.status == 5:
                self.locks[self.transfer.store] = False
                self._transfer_trigger(self.transfer.store, retry=True)
            return
        elif key == 'file-transfer-data-complete':
            self.log.debug('Transfer complete')
            if self.transfer is None:
                self.log.warning("Got FTDC without transfer active")
                return
            if contents.transfer != self.transfer.tid:
                return
            # Remove current item from the transfer queue
            queue = self.transfer_queue[self.transfer.store]
            self.transfer_queue[self.transfer.store] = queue[1:]

            if self.transfer.upload:
                self._raise('upload-done', self.transfer.store, self.transfer.slot)
                self.transfer_requested = False
            else:
                # Assemble the buffer
                data = self.transfer_buffer
                self.transfer_buffer = b''
                self.transfer_requested = False

                # Decompress the buffer if needed
                if self.transfer.store == 0:
                    data = rle_decode(data)

                self._raise('download-done', self.transfer.store, self.transfer.slot, data)

            # Start next transfer in the queue
            self._transfer_trigger(self.transfer.store)
            return
        elif key == 'transfer-complete':
            self.log.debug('Proxy transfer complete')

            # Remove current item from the transfer queue
            queue = self.transfer_queue[contents.store]
            self.transfer_queue[contents.store] = queue[1:]

            if contents.upload:
                self._raise('upload-done', contents.store, contents.slot)
            else:
                # TODO: Implement proxy download
                pass
            # Start next transfer in the queue
            self._transfer_trigger(self.transfer.store)
            return

        if key in self.FIELDNAME_UNIQUE:
            idxes = self.FIELDNAME_UNIQUE[key].unpack_from(raw, 0)
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
            self.transport.mark_next_connected = True
            if isinstance(self.transport, TcpProtocol):
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

    def queue_callback(self, remaining, size):
        if not self.transfer:
            return

        self.transfer.send_done += size
        fraction = self.transfer.send_done / self.transfer.send_length
        self._raise('upload-progress', self.transfer.store, self.transfer.slot, fraction * 100, self.transfer.send_done,
                    self.transfer.send_length)

    def download(self, store, index):
        self.log.info("Queue download of {}:{}".format(store, index))
        if store not in self.transfer_queue:
            self.transfer_queue[store] = []
        self.transfer_queue[store].append(TransferTask(store, index))
        self._transfer_trigger(store)

    def upload(self, store, index, data, compress=True, compressed=False, name=None, description=None, size=None,
               task=None):
        self.log.info("Queue upload of {}:{}".format(store, index))
        if store not in self.transfer_queue:
            self.transfer_queue[store] = []

        if task is None:
            task = TransferTask(store, index, upload=True)
            task.data = data
            task.send_length = len(data)
            task.name = name
            task.description = description
            if compressed:
                uncompressed = rle_decode(data)
                task.data = uncompressed
                task.calculate_hash()
                task.data = data
            else:
                task.calculate_hash()
            if compress:
                task.compress()
            elif compressed:
                task.data_length = len(rle_decode(data))

        self.log.info(f'New upload task is {len(task.data)} bytes, {task.data_length} uncompressed')

        if isinstance(self.transport, TcpProtocol):
            self.transport.upload(task)
        else:
            self.transfer_queue[store].append(task)
            self._transfer_trigger(store)

    def _queue_chunks(self):
        # Can't transfer without a chunk size
        if self.transfer_budget is None:
            self.log.error('Cannot transfer without chunk size')
            return

        # Only queue chunks if an upload is planned
        if self.transfer is None:
            self.log.error('No transfer scheduled')
            return

        if not self.transfer.upload:
            self.log.error('Current transfer is a download')
            return

        chunk_size = self.transfer_budget.size
        self.log.debug(f'Queue {self.transfer_budget.count} chunks of {chunk_size}')
        for i in range(0, self.transfer_budget.count):
            if len(self.transfer.data) == 0:
                break

            chunk = self.transfer.data[0:chunk_size]
            used = chunk_size
            if chunk[-8:] == b'\xFE\xFE\xFE\xFE\xFE\xFE\xFE\xFE':
                chunk = self.transfer.data[0:chunk_size - 8]
                used -= 8
            elif chunk[-16:-8] == b'\xFE\xFE\xFE\xFE\xFE\xFE\xFE\xFE':
                chunk = self.transfer.data[0:chunk_size - 16]
                used -= 16
            self.transfer.data = self.transfer.data[used:]

            self.transfer_budget.count -= 1
            if self.transfer_budget.count == 0:
                self.log.debug('Transfer budget ran out')
                self.transfer_budget = None

            cmd = TransferDataCommand(self.transfer.tid, chunk)
            packet = Packet()
            packet.flags = UdpProtocol.FLAG_RELIABLE
            packet.data = cmd.get_command()
            self.transport.queue_packet(packet)
        self.transport.queue_trigger()

    def _queue_flushed(self):
        self.log.info('Queue flushed')
        if len(self.transfer.data):
            self._queue_chunks()
            return
        self.log.info('Sending file metadata')
        cmd = TransferFileDataCommand(self.transfer.tid, self.transfer.hash,
                                      name=self.transfer.name, description=self.transfer.description)
        self.send_commands([cmd])

    def _transfer_trigger(self, store, retry=False):
        next = None

        self.log.info(f'transfer trigger for store {store} (retry={retry})')

        # Try the preferred queue
        if store in self.transfer_queue:
            if len(self.transfer_queue[store]) > 0:
                next = self.transfer_queue[store][0]

        # Try any queue
        if next is None:
            for store in self.transfer_queue:
                if len(self.transfer_queue[store]) > 0:
                    next = self.transfer_queue[store][0]
                    break

        self.log.info(f'next transfer: {next}')

        # All transfers done, clean locks
        if next is None:
            for lock in self.locks:
                if self.locks[lock]:
                    self.log.info('Releasing lock {}'.format(lock))
                    cmd = LockCommand(lock, False)
                    self.send_commands([cmd])
            return

        # Request a lock if needed
        if next.store != 0xffff and (next.store not in self.locks or not self.locks[next.store]):
            self.log.info('Requesting lock for {}'.format(next.store))
            cmd = PartialLockCommand(next.store, next.slot)
            self.send_commands([cmd])
            return

        # A transfer request is already running, don't start a new one
        if self.transfer_requested:
            self.log.info('Request already submitted, do nothing')
            return

        # Assign a transfer id and start the transfer
        if not retry:
            self.transfer_id += 1
        self.transfer = next
        self.transfer.tid = self.transfer_id

        if self.transfer.upload:
            cmd = TransferUploadRequestCommand(self.transfer.tid, self.transfer.store, self.transfer.slot,
                                               self.transfer.data_length, 1)
            self.log.info('Requesting upload to {}:{}'.format(next.store, next.slot))
        else:
            cmd = TransferDownloadRequestCommand(self.transfer.tid, self.transfer.store, self.transfer.slot)
            self.log.info('Requesting download of {}:{}'.format(next.store, next.slot))
        self.transfer_requested = True
        self.send_commands([cmd])
