import colorsys
import struct
import math

from pyatem.hexdump import hexdump


class FieldBase:
    def _get_string(self, raw):
        return raw.split(b'\x00')[0].decode()

    def make_packet(self):
        header = struct.pack('!H2x 4s', len(self.raw) + 8, self.__class__.CODE.encode())
        return header + self.raw


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

    CODE = "_ver"

    def __init__(self, raw):
        """
        :param raw:
        """
        self.raw = raw
        self.major, self.minor = struct.unpack('>HH', raw)
        self.version = "{}.{}".format(self.major, self.minor)

    def __repr__(self):
        return '<firmware-version {}>'.format(self.version)


class TimeField(FieldBase):
    """
    Data from the `Time` field. This contains the value of the internal clock of the hardware.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Hours
    1      1    u8     Minutes
    2      1    u8     Seconds
    3      1    u8     Frames
    4      1    u8     Is dropframe
    5      3    ?      unknown
    ====== ==== ====== ===========

    After parsing:

    :ivar hours: Timecode hour field
    :ivar minutes: Timecode minute field
    :ivar seconds: Timecode seconds field
    :ivar frames: Timecode frames field
    :ivar dropframe: Is dropframe
    """
    CODE = "Time"

    def __init__(self, raw):
        self.raw = raw
        self.hours, self.minutes, self.seconds, self.frames, self.dropframe = struct.unpack('>BBBB?3x', raw)

    def total_seconds(self):
        return self.seconds + (60 * self.minutes) + (60 * 60 * self.hours)

    def __repr__(self):
        return '<time {}>'.format(f'{self.hours}:{self.minutes}:{self.seconds}:{self.frames}')


class TimeConfigField(FieldBase):
    """
    Data from the `TCCc` field. This contains the freerun/time of day setting for the timecode mode.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mode [0=freerun, 1=time-of-day]
    1      3    ?      unknown
    ====== ==== ====== ===========

    After parsing:

    :ivar mode: Timecode mode
    """
    CODE = "TCCc"

    def __init__(self, raw):
        self.raw = raw
        self.mode = struct.unpack('>Bxxx', raw)

    def __repr__(self):
        return '<time-config mode={}>'.format(self.mode)


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

    CODE = "_pin"

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

    :ivar index: 0-based M/E index
    :ivar keyers: Number of upstream keyers on this M/E
    """

    CODE = "_MeC"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.keyers = struct.unpack('>2B2x', raw)

    def __repr__(self):
        return '<mixer-effect-config m/e {}: keyers={}>'.format(self.index, self.keyers)


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

    :ivar stills: Number of still slots
    :ivar clips: Number of clip slots
    """

    CODE = "_mpl"

    def __init__(self, raw):
        self.raw = raw
        self.stills, self.clips = struct.unpack('>2B2x', raw)

    def __repr__(self):
        return '<mediaplayer-slots: stills={} clips={}>'.format(self.stills, self.clips)


class MediaplayerSelectedField(FieldBase):
    """
    Data from the `MPCE` field. This defines what media from the media pool is loaded in a specific media player.
    There is one MPCE field per mediaplayer in the hardware.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mediaplayer index, 0-indexed
    1      1    u8     Source type, 1=still, 2=clip
    2      1    u8     Source index, 0-indexed
    3      1    ?      unknown
    ====== ==== ====== ===========

    After parsing:

    :ivar index: Mediaplayer index
    :ivar source_type: 1 for still, 2 for clip
    :ivar slot: Source index
    """

    CODE = "MPCE"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.source_type, self.slot = struct.unpack('>BBBx', raw)

    def __repr__(self):
        return '<mediaplayer-selected: index={} type={} slot={}>'.format(self.index, self.source_type, self.slot)


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
    18  4k50
    19  4k59.94
    20  8k23.98
    21  8k24
    22  8k25
    23  8k29.97
    24  8k50
    25  8k59.94
    26  1080p30
    27  1080p60
    === ==========

    After parsing:

    :ivar mode: mode number
    :ivar resolution: vertical resolution of the mode
    :ivar interlaced: the current mode is interlaced
    :ivar rate: refresh rate of the mode
    """

    CODE = "VidM"

    def __init__(self, raw):
        self.raw = raw
        self.mode, = struct.unpack('>1B3x', raw)

        # Resolution, Interlaced, Rate, Widescreen
        modes = {
            0: (525, True, 59.94, False),
            1: (625, True, 50, False),
            2: (525, True, 59.94, True),
            3: (625, True, 50, True),
            4: (720, False, 50, True),
            5: (720, False, 59.94, True),
            6: (1080, True, 50, True),
            7: (1080, True, 59.94, True),
            8: (1080, False, 23.98, True),
            9: (1080, False, 24, True),
            10: (1080, False, 25, True),
            11: (1080, False, 29.97, True),
            12: (1080, False, 50, True),
            13: (1080, False, 59.94, True),
            14: (2160, False, 23.98, True),
            15: (2160, False, 24, True),
            16: (2160, False, 25, True),
            17: (2160, False, 29.97, True),
            18: (2160, False, 50, True),
            19: (2160, False, 59.94, True),
            20: (4320, False, 23.98, True),
            21: (4320, False, 24, True),
            22: (4320, False, 25, True),
            23: (4320, False, 29.97, True),
            24: (4320, False, 50, True),
            25: (4320, False, 59.94, True),
            26: (1080, False, 30, True),
            27: (1080, False, 60, True),
        }

        if self.mode in modes:
            self.resolution = modes[self.mode][0]
            self.interlaced = modes[self.mode][1]
            self.rate = modes[self.mode][2]
            self.widescreen = modes[self.mode][3]

    def get_label(self):
        if self.resolution is None:
            return 'unknown [{}]'.format(self.mode)

        pi = 'p'
        if self.interlaced:
            pi = 'i'
        aspect = ''
        if self.resolution < 720:
            if self.widescreen:
                aspect = ' 16:9'
            else:
                aspect = ' 4:3'
        return '{}{}{}{}'.format(self.resolution, pi, self.rate, aspect)

    def get_pixels(self):
        w, h = self.get_resolution()
        return w * h

    def get_resolution(self):
        lut = {
            525: (720, 480),
            625: (720, 576),
            720: (1280, 720),
            1080: (1920, 1080),
            2160: (3840, 2160),
            4320: (7680, 4320),
        }
        return lut[self.resolution]

    def __repr__(self):
        return '<video-mode: mode={}: {}>'.format(self.mode, self.get_label())


class VideoModeCapabilityField(FieldBase):
    """
    Data from the `_VMC` field. This describes all the video modes supported by the hardware and
    the associated multiview and downconvert modes.

    The first 2 bytes is the number of modes supported, then there's a 13 byte block that's repeated for every
    mode that has the mode number, the possible multiview modes in this mode and the possible downconvert modes.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Number of video modes
    2      2    ?      padding
    4      1    u8     Video mode N
    5      3    ?      padding
    8      4    u32    Multiview modes bitfield
    12     4    u32    Downconvert modes bitfield
    13     1    bool   Requires reconfiguration
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
    18  4k50
    19  4k59.94
    20  8k23.98
    21  8k24
    22  8k25
    23  8k29.97
    24  8k50
    25  8k59.94
    26  1080p30
    27  1080p60
    === ==========

    The multiview and downconvert bitfields are the same values as the resultion numbers but the
    key is the bit instead.

    After parsing:

    :ivar mode: mode number
    :ivar resolution: vertical resolution of the mode
    :ivar interlaced: the current mode is interlaced
    :ivar rate: refresh rate of the mode
    """

    CODE = "_VMC"

    def __init__(self, raw):
        self.raw = raw
        count, = struct.unpack_from('>H', raw, 0)
        self.modes = []
        for i in range(0, count):
            vidm, multiview, downscale, reconfig = struct.unpack_from('>B3x I I ?', raw, 4 + (i * 13))
            self.modes.append({
                'modenum': vidm,
                'mode': self._int_to_mode(vidm),
                'multiview': self._bitfield_to_modes(multiview),
                'downscale': self._bitfield_to_modes(downscale),
                'reconfigure': reconfig,
            })

    def _bitfield_to_modes(self, bitfield):
        result = []
        for i in range(0, 32):
            if bitfield & (2 ** i):
                result.append(self._int_to_mode(i))
        return result

    def _int_to_mode(self, mode):
        return VideoModeField(struct.pack('>1B3x', mode))

    def __repr__(self):
        modenames = []
        for mode in self.modes:
            modenames.append(mode['mode'].get_label())
        lst = ' '.join(modenames)
        return '<video-mode-capability: {}>'.format(lst)


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
    131   Multiview output, or a dedicated status window (audio, recording, streaming)
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
    :ivar port_type: Integer describing the port type
    :ivar available_aux: Source can be routed to AUX
    :ivar available_multiview: Source can be routed to multiview
    :ivar available_supersource_art: Source can be routed to supersource
    :ivar available_supersource_box: Source can be routed to supersource
    :ivar available_key_source: Source can be used as keyer key source
    :ivar available_aux1: Source can be sent to AUX1 (Extreme only)
    :ivar available_aux2: Source can be sent to AUX2 (Extreme only)
    :ivar available_me1: Source can be routed to M/E 1
    :ivar available_me2: Source can be routed to M/E 2
    """

    PORT_EXTERNAL = 0
    PORT_BLACK = 1
    PORT_BARS = 2
    PORT_COLOR = 3
    PORT_MEDIAPLAYER = 4
    PORT_MEDIAPLAYER_KEY = 5
    PORT_SUPERSOURCE = 6
    PORT_PASSTHROUGH = 7
    PORT_ME_OUTPUT = 128
    PORT_AUX_OUTPUT = 129
    PORT_KEY_MASK = 130
    PORT_MULTIVIEW_OUTPUT = 131
    CODE = "InPr"

    def __init__(self, raw):
        self.raw = raw
        fields = struct.unpack('>H 20s 4s 10B', raw)
        self.index = fields[0]
        self.name = self._get_string(fields[1])
        self.short_name = self._get_string(fields[2])
        self.source_category = fields[3]
        self.port_type = fields[9]
        self.source_ports = fields[6]

        self.available_aux = fields[11] & (1 << 0) != 0
        self.available_multiview = fields[11] & (1 << 1) != 0
        self.available_supersource_art = fields[11] & (1 << 2) != 0
        self.available_supersource_box = fields[11] & (1 << 3) != 0
        self.available_key_source = fields[11] & (1 << 4) != 0
        self.available_aux1 = fields[11] & (1 << 5) != 0
        self.available_aux2 = fields[11] & (1 << 6) != 0

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

    CODE = "PrgI"

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

    CODE = "PrvI"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.source, in_program = struct.unpack('>B x H B 3x', raw)
        self.in_program = in_program == 1

    def __repr__(self):
        in_program = ''
        if self.in_program:
            in_program = ' in-program'
        return '<preview-bus-input: me={} source={}{}>'.format(self.index, self.source, in_program)


