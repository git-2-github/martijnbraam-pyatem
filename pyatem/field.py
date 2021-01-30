import struct


class FieldBase:
    def _get_string(self, raw):
        return raw.split(b'\x00')[0].decode()


class FirmwareVersionField(FieldBase):
    """
    Data from the `_ver` field. This stores the major/minor firmware version numbers

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Major version
    2      2    u16    Minor version
    ====== ==== ====== ===========

    After parsing:

    :ivar major: Major firmware version
    :ivar minor: Minor firmware version
    """

    def __init__(self, raw):
        """
        :param raw:
        """
        self.raw = raw
        self.major, self.minor = struct.unpack('>HH', raw)
        self.version = "{}.{}".format(self.major, self.minor)

    def __repr__(self):
        return '<firmware-version {}>'.format(self.version)


class ProductNameField(FieldBase):
    """
    Data from the `_pin` field. This stores the product name of the mixer

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      44   char[] Product name
    ====== ==== ====== ===========

    After parsing:

    :ivar name: User friendly product name
    """

    def __init__(self, raw):
        self.raw = raw
        self.name = self._get_string(raw)

    def __repr__(self):
        return '<product-name {}>'.format(self.name)


class MixerEffectConfigField(FieldBase):
    """
    Data from the `_MeC` field. This stores basic info about the M/E units.

    The mixer will send multiple fields, one for each M/E unit.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    u8     Number of keyers on this M/E
    2      2    ?      unknown
    ====== ==== ====== ===========

    After parsing:

    :ivar name: User friendly product name
    """

    def __init__(self, raw):
        self.raw = raw
        self.me, self.keyers = struct.unpack('>2B2x', raw)

    def __repr__(self):
        return '<mixer-effect-config m/e {}: keyers={}>'.format(self.me, self.keyers)


class MediaplayerSlotsField(FieldBase):
    """
    Data from the `_mpl` field. This stores basic info about the mediaplayer slots.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Number of still slots
    1      1    u8     Number of clip slots
    2      2    ?      unknown
    ====== ==== ====== ===========

    After parsing:

    :ivar name: User friendly product name
    """

    def __init__(self, raw):
        self.raw = raw
        self.stills, self.clips = struct.unpack('>2B2x', raw)

    def __repr__(self):
        return '<mediaplayer-slots: stills={} clips={}>'.format(self.stills, self.clips)


class VideoModeField(FieldBase):
    """
    Data from the `VidM` field. This sets the video standard the mixer operates on internally.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Video mode
    1      3    ?      unknown
    ====== ==== ====== ===========

    The `Video mode` is an enum of these values:

    === ==========
    Key Video mode
    === ==========
    0   NTSC (525i59.94)
    1   PAL (625i50)
    2   NTSC widescreen (525i59.94)
    3   PAL widescreen (625i50)
    4   720p50
    5   720p59.94
    6   1080i50
    7   1080i59.94
    8   1080p23.98
    9   1080p24
    10  1080p25
    11  1080p29.97
    12  1080p50
    13  1080p59.94
    14  4k23.98
    15  4k24
    16  4k25
    17  4k29.97
    26  1080p30
    27  1080p60
    === ==========

    After parsing:

    :ivar mode: mode number
    :ivar resolution: vertical resolution of the mode
    :ivar interlaced: the current mode is interlaced
    :ivar rate: refresh rate of the mode
    """

    def __init__(self, raw):
        self.raw = raw
        self.mode, = struct.unpack('>1B3x', raw)

        modes = {
            0: (525, True, 59.94),
            1: (625, True, 50),
            2: (525, True, 59.94),
            3: (625, True, 50),
            4: (720, False, 50),
            5: (720, False, 59.94),
            6: (1080, True, 50),
            7: (1080, True, 59.94),
            8: (1080, False, 23.98),
            9: (1080, False, 24),
            10: (1080, False, 25),
            11: (1080, False, 29.97),
            12: (1080, False, 50),
            13: (1080, False, 59.94),
            14: (2160, False, 23.98),
            15: (2160, False, 24),
            16: (2160, False, 25),
            17: (2160, False, 29.97),
            26: (1080, False, 30),
            27: (1080, False, 60),
        }

        self.resolution = modes[self.mode][0]
        self.interlaced = modes[self.mode][1]
        self.rate = modes[self.mode][2]

    def __repr__(self):
        pi = 'p'
        if self.interlaced:
            pi = 'i'

        return '<video-mode: mode={}: {}{}{}>'.format(self.mode, self.resolution, pi, self.rate)


