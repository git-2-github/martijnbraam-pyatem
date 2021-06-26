import socket
import struct
import logging
import time
from queue import Queue, Empty
from threading import Lock

import usb.core
import usb.util
from hexdump import hexdump


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
        hexdump(result)
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

        self.local_sequence_number = 0
        self.local_ack_number = 0
        self.remote_sequence_number = 0
        self.remote_ack_numbe = 0

        self.state = UdpProtocol.STATE_CLOSED
        self.session_id = 0x1337

        self.enable_ack = False

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
        data, address = self.sock.recvfrom(2048)
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
            if self.state == UdpProtocol.STATE_SYN_SENT:
                # Got response for the first handshake packet
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

    def __init__(self, port=None):
        port = port or "auto"
        self.port = port
        self.queue = Queue()

        self.handle = usb.core.find(idVendor=0x1edb, idProduct=0xbe55)
        self._detach_kernel()
        self.handle.set_configuration()

    @classmethod
    def device_exists(cls):
        return usb.core.find(idVendor=0x1edb, idProduct=0xbe55) is not None

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