class TransitionSettingsField(FieldBase):
    """
    Data from the `TrSS` field. This stores the config of the "Next transition" and "Transition style" blocks on the
    control panels.

    The mixer will send a field for every M/E unit in the mixer.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    u8     Transition style
    2      1    u8     Next transition layers
    3      1    u8     Next transition style
    4      1    u8     Next transition next transition layers
    ====== ==== ====== ===========

    There are two sets of style/layer settings. The first set is the active transition settings. The second one
    will store the transitions settings if you change any of them while a transition is active. These settings will be
    applied as soon as the transition ends. This is signified by blinking transition settings buttons in the official
    control panels.

    After parsing:

    :ivar index: M/E index in the mixer
    :ivar style: Active transition style
    :ivar style_next: Transition style for next transition
    :ivar next_transition_bkgd: Next transition will affect the background layer
    :ivar next_transition_key1: Next transition will affect the upstream key 1 layer
    :ivar next_transition_key2: Next transition will affect the upstream key 2 layer
    :ivar next_transition_key3: Next transition will affect the upstream key 3 layer
    :ivar next_transition_key4: Next transition will affect the upstream key 4 layer
    :ivar next_transition_bkgd_next: Next transition (after current) will affect the background layer
    :ivar next_transition_key1_next: Next transition (after current) will affect the upstream key 1 layer
    :ivar next_transition_key2_next: Next transition (after current) will affect the upstream key 2 layer
    :ivar next_transition_key3_next: Next transition (after current) will affect the upstream key 3 layer
    :ivar next_transition_key4_next: Next transition (after current) will affect the upstream key 4 layer

    """

    STYLE_MIX = 0
    STYLE_DIP = 1
    STYLE_WIPE = 2
    STYLE_DVE = 3
    STYLE_STING = 4
    CODE = "TrSS"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.style, nt, self.style_next, ntn = struct.unpack('>B 2B 2B 3x', raw)

        self.next_transition_bkgd = nt & (1 << 0) != 0
        self.next_transition_key1 = nt & (1 << 1) != 0
        self.next_transition_key2 = nt & (1 << 2) != 0
        self.next_transition_key3 = nt & (1 << 3) != 0
        self.next_transition_key4 = nt & (1 << 4) != 0

        self.next_transition_bkgd_next = ntn & (1 << 0) != 0
        self.next_transition_key1_next = ntn & (1 << 1) != 0
        self.next_transition_key2_next = ntn & (1 << 2) != 0
        self.next_transition_key3_next = ntn & (1 << 3) != 0
        self.next_transition_key4_next = ntn & (1 << 4) != 0

    def __repr__(self):
        return '<transition-settings: me={} style={}>'.format(self.index, self.style)


class TransitionPreviewField(FieldBase):
    """
    Data from the `TsPr` field. This represents the state of the "PREV TRANS" button on the mixer.

    The mixer will send a field for every M/E unit in the mixer.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    bool   Enabled
    2      2    ?      unknown
    ====== ==== ====== ===========

    After parsing:

    :ivar index: M/E index in the mixer
    :ivar enabled: True if the transition preview is enabled
    """

    CODE = "TsPr"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.enabled = struct.unpack('>B ? 2x', raw)

    def __repr__(self):
        return '<transition-preview: me={} enabled={}>'.format(self.index, self.enabled)


class TransitionPositionField(FieldBase):
    """
    Data from the `TrPs` field. This represents the state of the transition T-handle position

    The mixer will send a field for every M/E unit in the mixer.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    bool   In transition
    2      1    u8     Frames remaining
    3      1    ?      unknown
    4      2    u16    Position
    6      1    ?      unknown
    ====== ==== ====== ===========

    After parsing:

    :ivar index: M/E index in the mixer
    :ivar in_transition: True if the transition is active
    :ivar frames_remaining: Number of frames left to complete the transition on auto
    :ivar position: Position of the transition, 0-9999
    """

    CODE = "TrPs"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.in_transition, self.frames_remaining, position = struct.unpack('>B ? B x H 2x', raw)
        self.position = position

    def __repr__(self):
        return '<transition-position: me={} frames-remaining={} position={:02f}>'.format(self.index,
                                                                                         self.frames_remaining,
                                                                                         self.position)


class TallyIndexField(FieldBase):
    """
    Data from the `TlIn`. This is the status of the tally light for every input in order of index number.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Total of tally lights
    n      1    u8     Bitfield, bit0=PROGRAM, bit1=PREVIEW, repeated for every tally light
    ====== ==== ====== ===========

    After parsing:

    :ivar num: number of tally lights
    :ivar tally: List of tally values, every tally light is represented as a tuple with 2 booleans for PROGRAM and PREVIEW
    """

    CODE = "TlIn"

    def __init__(self, raw):
        self.raw = raw
        offset = 0
        self.num, = struct.unpack_from('>H', raw, offset)
        self.tally = []
        offset += 2
        for i in range(0, self.num):
            tally, = struct.unpack_from('>B', raw, offset)
            self.tally.append((tally & 1 != 0, tally & 2 != 0))
            offset += 1

    def __repr__(self):
        return '<tally-index: num={}, val={}>'.format(self.num, self.tally)


class TallySourceField(FieldBase):
    """
    Data from the `TlSr`. This is the status of the tally light for every input, but indexed on source index

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Total of tally lights
    n      2    u16    Source index for this tally light
    n+2    1    u8     Bitfield, bit0=PROGRAM, bit1=PREVIEW
    ====== ==== ====== ===========

    After parsing:

    :ivar num: number of tally lights
    :ivar tally: Dict of tally lights, every tally light is represented as a tuple with 2 booleans for PROGRAM and PREVIEW
    """

    CODE = "TlSr"

    def __init__(self, raw):
        self.raw = raw
        offset = 0
        self.num, = struct.unpack_from('>H', raw, offset)
        self.tally = {}
        offset += 2
        for i in range(0, self.num):
            source, tally, = struct.unpack_from('>HB', raw, offset)
            self.tally[source] = (tally & 1 != 0, tally & 2 != 0)
            offset += 3

    def __repr__(self):
        return '<tally-source: num={}, val={}>'.format(self.num, self.tally)


class KeyOnAirField(FieldBase):
    """
    Data from the `KeOn`. This is the on-air state of the upstream keyers

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    u8     Keyer index
    2      1    bool   On-air
    3      1    ?      unknown
    ====== ==== ====== ===========

    After parsing:

    :ivar index: M/E index in the mixer
    :ivar keyer: Upstream keyer number
    :ivar enabled: Wether the keyer is on-air
    """

    CODE = "KeOn"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.keyer, self.enabled = struct.unpack('>BB?x', raw)

    def __repr__(self):
        return '<key-on-air: me={}, keyer={}, enabled={}>'.format(self.index, self.keyer, self.enabled)


class ColorGeneratorField(FieldBase):
    """
    Data from the `ColV`. This is color set in the color generators of the mixer

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Color generator index
    1      1    ?      unknown
    2      2    u16    Hue [0-3599]
    4      2    u16    Saturation [0-1000]
    6      2    u16    Luma [0-1000]
    ====== ==== ====== ===========

    After parsing:

    :ivar index: M/E index in the mixer
    :ivar keyer: Upstream keyer number
    :ivar enabled: Wether the keyer is on-air
    """

    CODE = "ColV"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.hue, self.saturation, self.luma = struct.unpack('>Bx 3H', raw)
        self.hue = self.hue / 10.0
        self.saturation = self.saturation / 1000.0
        self.luma = self.luma / 1000.0

    def get_rgb(self):
        return colorsys.hls_to_rgb(self.hue / 360.0, self.luma, self.saturation)

    def __repr__(self):
        return '<color-generator: index={}, hue={} saturation={} luma={}>'.format(self.index, self.hue, self.saturation,
                                                                                  self.luma)


class AuxOutputSourceField(FieldBase):
    """
    Data from the `AuxS`. The routing for the AUX outputs of the hardware.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    u8     AUX output index
    1      1    ?      unknown
    2      2    u16    Source index
    ====== ==== ====== ===========

    After parsing:

    :ivar index: AUX index
    :ivar rate: Source index
    """

    CODE = "AuxS"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.source = struct.unpack('>BxH', raw)

    def __repr__(self):
        return '<aux-output-source: aux={}, source={}>'.format(self.index, self.source)


class FadeToBlackStateField(FieldBase):
    """
    Data from the `FtbS`. This contains the information about the fade-to-black transition.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    bool   Fade to black done
    2      1    bool   Fade to black is in transition
    3      1    u8     Frames remaining in transition
    ====== ==== ====== ===========

    After parsing:

    :ivar index: M/E index in the mixer
    :ivar done: Fade to black is completely done (blinking button state in the control panel)
    :ivar transitioning: Fade to black is fading, (Solid red in control panel)
    :ivar frames_remaining: Frames remaining in the transition
    """

    CODE = "FtbS"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.done, self.transitioning, self.frames_remaining = struct.unpack('>B??B', raw)

    def __repr__(self):
        return '<fade-to-black-state: me={}, done={}, transitioning={}, frames-remaining={}>'.format(self.index,
                                                                                                     self.done,
                                                                                                     self.transitioning,
                                                                                                     self.frames_remaining)


class MediaplayerFileInfoField(FieldBase):
    """
    Data from the `MPfe`. This is the metadata about a single frame slot in the mediaplayer

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     type
    1      1    ?      unknown
    2      2    u16    index
    4      1    bool   is used
    5      16   char[] hash
    21     2    ?      unknown
    23     ?    string name of the slot, first byte is number of characters
    ====== ==== ====== ===========

    After parsing:

    :ivar index: Slot index
    :ivar type: Slot type, 0=still
    :ivar is_used: Slot contains data
    :ivar hash: 16-byte md5 hash of the slot data
    :ivar name: Name of the content in the slot
    """

    CODE = "MPfe"

    def __init__(self, raw):
        self.raw = raw
        namelen = max(0, len(raw) - 23)
        self.type, self.index, self.is_used, self.hash, self.name = struct.unpack('>Bx H ? 16s 2x {}p'.format(namelen),
                                                                                  raw)

    def __repr__(self):
        return '<mediaplayer-file-info: type={} index={} used={} name={}>'.format(self.type, self.index, self.is_used,
                                                                                  self.name)


