# Copyright 2022 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import time

import usb.core
import usb.util
import struct

from pyatem.converters.lut import lut_to_bmd17, load_cube


class Field:
    def __init__(self, key, dtype, section, label, mapping=None, sys=False, ro=False):
        self.key = key
        self.section = section
        self.dtype = dtype
        self.label = label
        self.sys = sys
        self.mapping = mapping
        self.ro = ro

        self.value = None
        self.widget = None

    def __repr__(self):
        return f'<Field {self.key} ({self.label})>'


class Converter:
    VENDOR = 0x1edb
    PRODUCT = 0
    NAME = "Unknown"
    FIELDS = []
    PROTOCOL = "label"

    def __init__(self):
        self.handle = None

    @classmethod
    def is_plugged_in(cls, serial=None):
        if serial is not None:
            result = usb.core.find(idVendor=cls.VENDOR, idProduct=cls.PRODUCT, iSerialNumber=serial)
        else:
            result = usb.core.find(idVendor=cls.VENDOR, idProduct=cls.PRODUCT)
        return result is not None

    def connect(self, serial=None):
        if serial is not None:
            self.handle = usb.core.find(idVendor=self.VENDOR, idProduct=self.PRODUCT, iSerialNumber=serial)
        else:
            self.handle = usb.core.find(idVendor=self.VENDOR, idProduct=self.PRODUCT)

        self.handle.set_configuration(1)

    def get_name(self):
        # Fallback for devices that might not support renaming
        return self.NAME

    def get_version(self):
        return None

    def get_value(self, field):
        raise NotImplementedError()

    def set_value(self, field, value):
        raise NotImplementedError()

    def get_state(self):
        result = {}
        for field in self.FIELDS:
            ret = self.get_value(field)
            field.value = ret
            result[field.key] = field
        return result

    def factory_reset(self):
        raise NotImplementedError()


class LabelProtoConverter(Converter):
    PROTOCOL = 'label'
    NAME_FIELD = "DeviceName"
    VERSION_FIELD = "ReleaseVersion"

    def get_name(self):
        return self._communicate(self.NAME_FIELD, sys=True).decode()

    def get_version(self):
        return self._communicate(self.VERSION_FIELD, sys=True).decode()

    def factory_reset(self):
        self.handle.ctrl_transfer(bmRequestType=0x40,
                                  bRequest=20,
                                  wValue=0,
                                  wIndex=0,
                                  data_or_wLength=0)

    def get_value(self, field):
        return self._communicate(field.key, field.sys)

    def set_value(self, field, value):
        self._communicate(field.key, field.sys, write=value)

    def _communicate(self, name, sys=False, write=None):
        ep_read = 0xa1 if sys else 0xc0
        ep_write = 0x21 if sys else 0x40
        req_ticket = 1 if sys else 10
        req_name = 2 if sys else 11
        req_read = 3 if sys else 12
        req_write = 4 if sys else 13

        ticket = self.handle.ctrl_transfer(bmRequestType=ep_read,
                                           bRequest=req_ticket,
                                           wValue=0,
                                           wIndex=0,
                                           data_or_wLength=2)

        ticket, = struct.unpack('<H', bytes(ticket))

        self.handle.ctrl_transfer(bmRequestType=ep_write,
                                  bRequest=req_name,
                                  wValue=ticket,
                                  wIndex=0,
                                  data_or_wLength=name.encode())

        if write is not None:
            self.handle.ctrl_transfer(bmRequestType=ep_write,
                                      bRequest=req_write,
                                      wValue=ticket,
                                      wIndex=0,
                                      data_or_wLength=write)
        else:
            return bytes(self.handle.ctrl_transfer(bmRequestType=ep_read,
                                                   bRequest=req_read,
                                                   wValue=ticket,
                                                   wIndex=0,
                                                   data_or_wLength=255))


