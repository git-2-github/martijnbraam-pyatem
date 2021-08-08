import threading
import logging

from pyatem.protocol import AtemProtocol


class HardwareThread(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)
        self.name = 'hw.' + str(config['id'])
        self.config = config
        self.switcher = None
        self.stop = False
        self.status = 'init'

    def run(self):
        logging.info('HardwareThread run')
        self.status = 'connecting...'
        if self.config['address'] == 'usb':
            self.switcher = AtemProtocol(usb='auto')
        else:
            self.switcher = AtemProtocol(ip=self.config['address'])
        self.switcher.on('connected', self.on_connected)
        self.switcher.on('change', self.on_change)
        self.switcher.on('disconnected', self.on_disconnected)
        self.switcher.connect()
        while not self.stop:
            self.switcher.loop()

    def get_status(self):
        if self.status == 'connected':
            name = self.switcher.mixerstate["product-name"].name
            fw = self.switcher.mixerstate["firmware-version"].version
            self.status += f' ({name} fw {fw})'
        return self.status

    def on_connected(self):
        self.status = 'connected'
        logging.info('Initial state sync complete')

    def on_disconnected(self):
        self.status = 'lost connection'
        logging.error('Lost connection with the hardware')

    def on_change(self, key, value):
        pass
