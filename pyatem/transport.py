# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import select
import socket
import struct
import logging
import time
from queue import Queue, Empty
import collections
from urllib.parse import urlparse
import threading

import usb.core
import usb.util

from pyatem.socketqueue import SocketQueue
from pyatem.transfer import TransferQueueFlushed, TransferTask


class ConnectionReady:
    def __init__(self):
        pass


class Packet:
    STRUCT_HEADER = struct.Struct('>HHH 2x HH')
    STRUCT_USB = struct.Struct('<I')

    def __init__(self):
        self.flags = 0
        self.length = 0
        self.session = 0
        self.sequence_number = 0
        self.acknowledgement_number = 0
        self.remote_sequence_number = 0
        self.data = None
        self.debug = False
        self.original = None
        self.label = None
        self.last_packet_time = None

    @classmethod
    def from_bytes(cls, packet):
        res = cls()
        res.original = packet
        fields = cls.STRUCT_HEADER.unpack_from(packet)
        res.length = fields[0] & ~(0x1f << 11)
        res.flags = (fields[0] & (0x1f << 11)) >> 11

        if res.length != len(packet):
            raise ValueError(
                "Incomplete or corrupt packet received, {} in header but data length is {}".format(
                    res.length, len(packet)))

        res.session = fields[1]
        res.acknowledgement_number = fields[2]
        res.remote_sequence_number = fields[3]
        res.sequence_number = fields[4]
        res.data = packet[12:]
        return res

    def to_bytes(self):
        header_len = 12
        data_len = len(self.data) if self.data is not None else 0
        packet_len = header_len + data_len
        result = self.STRUCT_HEADER.pack(
            packet_len + (self.flags << 11),
            self.session,
            self.acknowledgement_number,
            self.remote_sequence_number,
            self.sequence_number)

        if self.data:
            result += bytes(self.data)

        return result

    def to_usb(self):
        data_len = len(self.data) if self.data is not None else 0
        result = self.STRUCT_USB.pack(data_len)
        if self.data:
            result += bytes(self.data)
        return result

    def __repr__(self):
        flags = ''
        extra = ''
        if self.flags & UdpProtocol.FLAG_RELIABLE:
            flags += ' RELIABLE'
        if self.flags & UdpProtocol.FLAG_SYN:
            flags += ' SYN'
        if self.flags & UdpProtocol.FLAG_RETRANSMISSION:
            flags += ' RETRANSMISSION'
        if self.flags & UdpProtocol.FLAG_REQUEST_RETRANSMISSION:
            flags += ' REQ-RETRANSMISSION'
            extra = ' req={}'.format(self.remote_sequence_number)
        if self.flags & UdpProtocol.FLAG_ACK:
            flags += ' ACK'
            extra = ' ack={}'.format(self.acknowledgement_number)
        flags = flags.strip()
        data_len = len(self.data) if self.data is not None else 0
        label = ''
        if self.label:
            label = ' ' + self.label
        return '<Packet flags={} data={} sequence={}{}{}>'.format(flags, data_len, self.sequence_number, extra, label)

    def get_flags(self):
        flags = [hex(self.flags), len(self.data)]
        if self.flags & 0x01:
            flags.append('AckRequest')
        if self.flags & 0x02:
            flags.append('Hello')
        if self.flags & 0x04:
            flags.append('Resend')
        if self.flags & 0x08:
            flags.append('Undefined')
        if self.flags & 0x10:
            flags.append('Ack')
        return flags


class BaseProtocol:
    def __init__(self):
        self.send_queue = collections.deque(maxlen=1024)
        self.queue_enabled = False
        self.queue_callback = None
        self.mark_next_connected = False
        self.batch_size = 1
        self.batch_delay = 0

    def _send_packet(self, packet):
        raise NotImplementedError()

    def queue_packet(self, packet):
        self.send_queue.append(packet)

    def queue_trigger(self):
        if len(self.send_queue) > 0:
            self.queue_enabled = True
            for i in range(0, min(len(self.send_queue), self.batch_size)):
                p = self.send_queue.popleft()
                self._send_packet(p)
                if self.queue_callback is not None:
                    self.queue_callback(len(self.send_queue), len(p.data) - 4)
            time.sleep(self.batch_delay)
        elif self.queue_enabled:
            self.queue_enabled = False
            return True
        return False

    def get_link_quality(self):
        return 100