class TopologyField(FieldBase):
    """
    Data from the `_top` field. This describes the internal video routing topology.

    =================== ========= ======= ======
    spec                Atem Mini 1M/E 4k TVS HD
    =================== ========= ======= ======
    M/E units           1         1       1
    upstream keyers     1         1       1
    downstream keyers   1         2       2
    dve                 1         1       1
    stinger             0         1       0
    supersources        0         0       0
    multiview           0         1       1
    rs485               0         1       1
    =================== ========= ======= ======

    ====== ==== ====== ========= ========= ======= ======= ====== ===========
    Offset Size Type   Atem Mini Mini Pro  1M/E 4k Prod 4k TVS HD Description
    ====== ==== ====== ========= ========= ======= ======= ====== ===========
    0      1    u8     1         1         1       1       1      Number of M/E units
    1      1    u8     14        15        31      24      24     Sources
    2      1    u8     1         1         2       2       2      Downstream keyers
    3      1    u8     1         1         3       1       1      AUX busses
    4      1    u8     0         0         0       0       4      MixMinus Outputs
    5      1    u8     1         1         2       2       2      Media players
    6      1    u8     0         1         1       1       1      Multiviewers
    7      1    u8     0         0         1       0       1      rs485
    8      1    u8     4         4         4       4       4      Hyperdecks
    9      1    u8     1         1         1       0       1      DVE
    10     1    u8     0         0         1       0       0      Stingers
    11     1    u8     0         0         0       0       0      supersources
    12     1    u8     0         0         1       1       1      ? Multiview routable?
    13     1    u8     0         0         0       0       1      Talkback channels
    14     1    u8     0         0         0       0       4      ?
    15     1    u8     1         1         0       0       0      ?
    16     1    u8     0         0         0       0       0      ?
    17     1    u8     0         0         1       1       0      ?
    18     1    u8     1         1         1       1       1      Camera Control
    19     1    u8     0         0         1       0       1      ?
    20     1    u8     0         0         1       0       1      ?
    21     1    u8     0         0         1       1       1      ? Multiview routable?
    22     1    u8     1         1         0       0       0      Advanced chroma keyers
    23     1    u8     1         1         0       0       0      Only configurable outputs
    24     1    u8     1         1         0       0       0      ?
    25     1    u8     0x20      0x2f      0x20    0       0x10   ?
    26     1    u8     3         108       0       0       0      ?
    27     1    u8     0xe8      0x69      0x00    0       0x0    ?
    ====== ==== ====== ========= ========= ======= ======= ====== ===========


    After parsing:

    :ivar me_units: Number of M/E units in the mixer
    :ivar sources: Number of internal and external sources
    :ivar downstream_keyers: Number of downstream keyers
    :ivar aux_outputs: Number of routable AUX outputs
    :ivar mixminus_outputs: Number of ouputs with MixMinus
    :ivar mediaplayers: Number of mediaplayers
    :ivar multiviewers: Number of multiview ouputs
    :ivar rs485: Number of RS-485 outputs
    :ivar hyperdecks: Number of hyperdeck slots
    :ivar dve: Number of DVE blocks
    :ivar stingers: Number of stinger blocks
    :ivar supersources: Number of supersources
    """

    CODE = "_top"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>28B', raw)

        self.me_units = field[0]
        self.sources = field[1]
        self.downstream_keyers = field[2]
        self.aux_outputs = field[3]
        self.mixminus_outputs = field[4]
        self.mediaplayers = field[5]
        self.multiviewers = field[6]
        self.rs485 = field[7]
        self.hyperdecks = field[8]
        self.dve = field[9]
        self.stingers = field[10]
        self.supersources = field[11]
        self.multiviewer_routable = field[12] == 1

    def __repr__(self):
        return '<topology, me={} sources={} aux={}>'.format(self.me_units, self.sources, self.aux_outputs)


class DkeyPropertiesBaseField(FieldBase):
    """
    Data from the `DskB`. Downstream keyer base info.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    u8     Downstream keyer index, 0-indexed
    1      1    ?      unknown
    2      2    u16    Fill source index
    4      2    u16    Key source index
    6      2    ?      unknown
    ====== ==== ====== ===========

    After parsing:

    :ivar index: DSK index
    :ivar fill_source: Source index for the fill input
    :ivar key_source: Source index for the key input
    """

    CODE = "DskB"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.fill_source, self.key_source = struct.unpack('>BxHH2x', raw)

    def __repr__(self):
        return '<downstream-keyer-base: dsk={}, fill={}, key={}>'.format(self.index, self.fill_source, self.key_source)


class DkeyPropertiesField(FieldBase):
    """
    Data from the `DskP`. Downstream keyer info.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    u8     Downstream keyer index, 0-indexed
    1      1    bool   Tie enabled
    2      1    u8     Transition rate in frames
    3      1    bool   Mask is pre-multiplied alpha
    4      2    u16    Clip [0-1000]
    6      2    u16    Gain [0-1000]
    8      1    bool   Invert key
    9      1    bool   Enable mask
    10     2    i16    Top [-9000 - 9000]
    12     2    i16    Bottom [-9000 - 9000]
    14     2    i16    Left [-9000 - 9000]
    16     2    i16    Right [-9000 - 9000]
    18     2    ?      unknown
    ====== ==== ====== ===========

    After parsing:

    :ivar index: M/E index in the mixer
    :ivar done: Fade to black is completely done (blinking button state in the control panel)
    :ivar transitioning: Fade to black is fading, (Solid red in control panel)
    :ivar frames_remaining: Frames remaining in the transition
    """

    CODE = "DskP"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>B?B ?HH? ?4h 2B', raw)
        self.index = field[0]
        self.tie = field[1]
        self.rate = field[2]
        self.premultiplied = field[3]
        self.clip = field[4]
        self.gain = field[5]
        self.invert_key = field[6]
        self.masked = field[7]
        self.top = field[8]
        self.bottom = field[9]
        self.left = field[10]
        self.right = field[11]

    def __repr__(self):
        return '<downstream-keyer-mask: dsk={}, tie={}, rate={}, masked={}>'.format(self.index, self.tie, self.rate,
                                                                                    self.masked)


class DkeyStateField(FieldBase):
    """
    Data from the `DskS`. Downstream keyer state.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    u8     Downstream keyer index, 0-indexed
    1      1    bool   On air
    2      1    bool   Is transitioning
    3      1    bool   Is autotransitioning
    4      1    u8     Frames remaining
    5      3    ?      unknown
    ====== ==== ====== ===========

    After parsing:

    :ivar index: Downstream keyer index
    :ivar on_air: Keyer is on air
    :ivar is_transitioning: Is transitioning
    :ivar is_autotransitioning: Is transitioning due to auto button
    :ivar frames_remaining: Frames remaining in transition
    """

    CODE = "DskS"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>B 3? B 3x', raw)
        self.index = field[0]
        self.on_air = field[1]
        self.is_transitioning = field[2]
        self.is_autotransitioning = field[3]
        self.frames_remaining = field[4]

    def __repr__(self):
        return '<downstream-keyer-state: dsk={}, onair={}, transitioning={} autotrans={} frames={}>'.format(self.index,
                                                                                                            self.on_air,
                                                                                                            self.is_transitioning,
                                                                                                            self.is_autotransitioning,
                                                                                                            self.frames_remaining)


class TransitionMixField(FieldBase):
    """
    Data from the `TMxP`. Settings for the mix transition.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    u8     rate in frames
    2      2    ?      unknown
    ====== ==== ====== ===========

    After parsing:

    :ivar index: M/E index in the mixer
    :ivar rate: Number of frames in the transition
    """

    CODE = "TMxP"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.rate = struct.unpack('>BBxx', raw)

    def __repr__(self):
        return '<transition-mix: me={}, rate={}>'.format(self.index, self.rate)


class FadeToBlackField(FieldBase):
    """
    Data from the `FtbP`. Settings for the fade-to-black transition.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    u8     rate in frames
    2      2    ?      unknown
    ====== ==== ====== ===========

    After parsing:

    :ivar index: M/E index in the mixer
    :ivar rate: Number of frames in transition
    """

    CODE = "FtbP"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.rate = struct.unpack('>BBxx', raw)

    def __repr__(self):
        return '<fade-to-black: me={}, rate={}>'.format(self.index, self.rate)


class TransitionDipField(FieldBase):
    """
    Data from the `TDpP`. Settings for the dip transition.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    u8     rate in frames
    2      2    u16    Source index for the DIP source
    ====== ==== ====== ===========

    After parsing:

    :ivar index: M/E index in the mixer
    :ivar rate: Number of frames in transition
    :ivar source: Source index for the dip
    """

    CODE = "TDpP"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.rate, self.source = struct.unpack('>BBH', raw)

    def __repr__(self):
        return '<transition-dip: me={}, rate={} source={}>'.format(self.index, self.rate, self.source)


class TransitionWipeField(FieldBase):
    """
    Data from the `TWpP`. Settings for the wipe transition.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    u8     Rate in frames
    2      1    u8     Pattern id
    3      1    ?      unknown
    4      2    u16    Border width
    6      2    u16    Border fill source index
    8      2    u16    Symmetry
    10     2    u16    Softness
    12     2    u16    Origin position X
    14     2    u16    Origin position Y
    16     1    bool   Reverse
    16     1    bool   Flip flop
    ====== ==== ====== ===========

    After parsing:

    :ivar index: M/E index in the mixer
    :ivar rate: Number of frames in transition
    :ivar source: Source index for the dip
    """

    CODE = "TWpP"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>BBBx 6H 2? 2x', raw)
        self.index = field[0]
        self.rate = field[1]
        self.pattern = field[2]
        self.width = field[3]
        self.source = field[4]
        self.symmetry = field[5]
        self.softness = field[6]
        self.positionx = field[7]
        self.positiony = field[8]
        self.reverse = field[9]
        self.flipflop = field[10]

    def __repr__(self):
        return '<transition-wipe: me={}, rate={} pattern={}>'.format(self.index, self.rate, self.pattern)


class TransitionDveField(FieldBase):
    """
    Data from the `TDvP`. Settings for the DVE transition.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    u8     Rate in frames
    2      1    ?      unknown
    3      1    u8     DVE style
    4      2    u16    Fill source index
    6      2    u16    Key source index
    8      1    bool   Enable key
    9      1    bool   Key is premultiplied
    10     2    u16    Key clip [0-1000]
    12     2    u16    Key gain [0-1000]
    14     1    bool   Key invert
    15     1    bool   Reverse
    16     1    bool   Flip flop
    17     3    ?      unknown
    ====== ==== ====== ===========

    After parsing:

    :ivar index: M/E index in the mixer
    :ivar rate: Number of frames in transition
    :ivar style: Style or effect index for the DVE
    :ivar fill_source: Fill source index
    :ivar key_source: Key source index
    :ivar key_premultiplied: Key is premultiplied alpha
    :ivar key_clip: Key clipping point
    :ivar key_gain: Key Gain
    :ivar key_invert: Invert key source
    :ivar reverse: Reverse transition
    :ivar flipflop: Flip flop transition
    """

    CODE = "TDvP"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>BBx B 2H 2? 2H 3? 3x', raw)
        self.index = field[0]
        self.rate = field[1]
        self.style = field[2]
        self.fill_source = field[3]
        self.key_source = field[4]
        self.key_enable = field[5]
        self.key_premultiplied = field[6]
        self.key_clip = field[7]
        self.key_gain = field[8]
        self.key_invert = field[9]
        self.reverse = field[10]
        self.flipflop = field[11]

    def __repr__(self):
        return '<transition-dve: me={}, rate={} style={}>'.format(self.index, self.rate, self.style)


