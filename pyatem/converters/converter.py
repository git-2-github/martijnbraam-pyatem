# Copyright 2022 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import ipaddress

from pyatem.converters.protocol import LabelProtoConverter, Field, WValueProtoConverter, AtemLegacyProtocol


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


class AtemProductionStudio4k(AtemLegacyProtocol):
    PRODUCT = 0xBD6E
    NAME = "Blackmagic design ATEM Production Studio 4K"

    FIELDS = [
        Field('name', (0x0048, 32), str, "Device", "Name"),
        Field('address', (0x0020, 4), ipaddress.IPv4Address, "Network", "Address"),
        Field('netmask', (0x0024, 4), ipaddress.IPv4Address, "Network", "Netmask"),
        Field('gateway', (0x0028, 4), ipaddress.IPv4Address, "Network", "Gateway"),
    ]
