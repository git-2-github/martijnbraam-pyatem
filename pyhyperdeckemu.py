import socketserver
import logging
import time


class VirtualHyperdeck(socketserver.BaseRequestHandler):
    def setup(self):
        self.remote = True
        self.uid = '1234'

        self.notify_transport = False
        self.notify_slot = False
        self.notify_remote = False
        self.notify_configuration = False

        self.transport_status = 'stopped'
        self.transport_speed = 0
        self.transport_slot_id = 1
        self.timecode = "01:00:00:00"
        self.display_timecode = "01:00:00:00"
        self.clip_id = 0
        self.video_format = "720p50"
        self.loop = False

        self.clips = [
            (1, "Test clip", 30),
            (2, "Another clip", 45)
        ]

    def handle(self):
        logging.info('connected')
        self.send(b'500 connection info:\r\nprotocol version: 1.9\r\nmodel: Linux\r\n\r\n')
        while True:
            data = self.request.recv(1024)
            if len(data) == 0:
                logging.info('disconnected')
                break
            logging.debug('< ' + data.decode())
            self.handle_line(data.decode().strip())

    def send(self, data):
        logging.debug('> ' + data.decode())
        self.request.sendall(data)

    def parse_line(self, line):
        parameters = {}
        parts = line.split(' ')
        name = parts[0].rstrip(':')
        key = None
        for part in parts[1:]:
            if part[-1] == ':':
                key = part.rstrip(':')
            else:
                if key not in parameters:
                    parameters[key] = ''
                parameters[key] += part
                parameters[key] = parameters[key].strip()
        return name, parameters

    def handle_line(self, line):
        if line.startswith('notify:'):
            _, parameters = self.parse_line(line)
            if 'transport' in parameters:
                self.notify_transport = parameters['transport'] == 'true'
            if 'slot' in parameters:
                self.notify_slot = parameters['slot'] == 'true'
            if 'remote' in parameters:
                self.notify_remote = parameters['remote'] == 'true'
            if 'configuration' in parameters:
                self.notify_configuration = parameters['configuration'] == 'true'

            self._send_notify(sync=True)

        elif line.startswith('transport info'):
            self._send_transport_info(sync=True)
        elif line == 'remote':
            self._send_remote_info(sync=True)
        elif line == 'clips count':
            self._send_clips_count()
        elif line.startswith('slot info'):
            _, parameters = self.parse_line(line)
            self._send_slot_info(sync=True)
        elif line.startswith('clips get: clip'):
            _, parameters = self.parse_line(line)
            self._send_clip_info(sync=True, clip=int(parameters['id']))
        elif line.startswith('goto: clip'):
            _, parameters = self.parse_line(line)
            self.clip_id = int(parameters['id'])
            self.send(b'200 ok\r\n')
            if self.notify_transport:
                self._send_transport_info(sync=False)
        else:
            time.sleep(0.5)

    def _send_notify(self, sync=True):
        if sync:
            response = b'209 notify:\r\n'
        else:
            response = b'509 remote info:\r\n'
        response += 'transport: {}\r\n'.format('true' if self.notify_transport else 'false').encode()
        response += 'slot: {}\r\n'.format('true' if self.notify_slot else 'false').encode()
        response += 'remote: {}\r\n'.format('true' if self.notify_remote else 'false').encode()
        response += 'configuration: {}\r\n'.format('true' if self.notify_configuration else 'false').encode()
        response += b'\r\n'
        self.send(response)

    def _send_remote_info(self, sync=True):
        if sync:
            response = b'210 remote info:\r\n'
        else:
            response = b'510 remote info:\r\n'
        response += b'enabled: true\r\n'
        response += b'override: true\r\n'
        response += b'\r\n'
        self.send(response)

    def _send_transport_info(self, sync=True):
        if sync:
            response = b'208 transport info:\r\n'
        else:
            response = b'508 transport info:\r\n'

        response += 'status: {}\r\n'.format(self.transport_status).encode()
        response += 'speed: {}\r\n'.format(self.transport_speed).encode()
        response += 'slot id: {}\r\n'.format(self.transport_slot_id or 'none').encode()
        response += 'timecode: {}\r\n'.format(self.timecode).encode()
        response += 'display timecode: {}\r\n'.format(self.display_timecode).encode()
        response += 'clip id: {}\r\n'.format(self.clip_id).encode()
        response += 'video format: {}\r\n'.format(self.video_format or 'none').encode()
        response += 'loop: {}\r\n'.format('true' if self.loop else 'false').encode()
        response += b'\r\n'
        self.send(response)

    def _send_slot_info(self, sync=True):
        if sync:
            response = b'202 slot info:\r\n'
        else:
            response = b'502 slot info:\r\n'
        response += b'slot id: 1\r\n'
        response += b'status: mounted\r\n'
        response += b'volume name: SD\r\n'
        response += b'recording time: 0\r\n'
        response += 'video format: {}\r\n'.format(self.video_format).encode()
        response += b'\r\n'
        self.send(response)

    def _send_configuration(self, sync=True):
        if sync:
            response = b'211 configuration:\r\n'
        else:
            response = b'511 configuration:\r\n'
        response += b'audio input: embedded\r\n'
        response += b'video input: HDMI\r\n'
        response += b'file format: H.264High\r\n'
        response += b'\r\n'
        self.send(response)

    def _send_clips_count(self):
        response = b'214 clips count:\r\n'
        response += 'clip count: {}\r\n'.format(len(self.clips)).encode()
        response += b'\r\n'
        self.send(response)

    def _send_clip_info(self, sync=True, clip=0):
        response = b'205 clips info:\r\n'
        response += 'clip count: {}\r\n'.format(len(self.clips)).encode()
        for clip in self.clips:
            cliplen = '00:00:{}:00'.format(clip[2])
            response += '{}: {} 00:00:00:00 {}\r\n'.format(clip[0], clip[1], cliplen).encode()
        response += b'\r\n'
        self.send(response)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    server = socketserver.TCPServer(('0.0.0.0', 9993), VirtualHyperdeck, bind_and_activate=False)
    server.allow_reuse_address = True
    server.server_bind()
    server.server_activate()
    server.serve_forever()