class AudioMixerMasterPropertiesField(FieldBase):
    """
    Data from the `AMMO`. Settings for the master bus on legacy audio units.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    u16    Program Gain
    2      2    ?      unknown
    4      1    bool   Follow fade to black
    5      1    ?      unknown
    ====== ==== ====== ===========

    After parsing:
    :ivar volume: Master volume for the mixer, unsigned int which maps [? - ?] to +10dB - -100dB (inf)
    :ivar afv: Wether the master volume follows the fade-to-bloack
    """

    CODE = "AMMO"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>H 2x ?x 2x', raw)
        self.volume = field[0]
        self.afv = field[1]

    def __repr__(self):
        return '<audio-master-properties: volume={} afv={}>'.format(self.volume, self.afv)


class AudioMixerMonitorPropertiesField(FieldBase):
    """
    Data from the `AMmO`. Settings for the monitor bus on legacy audio units.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    bool   Monitoring enabled
    1      1    ?      unknown
    2      2    u16    Volume
    4      1    bool   Mute
    5      1    bool   Solo
    6      2    u16    Solo source index
    8      1    bool   Dim
    10     2    u16    Dim volume
    ====== ==== ====== ===========

    After parsing:
    :ivar volume: Master volume for the mixer, unsigned int which maps [? - ?] to +10dB - -100dB (inf)
    """

    CODE = "AMmO"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>?xH? ?H ?x H', raw)
        self.enabled = field[0]
        self.volume = field[1]
        self.mute = field[2]
        self.solo = field[3]
        self.solo_source = field[4]
        self.dim = field[5]
        self.dim_volume = field[6]

    def __repr__(self):
        return '<audio-monitor-properties: volume={}>'.format(self.volume)


class AudioMixerInputPropertiesField(FieldBase):
    """
    Data from the `AMIP`. Settings for a channel strip on legacy audio units.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    u16    Audio source index
    2      1    u8     Type [0: External Video, 1: Media Player, 2: External Audio]
    3      3    ?      unknown
    6      1    bool   From Media Player
    7      1    u8     Plug Type [0: Internal, 1: SDI, 2: HDMI, 3: Component, 4: Composite, 5: SVideo, 32: XLR, 64, AES/EBU, 128 RCA]
    8      1    u8     Mix Option [0: Off, 1: On, 2: AFV]
    9      1    u8     unknown
    10     2    u16    Volume [0 - 65381]
    12     2    i16    Pan [-10000 - 10000]
    14     1    u8     unknown
    ====== ==== ====== ===========

    After parsing:
    :ivar volume: Master volume for the mixer, signed int which maps [-10000 - 1000] to +10dB - -100dB (inf)
    :ivar afv: Enable/disabled state for master audio-follow-video (for fade-to-black)
    """

    CODE = "AMIP"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>H B 2x ? B B x H h x x x', raw)
        self.index = field[0]
        self.type = field[1]
        self.is_media_player = field[2]
        self.number = field[3]
        self.mix_option = field[4]
        self.volume = field[5]
        self.balance = field[6]

        self.strip_id = str(self.index) + '.0'

    def __repr__(self):
        return '<audio-mixer-input-properties: index={} volume={} balance={} >'.format(self.strip_id, self.volume,
                                                                                       self.balance)


class AudioMixerTallyField(FieldBase):
    """
    Data from the `AMTl`. Encodes the state of tally lights on the audio mixer

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    u16    Number of tally lights
    2      2    u16    Audio Source
    4      1    bool   IsMixedIn (On/Off)
    ====== ==== ====== ===========
    """

    CODE = "AMTl"

    def __init__(self, raw):
        self.raw = raw
        offset = 0
        self.num, = struct.unpack_from('>H', raw, offset)
        self.tally = {}
        offset += 2
        for i in range(0, self.num):
            source, tally, = struct.unpack_from('>H?', raw, offset)
            strip_id = '{}.{}'.format(source, 0)
            self.tally[strip_id] = tally
            offset += 3

    def __repr__(self):
        return '<audio-mixer-tally {}>'.format(self.tally)


class FairlightMasterPropertiesField(FieldBase):
    """
    Data from the `FAMP`. Settings for the master bus on fairlight audio units.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    ?      unknown
    1      1    bool   Enable master EQ
    2      4    ?      unknown
    6      2    i16    EQ gain [-2000 - 2000]
    8      2    ?      unknown
    10     2    u16    Dynamics make-up gain [0 - 2000]
    12     4    i32    Master volume [-10000 - 1000]
    16     1    bool   Audio follow video
    17     3    ?      unknown
    ====== ==== ====== ===========

    After parsing:
    :ivar volume: Master volume for the mixer, signed int which maps [-10000 - 1000] to +10dB - -100dB (inf)
    :ivar eq_enable: Enabled/disabled state for the master EQ
    :ivar eq_gain: Gain applied after EQ, [-2000 - 2000] maps to -20dB - +20dB
    :ivar dynamics_gain: Make-up gain for the dynamics section, [0 - 2000] maps to 0dB - +20dB
    :ivar afv: Enable/disabled state for master audio-follow-video (for fade-to-black)
    """

    CODE = "FAMP"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>x ? 4x h 2x H i ? 3x', raw)
        self.eq_enable = field[0]
        self.eq_gain = field[1]
        self.dynamics_gain = field[2]
        self.volume = field[3]
        self.afv = field[4]

    def __repr__(self):
        return '<fairlight-master-properties: volume={} make-up={} eq={}>'.format(self.volume, self.dynamics_gain,
                                                                                  self.eq_gain)


class FairlightStripPropertiesField(FieldBase):
    """
    Data from the `FASP`. Settings for a channel strip on fairlight audio units.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    u16    Audio source index
    14     1    u8     Split indicator? [01 for normal, FF for split]
    15     1    u8     Subchannel index
    18     1    u8     Delay in frames
    22     2    i16    Gain [-10000 - 600]
    29     1    bool   Enable EQ
    34     2    i16    EQ Gain
    38     2    u16    Dynamics gain
    40     2    i16    Pan [-10000 - 10000]
    46     2    i16    Volume [-10000 - 1000]
    49     1    u8     AFV bitfield? 1=off 2=on 4=afv
    ====== ==== ====== ===========

    The way byte 14 and 15 work is unclear at the moment, this need verification on a mixer with an video input that has
    more than 2 embedded channels, of of these bytes might be a channel count.

    After parsing:
    :ivar volume: Master volume for the mixer, signed int which maps [-10000 - 1000] to +10dB - -100dB (inf)
    :ivar eq_enable: Enabled/disabled state for the master EQ
    :ivar eq_gain: Gain applied after EQ, [-2000 - 2000] maps to -20dB - +20dB
    :ivar dynamics_gain: Make-up gain for the dynamics section, [0 - 2000] maps to 0dB - +20dB
    :ivar afv: Enable/disabled state for master audio-follow-video (for fade-to-black)
    """

    CODE = "FASP"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>H 12xBBxB 4x h 5x ? 4x h 2x Hh 4x h x B 2x', raw)
        self.index = field[0]
        self.is_split = field[1]
        self.subchannel = field[2]
        self.delay = field[3]
        self.gain = field[4]
        self.eq_enable = field[5]
        self.eq_gain = field[6]
        self.dynamics_gain = field[7]
        self.pan = field[8]
        self.volume = field[9]
        self.state = field[10]

        self.strip_id = str(self.index)
        if self.is_split == 0xff:
            self.strip_id += '.' + str(self.subchannel)
        else:
            self.strip_id += '.0'

    def __repr__(self):
        extra = ''
        if self.eq_enable:
            extra += ' EQ {}'.format(self.eq_gain)

        return '<fairlight-strip-properties: index={} gain={} volume={} pan={} dgn={} {}>'.format(self.strip_id,
                                                                                                  self.gain,
                                                                                                  self.volume,
                                                                                                  self.pan,
                                                                                                  self.dynamics_gain,
                                                                                                  extra)


class FairlightStripDeleteField(FieldBase):
    """
    Data from the `FASD`. Fairlight strip delete, received only when changing the source routing in fairlight to remove
    channels that have changed.

    """

    CODE = "FASD"

    def __init__(self, raw):
        self.raw = raw

    def __repr__(self):
        return '<fairlight-strip-delete {}>'.format(self.raw)


class FairlightAudioInputField(FieldBase):
    """
    Data from the `FAIP`. Describes the inputs to the fairlight mixer

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    u16    Audio source index
    2      1    u8     Input type
    3      2    ?      unknown
    5      1    u8     Index in group
    10     1    u8     Changes when stereo is split into dual mono
    12     1    u8     Analog audio input level [1=mic, 2=line]
    ====== ==== ====== ===========

    === ==========
    Val Input type
    === ==========
    0   External video input
    1   Media player audio
    2   External audio input
    === ==========

    After parsing:
    :ivar volume: Master volume for the mixer, signed int which maps [-10000 - 1000] to +10dB - -100dB (inf)
    """

    CODE = "FAIP"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.type, self.number, self.split, self.level = struct.unpack('>HB 2x B xxxx B x B 3x', raw)

    def __repr__(self):
        return '<fairlight-input index={} type={}>'.format(self.index, self.type)


class FairlightTallyField(FieldBase):
    """
    Data from the `FMTl`. Encodes the state of tally lights on the audio mixer

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    u16    Number of tally lights
    2      1    u8     Input type
    3      2    ?      unknown
    5      1    u8     Index in group
    10     1    u8     Changes when stereo is split into dual mono
    12     1    u8     Analog audio input level [1=mic, 2=line]
    ====== ==== ====== ===========

    === ==========
    Val Input type
    === ==========
    0   External video input
    1   Media player audio
    2   External audio input
    === ==========

    After parsing:
    :ivar volume: Master volume for the mixer, signed int which maps [-10000 - 1000] to +10dB - -100dB (inf)
    """

    CODE = "FMTl"

    def __init__(self, raw):
        self.raw = raw
        offset = 0
        self.num, = struct.unpack_from('>H', raw, offset)
        self.tally = {}
        offset += 15
        for i in range(0, self.num):
            subchan, source, tally, = struct.unpack_from('>BH?', raw, offset)
            strip_id = '{}.{}'.format(source, subchan)
            self.tally[strip_id] = tally
            offset += 11

    def __repr__(self):
        return '<fairlight-tally {}>'.format(self.tally)


