# Copyright 2022 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import ipaddress

from pyatem.converters.protocol import LabelProtoConverter, Field, WValueProtoConverter, AtemLegacyProtocol


class MicroConverterBiDirectional12G(LabelProtoConverter):
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
            0x00: 'SMPTE standard',
            0xff: 'Consumer standard',
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


class MicroConverterSdiHdmi3G(WValueProtoConverter):
    PRODUCT = 0xBE90
    NAME = "Blackmagic design Micro Converter SDI to HDMI 3G"

    FIELDS = [
        Field((0x00c0, 64), str, "Device", "Name"),
        Field((0x0100, 1), int, "HDMI Output", "Clip signal to", mapping={
            0x01: 'Normal levels (16 - 235)',
            0x00: 'Illegal levels (0 - 255)',
        }),
        Field((0x0102, 1), int, 'HDMI Audio', 'For 5.1 surround use', mapping={
            0x00: 'SMPTE standard',
            0x01: 'Consumer standard',
        }),
        Field((0x0310, 64), str, 'LUTs', 'LUT name', ro=True),
        Field((0x0300, 1), int, 'LUTs', 'Enable 3D LUT', mapping={
            0x00: 'Enable',
            0xff: 'Disable',
        }),
        Field((0x0301, 1), int, 'LUTs', 'LUT on loop output', mapping={
            0x01: 'Enable',
            0x00: 'Disable',
        }),
        Field('LUT', open, 'LUTs', 'LUT'),
    ]


class MicroConverterHdmiSdi3G(WValueProtoConverter):
    PRODUCT = 0xBE91
    NAME = "Blackmagic design Micro Converter HDMI to SDI 3G"

    FIELDS = [
        Field((0x00c0, 64), str, "Device", "Name"),
        Field((0x0200, 1), int, "SDI Output", "3G SDI Output", mapping={
            0x01: 'Level A',
            0x00: 'Level B',
        }),
        Field((0x0310, 64), str, 'LUTs', 'LUT name', ro=True),
        Field((0x0300, 1), int, 'LUTs', 'Enable 3D LUT', mapping={
            0x00: 'Enable',
            0xff: 'Disable',
        }),
        Field('LUT', open, 'LUTs', 'LUT'),
    ]


class AtemProductionStudio4k(AtemLegacyProtocol):
    PRODUCT = 0xBD6E
    NAME = "Blackmagic design ATEM Production Studio 4K"

    FIELDS = [
        Field((0x0048, 32), str, "Device", "Name"),
        Field((0x0020, 4), ipaddress.IPv4Address, "Network", "Address"),
        Field((0x0024, 4), ipaddress.IPv4Address, "Network", "Netmask"),
        Field((0x0028, 4), ipaddress.IPv4Address, "Network", "Gateway"),
    ]
