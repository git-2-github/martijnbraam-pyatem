# Copyright 2022 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import ipaddress

from pyatem.converters.protocol import LabelProtoConverter, Field, WValueProtoConverter, WIndexProtoConverter, AtemLegacyProtocol


class MicroConverterSdiHdmi12G(LabelProtoConverter):
    PRODUCT = 0xbe77
    NAME = "Blackmagic design Micro Converter SDI to HDMI 12G"

    FIELDS = [
        Field('name', 'DeviceName', str, 'Device', 'Name', sys=True),
        Field(None, 'BuildId', str, 'Device', 'Build ID', sys=True, ro=True),
        Field(None, 'ReleaseVersion', str, 'Device', 'Software', sys=True, ro=True),
        Field('sdi-level', 'SdiLevelAEnable', int, 'SDI Output', '3G SDI Output', mapping={
            0xff: ('a', 'Level A'),
            0x00: ('b', 'Level B'),
        }),
        Field('hdmi-clamp', 'HdmiClampEnable', int, 'HDMI Output', 'Clip signal to', mapping={
            0x00: ('yes', 'Normal levels (16 - 235)'),
            0xff: ('no', 'Illegal levels (0 - 255)'),
        }),
        Field('hdmi-ch34-swap', 'HdmiTxCh34Swap', int, 'HDMI Audio', 'For 5.1 surround use', mapping={
            0x00: ('smpte', 'SMPTE standard'),
            0xff: ('consumer', 'Consumer standard'),
        }),
        Field('lut-hdmi', 'LutSelection', int, 'LUTs', 'LUT on HDMI', mapping={
            0x00: ('no', 'Enabled'),
            0xff: ('yes', 'Disabled'),
        }),
        Field('lut-loop', 'LutLoopEnable', int, 'LUTs', 'LUT on SDI loop', mapping={
            0x00: ('no', 'Disabled'),
            0xff: ('yes', 'Enabled'),
        }),
        Field(None, 'LutName', str, 'LUTs', 'LUT name', ro=True),
        Field('lut', 'LutData', open, 'LUTs', 'LUT'),
    ]


class MicroConverterBiDirectional12G(LabelProtoConverter):
    PRODUCT = 0xbe89
    NAME = "Blackmagic design Micro Converter BiDirectional SDI/HDMI 12G"

    FIELDS = [
        Field('name', 'DeviceName', str, 'Device', 'Name', sys=True),
        Field(None, 'BuildId', str, 'Device', 'Build ID', sys=True, ro=True),
        Field(None, 'ReleaseVersion', str, 'Device', 'Software', sys=True, ro=True),
        Field('camera-id', 'AtemId', int, 'SDI Camera Control', 'ATEM Camera ID'),
        Field('sdi-level', 'SdiLevelAEnable', int, 'SDI Output', '3G SDI Output', mapping={
            0xff: ('a', 'Level A'),
            0x00: ('b', 'Level B'),
        }),
        Field('hdmi-clamp', 'HdmiClampEnable', int, 'HDMI Output', 'Clip signal to', mapping={
            0x00: ('yes', 'Normal levels (16 - 235)'),
            0xff: ('no', 'Illegal levels (0 - 255)'),
        }),
        Field('hdmi-ch34-swap', 'HdmiTxCh34Swap', int, 'HDMI Audio', 'For 5.1 surround use', mapping={
            0x00: ('smpte', 'SMPTE standard'),
            0xff: ('consumer', 'Consumer standard'),
        }),
        Field('lut-enable', 'LutSelection', int, 'LUTs', 'Lut Selection', mapping={
            0x00: ('yes', 'False'),
            0xff: ('no', 'True'),
        }),
        Field('lut-sdi', 'LutSdiOutEnable', int, 'LUTs', 'SDI Out', mapping={
            0x00: ('yes', 'False'),
            0xff: ('no', 'True'),
        }),
        Field('lut-hdmi', 'LutHdmiOutEnable', int, 'LUTs', 'HDMI Out', mapping={
            0x00: ('yes', 'False'),
            0xff: ('no', 'True'),
        }),
        Field(None, 'LutName', str, 'LUTs', 'LUT name', ro=True),
        Field('lut', 'LutData', open, 'LUTs', 'LUT'),
    ]


class MicroConverterSdiHdmi3G(WValueProtoConverter):
    PRODUCT = 0xBE90
    NAME = "Blackmagic design Micro Converter SDI to HDMI 3G"

    FIELDS = [
        Field('name', (0x00c0, 64), str, "Device", "Name"),
        Field('hdmi-clip', (0x0100, 1), int, "HDMI Output", "Clip signal to", mapping={
            0x01: ('yes', 'Normal levels (16 - 235)'),
            0x00: ('no', 'Illegal levels (0 - 255)'),
        }),
        Field('hdmi-ch34-swap', (0x0102, 1), int, 'HDMI Audio', 'For 5.1 surround use', mapping={
            0x00: ('smpte', 'SMPTE standard'),
            0x01: ('consumer', 'Consumer standard'),
        }),
        Field(None, (0x0310, 64), str, 'LUTs', 'LUT name', ro=True),
        Field('lut-enable', (0x0300, 1), int, 'LUTs', 'Enable 3D LUT', mapping={
            0x00: ('yes', 'Enable'),
            0xff: ('no', 'Disable'),
        }),
        Field('lut-loop', (0x0301, 1), int, 'LUTs', 'LUT on loop output', mapping={
            0x01: ('yes', 'Enable'),
            0x00: ('no', 'Disable'),
        }),
        Field('lut', 'LUT', open, 'LUTs', 'LUT'),
    ]