class FairlightHeadphonesField(FieldBase):
    """
    Data from the `FMHP`, phones output volume and mute

    This doesn't get triggered when soloing channels.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      4    i32    Volume in 0.01 dB (-60.00 to +6.00 dB)
    5      4    ?      Unknown
    8      1    bool   Muted (0) / Umuted (1)
    9      1    u8     Last soloed channel (just the main part)
    10     22   ?      Unknown

    """

    def __init__(self, raw):
        self.raw = raw
        self.volume, self.unmuted = struct.unpack('> i 4x ? 23x', raw)

    def __repr__(self):
        return '<fairlight-headphones volume={} unmuted={}>'.format(self.volume, self.unmuted)


class FairlightSoloField(FieldBase):
    """
    Data from the `FAMS`, soloing channels to phones

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    bool   Anything soloed?
    1      7    ?      Unknown
    8      1    u8     Unknown: 0x00 for HDMI channels, 0x05 for 3.5mm jack
    9      1    u8     Soloed channel (main)
    10     12   ?      Unknown
    22     1    u8     No subchannels (0x01), split into L/R (0xff)
    23     1    u8     Soloed channel (subchannel)

    """

    def __init__(self, raw):
        self.raw = raw
        self.solo, self.channel, self.is_split_lr, self.subchannel = struct.unpack('> ? 8x B 12x BB', raw)

    def __repr__(self):
        return '<fairlight-solo active={} source={}>'.format(
            self.solo,
            self.channel if self.is_split_lr == 0x01 else '{}.{}'.format(self.channel, self.subchannel),
        )


class AtemEqBandPropertiesField(FieldBase):
    """
    Data from the `AEBP` field. This encodes the EQ settings in the fairlight mixer. For every channel there will
    be 6 off these fields sent, one for every band of the EQ. The "possible band filters" differentiates the first
    and last band which have a different option list for the filter dropdown in the UI.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    u16    Audio source index
    2      2    ?      unknown
    4      4    ?      unknown
    14     1    u8     Split indicator? [01 for normal, FF for split]
    15     1    u8     subchannel index
    16     1    u8     bond index
    17     1    bool   band enabled
    18     1    u8     possible band filters
    19     1    u8     band filter
    20     1    ?      ?
    21     1    ?      band frequency range
    26     2    u16    band frequency
    28     4    i32    band gain
    32     2    u16    band Q
    ====== ==== ====== ===========

    === ==========
    Val Band filter
    === ==========
    01  Low shelf
    02  Low pass
    04  Bell
    08  Notch
    10  High pass
    20  High shelf
    === ==========

    After parsing:
    :ivar volume: Master volume for the mixer, signed int which maps [-10000 - 1000] to +10dB - -100dB (inf)
    """

    CODE = "AEBP"

    def __init__(self, raw):
        self.raw = raw
        values = struct.unpack('>H 2x 4x 6x BB B ? B B x B 4x H i H 2x', raw)
        self.index = values[0]
        self.is_split = values[1]
        self.subchannel = values[2]
        self.band_index = values[3]
        self.band_enabled = values[4]
        self.band_possible_filters = values[5]
        self.band_filter = values[6]
        self.band_freq_range = values[7]
        self.band_frequency = values[8]
        self.band_gain = values[9]
        self.band_q = values[10]

        self.strip_id = str(self.index)
        if self.is_split == 0xff:
            self.strip_id += '.' + str(self.subchannel)
        else:
            self.strip_id += '.0'

    def __repr__(self):
        desc = ''
        filters = {
            0x01: 'low-shelf',
            0x02: 'low-pass',
            0x04: 'bell',
            0x08: 'notch',
            0x10: 'high-pass',
            0x20: 'high-shelf'
        }
        if self.band_filter in filters:
            desc += filters[self.band_filter]
        else:
            desc += 'filter ' + str(self.band_filter)

        if self.band_enabled:
            desc += '[on]'
        else:
            desc += '[off]'
        desc += ' freq ' + str(self.band_frequency)
        desc += ' gain ' + str(self.band_gain)
        desc += ' Q ' + str(self.band_q)
        return '<atem-eq-band-properties {} band {} {}>'.format(self.strip_id, self.band_index, desc)


class AudioInputField(FieldBase):
    """
    Data from the `AMIP`. Describes the inputs to the atem audio mixer

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    u16    Audio source index
    2      1    u8     Input type
    3      2    ?      unknown
    5      1    u8     Index in group
    6      1    ?      ?
    7      1    u8     Input plug
    8      1    u8     State [0=off, 1=on, 2=afv]
    10     2    u16    Channel volume
    12     2    i16    Channel balance [-10000 - 10000]
    ====== ==== ====== ===========

    === ==========
    Val Input type
    === ==========
    0   External video input
    1   Media player audio
    2   External audio input
    === ==========

    === =========
    Val Plug type
    === =========
    0   Internal
    1   SDI
    2   HDMI
    3   Component
    4   Composite
    5   SVideo
    32  XLR
    64  AES/EBU
    128 RCA
    === =========

    After parsing:
    :ivar volume: Master volume for the mixer, signed int which maps [-10000 - 1000] to +10dB - -100dB (inf)
    """

    CODE = "AMIP"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.type, self.number, self.plug, self.state, self.volume, self.balance = struct.unpack(
            '>HB 2x B x BB x Hh 2x', raw)
        self.strip_id = str(self.index) + '.0'

    def plug_name(self):
        """Return the display name for the connector"""
        lut = {
            0: "Internal",
            1: "SDI",
            2: "HDMI",
            3: "Component",
            4: "Composite",
            5: "SVideo",
            32: "XLR",
            64: "AES",
            128: "RCA",
        }
        if self.plug in lut:
            return lut[self.plug]
        else:
            return 'Analog'

    def __repr__(self):
        return '<audio-input index={} type={} plug={}>'.format(self.index, self.type, self.plug)


class KeyPropertiesBaseField(FieldBase):
    """
    Data from the `KeBP`. The upstream keyer base properties.
    """

    CODE = "KeBP"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>BBB Bx B HH ?x 4h', raw)
        self.index = field[0]
        self.keyer = field[1]
        self.type = field[2]
        self.enabled = field[3]
        self.fly_enabled = field[4]
        self.fill_source = field[5]
        self.key_source = field[6]
        self.mask_enabled = field[7]

        self.mask_top = field[8]
        self.mask_bottom = field[9]
        self.mask_left = field[10]
        self.mask_right = field[11]

    def __repr__(self):
        return '<key-properties-base me={}, key={}, type={}>'.format(self.index, self.keyer, self.type)


class KeyPropertiesDveField(FieldBase):
    """
    Data from the `KeDV`. The upstream keyer DVE-specific properties.
    """

    CODE = "KeDV"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>BBxx 5i ??Bx HH BBBBBx 4HB? 4hB 3x', raw)
        self.index = field[0]
        self.keyer = field[1]

        self.size_x = field[2]
        self.size_y = field[3]
        self.pos_x = field[4]
        self.pos_y = field[5]
        self.rotation = field[6]

        self.border_enabled = field[7]
        self.shadow_enabled = field[8]
        self.border_bevel = field[9]

        self.border_outer_width = field[10]
        self.border_inner_width = field[11]

        self.border_outer_softness = field[12]
        self.border_inner_softness = field[13]
        self.border_bevel_softness = field[14]
        self.border_bevel_position = field[15]
        self.border_opacity = field[16]

        self.border_hue = field[17] / 10.0
        self.border_saturation = field[18] / 1000.0
        self.border_luma = field[19] / 1000.0
        self.light_angle = field[20]
        self.light_altitude = field[21]
        self.mask_enabled = field[22]

        self.mask_top = field[23]
        self.mask_bottom = field[24]
        self.mask_left = field[25]
        self.mask_right = field[26]
        self.rate = field[27]

    def get_border_color_rgb(self):
        return colorsys.hls_to_rgb(self.border_hue / 360.0, self.border_luma, self.border_saturation)

    def __repr__(self):
        return '<key-properties-dve me={}, key={}>'.format(self.index, self.keyer)


class KeyPropertiesLumaField(FieldBase):
    """
    Data from the `KeLm`. The upstream keyer luma-specific properties.
    """

    CODE = "KeLm"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>BB?x HH ?3x', raw)
        self.index = field[0]
        self.keyer = field[1]
        self.premultiplied = field[2]

        self.clip = field[3]
        self.gain = field[4]
        self.key_inverted = field[5]

    def __repr__(self):
        return '<key-properties-luma me={}, key={}>'.format(self.index, self.keyer)


class KeyPropertiesAdvancedChromaField(FieldBase):
    """
    Data from the `KACk` field. This contains the data about the settings in the upstream advanced chroma keyer.
    """

    CODE = "KACk"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>BBH HH HH hhHhhh', raw)
        self.index = field[0]
        self.keyer = field[1]

        self.foreground = field[2]
        self.background = field[3]
        self.key_edge = field[4]

        self.spill_suppress = field[5]
        self.flare_suppress = field[6]

        self.brightness = field[7]
        self.contrast = field[8]
        self.saturation = field[9]
        self.red = field[10]
        self.green = field[11]
        self.blue = field[12]

    def __repr__(self):
        return '<key-properties-advanced-chroma me={}, key={}>'.format(self.index, self.keyer)


class KeyPropertiesAdvancedChromaColorpickerField(FieldBase):
    """
    Data from the `KACC` field. This contains the data about the color picker in the upstream advanced chroma keyer.
    """

    CODE = "KACC"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>BB?? hhH HHH', raw)
        self.index = field[0]
        self.keyer = field[1]
        self.cursor = field[2]
        self.preview = field[3]

        self.x = field[4]
        self.y = field[5]
        self.size = field[6]

        self.Y = (field[7] - 625) / 8544
        self.Cb = (field[8] - 5000) / 5000
        self.Cr = (field[9] - 5000) / 5000

    def get_rgb(self):
        r = self.Y + (self.Cr * 1.5748)
        g = self.Y + (self.Cb * -0.1873) + (self.Cr * -0.4681)
        b = self.Y + (self.Cb * 1.8556)
        r = max(0, min(1, r))
        g = max(0, min(1, g))
        b = max(0, min(1, b))
        return r, g, b

    def __repr__(self):
        return '<key-properties-advanced-chroma-colorpicker me={}, key={}>'.format(self.index, self.keyer)


class RecordingDiskField(FieldBase):
    """
    Data from the `RTMD`. Info about an attached recording disk.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      4    u32    Disk index
    4      4    u32    Recording time available in seconds
    8      2    u16    Status bitfield
    10     64   char[] Volume name
    ====== ==== ====== ===========

    === ==========
    Bit Status value
    === ==========
    0   Idle
    1   Unformatted
    2   Ready
    3   Recording
    4   ?
    5   Deleted
    === ==========

    """

    CODE = "RTMD"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>IIH 64s 2x', raw)
        self.index = field[0]
        self.time_available = field[1]
        self.status = field[2]
        self.volumename = self._get_string(field[3])

        self.is_attached = field[2] & 1 << 0 > 0
        self.is_attached = field[2] & 1 << 1 > 0
        self.is_ready = field[2] & 1 << 2 > 0
        self.is_recording = field[2] & 1 << 3 > 0
        self.is_deleted = field[2] & 1 << 5 > 0

    def __repr__(self):
        return '<recording-disk disk={} label={} status={} available={}>'.format(self.index, self.volumename,
                                                                                 self.status, self.time_available)


