# Copyright 2022 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import ipaddress
import math
import os.path
import time

import usb.core
import usb.util
import struct

from pyatem.converters.lut import lut_to_bmd17, load_cube, lut_to_bmd33


class Field:
    def __init__(self, code, key, dtype, section, label, mapping=None, sys=False, ro=False):
        self.code = code
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


class Option:
    def __init__(self, code, label):
        self.code = code
        self.label = label


class Converter:
    VENDOR = 0x1edb
    PRODUCT = 0
    NAME = "Unknown"
    FIELDS = []
    PROTOCOL = "label"

    STATUS_OK = 1
    STATUS_NEED_POWER = 2

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

    def get_status(self):
        return self.STATUS_OK

    def get_version(self):
        return None

    def get_value_raw(self, field):
        raise NotImplementedError()

    def set_value_raw(self, field, value):
        raise NotImplementedError()

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

    def get_value_raw(self, field):
        if field.dtype == open:
            return None
        return self._communicate(field.key, field.sys)

    def get_value(self, field):
        raw = self.get_value_raw(field)
        if field.dtype == str:
            value = raw.split(b'\0')[0].decode()
        elif field.dtype == int:
            value = int.from_bytes(raw, byteorder='little')
        elif field.dtype == bool:
            value = int.from_bytes(raw, byteorder='little') > 0
        elif field.dtype == ipaddress.IPv4Address:
            value = ipaddress.IPv4Address(raw)
        elif field.dtype == open:
            value = None
        else:
            raise ValueError("Unknown type")

        if field.mapping == 'dB':
            if value > 0:
                value = 20 * math.log10(value / 64)
            else:
                value = float('-inf')
        return value

    def set_value_raw(self, field, value):
        self._communicate(field.key, field.sys, write=value)

    def set_value(self, field, value):
        if isinstance(value, bytes):
            self.set_value_raw(field, value)

        if field.dtype == int:
            value = value.to_bytes(length=(8 + (value + (value < 0)).bit_length()), byteorder='little')
        elif field.dtype == str:
            value = value.encode()
        elif field.dtype == bool:
            value = 255 if value else 0
            value = value.to_bytes(field.key[1], byteorder='little')

        self.set_value_raw(field, value)

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
            large = len(write) > 4096
            while len(write) > 0:
                chunk = write[0:4096]
                write = write[4096:]
                self.handle.ctrl_transfer(bmRequestType=ep_write,
                                          bRequest=req_write,
                                          wValue=ticket,
                                          wIndex=0,
                                          data_or_wLength=chunk,
                                          timeout=10000 if large else None)
        else:
            return bytes(self.handle.ctrl_transfer(bmRequestType=ep_read,
                                                   bRequest=req_read,
                                                   wValue=ticket,
                                                   wIndex=0,
                                                   data_or_wLength=255))

    def set_lut(self, key, path):
        lut = load_cube(path)
        title = os.path.basename(path)
        title = '.'.join(title.split('.')[0:-1])
        stream = lut_to_bmd17(lut)

        self._communicate("LutData", False, stream)
        self._communicate("LutName", False, title)