class MicroConverterHdmiSdi3G(WValueProtoConverter):
    PRODUCT = 0xBE91
    NAME = "Blackmagic design Micro Converter HDMI to SDI 3G"

    FIELDS = [
        Field('name', (0x00c0, 64), str, "Device", "Name"),
        Field('sdi-level', (0x0200, 1), int, "SDI Output", "3G SDI Output", mapping={
            0x01: ('a', 'Level A'),
            0x00: ('b', 'Level B'),
        }),
        Field(None, (0x0310, 64), str, 'LUTs', 'LUT name', ro=True),
        Field('lut-enable', (0x0300, 1), int, 'LUTs', 'Enable 3D LUT', mapping={
            0x00: ('yes', 'Enabled'),
            0xff: ('no', 'Disabled'),
        }),
        Field('lut', (0x3f000000, 0x01000000), open, 'LUTs', 'LUT'),
    ]


class MicroConverterSdiHdmi6G(WValueProtoConverter):
    PRODUCT = 0xBDF2
    NAME = "Blackmagic design Mini Converter SDI to HDMI 6G"
    HAS_NAME = False
    NEEDS_POWER = True
    LUT_SIZE = 33

    FIELDS = [
        Field('hdmi-clip', (0x0038, 4), int, "HDMI Output", "Clip signal to", mapping={
            0x00: ('yes', 'Normal levels (16 - 235)'),
            0x01: ('no', 'Illegal levels (0 - 255)'),
        }),
        Field(None, (0x0200, 40), str, 'Processing', 'LUT 1 name', ro=True),
        Field('lut1', (0x38000000, 0x03000000), open, 'Processing', 'LUT 1'),
        Field(None, (0x0300, 40), str, 'Processing', 'LUT 2 name', ro=True),
        Field('lut2', (0x3b000000, 0x03000000), open, 'Processing', 'LUT 2'),
        Field('audio1', (0x0014, 4), int, "Audio", "Ch 1", mapping='dB'),
        Field('audio2', (0x0018, 4), int, "Audio", "Ch 2", mapping='dB'),
        Field('aes', (0x0024, 4), int, "Audio", "AES/EBU", mapping='dB'),
    ]


class MicroConverterSdiHdmi(WValueProtoConverter):
    PRODUCT = 0xBDC5
    NAME = "Blackmagic design Micro Converter SDI to HDMI"

    FIELDS = [
        Field('hdmi-clip', (0x0038, 1), int, "Processing", "Clip video output to", mapping={
            0x00: ('yes', 'Legal levels (16 - 235)'),
            0x01: ('no', 'Illegal levels (0 - 255)'),
        }),
    ]


class MicroConverterBiDirectionalSdiHdmi(WValueProtoConverter):
    PRODUCT = 0xBE0C
    NAME = "Blackmagic design Micro Converter BiDirectional SDI/HDMI"

    FIELDS = [
        Field('hdmi-clip', (0x0038, 1), int, "Processing", "Clip HDMI video output to", mapping={
            0x00: ('yes', 'Legal levels (16 - 235)'),
            0x01: ('no', 'Illegal levels (0 - 255)'),
        }),
        Field('sdi-level', (0x003c, 1), int, "Processing", "3G SDI Output", mapping={
            0x01: ('a', 'Level A'),
            0x00: ('b', 'Level B'),
        }),
    ]


class MiniConverterSdiAudio(WIndexProtoConverter):
    PRODUCT = 0xBD28
    NAME = "Blackmagic design Mini Converter SDI to Audio"
    HAS_NAME = False
    NEEDS_POWER = True


    FIELDS = [
        Field('audio1', (0x0500, 1), int, 'Audio Output Levels', 'Ch 1', mapping='dB'),
        Field('audio2', (0x0600, 1), int, 'Audio Output Levels', 'Ch 2', mapping='dB'),
        Field('audio3', (0x0700, 1), int, 'Audio Output Levels', 'Ch 3', mapping='dB'),
        Field('audio4', (0x0800, 1), int, 'Audio Output Levels', 'Ch 4', mapping='dB'),
        Field('aes', (0x0900, 1), int, 'Audio Output Levels', 'AES/EBU', mapping='dB'),
    ]