class RecordingSettingsField(FieldBase):
    """
    Data from the `RMSu`. The settings for the stream recorder.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      128  char[] Audio source index
    128    4    i32    Disk slot 1 index, or -1 for no disk
    132    4    i32    Disk slot 2 index, or -1 for no disk
    136    1    bool   Trigger recording in cameras
    137    3    ?      ?
    ====== ==== ====== ===========

    The recorder settings has 2 slots to select attached USB disks. If no disk is selected the i32 will be -1 otherwise
    it will be the disk number referring a RTMD field
    """

    CODE = "RMSu"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>128s ii ?3x', raw)
        self.filename = self._get_string(field[0])
        self.disk1 = field[1] if field[1] != -1 else None
        self.disk2 = field[2] if field[2] != -1 else None
        self.record_in_cameras = field[3]

    def __repr__(self):
        return '<recording-settings filename={} disk1={} disk2={} in-camera={}>'.format(self.filename, self.disk1,
                                                                                        self.disk2,
                                                                                        self.record_in_cameras)


class RecordingStatusField(FieldBase):
    """
    Data from the `RTMS`. The status for the stream recorder and total space left in the target device.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    u16    Recording status
    4      4    i32    Total recording time available
    ====== ==== ====== ===========

    === ==========
    Bit Status value
    === ==========
    0   Recording
    1   ?
    2   Disk full
    3   Disk error
    4   Disk unformatted
    5   Frames dropped
    6   ?
    7   Stopping
    === ==========

    """

    CODE = "RMTS"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>H2xi', raw)
        self.status = field[0]
        self.time_available = field[1] if field[1] != -1 else None

        self.is_recording = field[0] & 1 << 0 > 0
        self.is_stopping = field[0] & 1 << 7 > 0
        self.disk_full = field[0] & 1 << 2 > 0
        self.disk_error = field[0] & 1 << 3 > 0
        self.disk_unformatted = field[0] & 1 << 4 > 0
        self.has_dropped = field[0] & 1 << 5 > 0

    def __repr__(self):
        return '<recording-status status={} time-available={}>'.format(self.status, self.time_available)


class RecordingDurationField(FieldBase):
    """
    Data from the `RTMR`. The current recording duration, this does not update very often. The dropped
    frames field signifies that the disk cannot keep up with writing the data and triggers the warning in the
    UI.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    u8     Hours
    1      1    u8     Minutes
    2      1    u8     Seconds
    3      1    u8     Frames
    4      1    bool   Has dropped frames
    5      3    ?      unknown
    ====== ==== ====== ===========

    """

    CODE = "RTMR"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>4B ?3x', raw)
        self.hours = field[0]
        self.minutes = field[1]
        self.seconds = field[2]
        self.frames = field[3]
        self.has_dropped_frames = field[4]

    def __repr__(self):
        drop = ''
        if self.has_dropped_frames:
            drop = ' dropped-frames'
        return '<recording-duration {}:{}:{}:{}{}>'.format(self.hours, self.minutes, self.seconds, self.frames, drop)


class MultiviewerPropertiesField(FieldBase):
    """
    Data from the `MvPr`. The layout preset for the multiviewer output.

    The multiviewer is divided in 4 quadrants and the layout bitfield describes which of those quadrants are
    subdivided again in 4 more viewers. The default layout will have the top 2 quadrants not divided and the bottom
    quadrants used for small viewers.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    u8     Multiviewer index, 0-indexed
    1      1    u8     Layout bitfield
    1      1    bool   Flip program/preview
    1      1    ?      unknown
    ====== ==== ====== ===========

    === ==========
    Bit Layout value
    === ==========
    0   Top left small
    1   Top right small
    2   Bottom left small
    4   Bottom right small
    === ==========

    After parsing:
    :ivar index: Multiviewer index, 0-indexed
    :ivar layout: Layout number from the enum above
    :ivar flip: Swap the program/preview window

    """

    CODE = "MvPr"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>BB?B', raw)
        self.index = field[0]
        self.layout = field[1]
        self.flip = field[2]
        self.u1 = field[3]

        self.top_left_small = field[1] & 0x01 > 0
        self.top_right_small = field[1] & 0x02 > 0
        self.bottom_left_small = field[1] & 0x04 > 0
        self.bottom_right_small = field[1] & 0x08 > 0

    def __repr__(self):
        return '<multiviewer-properties mv={} layout={} flip={} u1={}>'.format(self.index, self.layout, self.flip,
                                                                               self.u1)


class MultiviewerInputField(FieldBase):
    """
    Data from the `MvIn`. The input routing for the multiviewer.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    u8     Multiviewer index, 0-indexed
    1      1    u8     Window index 0-9
    2      2    u16    Source index
    4      1    bool   Supports enabling the VU meter
    5      1    bool   Supports enabling the safe area overlay
    6      2    ?      unknown
    ====== ==== ====== ===========

    Window numbering differs between switcher families. For example, on Atem
    Mini Extreme, windows are numbered on a row-by-row basis, starting at upper
    left. If a quadrant is not split, it gets the number of its upper left
    mini-window. This is an example of a layout on Atem Mini Extreme:

     +----+----+---------+
     |  0 |  1 |    2    |
     |  4 |  5 |         |
     +----+----+----+----+
     |    8    | 10 | 11 |
     |         | 14 | 15 |
     +---------+----+----+

    On the non-Extreme Mini switchers, the window layout does not appear to be
    configurable, and therefore the numbers are allocated on a contiguous
    basis:

     +----+----+---------+
     |  0      |    1    |
     +----+----+----+----+
     |  2 |  3 |  4 |  5 |
     +----+----+----+----+
     |  6 | 7? | 8? | 9? |
     +----+----+----+----+

    Since the windows marked '?' are not configurable on non-Extreme Minis,
    these numbers are just an educated guess.

    Audio VU meters appear to be supported on small and big windows alike, but
    only on those which show a video input or the Program output. The safe area
    overlay appears to only work on full-sized Preview.

    After parsing:
    :ivar index: Multiviewer index, 0-indexed
    :ivar window: Window number inside the multiview
    :ivar source: Source index for this window
    :ivar vu: True if VU meter overlays can be enabled
    :ivar safearea: True if safe area overlays can be enabled
    """

    CODE = "MvIn"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.window, self.source, self.vu, self.safearea = struct.unpack('>BBH??2x', raw)

    def __repr__(self):
        return '<multiviewer-input mv={} win={} source={}>'.format(self.index, self.window, self.source)


class MultiviewerVuField(FieldBase):
    """
    Data from the `VuMC`. This describes if a multiview window has the VU meter overlay enabled.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    u8     Multiviewer index, 0-indexed
    1      1    u8     Window index 0-9
    2      1    bool   VU enabled
    3      1    ?      unknown
    ====== ==== ====== ===========

    After parsing:
    :ivar index: Multiviewer index, 0-indexed
    :ivar window: Window number inside the multiview
    :ivar enabled: True if the VU meter overlay is enabled for this window
    """

    CODE = "VuMC"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.window, self.enabled = struct.unpack('>BB?x', raw)

    def __repr__(self):
        return '<multiviewer-vu mv={} win={} enabled={}>'.format(self.index, self.window, self.enabled)


class MultiviewerSafeAreaField(FieldBase):
    """
    Data from the `SaMw`. This describes if a multiview window has the safe area overlay enabled. This is generally
    only enabled on the preview window.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      1    u8     Multiviewer index, 0-indexed
    1      1    u8     Window index 0-9
    2      1    bool   safe area enabled
    3      1    ?      unknown
    ====== ==== ====== ===========

    After parsing:
    :ivar index: Multiviewer index, 0-indexed
    :ivar window: Window number inside the multiview
    :ivar enabled: True if the safe area meter overlay is enabled for this window
    """

    CODE = "SaMw"

    def __init__(self, raw):
        self.raw = raw
        self.index, self.window, self.enabled = struct.unpack('>BB?x', raw)

    def __repr__(self):
        return '<multiviewer-safe-area mv={} win={} enabled={}>'.format(self.index, self.window, self.enabled)


class LockObtainedField(FieldBase):
    """
    Data from the `LKOB`. This signals that a datastore lock has been successfully obtained for
    a specific datastore index. Used for data transfers.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    u16    Store id
    2      2    ?      Unknown
    ====== ==== ====== ===========

    After parsing:
    :ivar store: Store index
=    """

    CODE = "LKOB"

    def __init__(self, raw):
        self.raw = raw
        self.store, = struct.unpack('>H2x', raw)

    def __repr__(self):
        return '<lock-obtained store={}>'.format(self.store)


class LockStateField(FieldBase):
    """
    Data from the `LKST`. This updates the state of the locks.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    u16    Store id
    2      1    bool   State
    3      1    ?      unknown
    ====== ==== ====== ===========

    After parsing:
    :ivar store: Store index
    :ivar state: True if a lock is held
    """

    CODE = "LKST"

    def __init__(self, raw):
        self.raw = raw
        self.store, self.state, self.u1 = struct.unpack('>H?B', raw)

    def __repr__(self):
        state = 'locked' if self.state else 'unlocked'
        return '<lock-state store={} state={}>'.format(self.store, state)


class FileTransferDataField(FieldBase):
    """
    Data from the `FTDa`. This is an incoming chunk of data for a running file transfer.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    u16    Transfer id
    2      2    u16    Data length
    ?      ?    bytes  The rest of the packet contains [Data length] bytes of data
    ====== ==== ====== ===========

    After parsing:
    :ivar transfer: Transfer index
    :ivar size: Length of the transfer chunk
    :ivar data: Contents of the transfer chunk
    """

    CODE = "FTDa"

    def __init__(self, raw):
        self.raw = raw
        self.transfer, self.size = struct.unpack('>HH', raw[0:4])
        self.data = raw[4:(4 + self.size)]

    def __repr__(self):
        return '<file-transfer-data transfer={} size={}>'.format(self.transfer, self.size)


class FileTransferErrorField(FieldBase):
    """
    Data from the `FTDE`. Something went wrong with a file transfer and it has been aborted.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    u16    Transfer id
    2      1    u8     Error code
    3      1    ?      unknown
    ====== ==== ====== ===========

    ========== ===========
    Error code Description
    ========== ===========
    1          try-again, Try the transfer again
    2          not-found, The requested store/slot index doesn't contain data
    5          no-lock, You didn't obtain the lock before doing the transfer
    ========== ===========

    After parsing:
    :ivar transfer: Transfer index
    :ivar status: Status id from the enum above
    """

    CODE = "FTDE"

    def __init__(self, raw):
        self.raw = raw
        self.transfer, self.status = struct.unpack('>HBx', raw)

    def __repr__(self):
        errors = {
            1: 'try-again',
            2: 'not-found',
            5: 'no-lock'
        }

        if self.status in errors:
            status = errors[self.status]
        else:
            status = f'unknown ({self.status})'
        return '<file-transfer-error transfer={} status={}>'.format(self.transfer, status)


