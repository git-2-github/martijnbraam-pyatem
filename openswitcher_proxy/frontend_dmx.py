import threading
import logging
from functools import partial

from .error import DependencyError

try:
    import serial
except ModuleNotFoundError:
    serial = None


class DmxFrontendThread(threading.Thread):
    def __init__(self, config, threadlist):
        threading.Thread.__init__(self)
        if serial is None:
            raise DependencyError("The pyserial library is not available")
        self.name = 'dmx.' + str(config['host'])
        self.config = config
        self.threadlist = threadlist
        self.hw_name = self.config['hardware'].split(',')
        self.client = None
        self.status = 'initializing...'
        self.error = None
        self.port = None

    def run(self):
        logging.info('DMX frontend run')
        try:
            self.port = serial.Serial(self.config['host'], 57600)
        except Exception as e:
            logging.error(e)
            self.error = f'could not connect to {self.config["host"]}'
            self.status = 'error'
            return
        for hw in self.hw_name:
            sw = self.threadlist['hardware'][hw].switcher
            sw.on('change', partial(self.on_switcher_changed, hw))

        self.client.loop_forever()

    def on_switcher_changed(self, hw, field, value):
        if field == 'camera-control':
            print(value)

    def get_status(self):
        if self.status == 'error':
            return f'{self.status}, {self.error}'
        if self.readonly:
            return self.status + ' (readonly)'
        else:
            return self.status + ' (writable)'
