import hmac
import struct
import threading
import logging
import socketserver
from functools import partial


class TCPHandler(socketserver.BaseRequestHandler):
    def __init__(self, config, threadpool, *args, **kwargs):
        self.config = config
        self.threadpool = threadpool
        self.device = None
        self.callback_id = None
        super().__init__(*args, **kwargs)

    def setup(self):
        if not hasattr(self.server, 'numclients'):
            self.server.numclients = 0
        self.server.numclients += 1

    def decode_packet(self, data):
        offset = 0
        if len(data) < 8:
            raise ValueError("Packet too short")
        while offset < len(data):
            datalen, cmd = struct.unpack_from('!H2x 4s', data, offset)
            if datalen > 8 + 32:
                raise ValueError("Received large packet")
            raw = data[offset + 8:offset + datalen]
            yield (cmd, raw)
            offset += datalen

    def list_to_packets(self, data):
        result = b''
        for key, value in data:
            result += struct.pack('!H2x 4s', len(value) + 8, key)
            result += value
        return result

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

    def send_packets(self, data):
        data = self.list_to_packets(data)
        self.send_raw(data)

    def send_raw(self, data):
        header = struct.pack('!H', len(data))
        self.request.sendall(header + data)

    def send_fields(self, fields):
        data = b''
        for field in fields:
            data += field.make_packet()
        header = struct.pack('!H', len(data))
        self.request.sendall(header + data)

    def send_initial_sync(self):
        mixerstate = self.threadpool['hardware'][self.device].switcher.mixerstate
        state = self._flatten(mixerstate)

        buffer = []
        size = 0
        for field in state:
            if isinstance(field, bytes):
                continue
            fsize = len(field.raw) + 8
            if size + fsize > 1000:
                self.send_fields(buffer)
                buffer = []
                size = 0
            buffer.append(field)
            size += fsize
        self.send_fields(buffer)

    def receive(self):
        header = self.request.recv(2)
        if len(header) == 0:
            raise ValueError("Client disconnected")
        datalength, = struct.unpack('!H', header)
        return self.request.recv(datalength)

    def handle(self):
        # Rename thread
        t = threading.currentThread()
        t.setName('tcp.{}:{}'.format(self.client_address[0], self.client_address[1]))

        try:
            # Handshake magic packet
            handshake = self.receive()
            packets = list(self.decode_packet(handshake))
            if len(packets) > 1:
                logging.warning('Too many packets in handshake, rejecting')
                return

            if packets[0][0] != b'*SW*':
                logging.warning('Invalid magic on new connection, rejecting')
                return

            # Optionally run the auth
            if self.config['auth']:
                self.send_packets([(b'AUTH', b'')])
                raw = self.receive()
                packets = list(self.decode_packet(raw))
                fields = {}
                for packet in packets:
                    fields[packet[0]] = packet[1]
                username = fields[b'*USR'].decode()
                password = fields[b'*PWD'].decode()
                user_ok = hmac.compare_digest(self.config['username'], username)
                pass_ok = hmac.compare_digest(self.config['password'], password)
                if not user_ok or not pass_ok:
                    logging.warning("Invalid login information supplied, rejecting")
                    return

            # Send device list to client
            logging.info('Client connected')
            hardware = []
            for key in self.config['hardware'].split(','):
                label = self.threadpool['hardware'][key].config['label']
                hardware.append((b'*HW*', struct.pack('>20s20s', key.encode(), label.encode())))
            self.send_packets(hardware)

            # Device selection
            raw = self.receive()
            packets = list(self.decode_packet(raw))
            if packets[0][0] != b'*DEV':
                logging.error('Expected *DEV response, rejecting')
                return
            self.device = packets[0][1].decode()
            logging.info('selected device ' + str(self.device))

            # Initial sync
            self.send_initial_sync()

            # Register events
            self.callback_id = self.threadpool['hardware'][self.device].switcher.on('change', self.proxy_change)

            # Proxying
            while True:
                packet = self.receive()
                self.threadpool['hardware'][self.device].switcher.send_raw(packet)


        except ValueError as e:
            logging.error("Protocol error: " + str(e))
            return

    def finish(self):
        if self.callback_id is not None:
            self.threadpool['hardware'][self.device].switcher.off('change', self.callback_id)
        self.server.numclients -= 1

    def proxy_change(self, key, val):
        if isinstance(val, bytes):
            pass
            # Don't send packets we can't decode yet
            # self.send_raw(val)
        else:
            self.send_raw(val.make_packet())


class TcpFrontendThread(threading.Thread):
    def __init__(self, config, threadlist):
        threading.Thread.__init__(self)
        self.name = 'tcp.' + str(config['bind'])
        self.config = config
        self.threadlist = threadlist
        self.stop = False
        self.server = None

    def run(self):
        logging.info('TCP frontend run')
        host, port = self.config['bind'].split(':')
        address = (host, int(port))
        logging.info(f'binding to {address}')

        socketserver.TCPServer.allow_reuse_address = True
        handler = partial(TCPHandler, self.config, self.threadlist)
        self.server = socketserver.ThreadingTCPServer(address, handler)
        self.server.numclients = 0
        self.server.serve_forever()

    def get_status(self):
        return 'running, {} clients'.format(self.server.numclients)