class FileTransferDataCompleteField(FieldBase):
    """
    Data from the `FTDC`. Sent after pushing a file.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    u16    Transfer id
    2      1    u8     ? (always 1)
    3      1    u8     ? (always 2 or 6)
    ====== ==== ====== ===========

    After parsing:
    :ivar transfer: Transfer index that has completed
    """

    CODE = "FTDC"

    def __init__(self, raw):
        self.raw = raw
        self.transfer, self.u1, self.u2 = struct.unpack('>HBB', raw)

    def __repr__(self):
        return '<file-transfer-complete transfer={} u1={} u2={}>'.format(self.transfer, self.u1, self.u2)


class FileTransferContinueDataField(FieldBase):
    """
    Data from the `FTCD`. This is an field telling the client what chunk size to use to continue the upload
    of data to the hardware.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    u16    Transfer id
    2      4    ?      unknown
    6      2    u16    Chunk size
    8      2    u16    Chunk count
    10     2    ?      unknown
    ====== ==== ====== ===========

    After parsing:
    :ivar transfer: Transfer index
    :ivar size: Length of the transfer chunk
    :ivar count: Contents of the transfer chunk
    """

    CODE = "FTCD"

    def __init__(self, raw):
        self.raw = raw
        self.transfer, self.size, self.count = struct.unpack('>H 4x HH 2x', raw)

    def __repr__(self):
        return '<file-transfer-continue transfer={} size={} count={}>'.format(self.transfer, self.size, self.count)


class MacroPropertiesField(FieldBase):
    """
    Data from the `MPrp`. This is the metadata about a stored macro

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Macro slot index
    2      1    bool   is used
    3      1    bool   has invalid commands
    4      2    u16    Name length
    6      2    u16    Description length
    8      ?    char[] Name
    ?      ?    char[] Description
    ====== ==== ====== ===========

    After parsing:

    :ivar index: Macro slot index
    :ivar is_used: Slot contains data
    :ivar is_invalid: Slot contains invalid data
    :ivar name: Name of the macro
    :ivar description: Description of the macro
    """

    CODE = "MPrp"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack_from('>H ?? H H', raw, 0)
        self.index = field[0]
        self.is_used = field[1]
        self.is_invalid = field[2]
        name_length = field[3]
        desc_length = field[4]
        self.name, self.description = struct.unpack_from('>{}s {}s'.format(name_length, desc_length), raw, 8)

    def __repr__(self):
        return '<macro-properties: index={} used={} name={}>'.format(self.index, self.is_used,
                                                                     self.name)