class UdpProtocol(BaseProtocol):
    STATE_CLOSED = 0
    STATE_SYN_SENT = 1
    STATE_SYN_RECEIVED = 2
    STATE_ESTABLISHED = 3

    FLAG_RELIABLE = 1
    FLAG_SYN = 2
    FLAG_RETRANSMISSION = 4
    FLAG_REQUEST_RETRANSMISSION = 8
    FLAG_ACK = 16

    def __init__(self, ip, port=9910):
        super().__init__()
        self.ip = ip
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024 * 16)

        self.thread = threading.Thread(None, self._udp_thread, "atem-udp", daemon=True)

        self.local_sequence_number = 0
        self.local_ack_number = 0
        self.remote_sequence_number = 0
        self.remote_ack_numbe = 0

        self.state = UdpProtocol.STATE_CLOSED
        self.session_id = 0x1337

        self.enable_ack = False
        self.had_traffic = False

        self.received_packets = collections.deque(maxlen=1024)
        self.retransmission_buffer = {}

        self.thread_queue = SocketQueue()
        self.thread_recv_queue = Queue()

        self.batch_size = 5
        self.batch_delay = 0.003

        self.log = logging.getLogger('UdpTransport')
        self.packet_sucess = 0
        self.packet_errors = 0

    def _udp_thread(self):
        while True:
            readable, _, _ = select.select([self.sock, self.thread_queue], [], [])
            for queue in readable:
                if queue is self.sock:
                    packet = self._receive_packet_low()
                    if packet is not None:
                        self.thread_recv_queue.put(packet)
                elif queue is self.thread_queue:
                    try:
                        self._send_packet_low(queue.get())
                    except OSError as e:
                        self.log.error(e)
                        # Queue a None to signal the socket died
                        self.thread_recv_queue.put(None)
                        return
                else:
                    self.thread_recv_queue.put(None)
                    RuntimeError("Unexpected result from select()")

    def get_link_quality(self):
        return 100 - (self.packet_errors / self.packet_sucess * 100)

    def _send_packet(self, packet):
        self.thread_queue.put(packet)
        self.packet_sucess += 1

    def _send_packet_low(self, packet):
        packet.session = self.session_id
        if not packet.flags & UdpProtocol.FLAG_ACK:
            if self.local_sequence_number == -1:
                self.local_sequence_number = 0
            packet.sequence_number = (self.local_sequence_number + 1) % 2 ** 16
        raw = packet.to_bytes()
        self.sock.sendto(raw, (self.ip, self.port))
        self.log.debug('> {}'.format(packet))
        if packet.debug:
            # hexdump(raw)
            pass
        if packet.flags & (UdpProtocol.FLAG_SYN | UdpProtocol.FLAG_ACK) == 0:
            self.local_sequence_number = (self.local_sequence_number + 1) % 2 ** 16
        self.retransmission_buffer[self.local_sequence_number] = packet

        if packet.label == "_handshake":
            # Clear temporary session id, use the session id received in the first packet from the remote
            self.session_id = None

    def _receive_packet(self):
        return self.thread_recv_queue.get()

    def _receive_packet_low(self):
        try:
            data, address = self.sock.recvfrom(2048)
        except socket.timeout:
            # No longer receiving data from the hardware, reset the state of the connection and re-init
            self.state = UdpProtocol.STATE_CLOSED
            self.connect()
            return
        packet = Packet.from_bytes(data)

        if packet.flags & UdpProtocol.FLAG_RETRANSMISSION:
            if len(data) > 12:
                self.log.error("retransmission detected")
                self.packet_errors += 1
                if self.get_link_quality() < 80:
                    self.log.error(f"Connection quality bad ({self.get_link_quality():.1f}%)")
            else:
                self.log.warning("retransmission of PING detected, non-fatal")
        else:
            self.packet_sucess += 1

        if packet.flags & UdpProtocol.FLAG_REQUEST_RETRANSMISSION:
            self.log.error("retransmission requested")
            self.packet_errors += 1
            # hexdump(data)

        new_sequence_number = packet.sequence_number
        self.remote_sequence_number = new_sequence_number

        if self.session_id is None:
            self.session_id = packet.session

        is_retransmissions = packet.flags & UdpProtocol.FLAG_RETRANSMISSION
        if is_retransmissions:
            if self.remote_sequence_number in self.received_packets:
                return True

        self.received_packets.append(self.remote_sequence_number)

        if (packet.flags & UdpProtocol.FLAG_RELIABLE and self.enable_ack) or \
                (not self.enable_ack and UdpProtocol.FLAG_ACK and len(packet.data) == 0):
            self.enable_ack = True
            # ACK this
            ack = Packet()
            ack.flags = UdpProtocol.FLAG_ACK
            ack.acknowledgement_number = self.remote_sequence_number
            ack.remote_sequence_number = 0x61
            self._send_packet(ack)

        return packet

    def _handshake(self, packet):
        if not packet.flags & UdpProtocol.FLAG_SYN:
            return

        if not packet.session == self.session_id:
            return

        response_code = packet.data[0]

        self.log.debug('Got response 0x{:02X} to handshake'.format(response_code))

        if response_code == 0x02:
            self.state = UdpProtocol.STATE_ESTABLISHED

        # Got a valid 2nd handshake packet, send back the third one
        response = Packet()
        response.flags = UdpProtocol.FLAG_ACK
        response.label = "_handshake"
        self._send_packet(response)

    def connect(self):
        if self.state != UdpProtocol.STATE_CLOSED:
            raise RuntimeError("Trying to open an connection that's already open")

        if not self.thread.is_alive():
            self.thread.start()

        # Reset internal state
        self.local_sequence_number = -1
        self.local_ack_number = 0
        self.remote_sequence_number = 0
        self.remote_ack_numbe = 0
        self.session_id = 0x1337
        self.enable_ack = False

        # Create first syn packet
        syn = Packet()
        syn.flags = UdpProtocol.FLAG_SYN
        syn.data = [
            0x01, 0x00,
            0x00, 0x00,
            0x00, 0x00,
            0x00, 0x00,
        ]
        self._send_packet(syn)
        self.state = UdpProtocol.STATE_SYN_SENT

    def receive_packet(self):
        while True:
            packet = self._receive_packet()

            if packet is True:
                continue
            if packet is None and not self.had_traffic:
                continue
            if packet is None and self.state == UdpProtocol.STATE_SYN_SENT:
                # No response in connect, retry connection
                self.state = UdpProtocol.STATE_CLOSED
                self.had_traffic = False
                self.connect()
                return None

            if packet is None:
                # When None is in the receive queue the socket has disconnected
                return None

            if self.mark_next_connected:
                self.mark_next_connected = False
                return ConnectionReady()

            if self.enable_ack and self.queue_trigger():
                return TransferQueueFlushed()

            if self.state == UdpProtocol.STATE_SYN_SENT:
                # Got response for the first handshake packet
                self.had_traffic = True
                self._handshake(packet)
            elif self.state == UdpProtocol.STATE_ESTABLISHED:
                if packet.length == 12:
                    # This is a control packet, deal with it in the transport layer
                    if not self.enable_ack:
                        # This is the first ACK from the mixer, after this we should send ACKs bac
                        self.enable_ack = True
                        # self.local_sequence_number = 0
                        ack = Packet()
                        ack.flags = UdpProtocol.FLAG_ACK
                        ack.acknowledgement_number = self.remote_sequence_number
                        ack.remote_sequence_number = 0x61
                        ack.label = 'initial ack after connection'
                        self._send_packet(ack)
                    # TODO: Implement other control packets, like request for retransmission

                    # Send queued up bulk traffic after the ack
                    if self.queue_trigger():
                        return TransferQueueFlushed()
                else:
                    # Data packet for the upper layer
                    return packet

    def send_packet(self, packet):
        self._send_packet(packet)