class WValueProtoConverter(Converter):
    PROTOCOL = 'wValue'
    NAME_FIELD = 0x00C0
    VERSION_FIELD = 0x00B0
    LUTFIELD = False

    def get_name(self):
        raw = bytes(self.handle.ctrl_transfer(bmRequestType=0xc1,
                                              bRequest=83,
                                              wValue=self.NAME_FIELD,
                                              wIndex=0,
                                              data_or_wLength=64))

        return raw.split(b'\0')[0].decode()

    def get_version(self):
        raw = bytes(self.handle.ctrl_transfer(bmRequestType=0xc1,
                                              bRequest=83,
                                              wValue=self.VERSION_FIELD,
                                              wIndex=0,
                                              data_or_wLength=7))

        return raw.split(b'\0')[0].decode()

    def get_value(self, field):
        if field.dtype == open:
            return
        return bytes(self.handle.ctrl_transfer(bmRequestType=0xc1,
                                               bRequest=83,
                                               wValue=field.key[0],
                                               wIndex=0,
                                               data_or_wLength=field.key[1]))

    def set_value(self, field, value):
        self.handle.ctrl_transfer(bmRequestType=0x41,
                                  bRequest=82,
                                  wValue=field.key[0],
                                  data_or_wLength=value)

    def _read(self, bRequest, length):
        return bytes(self.handle.ctrl_transfer(bmRequestType=0xc1,
                                               bRequest=bRequest,
                                               wValue=0,
                                               wIndex=0,
                                               data_or_wLength=length))

    def _write(self, bRequest, data):
        self.handle.ctrl_transfer(bmRequestType=0x41,
                                  bRequest=bRequest,
                                  wValue=0,
                                  wIndex=0,
                                  data_or_wLength=data)

    def set_lut(self, path):
        lut = load_cube(path)
        stream = lut_to_bmd17(lut)

        # Wait for the LUT engine to be ready
        for i in range(0, 20):
            status = self._read(48, 6)
            data = struct.unpack('>6B', status)
            if data[4] == 255 and data[5] == 255:
                break
            time.sleep(0.5)
        else:
            raise TimeoutError("Status did not update")

        # The function of this is completely unknown
        self._write(49, b'')
        self._write(52, b'')
        data_53 = self._read(53, 16)
        self._write(55, b'\x3f\0\0\0\x01\0\0\0')
        data_56 = self._read(56, 15)
        data_16 = self._read(16, 1)
        data_83 = self._read(83, 4)
        data_56b = self._read(56, 15)
        data_53b = self._read(53, 16)
        self._write(57, b'\x00\x3f\x00\x00')

        # Write the new LUT
        self.handle.write(1, stream)
        self.handle.write(1, b'')

        # Wait for the LUT to be processed on the converter
        for i in range(0, 10):
            status = self._read(48, 6)
            data = struct.unpack('>6B', status)
            if data[1] == 0 and data[2] == 0:
                break
            time.sleep(0.5)
        else:
            raise TimeoutError("Status did not update")

        self._write(50, b'')

        # Write the new LUT name and finalize the upload
        self.set_value(Field((0x0410, 64), str, '', 'LUT name'), struct.pack('>64s', lut.title.encode()))
        self.set_value(Field((0x0400, 1), int, '', 'Unknown'), struct.pack('>B', 3))


class AtemLegacyProtocol(Converter):
    PROTOCOL = 'AtemLegacy'
    NAME_FIELD = 0x0048

    def get_name(self):
        return self.get_value(Field((self.NAME_FIELD, 32), str, "Device", "Name")).decode()

    def get_version(self):
        return 'Unsupported'

    def get_value(self, field):
        if field.dtype == open:
            return

        result = b''
        for i in range(0, field.key[1]):
            char = bytes(self.handle.ctrl_transfer(bmRequestType=0xc0,
                                                   bRequest=214,
                                                   wValue=0,
                                                   wIndex=field.key[0] + i,
                                                   data_or_wLength=1))
            if char == '\0':
                break
            result += char
        return result

    def set_value(self, field, value):
        if field.dtype == str:
            if len(value) > field.key[1] - 1:
                value = value[0:field.key[1] - 2]
            value += b'\0'
        for i in range(0, len(value)):
            self.handle.ctrl_transfer(bmRequestType=0x40,
                                      bRequest=215,
                                      wIndex=field.key[0] + i,
                                      wValue=value[i])