class AudioMeterLevelsField(FieldBase):
    """
    Data from the `AMLv`. This contains the realtime audio levels for the audio mixer

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Number of input channels
    2      2    ?      padding
    4      4    u32    Master left level
    8      4    u32    Master right level
    12     4    u32    Master left peak
    16     4    u32    Master right peak
    20     4    u32    Monitor left level
    24     4    u32    Monitor right level
    28     4    u32    Monitor left peak
    32     4    u32    Monitor right peak
    ?      4    u32    Input left level [These 4 repeat for the number of channels above]
    ?      4    u32    Input right level
    ?      4    u32    Input left peak
    ?      4    u32    Input right peak

    ====== ==== ====== ===========

    After parsing:
    The levels are tuples in the format (left level, right level, left peak, right peak).
    :ivar count: Number of channels
    :ivar master: Master levels
    :ivar monitor: Monitor levels
    :ivar input: All input levels as a dict, the key is the channel number and the value a level tuple
    """

    CODE = "AMLv"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack_from('>H2x 4I 4I', raw, 0)
        self.count = field[0]
        self.master = (
            self._level(field[1]),
            self._level(field[2]),
            self._level(field[3]),
            self._level(field[4])
        )
        self.monitor = (
            self._level(field[5]),
            self._level(field[6]),
            self._level(field[7]),
            self._level(field[8])
        )
        self.input = {}
        offset = struct.calcsize('>H2x 4I 4I')
        sources = struct.unpack_from('>{}H'.format(self.count), raw, offset)
        offset = int(math.ceil((offset + (2 * self.count)) / 4.0) * 4)
        field = struct.unpack_from('>{}I'.format(self.count * 4), raw, offset)
        for i in range(0, self.count * 4, 4):
            level = (
                self._level(field[i]),
                self._level(field[i + 1]),
                self._level(field[i + 2]),
                self._level(field[i + 3])
            )
            self.input[sources[i // 4]] = level

    def _level(self, value):
        if value == 0:
            return -60
        val = math.log10(value / (128 * 65536)) * 20
        return val

    def __repr__(self):
        return '<audio-meter-levels count={}>'.format(self.count)


class FairlightMeterLevelsField(FieldBase):
    """
    Data from the `FMLv`. This contains the realtime audio levels for the fairlight audio mixer

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      6    ?      Unknown
    6      1    u8     is_split, 255 when split or 0 when it isn't
    7      1    u8     subchannel index
    8      2    u16    source index
    10     2    i16    Input level left, -10000 to 0
    12     2    i16    Input level right, -10000 to 0
    14     2    i16    Input peak left, -10000 to 0
    16     2    i16    Input peak right, -10000 to 0
    18     2    i16    Expander gain reduction, -10000 to 0
    20     2    i16    Compressor gain reduction, -10000 to 0
    22     2    i16    Limiter gain reduction, -10000 to 0
    24     2    i16    Output level left, -10000 to 0
    26     2    i16    Output level right, -10000 to 0
    28     2    i16    Output peak left, -10000 to 0
    30     2    i16    Output peak right, -10000 to 0
    32     2    i16    Fader level left, -10000 to 0
    34     2    i16    Fader level right, -10000 to 0
    36     2    i16    Fader peak left, -10000 to 0
    38     2    i16    Fader peak right, -10000 to 0
    ====== ==== ====== ===========

    After parsing:

    :ivar index: Channel source index
    :ivar is_split: Stereo channel is split into dual mono
    :ivar subchannel: Channel index after splitting
    :ivar strip_id: Strip identifier in {source}.{subchannel} format
    :ivar input: Volume level before dynamics
    :ivar output: Volume level after dynamics
    :ivar level: Volume level after fader
    :ivar expander_gr: Gain reduction by the expander
    :ivar compressor_gr: Gain reduction by the compressor
    :ivar limiter_gr: Gain reduction by the limiter
    """

    CODE = "FMLv"
    COEFF = 10 ** (40 / 20)

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack_from('>6xBBH 15h', raw, 0)
        self.index = field[2]
        self.is_split = field[0]
        self.subchannel = field[1]

        if self.is_split == 0xff:
            self.strip_id = f"{self.index}.{self.subchannel}"
        else:
            self.strip_id = f"{self.index}.0"

        self.input = (
            self._level(field[3]),
            self._level(field[4]),
            self._level(field[5]),
            self._level(field[6])
        )

        self.expander_gr = self._level(field[7])
        self.compressor_gr = self._level(field[8])
        self.limiter_gr = self._level(field[9])

        self.output = (
            self._level(field[10]),
            self._level(field[11]),
            self._level(field[12]),
            self._level(field[13])
        )
        self.level = (
            self._level(field[14]),
            self._level(field[15]),
            self._level(field[16]),
            self._level(field[17])
        )

    def _level(self, value):
        if value == 0:
            return 0
        value += 10000
        value /= 10000
        if value == 0:
            return -60
        val = (math.exp((math.log(self.COEFF + 1) * value)) - 1) / self.COEFF
        val = val * 60 - 60
        return val

    def __repr__(self):
        return '<fairlight-meter-levels source={}>'.format(self.strip_id)


class FairlightMasterLevelsField(FieldBase):
    """
    Data from the `FDLv`. This contains the realtime audio levels for the master channel of the fairlight mixer

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    i16    Input level left, -10000 to 0
    2      2    i16    Input level right, -10000 to 0
    4      2    i16    Input peak left, -10000 to 0
    6      2    i16    Input peak right, -10000 to 0
    8      2    i16    Compressor gain reduction, -10000 to 0
    10     2    i16    Limiter gain reduction, -10000 to 0
    12     2    i16    Output level left, -10000 to 0
    14     2    i16    Output level right, -10000 to 0
    16     2    i16    Output peak left, -10000 to 0
    18     2    i16    Output peak right, -10000 to 0
    20     2    i16    Fader level left, -10000 to 0
    22     2    i16    Fader level right, -10000 to 0
    24     2    i16    Fader peak left, -10000 to 0
    26     2    i16    Fader peak right, -10000 to 0
    ====== ==== ====== ===========

    After parsing:
    :ivar input: Volume level before dynamics
    :ivar output: Volume level after dynamics
    :ivar level: Volume level after fader
    :ivar compressor_gr: Gain reduction by the compressor
    :ivar limiter_gr: Gain reduction by the limiter
    """

    CODE = "FDLv"
    COEFF = 10 ** (40 / 20)

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack_from('>14h', raw, 0)

        self.input = (
            self._level(field[0]),
            self._level(field[1]),
            self._level(field[2]),
            self._level(field[3])
        )

        self.compressor_gr = self._level(field[4])
        self.limiter_gr = self._level(field[5])

        self.output = (
            self._level(field[6]),
            self._level(field[7]),
            self._level(field[8]),
            self._level(field[9])
        )
        self.level = (
            self._level(field[10]),
            self._level(field[11]),
            self._level(field[12]),
            self._level(field[13])
        )

    def _level(self, value):
        if value == 0:
            return 0
        value += 10000
        value /= 10000
        if value == 0:
            return -60
        val = (math.exp((math.log(self.COEFF + 1) * value)) - 1) / self.COEFF
        val = val * 60 - 60
        return val

    def __repr__(self):
        return '<fairlight-master-levels>'


class CameraControlDataPacketFieldDisabled(FieldBase):
    """

    !! This parser is not production ready !!
    The packet length is somewhat inconsistent which can cause the TCP protocol to fail due to the alignment in the
    protocol breaking

    Data from the `CCdP`. This contains a single packet for the remote shading unit in the blackmagic cameras. This
    protocol seems to roughly match up to the official BMD SDI camera control documentation with the bytes packed
    differently.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Destination, 255 = broadcast to all
    1      1    u8     Category
    2      1    u8     Parameter
    3      1    u8     Data type
    4      12   ?      padding
    16     8    ?      variable data, absent for commands.
    ====== ==== ====== ===========

    ========== ===========
    Data type  Description
    ========== ===========
    0          Boolean, or no data
    1          Signed byte
    2          Signed short
    3          Signed integer
    4          Signed long
    5          UTF-8 data
    128        16-bit Fixed point
    ========== ===========

    ========== ======== ======== ===========
    Command    DataType Elements Description
    ========== ======== ======== ===========
    0.0        fixed16  1        Focus 0=near 1=far
    0.1        -        0        Trigger autofocus
    0.2        fixed16  1        Aperture f-stop
    0.3        fixed16  1        Aperture normalized 0=closed 1=open
    0.4        fixed16  1        Aperture by index 0...n
    0.5        -        0        Trigger auto aperture
    0.6        boolean  1        Enable optical image stabilisation
    0.7        int16    1        Zoom, focal length in mm
    0.8        fixed16  1        Zoom, normalized 0.0...1.0
    0.9        fixed16  1        Zoom, rate -1.0...1.0
    1.0        int8     5        Frame rate, M-rate, dimensions, interlaced, colorpsace
    1.1        int8     1        Gain, absolute iso as ISO/100
    1.2        int16    2        White balance, temperature 2500...10000, tint -50...50
    1.3        -        0        Trigger auto whitebalance
    1.4        -        0        Restore previous auto whitebalance
    1.5        int32    1        Exposure time in us
    1.6        int16    1        Exposure by index 0...n
    1.7        int8     1        Dynamic range mode, 0=film 1=video
    1.8        int8     1        Sharpening level, 0=off, 1=low, 2=medium, 3=high
    1.9        int16    1        Recording format
    1.10       int8     1        Auto exposure mode, 0=manual trigger, 1=iris, 2=shutter, 3=iris+shutter, 4=shutter+iris
    1.11       int32    1        Shutter angle in degrees*100 100...36000
    1.12       int32    1        Shutter speed in 1/n, 24...2000
    1.13       int8     1        Gain in dB, -128...127
    1.14       int32    1        Gain in iso value
    2.0        fixed16  1        Mic level 0.0...1.0
    2.1        fixed16  1        Headphone level 0.0...1.0
    2.2        fixed16  1        Headphone program mix 0.0...1.0
    2.3        fixed16  1        Speaker level 0.0...1.0
    2.4        int8     1        Input type, 0=internal mic, 1=line in, 2=low gain mic in, 3=high gain mic in
    2.5        fixed16  2        Input levels, one element per channel. 0.0...1.0
    2.6        boolean  1        Phantom power enabled
    3.0        uint16   1        Enable overlays, undocumented bitfield
    3.1        int8     1        Frame guide style, enum
    3.2        fixed16  1        Frame guide opacity
    3.3        int8     4        Overlay settings
    4.0        fixed16  1        Display brightness 0.0...1.0
    4.1        uint16   1        Display overlay enable, undocumented
    4.2        fixed16  1        Display zebra level, 0.0...1.0
    4.3        fixed16  1        Display peaking levle, 0.0...1.0
    4.4        int8     1        Enable bars with timeout, 0=disable, 1...30=seconds
    4.5        int8     2        Display focus assist, first element is method and second element is color
    5.0        fixed16  1        Tally brightness, 0.0...1.0
    5.1        fixed16  1        Tally front brightness, 0.0...1.0
    5.2        fixed16  1        Tally rear brightness, 0.0...1.0
    6.0        int8     1        Reference source, 0=internal, 1=program, 2=external
    6.1        int32    1        Reference offset in pixels
    7.0        int32    2        Real time clock value
    7.1        utf8     1        System language
    7.2        int32    1        Timezone offset, minute from UTC
    7.3        int64    2        Location, latitude and longitude
    8.0        fixed16  4        Primary color corrector lift, RGBY
    8.1        fixed16  4        Primary color corrector gamma, RGBY
    8.2        fixed16  4        Primary color corrector gain, RGBY
    8.3        fixed16  4        Primary color corrector offset, RGBY
    8.4        fixed16  2        Contrast, pivot 0.0..1.0, adjustment 0.0...2.0
    8.5        fixed16  1        Luma mix, 0.0...1.0
    8.6        fixed16  2        Color adjust, hue -1.0...1.0, saturation 0.0...2.0
    8.7        -        0        Reset color corrector to defaults
    10.0       int8     2        Codec enum
    10.1       int8     4        Transport mode
    11.0       fixed16  2        PTZ Control, pan velocity -1.0...1.0, tilt velocity -1.0...1.0
    11.1       int8     2        PTZ memory preset. command 0=reset, 1=store, 2=recall. Slot ID 0...5
    ========== ===========


    After parsing:
    :ivar destination: Command destination address
    :ivar category: First number of the command
    :ivar parameter: Second number of the command
    :ivar datatype: Data type
    :ivar data: Data attached to the command
    """

    CODE = "CCdP"

    def __init__(self, raw):
        self.raw = raw
        self.destination, self.category, self.parameter, self.datatype, *weird = struct.unpack_from('>4B 4B 4B', raw, 0)

        num_elements = sum(weird)
        num_overrides = {
            (0, 0): 1,
            (0, 1): 0,
            (0, 2): 1,
            (0, 3): 1.,
            (0, 4): 1,
            (0, 6): 1,
            (1, 2): 2
        }
        if (self.category, self.parameter) in num_overrides:
            num_elements = num_overrides[(self.category, self.parameter)]
        self.length = num_elements

        self.data = None
        if len(raw) > 16:
            dfmt = '>'
            if self.datatype == 0:  # Boolean
                dfmt += '?' * num_elements
            elif self.datatype == 1:  # Signed byte
                dfmt += 'b' * num_elements
            elif self.datatype == 2:  # Signed short
                dfmt += 'h' * num_elements
            elif self.datatype == 3:  # Signed int
                dfmt += 'i' * num_elements
            elif self.datatype == 4:  # Signed long
                dfmt += 'q' * num_elements
            elif self.datatype == 5:  # UTF-8
                pass
            elif self.datatype == 128:  # Fixed 16
                dfmt += 'h' * num_elements
            self.data = struct.unpack_from(dfmt, raw, 16)
            if self.datatype == 128:
                self.data = self.unpack_fixed16(self.data)

    def unpack_fixed16(self, raw):
        result = []
        for f16 in raw:
            result.append(f16 / (2 ** 11))
        return result

    def __repr__(self):
        return '<camera-control-data-packet dest={} command={}.{} type={} data={}>'.format(self.destination,
                                                                                           self.category,
                                                                                           self.parameter,
                                                                                           self.datatype,
                                                                                           self.data)


class StreamingAudioBitrateField(FieldBase):
    """
    Data from the `STAB`. This is the audio bitrate for the internal encoder used for recording and streaming
    This is always 128k for min and max on tested devices.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      4    u32    Min bitrate
    4      4    u32    Max bitrate
    ====== ==== ====== ===========

    """

    CODE = "STAB"

    def __init__(self, raw):
        self.raw = raw
        self.min, self.max = struct.unpack('>II', raw)

    def __repr__(self):
        return '<streaming-audio-bitrate min={} max={}>'.format(self.min, self.max)


class StreamingServiceField(FieldBase):
    """
    Data from the `SRSU`. This the settings for the live stream output, it also sets the video bitrate for
    the internal encoder which is shared with the recorder component so this influences recording quality.

    The ATEM Software Control application only uses the rtsp URL to display the streaming service name and
    has a preset list of rtsp urls for various streaming services.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      64   char[] Service display name
    65     512  char[] Target rtsp url
    557    512  char[] Stream key/secret
    1089   4    u32    Video bitrate minimum
    1093   4    u32    Video bitrate maximum
    ====== ==== ====== ===========

    """

    CODE = "SRSU"

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack_from('>64s512s512sII', raw, 0)
        self.name = self._get_string(field[0])
        self.url = self._get_string(field[1])
        self.key = self._get_string(field[2])
        self.min = field[3]
        self.max = field[4]

    def __repr__(self):
        return '<streaming-service {} url={} min={} max={}>'.format(self.name, self.url, self.min,
                                                                    self.max)


class StreamingStatusField(FieldBase):
    """
    Data from the `StRS`. The displayed status of the live stream

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    i16    Status
    2      2    ?      unknown
    ====== ==== ====== ===========

    ====== =====
    Status Value
    ====== =====
    -1     unknown
    0      nothing?
    1      idle
    2      connecting
    4      on-air
    22     stopping
    36     stopping
    ====== =====
    """

    CODE = "StRS"

    def __init__(self, raw):
        self.raw = raw
        self.status, = struct.unpack('>h 2x', raw)

    def __repr__(self):
        return '<streaming-status status={}>'.format(self.status)


class StreamingStatsField(FieldBase):
    """
    Data from the `SRSS`. The displayed status of the live stream

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      4    u32    Bitrate
    4      2    u16    Cache used
    ====== ==== ====== ===========

    """

    CODE = "SRSS"

    def __init__(self, raw):
        self.raw = raw
        self.bitrate, self.cache = struct.unpack('>IHxx', raw)

    def __repr__(self):
        return '<streaming-stats bitrate={} cache={}>'.format(self.bitrate, self.cache)


class AutoInputVideoModeField(FieldBase):
    """
    Data from the `AiVM`. This field only exists for hardware that can auto-detect a video mode from the input signal.
    This defines wether the auto detection is enabled and shows if it has actually detected a signal

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    bool   Enabled
    1      1    bool   Detected
    2      2    ?      unknown
    ====== ==== ====== ===========

    After parsing:

    :ivar enabled: Auto mode detection is enabled
    :ivar detected: A video mode has been detected from an input
    """

    CODE = "AiVM"

    def __init__(self, raw):
        self.raw = raw
        self.enabled, self.detected = struct.unpack('>??2x', raw)

    def __repr__(self):
        return '<auto-input-video-mode: enabled={} detected={}>'.format(self.enabled, self.detected)


class InitCompleteField(FieldBase):
    """
    Data from the `InCm`. This notifies the app that all the initial state has been sent

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      4    ?      unknown
    ====== ==== ====== ===========
    """

    CODE = "InCm"

    def __init__(self, raw):
        self.raw = raw

    def __repr__(self):
        return '<init-complete>'


class TransferCompleteField(FieldBase):
    """
    Data from the `*XFC`. This is an command that's part of OpenSwitcher for the TCP protocol and not part
    of the actual ATEM protocol. This command is send over the TCP connection when the upstream atem has completed
    a file transfer

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Store
    2      2    u16    Slot
    4      1    bool   Is upload
    5      3    x      padding
    ====== ==== ====== ===========

    After parsing:

    :ivar store: Transfer store index
    :ivar slot: Transfer slot index
    :ivar upload: True if the transfer was an upload, False if the transfer was a download
    """

    CODE = "*XFC"

    def __init__(self, raw):
        self.raw = raw
        self.store, self.slot, self.upload = struct.unpack('>HH ?xxx', raw)

    def __repr__(self):
        return '<*transfer-complete: store={} slot={} upload={}>'.format(self.store, self.slot, self.upload)