class InputPropertiesField(FieldBase):
    """
    Data from the `InPr` field. This stores information about all the internal and external inputs.

    The mixer will send multiple fields, one for each input

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Source index
    2      20   char[] Long name
    22     4    char[] Short name for button
    26     1    u8     Source category 0=input 1=output
    27     1    u8     ? bitfield
    28     1    u8     same as byte 26
    29     1    u8     port
    30     1    u8     same as byte 26
    31     1    u8     same as byte 29
    32     1    u8     port type
    33     1    u8     bitfield
    34     1    u8     bitfield
    35     1    u8     direction
    ====== ==== ====== ===========

    ===== =========
    value port type
    ===== =========
    0     external
    1     black
    2     color bars
    3     color generator
    4     media player
    5     media player key
    6     supersource
    7     passthrough
    128   M/E output
    129   AUX output
    ===== =========

    ===== ===============
    value available ports
    ===== ===============
    0     SDI
    1     HDMI
    2     Component
    3     Composite
    4     S/Video
    ===== ===============

    ===== =============
    value selected port
    ===== =============
    0     internal
    1     SDI
    2     HDMI
    3     Composite
    4     Component
    5     S/Video
    ===== =============

    After parsing:

    :ivar index: Source index
    :ivar name: Long name
    :ivar short_name: Short name for button
    :ivar available_aux: Source can be routed to AUX
    :ivar available_multiview: Source can be routed to multiview
    :ivar available_supersource_art: Source can be routed to supersource
    :ivar available_supersource_box: Source can be routed to supersource
    :ivar available_key_source: Source can be used as keyer key source
    :ivar available_me1: Source can be routed to M/E 1
    :ivar available_me2: Source can be routed to M/E 2
    """

    def __init__(self, raw):
        self.raw = raw
        fields = struct.unpack('>H 20s 4s 10B', raw)
        self.index = fields[0]
        self.name = self._get_string(fields[1])
        self.short_name = self._get_string(fields[2])
        self.source_category = fields[3]
        self.source_ports = fields[6]

        self.available_aux = fields[11] & (1 << 0) != 0
        self.available_multiview = fields[11] & (1 << 1) != 0
        self.available_supersource_art = fields[11] & (1 << 2) != 0
        self.available_supersource_box = fields[11] & (1 << 3) != 0
        self.available_key_source = fields[11] & (1 << 4) != 0

        self.available_me1 = fields[12] & (1 << 0) != 0
        self.available_me2 = fields[12] & (1 << 1) != 0

    def __repr__(self):
        return '<input-properties: index={} name={} button={}>'.format(self.index, self.name, self.short_name)


class ProgramBusInputField(FieldBase):
    """
    Data from the `PrgI` field. This represents the active channel on the program bus of the specific M/E unit.

    The mixer will send a field for every M/E unit in the mixer.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    ?      unknown
    2      2    u16    Source index
    ====== ==== ====== ===========

    After parsing:

    :ivar index: M/E index in the mixer
    :ivar source: Input source index, refers to an InputPropertiesField index
    """

    def __init__(self, raw):
        self.raw = raw
        self.index, self.source = struct.unpack('>BxH', raw)

    def __repr__(self):
        return '<program-bus-input: me={} source={}>'.format(self.index, self.source)


class PreviewBusInputField(FieldBase):
    """
    Data from the `PrvI` field. This represents the active channel on the preview bus of the specific M/E unit.

    The mixer will send a field for every M/E unit in the mixer.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    ?      unknown
    2      2    u16    Source index
    4      1    u8     1 if preview is mixed in program during a transition
    5      3    ?      unknown
    ====== ==== ====== ===========

    After parsing:

    :ivar index: M/E index in the mixer
    :ivar source: Input source index, refers to an InputPropertiesField index
    :ivar in_program: Preview source is mixed into progam
    """

    def __init__(self, raw):
        self.raw = raw
        self.index, self.source, in_program = struct.unpack('>B x H B 3x', raw)
        self.in_program = in_program == 1

    def __repr__(self):
        in_program = ''
        if self.in_program:
            in_program = ' in-program'
        return '<preview-bus-input: me={} source={}{}>'.format(self.index, self.source, in_program)