class WValueProtoConverter(Converter):
    PROTOCOL = 'wValue'
    NAME_FIELD = 0x00C0
    VERSION_FIELD = 0x00B0
    LUTFIELD = False
    HAS_NAME = True
    NEEDS_POWER = False
    LUT_SIZE = 17

    REG_STATUS = 48
    CMD_CLEAR = 55
    REG_CLEARSTATUS = 56
    CMD_WRITE = 57

    """
    bRequest:
      82: setting write
      83: setting read
      160: is powered?
    """

    def get_name(self):
        if not self.HAS_NAME:
            name = self.NAME.replace('Blackmagic design ', '')
            name = name.replace('Mini', '').replace('Micro', '').replace('Converter', '')
            return name.strip()

        raw = bytes(self.handle.ctrl_transfer(bmRequestType=0xc1,
                                              bRequest=83,
                                              wValue=self.NAME_FIELD,
                                              wIndex=0,
                                              data_or_wLength=64))

        return raw.split(b'\0')[0].decode()

    def get_status(self):
        if not self.NEEDS_POWER:
            return Converter.STATUS_OK
        raw = bytes(self.handle.ctrl_transfer(bmRequestType=0xc1,
                                              bRequest=160,
                                              wValue=0x00,
                                              wIndex=0,
                                              data_or_wLength=1))
        if raw == b'\0':
            return Converter.STATUS_NEED_POWER
        return Converter.STATUS_OK

    def get_version(self):
        raw = bytes(self.handle.ctrl_transfer(bmRequestType=0xc1,
                                              bRequest=83,
                                              wValue=self.VERSION_FIELD,
                                              wIndex=0,
                                              data_or_wLength=7))

        return raw.split(b'\0')[0].decode()

    def get_value_raw(self, field):
        if field.dtype == open:
            return
        return bytes(self.handle.ctrl_transfer(bmRequestType=0xc1,
                                               bRequest=83,
                                               wValue=field.key[0],
                                               wIndex=0,
                                               data_or_wLength=field.key[1]))

    def get_value(self, field):
        raw = self.get_value_raw(field)
        if field.dtype == str:
            value = raw.split(b'\0')[0].decode()
        elif field.dtype == int:
            value = int.from_bytes(raw, byteorder='little')
        elif field.dtype == bool:
            value = int.from_bytes(raw, byteorder='little') > 0
        elif field.dtype == ipaddress.IPv4Address:
            value = ipaddress.IPv4Address(raw)
        elif field.dtype == open:
            value = None
        else:
            raise ValueError("Unknown type")

        if field.mapping == 'dB':
            if value > 0:
                value = 20 * math.log10(value / 64)
            else:
                value = float('-inf')
        return value

    def set_value_raw(self, field, value):
        self.handle.ctrl_transfer(bmRequestType=0x41,
                                  bRequest=82,
                                  wValue=field.key[0],
                                  data_or_wLength=value)

    def set_value(self, field, value):
        if isinstance(value, bytes):
            self.set_value_raw(field, value)

        if field.mapping == "dB":
            print(f"set {value} dB")
            value = float(value)
            value = int(round(math.pow(10, value / 20) * 64))

        if field.dtype == int:
            value = value.to_bytes(field.key[1], byteorder='little')
        elif field.dtype == str:
            # TODO(Peter): Fix me! This has some "fun" edge cases if unicode is
            # allowed...
            if len(value.encode()) > field.key[1] - 1:
                value = value[0:field.key[1] - 2].encode()
            else:
                value = value.encode()
            value += b'\0'
        elif field.dtype == bool:
            value = 255 if value else 0
            value = value.to_bytes(field.key[1], byteorder='little')
        elif field.dtype == ipaddress.IPv4Address:
            addr = ipaddress.IPv4Address(value)
            value = addr.packed

        self.set_value_raw(field, value)

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

    def _wait_on_status(self, status0=None, status1=None, status2=None, status3=None, status4=None, status5=None):
        # Wait for the LUT engine to be ready
        wanted = [status0, status1, status2, status3, status4, status5]
        for i in range(0, 20):
            status = self._read(self.REG_STATUS, 6)
            data = struct.unpack('>6B', status)

            fail = False
            for idx, s in enumerate(wanted):
                if s is not None and data[idx] != s:
                    fail = True
            if not fail:
                break

            time.sleep(0.5)
        else:
            raise TimeoutError("Status did not update")

    def _clear_region(self, address, length):
        self._write(self.CMD_CLEAR, struct.pack('>II', address, length))
        while True:
            status = self._read(self.REG_CLEARSTATUS, 15)
            part = struct.unpack('>II I BBB', status)
            # 0 address
            # 1 length
            # 2 clear ptr
            # 3 ?
            # 4 ?
            # 5 ?

            progress = ((part[2] - part[0]) / part[1]) * 100
            if part[3] == 0 and part[4] == 0 and part[5] == 0:
                break

            time.sleep(0.3)

    def _bulk_write(self, address, data):
        # position in blocks maybe?
        block = address >> 8
        self._write(self.CMD_WRITE, struct.pack('>I', block))

        self.handle.write(1, data)
        self.handle.write(1, b'')

    def _set_lut_33(self, key, path):
        address, length = key
        lut = load_cube(path)
        title = os.path.basename(path)
        title = '.'.join(title.split('.')[0:-1])
        stream = lut_to_bmd33(lut, title)

        self._wait_on_status(status4=0xFF, status5=0xFF)
        self._write(49, b'')
        self._write(52, b'')

        self._clear_region(address, length)
        self._bulk_write(address, stream)
        self._wait_on_status(status1=0x00, status2=0x00)
        self._write(50, b'')

    def _set_lut_17(self, key, path):
        address, length = key
        lut = load_cube(path)
        stream = lut_to_bmd17(lut)

        self._wait_on_status(status4=0xFF, status5=0xFF)
        self._write(49, b'')
        self._write(52, b'')
        self._clear_region(address, length)
        self._bulk_write(address, stream)
        self._wait_on_status(status1=0x00, status2=0x00)
        self._write(50, b'')

        # Write the new LUT name and finalize the upload
        self.set_value(Field(None, (0x0410, 64), str, '', 'LUT name'), struct.pack('>64s', lut.title.encode()))
        self.set_value(Field(None, (0x0400, 1), int, '', 'Unknown'), struct.pack('>B', 3))

    def set_lut(self, key, path):
        if self.LUT_SIZE == 17:
            self._set_lut_17(key, path)
        elif self.LUT_SIZE == 33:
            self._set_lut_33(key, path)
        else:
            raise ValueError("Unsupported LUT size")


