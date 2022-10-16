# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import ipaddress
import logging
import sys

try:
    from zeroconf import ServiceBrowser, Zeroconf

    has_zeroconf = True
except ImportError:
    has_zeroconf = False

from pyatem.transport import UsbProtocol

browser = None
zeroconf = None


class AtemListener:
    def __init__(self, on_add, on_remove):
        self.on_add = on_add
        self.on_remove = on_remove

    def remove_service(self, zeroconf, type, name):
        if self.on_remove is not None:
            self.on_remove()

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info is None:
            return
        if info.properties[b'class'] != b'AtemSwitcher':
            return

        address = ipaddress.ip_address(info.addresses[0])
        port = info.port
        name = info.properties[b'name'].decode()
        logging.info('Dicovered "{}" at {} port {}'.format(name, address, port))
        subtitle = 'Atem protocol'
        if b'release version' in info.properties:
            subtitle = "Firmware " + info.properties[b'release version'].decode()
        if self.on_add is not None:
            self.on_add(name, subtitle, 'udp', (address, port))

    def update_service(self, *args):
        pass


def listen(on_add, on_remove=None):
    global browser, zeroconf
    device = UsbProtocol.find_device()
    if device is not None and on_add is not None:
        pid = device.idProduct
        on_add(UsbProtocol.PRODUCTS[pid], 'USB protocol', 'usb', ('USB', 0))

    if not has_zeroconf:
        sys.stderr.write("zeroconf discovery unavailable without pyzeroconf\n")
        return
    zeroconf = Zeroconf()
    listener = AtemListener(on_add, on_remove)
    browser = ServiceBrowser(zeroconf, "_blackmagic._tcp.local.", listener)


def stop():
    global zeroconf
    if not has_zeroconf:
        return
    if zeroconf is not None:
        zeroconf.close()


if __name__ == '__main__':
    def test(*args):
        print('test', args)


    logging.basicConfig(level=logging.INFO)
    listen(test)
    input()
