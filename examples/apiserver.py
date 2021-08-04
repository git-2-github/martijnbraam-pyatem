import argparse
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qsl

import pyatem.command as commandmodule
from pyatem.protocol import AtemProtocol

switcher = None
_port = None
_inputs = {}


class ApiServer(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        print(path)

        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"OpenSwitcher API server\n")
            return

        parts = urlparse(path)
        command = parts.path[1:]
        args = parts.query

        classname = command.title().replace('-', '') + "Command"
        print("Command: " + classname)
        if not hasattr(commandmodule, classname):
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Unknown command\n")
            return

        arguments = dict(parse_qsl(args))
        for key in arguments:
            try:
                arguments[key] = int(arguments[key])
            except:
                pass
        if 'source' in arguments:
            if arguments['source'] in _inputs:
                arguments['source'] = _inputs[arguments['source']]

        try:
            cmd = getattr(commandmodule, classname)(**arguments)
            switcher.send_commands([cmd])
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(str(e).encode())
            return
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK\n")


class WebThread(threading.Thread):
    def run(self):
        print("Running API server on :" + str(_port))
        httpd = HTTPServer(("", _port), ApiServer)
        httpd.serve_forever()


def input_changed(inputproperties):
    global _inputs
    _inputs[inputproperties.short_name] = inputproperties.index


def connection_ready(*args):
    WebThread().start()


def main():
    global switcher, _port
    parser = argparse.ArgumentParser(description="Atem CLI")
    parser.add_argument('ip', help='Atem ip or "usb" for usb')
    parser.add_argument('port', help='Port to run the HTTP server on', type=int)
    args = parser.parse_args()

    _port = args.port

    if args.ip == 'usb':
        print("Connecting to USB switcher")
        switcher = AtemProtocol(usb='auto')
    else:
        print("Connecting to " + args.ip)
        switcher = AtemProtocol(ip=args.ip)

    switcher.on('change:input-properties:*', input_changed)
    switcher.on('connected', connection_ready)

    switcher.connect()
    while True:
        switcher.loop()


if __name__ == '__main__':
    main()