class UsbProtocol(BaseProtocol):
    STATE_INIT = 0

    PRODUCTS = {
        0xbe49: "Atem Mini",
        0xbe55: "Atem Mini Pro",
        0xbe7c: "Atem Mini Extreme",
    }

    def __init__(self, port=None):
        super().__init__()
        port = port or "auto"
        self.port = port
        self.queue = Queue()

        self.log = logging.getLogger('USBTransport')

        self.handle = UsbProtocol.find_device()
        self._detach_kernel()
        self.handle.set_configuration()

    @classmethod
    def device_exists(cls):
        return cls.find_device() is not None

    @classmethod
    def find_device(cls):
        for prod in UsbProtocol.PRODUCTS.keys():
            device = usb.core.find(idVendor=0x1edb, idProduct=prod)
            if device is not None:
                return device
        return None

    def _detach_kernel(self):
        try:
            for config in self.handle:
                for i in range(config.bNumInterfaces):
                    if self.handle.is_kernel_driver_active(i):
                        try:
                            self.handle.detach_kernel_driver(i)
                            self.log.debug('kernel driver detached')
                        except usb.core.USBError as e:
                            self.log.error('Could not detach kernel driver: ' + str(e))
        except usb.core.USBError as e:
            if e.errno == 13:
                raise PermissionError(e)


    def _send_packet(self, packet):
        raw = packet.to_usb()
        self.queue.put(raw)

    def _receive_packet(self):
        try:
            # Lower the timeout when doing an bulk upload to not wait a second between packets
            t = 1 if self.queue_enabled else 1100
            data = self.handle.read(0x82, 8192 * 4, timeout=t)
        except:
            if self.queue_trigger():
                return TransferQueueFlushed()
            return None

        raw = bytes(data)
        if len(raw) == 0:
            # Send queued up bulk traffic after the ack
            if self.queue_trigger():
                return TransferQueueFlushed()

            return None

        chunks = []
        while True:
            length, = Packet.STRUCT_USB.unpack_from(raw)
            chunks.append(raw[4:length + 4])
            raw = raw[length + 4:]
            if len(raw) == 0:
                break

        packet = Packet()
        packet.data = b''.join(chunks)
        return packet

    def connect(self):
        self.handle.ctrl_transfer(0x21, 0, 0x0000, 2, [])

    def receive_packet(self):
        while True:

            try:
                item = self.queue.get(block=False)
                self.handle.write(0x02, item)
            except Empty as e:
                self.handle.write(0x02, b'')
                time.sleep(0.020)

            if self.mark_next_connected:
                self.mark_next_connected = False
                return ConnectionReady()

            packet = self._receive_packet()
            if packet is not None:
                return packet

    def send_packet(self, packet):
        self._send_packet(packet)


