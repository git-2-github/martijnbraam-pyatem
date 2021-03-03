import socket
import struct
import logging


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
