import base64
import json
import threading
import logging
import http.server
from functools import partial
from urllib.parse import urlparse, parse_qsl

from openswitcher_proxy.frontend import AuthRequestHandler
from pyatem.field import FieldBase
import pyatem.command as commandmodule


class FieldEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, FieldBase):
            temp = obj.__dict__
            result = {}
            for key in temp:
                if key == 'raw':
                    continue
                result[key] = temp[key]
            return result
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode()
        return obj


class ApiRequestHandler(AuthRequestHandler):
    def __init__(self, config, threadpool, *args, **kwargs):
        self.config = config
        self.threadpool = threadpool
        super().__init__(*args, **kwargs)

    def response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        raw = json.dumps(data, cls=FieldEncoder, indent=2)
        self.wfile.write(raw.encode())

    def do_GET(self):
        if not self.verify_auth():
            return
        path = self.path
        allowed_hw = self.config['hardware'].split(',')
        if path == '/':
            hardware = []
            for hw in allowed_hw:
                row = {
                    'id': hw,
                }
                if hw not in self.threadpool['hardware']:
                    row['status'] = 'missing'
                else:
                    row['status'] = self.threadpool['hardware'][hw].get_status()
                hardware.append(row)
            self.response({'hardware': hardware})
            return
        parts = urlparse(path)
        path = parts.path[1:]
        part = path.split('/')
        args = parts.query
        if len(part) < 2:
            return self.response({}, 400)
        if part[0] not in allowed_hw:
            return self.response({'error': 'unknown device specified'}, 404)

        hw = part[0]
        fieldname = part[1]
        if fieldname in self.threadpool['hardware'][hw].switcher.mixerstate:
            field = self.threadpool['hardware'][hw].switcher.mixerstate[fieldname]
            return self.response(field)
        else:
            return self.response({'error': 'unknown field'}, 404)

    def do_POST(self):
        if not self.verify_auth():
            return
        path = self.path
        allowed_hw = self.config['hardware'].split(',')
        parts = urlparse(path)
        path = parts.path[1:]
        part = path.split('/')
        args = parts.query
        if len(part) < 2:
            return self.response({}, 400)
        if part[0] not in allowed_hw:
            return self.response({'error': 'unknown device specified'}, 404)

        hw = part[0]
        fieldname = part[1]
        classname = fieldname.title().replace('-', '') + "Command"
        if not hasattr(commandmodule, classname):
            return self.response({'error': 'unknown command'}, 404)

        rt = self.headers['Content-type']
        if rt is None:
            arguments = dict(parse_qsl(args))
        elif rt == 'application/x-www-form-urlencoded':
            length = int(self.headers['Content-length'])
            raw = self.rfile.read(length).decode()
            arguments = dict(parse_qsl(raw))
        elif rt == 'application/json':
            length = int(self.headers['Content-length'])
            raw = self.rfile.read(length).decode()
            arguments = json.loads(raw)
        else:
            return self.response({'error': 'unknown content-type'}, 400)

        for key in arguments:
            try:
                arguments[key] = int(arguments[key])
            except:
                pass
        if 'source' in arguments:
            inputs = self.threadpool['hardware'][hw].switcher.inputs
            if arguments['source'] in inputs:
                arguments['source'] = inputs[arguments['source']]

        try:
            cmd = getattr(commandmodule, classname)(**arguments)
            self.threadpool['hardware'][hw].switcher.send_commands([cmd])
        except Exception as e:
            return self.response({"error": str(e)}, 500)
        return self.response({"status": "ok"})


class HttpApiFrontendThread(threading.Thread):
    def __init__(self, config, threadlist):
        threading.Thread.__init__(self)
        self.name = 'http-api.' + str(config['bind'])
        self.config = config
        self.threadlist = threadlist
        self.stop = False
        self.server = None

    def run(self):
        logging.info('HTTP-Api frontend run')
        host, port = self.config['bind'].split(':')
        address = (host, int(port))
        logging.info(f'binding to {address}')

        handler = partial(ApiRequestHandler, self.config, self.threadlist)

        self.server = http.server.HTTPServer(address, handler)
        with self.server:
            self.server.serve_forever()

    def handler(self, *args):
        print(args)

    def get_status(self):
        return 'running'
