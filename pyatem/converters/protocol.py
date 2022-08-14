import usb.core
import usb.util
import struct


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
    def is_plugged_in(cls):
        result = usb.core.find(idVendor=cls.VENDOR, idProduct=cls.PRODUCT)
        return result is not None

    def connect(self):
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
