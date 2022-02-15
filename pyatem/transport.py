import socket
import struct
import logging
import time
from queue import Queue, Empty
import collections
from urllib.parse import urlparse

import usb.core
import usb.util


class Packet:
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
        fields = struct.unpack('>HHH 2x HH', packet[0:12])
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
        result = struct.pack('!HHH 2x HH',
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
        result = struct.pack('<I', data_len)
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


class UdpProtocol:
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
        self.ip = ip
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024 * 16)

        self.local_sequence_number = 0
        self.local_ack_number = 0
        self.remote_sequence_number = 0
        self.remote_ack_numbe = 0

        self.state = UdpProtocol.STATE_CLOSED
        self.session_id = 0x1337

        self.enable_ack = False
        self.had_traffic = False

        self.received_packets = collections.deque(maxlen=128)

    def _send_packet(self, packet):
        packet.session = self.session_id
        if not packet.flags & UdpProtocol.FLAG_ACK:
            packet.sequence_number = (self.local_sequence_number + 1) % 2 ** 16
        raw = packet.to_bytes()
        self.sock.sendto(raw, (self.ip, self.port))
        logging.debug('> {}'.format(packet))
        if packet.debug:
            # hexdump(raw)
            pass
        if packet.flags & (UdpProtocol.FLAG_SYN | UdpProtocol.FLAG_ACK) == 0:
            self.local_sequence_number = (self.local_sequence_number + 1) % 2 ** 16

    def _receive_packet(self):
        try:
            data, address = self.sock.recvfrom(2048)
        except socket.timeout:
            # No longer receiving data from the hardware, reset the state of the connection and re-init
            self.state = UdpProtocol.STATE_CLOSED
            self.connect()
            return
        packet = Packet.from_bytes(data)
        logging.debug('< {}'.format(packet))

        if packet.flags & UdpProtocol.FLAG_REQUEST_RETRANSMISSION:
            pass
            # hexdump(data)

        new_sequence_number = packet.sequence_number
        if new_sequence_number > self.remote_sequence_number + 1:
            pass
        self.remote_sequence_number = new_sequence_number

        if self.session_id is None:
            self.session_id = packet.session

        is_retransmissions = packet.flags & UdpProtocol.FLAG_RETRANSMISSION
        if is_retransmissions:
            if self.remote_sequence_number in self.received_packets:
                return True

        self.received_packets.append(self.remote_sequence_number)

        if packet.flags & UdpProtocol.FLAG_RELIABLE and self.enable_ack:
            # This packet needs an ACK
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

        logging.debug('Got response 0x{:02X} to handshake'.format(response_code))

        if response_code == 0x02:
            self.state = UdpProtocol.STATE_ESTABLISHED

        # Got a valid 2nd handshake packet, send back the third one
        response = Packet()
        response.flags = UdpProtocol.FLAG_ACK
        self._send_packet(response)

        # Clear temporary session id, use the session id received in the first packet from the remote
        self.session_id = None

    def connect(self):
        if self.state != UdpProtocol.STATE_CLOSED:
            raise RuntimeError("Trying to open an connection that's already open")

        # Reset internal state
        self.local_sequence_number = 0
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
                continue

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
                        ack = Packet()
                        ack.flags = UdpProtocol.FLAG_ACK
                        ack.acknowledgement_number = self.remote_sequence_number
                        ack.remote_sequence_number = 0x61
                        ack.label = 'initial ack after connection'
                        self._send_packet(ack)

                    # TODO: Implement other control packets, like request for retransmission
                else:
                    # Data packet for the upper layer
                    return packet

    def send_packet(self, packet):
        self._send_packet(packet)


class UsbProtocol:
    STATE_INIT = 0

    PRODUCTS = {
        0xbe49: "Atem Mini",
        0xbe55: "Atem Mini Pro",
    }

    def __init__(self, port=None):
        port = port or "auto"
        self.port = port
        self.queue = Queue()

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
        for config in self.handle:
            for i in range(config.bNumInterfaces):
                if self.handle.is_kernel_driver_active(i):
                    try:
                        self.handle.detach_kernel_driver(i)
                        logging.debug('kernel driver detached')
                    except usb.core.USBError as e:
                        logging.error('Could not detach kernel driver: ' + str(e))

    def _send_packet(self, packet):
        raw = packet.to_usb()
        self.queue.put(raw)

    def _receive_packet(self):
        try:
            data = self.handle.read(0x82, 8192 * 4, timeout=1100)
        except:
            return None

        raw = bytes(data)
        if len(raw) == 0:
            return None

        chunks = []
        while True:
            length, = struct.unpack('<I', raw[0:4])
            chunks.append(raw[4:length + 4])
            raw = raw[length + 4:]
            if len(raw) == 0:
                break

        packet = Packet()
        packet.data = b''.join(chunks)
        return packet

    def connect(self):
        self.handle.ctrl_transfer(0xa1, 2, 0x0000, 2, 1)
        self.handle.ctrl_transfer(0x21, 0, 0x0000, 2, [])
        self.handle.ctrl_transfer(0xa1, 2, 0x0000, 2, 1)

    def receive_packet(self):
        while True:

            try:
                item = self.queue.get(block=False)
                self.handle.write(0x02, item)
            except Empty as e:
                self.handle.write(0x02, b'')
                time.sleep(0.020)

            packet = self._receive_packet()
            if packet is not None:
                return packet

    def send_packet(self, packet):
        self._send_packet(packet)


class TcpProtocol:
    STATE_INIT = 0
    STATE_AUTH = 1
    STATE_CONNECTED = 2

    def __init__(self, url=None, host=None, port=None, username=None, password=None, device=None):
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

    def _send_packet(self, data):
        header = struct.pack('!H', len(data))
        self.sock.sendall(header + data)

    def _receive_packet(self):
        try:
            header = self.sock.recv(2)
            datalength, = struct.unpack('!H', header)
            data_left = datalength
            data = b''
            while data_left > 0:
                block = self.sock.recv(data_left)
                if len(block) == 0:
                    print("Connection closed")
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
            datalen, cmd = struct.unpack_from('!H2x 4s', data, offset)
            raw = data[offset + 8:offset + datalen]
            yield (cmd, raw)
            offset += datalen

    def list_to_packets(self, data):
        result = b''
        for key, value in data:
            result += struct.pack('!H2x 4s', len(value) + 8, key)
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
