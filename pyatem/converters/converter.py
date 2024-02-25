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


class TeranexMiniConverterHdmiToSdi12G(WValueProtoConverter):
    PRODUCT = 0xBDAF
    NAME = "Blackmagic design Teranex Mini Converter HDMI to SDI 12G"
    NAME_FIELD = 0x48

    # Add more fields!
    FIELDS = [
        # Length of name may technically be a byte or two longer than 61...
        Field('name', (0x0048, 61), str, "Device", "Name"),
        # Some fields seem to be embedded within a wValue of 0x00a8 or 0x00aa with different data fragments
        # This works, in that identify triggers, but it doesn't seem to clear when identify times out
        Field('identify', (0x00aa, 1), int, "Device", "Identify Device", mapping={
            0x02: ('on', 'On'),
            0x00: ('off', 'Off'),
        }),
        # Maybe also 0xd0, or does one actually do left and one right?
        Field('analog-embedding', (0x00c0, 1), int, "Audio", "Analog Embedding", mapping={
            0x08: ('12', '1 & 2'),
            0x09: ('34', '3 & 4'),
            0x0a: ('56', '5 & 6'),
            0x0b: ('78', '7 & 8'),
            0x0c: ('910', '9 & 10'),
            0x0d: ('1112', '11 & 12'),
            0x0e: ('1314', '13 & 14'),
            0x0f: ('1516', '15 & 16'),
        }),
        # Maybe also 0xd1, or does one actually do out 1 and one out 2?
        Field('aesebu-embedding', (0x00c1, 1), int, "Audio", "AES/EBU Embedding", mapping={
            0x03: ('14', '1 - 4'),
            0x04: ('58', '5 - 8'),
            0x05: ('912', '9 - 12'),
            0x06: ('1316', '13 - 16'),
        }),
        Field('conversion', (0x00b3, 1), int, "Video Processing", "Conversion", mapping={
            0x00: ('auto', 'Auto'),
            0x01: ('hd', 'Force to HD'),
            0x02: ('uhd', 'Force to Ultra HD'),
        }),
        Field('sdi-level', (0x00b8, 1), int, "Video Processing", "3G Output", mapping={
            0x04: ('a', 'Level A'),
            0x00: ('b', 'Level B'),
        }),
        Field('convert-60p-5994i', (0x00b7, 1), int, "Video Processing", "Convert 60p to 59.95i", mapping={
            0x30: ('yes', 'Enabled'),
            0x10: ('no', 'Disabled'),
        }),
        # In the config tool, XLR input format and sample rate converter are separate settings
        # I suspect it's really a bit mask, probably a bit like as follows:
        # Bit 0 (LSB) - Audio/Timecode
        # Bit 1       - Analog/Digital?
        # Bit 2       - SRC (enabled for analog too)
        # There is unfortunately some complicated interaction with this and 0x00dc  when setting these
        Field('xlr-input', (0x00be, 1), int, "Audio", "XLR Input", mapping={
            0x06: ('analog', 'Analog'),
            0x00: ('aesebu', 'AES/EBU (No Sample Rate Converter)'),
            0x04: ('aesebusrc', 'AES/EBU (Sample Rate Converter)'),
            0x02: ('hdmi', 'HDMI'),
            0x03: ('timecodehdmi', 'Timecode (Right) with HDMI'),
            0x07: ('timecodexlr', 'Timecode (Right) with XLR'),
        }),
        Field('audio-input', (0x00dc, 1), int, "Audio", "Audio Input", mapping={
            0x00: ('xlr', 'XLR'),
            0x02: ('hdmi', 'HDMI'),
        }),
        Field('audio1', (0x00e0, 1), int, "Audio", "Analog In 1", mapping='dB'),
        Field('audio2', (0x00e1, 1), int, "Audio", "Analog In 2", mapping='dB'),
        Field('aes12', (0x00e2, 1), int, "Audio", "AES/EBU In 1 & 2", mapping='dB'),
        Field('aes34', (0x00e3, 1), int, "Audio", "AES/EBU In 3 & 4", mapping='dB'),
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
        # In the config tool, XLR output format and 5.1 surround format are separate settings
        # I suspect it's really a bit mask, probably as follows:
        # Bit 0 (LSB) - Analog/Digital
        # Bit 1       - Timecode/Audio
        # Bit 2       - Unknown/N/A?
        # Bit 3       - Consumer/SMPTE 5.1
        Field('xlr-output', (0x00be, 1), int, "Audio", "XLR Output", mapping={
            0x02: ('smpteanalog', 'Analog & SMPTE 5.1 (L, R, C, LFE, Ls, Rs)'),
            0x00: ('smpteaesebu', 'AES/EBU & SMPTE 5.1 (L, R, C, LFE, Ls, Rs)'),
            0x03: ('smptetimecode', 'Timecode (Right) & SMPTE 5.1 (L, R, C, LFE, Ls, Rs)'),
            0x0a: ('consumeranalog', 'Analog & Consumer 5.1 (L, R, LFE, C, Ls, Rs)'),
            0x08: ('consumeraesebu', 'AES/EBU & Consumer 5.1 (L, R, LFE, C, Ls, Rs)'),
            0x0b: ('consumertimecode', 'Timecode (Right) & Consumer 5.1 (L, R, LFE, C, Ls, Rs)'),
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


class TeranexMiniConverter12GSdiToQuadSdi(WValueProtoConverter):
    PRODUCT = 0xBDC0
    NAME = "Blackmagic design Teranex Mini Converter 12G-SDI to Quad SDI"
    NAME_FIELD = 0x48

    FIELDS = [
        # Length of name may technically be a byte or two longer than 61...
        Field('name', (0x0048, 61), str, "Device", "Name"),
        # This works, in that identify triggers, but it doesn't seem to clear when identify times out
        Field('identify', (0x00aa, 1), int, "Device", "Identify Device", mapping={
            0x02: ('on', 'On'),
            0x00: ('off', 'Off'),
        }),
        Field('sdi-level', (0x00b8, 1), int, "Processing", "SDI Output", mapping={
            0x00: ('sl3gb', 'Single Link - 3G Level B'),
            0x01: ('dl3gb', 'Dual Link - 3G Level B'),
            0x02: ('ql3gb', 'Quad Link - 3G Level A'),
            0x03: ('qhds3gb', 'Quad HD Split - 3G Level B'),
            0x04: ('sl3ga', 'Single Link - 3G Level A'),
            0x05: ('dl3ga', 'Dual Link - 3G Level A'),
            0x06: ('ql3ga', 'Quad Link - 3G Level A'),
            0x07: ('qhds3ga', 'Quad HD Split - 3G Level A'),
        }),
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


class TeranexMiniConverterQuadSdiTo12GSdi(WValueProtoConverter):
    PRODUCT = 0xBDC1
    NAME = "Blackmagic design Teranex Mini Converter Quad SDI to 12G-SDI"
    NAME_FIELD = 0x48

    FIELDS = [
        # Length of name may technically be a byte or two longer than 61...
        Field('name', (0x0048, 61), str, "Device", "Name"),
        Field('sdi-level', (0x00b8, 1), int, "Processing", "3G SDI Output", mapping={
            0x04: ('a', 'Level A'),
            0x00: ('b', 'Level B'),
        }),
        # This works, in that identify triggers, but it doesn't seem to clear when identify times out
        Field('identify', (0x00aa, 1), int, "Device", "Identify Device", mapping={
            0x02: ('on', 'On'),
            0x00: ('off', 'Off'),
        }),
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


class MultiView4(WValueProtoConverter):
    PRODUCT = 0xBDD2
    NAME = "Blackmagic design MultiView 4"
    NAME_FIELD = 0x50

    # Add more fields!
    FIELDS = [
        # Confirm name length
        # Length of name may technically be a byte or two longer than 61...
        Field('name', (0x0050, 61), str, "Device", "Name"),
        # No identify on this unit
        # No DHCP or current address on this unit
        Field('address', (0x0094, 4), ipaddress.IPv4Address, "Network", "Address"),
        Field('netmask', (0x0098, 4), ipaddress.IPv4Address, "Network", "Netmask"),
        Field('gateway', (0x009c, 4), ipaddress.IPv4Address, "Network", "Gateway"),
        Field('video-format', (0x00d2, 1), int, "Video Output", "Video Format", mapping={
            0x04: ('1080i50', '1080i50'),
            0x0c: ('1080i5994', '1080i59.94'),
            0x14: ('2160p25', '2160p25'),
            0x1c: ('2160p2997', '2160p29.97'),
        }),
        # SDI Level not available via USB!
        Field('sd-aspect', (0x00d6, 1), int, "Video Output", "SD aspect ratio", mapping={
            0x01: ('169', 'Output as 16:9'),
            0x00: ('43', 'Output as 4:3'),
        }),
        Field('screen-layout', (0x00da, 1), int, "Screen Layout", "Views", mapping={
            0x01: ('solo', 'Solo'),
            0x00: ('2x2', '2 x 2'),
        }),
        Field('borders', (0x00d7, 1), int, 'Overlay Displays', 'Turn on borders', mapping={
            0x01: ('yes', 'Enable'),
            0x00: ('no', 'Disable'),
        }),
        Field('labels', (0x00d8, 1), int, 'Overlay Displays', 'Turn on labels', mapping={
            0x01: ('yes', 'Enable'),
            0x00: ('no', 'Disable'),
        }),
        Field('audio-meters', (0x00d5, 1), int, 'Overlay Displays', 'Turn on audio meters', mapping={
            0x01: ('yes', 'Enable'),
            0x00: ('no', 'Disable'),
        }),
        Field('sdi-tally', (0x00d9, 1), int, 'Overlay Displays', 'Turn on SDI tally', mapping={
            0x01: ('yes', 'Enable'),
            0x00: ('no', 'Disable'),
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
