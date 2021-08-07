import socket
import time

from pyatem.debuglog import DebugLog
from pyatem.field import FirmwareVersionField, ProductNameField, MixerEffectConfigField, MediaplayerSlotsField, \
    VideoModeField, InputPropertiesField, InitCompleteField, ManualField
from pyatem.protocol import AtemProtocol
from pyatem.transport import Packet, UdpProtocol

logger_emulator = DebugLog("/workspace/emulator.html")


class AtemClient:
    STATE_CLOSED = 0
    STATE_HANDSHAKE = 1
    STATE_CONNECTED = 2

    def __init__(self, emulator, addr, session):
        self.emulator = emulator
        self.sock = emulator.sock
        self.addr = addr
        self.session = session

        self.state = AtemClient.STATE_CLOSED

        self.local_sequence_number = 0
        self.local_ack_number = 0
        self.remote_sequence_number = 0
        self.remote_ack_number = 0

    def send_packet(self, data, flags=0, session=None, client_packet_id=None):
        packet = Packet()
        packet.emulator = True
        packet.flags = flags
        packet.data = data
        if client_packet_id:
            packet.remote_sequence_number = client_packet_id
        if session:
            packet.session = session
        else:
            packet.session = self.session
        if not packet.flags & UdpProtocol.FLAG_SYN:
            packet.sequence_number = (self.local_sequence_number + 1) % 2 ** 16
        raw = packet.to_bytes()
        print('> {}'.format(packet))
        logger_emulator.add_packet(sending=True, raw=raw)
        self.sock.sendto(raw, self.addr)

        if packet.flags & (UdpProtocol.FLAG_SYN) == 0:
            self.local_sequence_number = (self.local_sequence_number + 1) % 2 ** 16

    def send_fields(self, fields):
        data = b''
        for field in fields:
            data += field.make_packet()

        if len(data) > 1300:
            raise ValueError("Field list too long for UDP packet")

        self.send_packet(data, flags=UdpProtocol.FLAG_RELIABLE)

    def _flatten(self, idict):
        result = []
        for key in idict:
            if isinstance(idict[key], dict):
                result.extend(self._flatten(idict[key]))
            elif isinstance(idict[key], list):
                result.extend(idict[key])
            else:
                result.append(idict[key])
        return result

    def send_initial_state(self):
        # fields = self._flatten(self.emulator.mixerstate)
        fields = self.emulator.mixerstate
        fields.append(InitCompleteField.create())
        buffer = []
        size = 0
        # Flag should be 0x01
        for field in fields:
            if isinstance(field, bytes):
                continue
            fsize = len(field.raw) + 8
            if size + fsize > 1300:
                self.send_fields(buffer)
                buffer = []
                size = 0
            buffer.append(field)
            size += fsize
        self.send_fields(buffer)

        # Flag should be 0x11
        self.send_packet(b'', flags=(UdpProtocol.FLAG_RELIABLE | UdpProtocol.FLAG_ACK))

    def on_packet(self, raw):
        logger_emulator.add_packet(sending=False, raw=raw)
        packet = Packet.from_bytes(raw)
        packet.emulator = True
        print('< {}'.format(packet))
        if self.state == AtemClient.STATE_CLOSED:
            print("Temp session id is {}".format(packet.session))
            self.state = AtemClient.STATE_HANDSHAKE

            raw = b'\x02\0\0\xc2\0\0\0\0'
            # Flag should be 0x02
            self.send_packet(raw, flags=UdpProtocol.FLAG_SYN, session=packet.session, client_packet_id=0xad)
        elif self.state == AtemClient.STATE_HANDSHAKE:
            print("Handshake complete, session is now {}".format(self.session))
            self.state = AtemClient.STATE_CONNECTED
            # Handshake done, start dumping state
            self.send_initial_state()


class AtemEmulator:
    def __init__(self, host=None, port=9910):
        if host is None:
            host = ''
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.clients = {}
        self.mixerstate = {}

    def listen(self):
        self.sock.bind((self.host, self.port))
        while True:
            raw, addr = self.sock.recvfrom(9000)
            if addr not in self.clients:
                self.on_connect(addr)
            self.clients[addr].on_packet(raw)

    def on_connect(self, addr):
        print("New client on {}".format(addr))
        self.clients[addr] = AtemClient(self, addr, len(self.clients) + 0x8100)


if __name__ == '__main__':
    def passthrough_done():
        print("Passthrough initialized")
        testdev.mixerstate = unknown_stuff
        testdev.listen()


    def passthrough_unknown_field(key, raw):
        if not isinstance(raw, bytes):
            unknown_stuff.append(raw)
        else:
            if len(key) > 4:
                print(key)
            unknown_stuff.append(ManualField(key, raw))


    unknown_stuff = []
    testdev = AtemEmulator()
    pt = AtemProtocol(ip='192.168.2.84')
    pt.on('change', passthrough_unknown_field)
    pt.on('connected', passthrough_done)
    pt.connect()
    print("Connecting to passthrough device")
    while True:
        pt.loop()

    testdev.mixerstate = {
        'firmware-version': FirmwareVersionField.create(1, 0),
        'product-name': ProductNameField.create("Emulated mixer"),
        'mixer-effect-config': {
            '0': MixerEffectConfigField.create(0, 4),
            '1': MixerEffectConfigField.create(1, 4),
        },
        'mediaplayer-slots': MediaplayerSlotsField.create(0, 0),
        'video-mode': VideoModeField.create(27),
        'input-properties': {
            '0': InputPropertiesField.create(0, 'Black', 'BLK', 0, 0, 0, 0xff, True, True),
        }
    }
    testdev.listen()