class TcpProtocol(BaseProtocol):
    STATE_INIT = 0
    STATE_AUTH = 1
    STATE_CONNECTED = 2

    STRUCT_HEADER = struct.Struct('!H')
    STRUCT_FIELD = struct.Struct('!H2x 4s')

    def __init__(self, url=None, host=None, port=None, username=None, password=None, device=None):
        super().__init__()
        if url is not None:
            part = urlparse(url)
            host = part.hostname
            port = part.port or 4532
            username = part.username
            password = part.password
            device = part.path[1:]
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.device = device

        self.sock = None
        self.state = TcpProtocol.STATE_INIT

        self.log = logging.getLogger('TcpTransport')

    def _send_packet(self, data):
        header = self.STRUCT_HEADER.pack(len(data))
        self.sock.sendall(header + data)

    def _receive_packet(self):
        try:
            header = self.sock.recv(2)
            datalength, = self.STRUCT_HEADER.unpack(header)
            data_left = datalength
            data = b''
            while data_left > 0:
                block = self.sock.recv(data_left)
                if len(block) == 0:
                    self.log.error("Connection closed")
                    return
                data_left -= len(block)
                data += block
        except:
            return None

        packet = Packet()
        packet.data = data
        return packet

    def decode_packet(self, data):
        offset = 0
        if len(data) < 8:
            raise ValueError("Packet too short")
        while offset < len(data):
            datalen, cmd = self.STRUCT_FIELD.unpack_from(data, offset)
            raw = data[offset + 8:offset + datalen]
            yield (cmd, raw)
            offset += datalen

    def list_to_packets(self, data):
        result = b''
        for key, value in data:
            result += self.STRUCT_FIELD.pack(len(value) + 8, key)
            result += value
        return result

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

        # Send magic packet to init the connection
        self._send_packet(self.list_to_packets([(b'*SW*', b'')]))

    def send_auth(self):
        if self.username is None or self.password is None:
            raise ValueError("Proxy requests AUTH but username or password is not set")
        self._send_packet(self.list_to_packets([
            (b'*USR', self.username.encode()),
            (b'*PWD', self.password.encode()),
        ]))

    def connect_device(self):
        self._send_packet(self.list_to_packets([
            (b'*DEV', self.device.encode()),
        ]))

    def receive_packet(self):
        while True:
            packet = self._receive_packet()
            if packet is None:
                continue
            if self.state == TcpProtocol.STATE_INIT:
                fields = list(self.decode_packet(packet.data))
                if fields[0][0] == b'AUTH':
                    self.send_auth()
                    continue
                elif fields[0][0] == b'*HW*':
                    self.connect_device()
                    self.state = TcpProtocol.STATE_CONNECTED
            elif self.state == TcpProtocol.STATE_CONNECTED:
                if packet is not None:
                    return packet

    def send_packet(self, packet):
        self._send_packet(packet.data)

    def upload(self, task):
        if not isinstance(task, TransferTask):
            raise ValueError()
        for packet in task.to_tcp():
            self._send_packet(self.list_to_packets([packet]))

    def download(self, task):
        pass