class WIndexProtoConverter(Converter):
    PROTOCOL = 'wIndex'
#    NAME_FIELD = 0x00C0
#    VERSION_FIELD = 0x00B0
#    LUTFIELD = False
    HAS_NAME = True
    NEEDS_POWER = False
#    LUT_SIZE = 17

    REG_STATUS = 48
    CMD_CLEAR = 55
    REG_CLEARSTATUS = 56
    CMD_WRITE = 57

    """
    bRequest:
      215: setting write
      214: setting read
      225: is powered?
    """

    def get_name(self):
        if not self.HAS_NAME:
            name = self.NAME.replace('Blackmagic design ', '')
            name = name.replace('Mini', '').replace('Micro', '').replace('Converter', '')
            return name.strip()

        raise NotImplementedError()
#        raw = bytes(self.handle.ctrl_transfer(bmRequestType=0xc1,
#                                              bRequest=83,
#                                              wValue=self.NAME_FIELD,
#                                              wIndex=0,
#                                              data_or_wLength=64))
#
#        return raw.split(b'\0')[0].decode()

    def get_status(self):
        if not self.NEEDS_POWER:
            return Converter.STATUS_OK
        raw = bytes(self.handle.ctrl_transfer(bmRequestType=0xc0,
                                              bRequest=225,
                                              wValue=0x0000,
                                              wIndex=0,
                                              data_or_wLength=1))
        if raw == b'\0':
            return Converter.STATUS_NEED_POWER
        return Converter.STATUS_OK

    def get_version(self):
        raise NotImplementedError()
        print("TODO: fixme!")
#        raw = bytes(self.handle.ctrl_transfer(bmRequestType=0xc1,
#                                              bRequest=83,
#                                              wValue=self.VERSION_FIELD,
#                                              wIndex=0,
#                                              data_or_wLength=7))
#
#        return raw.split(b'\0')[0].decode()

    def get_value_raw(self, field):
        if field.dtype == open:
            return
        return bytes(self.handle.ctrl_transfer(bmRequestType=0xc0,
                                               bRequest=214,
                                               wValue=0,
                                               wIndex=field.key[0],
                                               data_or_wLength=field.key[1]))

    def get_value(self, field):
        raw = self.get_value_raw(field)
        if field.dtype == str:
            value = raw.split(b'\0')[0].decode()
        elif field.dtype == int:
            value = int.from_bytes(raw, byteorder='little')
        elif field.dtype == bool:
            value = int.from_bytes(raw, byteorder='little') > 0
        elif field.dtype == open:
            value = None
        else:
            raise ValueError("Unknown type")

        if field.mapping == 'dB':
            if value > 0:
                value = 20 * math.log10(value / 64)
            else:
                value = float('-inf')
        return value

    def set_value_raw(self, field, value):
