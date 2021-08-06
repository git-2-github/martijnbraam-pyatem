import threading
import logging
import http.server
from functools import partial

from openswitcher_proxy.frontend import AuthRequestHandler


class StatusRequestHandler(AuthRequestHandler):
    def __init__(self, config, threadpool, *args, **kwargs):
        self.config = config
        self.threadpool = threadpool
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if not self.verify_auth():
            return

        if self.path == '/favicon.ico':
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            return

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("<!DOCTYPE html>\n<title>OpenSwitcher proxy status</title>".encode())
        self.wfile.write("<h1>Status</h1>".encode())
        self.wfile.write("<h2>Hardware</h2>".encode())
        if 'hardware' in self.threadpool:
            self.wfile.write(
                '<table border="1"><tr><th>id</th><th>label</th><th>address</th><th>status</th></tr>'.encode())
            for hwid in self.threadpool['hardware']:
                hardware = self.threadpool['hardware'][hwid]
                self.wfile.write('<tr>'.encode())
                self.wfile.write(f'<td>{hwid}</td>'.encode())
                self.wfile.write(f'<td>{hardware.config["label"]}</td>'.encode())
                self.wfile.write(f'<td>{hardware.config["address"]}</td>'.encode())
                self.wfile.write(f'<td>{hardware.get_status()}</td>'.encode())
                self.wfile.write('</tr>'.encode())
            self.wfile.write('</table>'.encode())
        else:
            self.wfile.write("No hardware is defined".encode())

        self.wfile.write("<h2>Frontends</h2>".encode())
        if 'frontend' in self.threadpool:
            self.wfile.write(
                '<table border="1"><tr><th>bind</th><th>type</th><th>auth</th><th>status</th></tr>'.encode())
            for bind in self.threadpool['frontend']:
                frontend = self.threadpool['frontend'][bind]
                self.wfile.write('<tr>'.encode())
                self.wfile.write(f'<td>{bind}</td>'.encode())
                self.wfile.write(f'<td>{frontend.config["type"]}</td>'.encode())
                self.wfile.write(f'<td>{frontend.config["auth"]}</td>'.encode())
                self.wfile.write(f'<td>{frontend.get_status()}</td>'.encode())
                self.wfile.write('</tr>'.encode())
            self.wfile.write('</table>'.encode())
        else:
            self.wfile.write("No hardware is defined".encode())


class StatusFrontendThread(threading.Thread):
    def __init__(self, config, threadlist):
        threading.Thread.__init__(self)
        self.name = 'status.' + str(config['bind'])
        self.config = config
        self.threadlist = threadlist
        self.stop = False
        self.server = None

    def run(self):
        logging.info('Status frontend run')
        host, port = self.config['bind'].split(':')
        address = (host, int(port))
        logging.info(f'binding to {address}')

        handler = partial(StatusRequestHandler, self.config, self.threadlist)

        self.server = http.server.HTTPServer(address, handler)
        with self.server:
            self.server.serve_forever()

    def handler(self, *args):
        print(args)

    def get_status(self):
        return 'running'