class TeranexAV(WIndexProtoConverter):
    PRODUCT = 0xBDD8
    NAME = "Blackmagic design Teranex AV"
    HAS_NAME = False

    # Check/add fields
    FIELDS = [
    ]


class TeranexMiniConverterOpticalToHdmi12G(WValueProtoConverter):
    PRODUCT = 0xBDB4
    NAME = "Blackmagic design Teranex Mini Converter Optical to HDMI 12G"
    NAME_FIELD = 0x48

    # Add more fields!
    FIELDS = [
        # Length of name may technically be a byte or two longer than 61...
        Field('name', (0x0048, 61), str, "Device", "Name"),
        # Some fields seem to be embedded within a wValue of 0x00a8 or 0x00aa with different data fragments
        #Field('identify', (0x00, 1), bool, "Device", "Identify Device"),
        Field('video-input', (0x00ba, 1), int, "Video", "Video Input", mapping={
            0x00: ('sdi', 'SDI'),
            0x01: ('auto', 'Auto'),
        }),
        Field('hdmi-clip', (0x00b7, 1), int, "Video", "Clip HDMI video output to", mapping={
            0x10: ('yes', 'Legal levels (16 - 235)'),
            0x00: ('no', 'Illegal levels (0 - 255)'),
        }),
        Field('instant-lock', (0x00b9, 1), int, "Video", "HDMI instant lock", mapping={
            0x01: ('yes', 'Enable'),
            0x00: ('no', 'Disable'),
        }),
        Field('xlr-output', (0x00be, 1), int, "Audio", "XLR Output", mapping={
            0x0a: ('analog', 'Analog'),
            0x08: ('aesebu', 'AES/EBU'),
            0x0b: ('timecode', 'Timecode (Right)'),
        }),
        # Maybe also 0xc0, or does one actually do left and one right?
        Field('analog-de-embedding', (0x00d0, 1), int, "Audio", "Analog De-embedding", mapping={
            0x08: ('12', '1 & 2'),
            0x09: ('34', '3 & 4'),
            0x0a: ('56', '5 & 6'),
            0x0b: ('78', '7 & 8'),
            0x0c: ('910', '9 & 10'),
            0x0d: ('1112', '11 & 12'),
            0x0e: ('1314', '13 & 14'),
            0x0f: ('1516', '15 & 16'),
        }),
        # Maybe also 0xc1, or does one actually do out 1 and one out 2?
        Field('aesebu-de-embedding', (0x00d1, 1), int, "Audio", "AES/EBU De-embedding", mapping={
            0x03: ('14', '1 - 4'),
            0x04: ('58', '5 - 8'),
            0x05: ('912', '9 - 12'),
            0x06: ('1316', '13 - 16'),
        }),
        Field('audio1', (0x00e0, 1), int, "Audio", "Analog Out 1", mapping='dB'),
        Field('audio2', (0x00e1, 1), int, "Audio", "Analog Out 2", mapping='dB'),
        Field('aes12', (0x00e2, 1), int, "Audio", "AES/EBU Out 1 & 2", mapping='dB'),
        Field('aes34', (0x00e3, 1), int, "Audio", "AES/EBU Out 3 & 4", mapping='dB'),
        #Field('surround-use', (0x00, 1), int, "Audio", "5.1 surround use", mapping={
        #    0x0: ('smpte', 'SMPTE standard (L, R, C, LFE, Ls, Rs)'),
        #    0x0: ('consumer', 'Consumer standard (L, R, LFE, C, Ls, Rs)'),
        #}),
        Field('dhcp', (0x0087, 1), int, "Network", "IP Setting", mapping={
            0x01: ('dhcp', 'DHCP'),
            0x00: ('static', 'Static IP'),
        }),
        Field('address', (0x0088, 4), ipaddress.IPv4Address, "Network", "Address"),
        Field('netmask', (0x008c, 4), ipaddress.IPv4Address, "Network", "Netmask"),
        Field('gateway', (0x0090, 4), ipaddress.IPv4Address, "Network", "Gateway"),
        # Read only
        Field('dhcpaddress', (0x0094, 4), ipaddress.IPv4Address, "Network", "DHCP Address", ro=True),
        Field('dhcpnetmask', (0x0098, 4), ipaddress.IPv4Address, "Network", "DHCP Netmask", ro=True),
        Field('dhcpgateway', (0x009c, 4), ipaddress.IPv4Address, "Network", "DHCP Gateway", ro=True),
    ]


class AtemProductionStudio4k(AtemLegacyProtocol):
    PRODUCT = 0xBD6E
    NAME = "Blackmagic design ATEM Production Studio 4K"

    FIELDS = [
        Field('name', (0x0048, 32), str, "Device", "Name"),
        Field('address', (0x0020, 4), ipaddress.IPv4Address, "Network", "Address"),
        Field('netmask', (0x0024, 4), ipaddress.IPv4Address, "Network", "Netmask"),
        Field('gateway', (0x0028, 4), ipaddress.IPv4Address, "Network", "Gateway"),
    ]