# Set seems to be URB Control wIndex of field ID ORed with the desired field
# value with bmRequestType of 0x40
        self.handle.ctrl_transfer(bmRequestType=0x40,
                                  bRequest=215,
                                  wValue=0,
                                  # Or the field ID with the first byte of the
                                  # value in case there is more than one byte
                                  wIndex=field.key[0] | value[0],
                                  data_or_wLength=0),

    def set_value(self, field, value):
        if isinstance(value, bytes):
            self.set_value_raw(field, value)

        if field.mapping == "dB":
            print(f"set {value} dB")
            value = float(value)
            value = int(round(math.pow(10, value / 20) * 64))

        if field.dtype == int:
            value = value.to_bytes(field.key[1], byteorder='little')
        elif field.dtype == str:
            # TODO(Peter): Test me, this is probably more correct than what's
            # currently used, but untested and given it's a set...
            # TODO(Peter): Fix me! This has some "fun" edge cases if unicode is
            # allowed...
            # if len(value.encode()) > field.key[1] - 1:
            #     value = value[0:field.key[1] - 2].encode()
            # else:
            #     value = value.encode()
            # value += b'\0'
            value = value.encode()
        elif field.dtype == bool:
            value = 255 if value else 0
            value = value.to_bytes(field.key[1], byteorder='little')
        # TODO(Peter): Test me, this is probably correct, but untested and
        # given it's a set...
        # elif field.dtype == ipaddress.IPv4Address:
        #     addr = ipaddress.IPv4Address(value)
        #     value = addr.packed

        self.set_value_raw(field, value)

    def _read(self, bRequest, length):
        raise NotImplementedError()
#        return bytes(self.handle.ctrl_transfer(bmRequestType=0xc1,
#                                               bRequest=bRequest,
#                                               wValue=0,
#                                               wIndex=0,
#                                               data_or_wLength=length))

    def _write(self, bRequest, data):
        raise NotImplementedError()
#        self.handle.ctrl_transfer(bmRequestType=0x41,
#                                  bRequest=bRequest,
#                                  wValue=0,
#                                  wIndex=0,
#                                  data_or_wLength=data)

    def _wait_on_status(self, status0=None, status1=None, status2=None, status3=None, status4=None, status5=None):
        # Wait for the LUT engine to be ready
        wanted = [status0, status1, status2, status3, status4, status5]
        for i in range(0, 20):
            status = self._read(self.REG_STATUS, 6)
            data = struct.unpack('>6B', status)

            fail = False
            for idx, s in enumerate(wanted):
                if s is not None and data[idx] != s:
                    fail = True
            if not fail:
                break

            time.sleep(0.5)
        else:
            raise TimeoutError("Status did not update")

    def _clear_region(self, address, length):
        self._write(self.CMD_CLEAR, struct.pack('>II', address, length))
        while True:
            status = self._read(self.REG_CLEARSTATUS, 15)
            part = struct.unpack('>II I BBB', status)
            # 0 address
            # 1 length
            # 2 clear ptr
            # 3 ?
            # 4 ?
            # 5 ?

            progress = ((part[2] - part[0]) / part[1]) * 100
            if part[3] == 0 and part[4] == 0 and part[5] == 0:
                break

            time.sleep(0.3)

    def _bulk_write(self, address, data):
        # position in blocks maybe?
        block = address >> 8
        self._write(self.CMD_WRITE, struct.pack('>I', block))

        self.handle.write(1, data)
        self.handle.write(1, b'')

    def _set_lut_33(self, key, path):
        address, length = key
        lut = load_cube(path)
        title = os.path.basename(path)
        title = '.'.join(title.split('.')[0:-1])
        stream = lut_to_bmd33(lut, title)

        self._wait_on_status(status4=0xFF, status5=0xFF)
        self._write(49, b'')
        self._write(52, b'')

        self._clear_region(address, length)
        self._bulk_write(address, stream)
        self._wait_on_status(status1=0x00, status2=0x00)
        self._write(50, b'')

    def _set_lut_17(self, key, path):
        address, length = key
        lut = load_cube(path)
        stream = lut_to_bmd17(lut)

        self._wait_on_status(status4=0xFF, status5=0xFF)
        self._write(49, b'')
        self._write(52, b'')
        self._clear_region(address, length)
        self._bulk_write(address, stream)
        self._wait_on_status(status1=0x00, status2=0x00)
        self._write(50, b'')

        # Write the new LUT name and finalize the upload
        self.set_value(Field(None, (0x0410, 64), str, '', 'LUT name'), struct.pack('>64s', lut.title.encode()))
        self.set_value(Field(None, (0x0400, 1), int, '', 'Unknown'), struct.pack('>B', 3))

    def set_lut(self, key, path):
        if self.LUT_SIZE == 17:
            self._set_lut_17(key, path)
        elif self.LUT_SIZE == 33:
            self._set_lut_33(key, path)
        else:
            raise ValueError("Unsupported LUT size")


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
