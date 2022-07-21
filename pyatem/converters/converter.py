import usb.core
import usb.util
import struct


class Field:
    def __init__(self, name, dtype, section, label, mapping=None, sys=False, ro=False):
        self.name = name
        self.section = section
        self.dtype = dtype
        self.label = label
        self.sys = sys
        self.mapping = mapping
        self.ro = ro

        self.value = None
        self.widget = None

    def __repr__(self):
        return f'<Field {self.name} ({self.label})>'


class Converter:
    VENDOR = 0x1edb
    PRODUCT = 0
    NAME = "Unknown"
    FIELDS = []
    NAME_FIELD = "DeviceName"

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
        if self.NAME_FIELD is None:
            return self.NAME

        # Get the name field
        return self.get_field(self.NAME_FIELD, sys=True).decode()

    def get_field(self, name, sys=False, write=None):
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

    def set_field(self, name, value, sys=False):
        return self.get_field(name, sys=sys, write=value)

    def get_state(self):
        result = {}
        for field in self.FIELDS:
            ret = self.get_field(field.name, sys=field.sys)
            field.value = ret
            result[field.name] = field
        return result


class MicroConverterBiDirectional12G(Converter):
    PRODUCT = 0xbe89
    NAME = "Blackmagic design Micro Converter BiDirectional SDI/HDMI 12G"

    FIELDS = [
        Field('DeviceName', str, 'Device', 'Name', sys=True),
        Field('BuildId', str, 'Device', 'Build ID', sys=True, ro=True),
        Field('ReleaseVersion', str, 'Device', 'Software', sys=True, ro=True),
        Field('AtemId', int, 'SDI Camera Control', 'ATEM Camera ID'),
        Field('SdiLevelAEnable', int, 'SDI Output', '3G SDI Output', mapping={
            0xff: 'Level A',
            0x00: 'Level B',
        }),
        Field('HdmiClampEnable', int, 'HDMI Output', 'Clip signal to', mapping={
            0x00: 'Normal levels (16 - 235)',
            0xff: 'Illegal levels (0 - 255)',
        }),
        Field('HdmiTxCh34Swap', int, 'HDMI Audio', 'For 5.1 surround use', mapping={
            0x00: 'SMPTE standard (L, R, C, LFE, Ls, Rs)',
            0xff: 'Consumer standard (L, R, LFE, C, Ls, Rs)',
        }),
        Field('LutSelection', int, 'LUTs', 'Lut Selection', mapping={
            0x00: 'False',
            0xff: 'True',
        }),
        Field('LutSdiOutEnable', int, 'LUTs', 'SDI Out', mapping={
            0x00: 'False',
            0xff: 'True',
        }),
        Field('LutHdmiOutEnable', int, 'LUTs', 'HDMI Out', mapping={
            0x00: 'False',
            0xff: 'True',
        }),
        Field('LutName', str, 'LUTs', 'LUT name', ro=True),
    ]
