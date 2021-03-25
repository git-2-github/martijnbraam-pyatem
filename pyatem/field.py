import colorsys
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

    :ivar index: 0-based M/E index
    :ivar keyers: Number of upstream keyers on this M/E
    """

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

        if self.mode in modes:
            self.resolution = modes[self.mode][0]
            self.interlaced = modes[self.mode][1]
            self.rate = modes[self.mode][2]

    def get_label(self):
        if self.resolution is None:
            return 'unknown [{}]'.format(self.mode)

        pi = 'p'
        if self.interlaced:
            pi = 'i'
        return '{}{}{}'.format(self.resolution, pi, self.rate)

    def __repr__(self):
        return '<video-mode: mode={}: {}>'.format(self.mode, self.get_label())


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
    :ivar port_type: Integer describing the port type
    :ivar available_aux: Source can be routed to AUX
    :ivar available_multiview: Source can be routed to multiview
    :ivar available_supersource_art: Source can be routed to supersource
    :ivar available_supersource_box: Source can be routed to supersource
    :ivar available_key_source: Source can be used as keyer key source
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
        return '<tally-index: num={}, val={}>'.format(self.num, self.tally)


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

    def __init__(self, raw):
        self.raw = raw
        namelen = len(raw) - 23
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

    ====== ==== ====== ========= ======= ====== ===========
    Offset Size Type   Atem Mini 1M/E 4k TVS HD Description
    ====== ==== ====== ========= ======= ====== ===========
    0      1    u8     1         1       1      Number of M/E units
    1      1    u8     14        31      24     Sources
    2      1    u8     1         2       2      Downstream keyers
    3      1    u8     1         3       1      AUX busses
    4      1    u8     0         0       4      MixMinus Outputs
    5      1    u8     1         2       2      Media players
    6      1    u8     0         1       1      Multiviewers
    7      1    u8     0         1       1      rs485
    8      1    u8     4         4       4      Hyperdecks
    9      1    u8     1         1       1      DVE
    10     1    u8     0         1       0      Stingers
    11     1    u8     0         0       0      supersources
    12     1    u8     0         1       1      ?
    13     1    u8     0         0       1      Talkback channels
    14     1    u8     0         0       4      ?
    15     1    u8     1         0       0      ?
    16     1    u8     0         0       0      ?
    17     1    u8     0         1       0      ?
    18     1    u8     1         1       1      Camera Control
    19     1    u8     0         1       1      ?
    20     1    u8     0         1       1      ?
    21     1    u8     0         1       1      ?
    22     1    u8     1         0       0      Advanced chroma keyers
    23     1    u8     1         0       0      Only configurable outputs
    24     1    u8     1         0       0      ?
    25     1    u8     0x20      0x20    0x10   ?
    26     1    u8     3         0       0      ?
    27     1    u8     0xe8      0x00    0x0    ?
    ====== ==== ====== ========= ======= ====== ===========


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

    def __repr__(self):
        return '<topology, me={} sources={} aux={}>'.format(self.me_units, self.sources, self.aux_outputs)


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

    def __init__(self, raw):
        self.raw = raw
        self.index, self.type, self.number, self.plug, self.state, self.volume, self.balance = struct.unpack(
            '>HB 2x B x BB x Hh 2x', raw)
        self.strip_id = str(self.index) + '.0'

    def __repr__(self):
        return '<audio-input index={} type={} plug={}>'.format(self.index, self.type, self.plug)


class KeyPropertiesBaseField(FieldBase):
    """
    Data from the `KeBP`. The upstream keyer base properties.
    """

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
    Data from the `RTMS`. The status for the stream recorder.

    ====== ==== ====== ===========
    Offset Size Type   Descriptions
    ====== ==== ====== ===========
    0      2    u16    Recording status
    4      4    i32    Total recording time available
    ====== ==== ====== ===========

    === ==========
    Bit Status value
    === ==========
    0   Idle
    1   Recording
    2   Disk full
    3   Disk error
    4   Disk unformatted
    5   Frames dropped
    6   ?
    7   ?
    8   Stopping
    === ==========

    """

    def __init__(self, raw):
        self.raw = raw
        field = struct.unpack('>H2xi', raw)
        self.status = field[0]
        self.time_available = field[1] if field[1] != -1 else None

    def __repr__(self):
        return '<recording-status status={} time-available={}>'.format(self.status, self.time_available)


class RecordingDurationField(FieldBase):
    """
    Data from the `RTMS`. The status for the stream recorder.

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
