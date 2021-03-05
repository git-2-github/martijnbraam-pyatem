import colorsys
import struct

from hexdump import hexdump


class Command:
    def get_command(self):
        pass

    def _make_command(self, name, data):
        header = struct.pack('>H 2x 4s', len(data) + 8, name.encode())
        return header + data


class CutCommand(Command):
    """
    Implementation of the `DCut` command. This is equivalent to pressing the CUT button in the UI

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      3    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, index):
        """
        :param index: 0-indexed M/E number to send the CUT to
        """
        self.index = index

    def get_command(self):
        data = struct.pack('>B 3x', self.index)
        return self._make_command('DCut', data)


class AutoCommand(Command):
    """
    Implementation of the `DAut` command. This is equivalent to pressing the CUT button in the UI

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      3    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, index):
        """
        :param index: 0-indexed M/E number to send the AUTO transition to
        """
        self.index = index

    def get_command(self):
        data = struct.pack('>B 3x', self.index)
        return self._make_command('DAut', data)


class ProgramInputCommand(Command):
    """
    Implementation of the `CPgI` command. This is equivalent to pressing the buttons on the program bus on a control
    panel.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    ?      unknown
    2      2    u16    Source index
    ====== ==== ====== ===========

    """

    def __init__(self, index, source):
        """
        :param index: 0-indexed M/E number to control the program bus of
        :param source: Source index to activate on the program bus
        """
        self.index = index
        self.source = source

    def get_command(self):
        data = struct.pack('>B x H', self.index, self.source)
        return self._make_command('CPgI', data)


class PreviewInputCommand(Command):
    """
    Implementation of the `CPvI` command. This is equivalent to pressing the buttons on the preview bus on a control
    panel.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    ?      unknown
    2      2    u16    Source index
    ====== ==== ====== ===========

    """

    def __init__(self, index, source):
        """
        :param index: 0-indexed M/E number to control the preview bus of
        :param source: Source index to activate on the preview bus
        """
        self.index = index
        self.source = source

    def get_command(self):
        data = struct.pack('>B x H', self.index, self.source)
        return self._make_command('CPvI', data)


class TransitionPositionCommand(Command):
    def __init__(self, index, position):
        self.index = index
        self.position = position

    def get_command(self):
        position = self.position
        data = struct.pack('>BxH', self.index, position)
        return self._make_command('CTPs', data)


class TransitionSettingsCommand(Command):
    """
    Implementation of the `CTTp` command. This is equivalent to pressing the buttons on the preview bus on a control
    panel.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask, bit0=set style, bit1=set next transition
    1      1    u8     M/E index
    2      1    u8     Style
    3      1    u8     Next transition
    ====== ==== ====== ===========

    """

    def __init__(self, index, style=None, next_transition=None):
        """
        :param index: 0-indexed M/E number to control the preview bus of
        :param style: Set new transition style, or None
        :param style: Set next transition layers, or None
        """

        self.index = index
        self.style = style
        self.next_transition = next_transition

    def get_command(self):
        mask = 0
        if self.style is not None:
            mask |= 0x01
        if self.next_transition is not None:
            mask |= 0x02

        style = 0 if self.style is None else self.style
        next_transition = 0 if self.next_transition is None else self.next_transition
        data = struct.pack('>BBBB', mask, self.index, style, next_transition)
        return self._make_command('CTTp', data)


class TransitionPreviewCommand(Command):
    """
    Implementation of the `CTPr` command. This sets the state of the Transition Preview function of the mixer

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    bool   Preview enabled
    2      2    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, index, enabled):
        """
        :param index: 0-indexed M/E number to control the preview bus of
        :param enabled: New state of the preview function
        """
        self.index = index
        self.enabled = enabled

    def get_command(self):
        data = struct.pack('>B ? 2x', self.index, self.enabled)
        return self._make_command('CTPr', data)


class ColorGeneratorCommand(Command):
    """
    Implementation of the `CClV` command. This sets the color for a color generator

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Set mask
    1      1    u8     Color generator index
    2      2    u16    Hue [0-3599]
    4      2    u16    Saturation [0-1000]
    6      2    u16    Luma [0-1000]
    ====== ==== ====== ===========

    """

    def __init__(self, index, hue=None, saturation=None, luma=None):
        """
        :param index: Color generator index
        :param hue: New Hue for the generator, or None
        :param saturation: New Saturation for the generator, or None
        :param luma: New Luma for the generator, or None
        """
        self.index = index
        self.hue = hue
        self.luma = luma
        self.saturation = saturation

    @classmethod
    def from_rgb(cls, index, red, green, blue):
        h, l, s = colorsys.rgb_to_hls(red, green, blue)
        return cls(index, hue=h * 359, saturation=s, luma=l)

    def get_command(self):
        mask = 0
        if self.hue is not None:
            mask |= 0x01
        if self.saturation is not None:
            mask |= 0x02
        if self.luma is not None:
            mask |= 0x04

        hue = 0 if self.hue is None else int(self.hue * 10)
        saturation = 0 if self.saturation is None else int(self.saturation * 1000)
        luma = 0 if self.luma is None else int(self.luma * 1000)
        data = struct.pack('>BB 3H', mask, self.index, hue, saturation, luma)
        return self._make_command('CClV', data)


class FadeToBlackCommand(Command):
    """
    Implementation of the `FtbA` command. This triggers the fade-to-black transition

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    ?      unknown
    2      1    ?      unknown
    3      1    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, index):
        """
        :param index: 0-indexed M/E number to trigger FtB on
        """
        self.index = index

    def get_command(self):
        data = struct.pack('>B 3x', self.index)
        return self._make_command('FtbA', data)


class FadeToBlackConfigCommand(Command):
    """
    Implementation of the `FtbC` command. This sets the duration for the fade-to-black block

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask, always 1
    1      1    u8     M/E index
    2      1    u8     frames
    3      1    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, index, frames):
        """
        :param index: 0-indexed M/E number to configure
        :param index: Number of frames in the FTB transition
        """
        self.index = index
        self.frames = frames

    def get_command(self):
        data = struct.pack('>BBBx', 1, self.index, self.frames)
        return self._make_command('FtbC', data)


class CaptureStillCommand(Command):
    """
    Implementation of the `Capt` command. This saves the current frame of the program output into the media slots

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
                       this command has no data
    ====== ==== ====== ===========

    """

    def get_command(self):
        return self._make_command('Capt', b'')


class DkeyOnairCommand(Command):
    """
    Implementation of the `CDsL` command. This setting the "on-air" state of the downstream keyer on or off
    panel.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Keyer index, 0-indexed
    1      1    ?      On air
    2      2    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, index, on_air):
        """
        :param index: 0-indexed DSK number to control
        :param on_air: The new on-air state for the keyer
        """
        self.index = index
        self.on_air = on_air

    def get_command(self):
        data = struct.pack('>B?xx', self.index, self.on_air)
        return self._make_command('CDsL', data)


class DkeyTieCommand(Command):
    """
    Implementation of the `CDsT` command. This setting the "tie" state of the downstream keyer on or off
    panel.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Keyer index, 0-indexed
    1      1    ?      Tie
    2      2    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, index, tie):
        """
        :param index: 0-indexed DSK number to control
        :param tie: The new tie state for the keyer
        """
        self.index = index
        self.tie = tie

    def get_command(self):
        data = struct.pack('>B?xx', self.index, self.tie)
        return self._make_command('CDsT', data)


class DkeyAutoCommand(Command):
    """
    Implementation of the `DDsA` command. This triggers the auto transition of a downstream keyer
    panel.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Keyer index, 0-indexed
    1      3    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, index):
        """
        :param index: 0-indexed DSK number to trigger
        """
        self.index = index

    def get_command(self):
        data = struct.pack('>Bxxx', self.index)
        return self._make_command('DDsA', data)


class DkeyRateCommand(Command):
    """
    Implementation of the `CDsR` command. This sets the transition rate for the downstream keyer
    panel.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Keyer index, 0-indexed
    1      1    u8     Rate in frames
    2      2    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, index, rate):
        """
        :param index: 0-indexed DSK number to change
        :param rate: New rate for the keyer
        """
        self.index = index
        self.rate = rate

    def get_command(self):
        data = struct.pack('>BBxx', self.index, self.rate)
        return self._make_command('CDsR', data)


class MixSettingsCommand(Command):
    """
    Implementation of the `CTMx` command. This sets the transition duration for the mix transition
    panel.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index, 0-indexed
    1      1    u8     Rate in frames
    2      2    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, index, rate):
        """
        :param index: 0-indexed DSK number to trigger
        :param rate: Transition length in frames
        """
        self.index = index
        self.rate = rate

    def get_command(self):
        data = struct.pack('>BBxx', self.index, self.rate)
        return self._make_command('CTMx', data)


class DipSettingsCommand(Command):
    """
    Implementation of the `CTDp` command. This sets the settings for the dip transition
    panel.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask, bit0=set rate, bit1=set source
    1      1    u8     M/E index
    2      1    u8     Rate in frames
    3      1    ?      unknown
    4      2    u16    Source index
    6      2    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, index, rate=None, source=None):
        """
        :param index: 0-indexed M/E number to control the preview bus of
        :param rate: Set new transition rate, or None
        :param source: Set the dip source, or None
        """

        self.index = index
        self.rate = rate
        self.source = source

    def get_command(self):
        mask = 0
        if self.rate is not None:
            mask |= 0x01
        if self.source is not None:
            mask |= 0x02

        rate = 0 if self.rate is None else self.rate
        source = 0 if self.source is None else self.source
        data = struct.pack('>BBBx H 2x', mask, self.index, rate, source)
        return self._make_command('CTDp', data)


class WipeSettingsCommand(Command):
    """
    Implementation of the `CTWp` command. This sets the settings for the wipe transition
    panel.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Mask, see table below
    2      1    u8     M/E index
    3      1    u8     Rate in frames
    4      1    u8     Pattern style [0-17]
    5      1    ?      unknown
    6      2    u16    Border width [0-10000]
    8      2    u16    Border fill source
    10     2    u16    Symmetry [0-10000]
    12     2    u16    Softness [0-10000]
    14     2    16     Transition origin x [0-10000]
    16     2    16     Transition origin y [0-10000]
    18     1    bool   Reverse
    19     1    bool   Flip flop
    ====== ==== ====== ===========

    === ==========
    Bit Mask value
    === ==========
    0   Rate
    1   Pattern
    2   Border width
    3   Border fill source
    4   Symmetry
    5   Softness
    6   Position x
    7   Position y
    8   Reverse
    9   Flip flop
    === ==========
    """

    def __init__(self, index, rate=None, pattern=None, width=None, source=None, symmetry=None, softness=None,
                 positionx=None, positiony=None, reverse=None, flipflop=None):
        """
        :param index: 0-indexed M/E number to control the preview bus of
        :param rate: Set new transition rate, or None
        :param pattern: Set transition pattern id, or None
        :param width: Set transition border width, or None
        :param source: Set transition border fill source index, or None
        :param symmetry: Set transition symmetry, or None
        :param softness: Set transition softness, or None
        :param positionx: Set transition origin x, or None
        :param positiony: Set transition origin y, or None
        :param reverse: Set the reverse flag for the transition, or None
        :param flipflop: Set the flipflop flag for the transition, or None
        """

        self.index = index
        self.rate = rate
        self.pattern = pattern
        self.width = width
        self.source = source
        self.symmetry = symmetry
        self.softness = softness
        self.positionx = positionx
        self.positiony = positiony
        self.reverse = reverse
        self.flipflop = flipflop

    def get_command(self):
        mask = 0
        if self.rate is not None:
            mask |= 1 << 0
        if self.pattern is not None:
            mask |= 1 << 1
        if self.width is not None:
            mask |= 1 << 2
        if self.source is not None:
            mask |= 1 << 3
        if self.symmetry is not None:
            mask |= 1 << 4
        if self.softness is not None:
            mask |= 1 << 5
        if self.positionx is not None:
            mask |= 1 << 6
        if self.positiony is not None:
            mask |= 1 << 7
        if self.reverse is not None:
            mask |= 1 << 8
        if self.flipflop is not None:
            mask |= 1 << 9

        rate = 0 if self.rate is None else self.rate
        pattern = 0 if self.pattern is None else self.pattern
        width = 0 if self.width is None else self.width
        source = 0 if self.source is None else self.source
        symmetry = 0 if self.symmetry is None else self.symmetry
        softness = 0 if self.softness is None else self.softness
        x = 0 if self.positionx is None else self.positionx
        y = 0 if self.positiony is None else self.positiony
        reverse = False if self.reverse is None else self.reverse
        flipflop = False if self.flipflop is None else self.flipflop
        data = struct.pack('>HBBBx HHHHHH??', mask, self.index, rate, pattern, width, source, symmetry, softness, x, y,
                           reverse, flipflop)
        return self._make_command('CTWp', data)


class DveSettingsCommand(Command):
    """
    Implementation of the `CTDv` command. This sets the settings for the DVE transition
    panel.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Mask, see table below
    2      1    u8     M/E index
    3      1    u8     Rate in frames
    4      1    u8     Pattern style [0-17]
    5      1    ?      unknown
    6      2    u16    Fill source index
    8      2    u16    Key source index
    10     1    bool   Enable key
    11     1    bool   Key is premultiplied
    12     2    u16    Key clip [0-1000]
    14     2    u16    Key gain [0-1000]
    16     1    bool   Invert key
    17     1    bool   Reverse transition direction
    18     1    bool   Enable flip-flop
    19     1    ?      unknown
    ====== ==== ====== ===========

    === ==========
    Bit Mask value
    === ==========
    0   Rate
    1   ?
    2   Style
    3   Fill source
    4   Key source
    5   Enable key
    6   Key is premultiplied
    7   Key clip
    8   Key gain
    9   Invert key
    10  Reverse
    11  Flip-flop
    === ==========
    """

    def __init__(self, index, rate=None, style=None, fill_source=None, key_source=None, key_enable=None,
                 key_premultiplied=None, key_clip=None, key_gain=None, key_invert=None, reverse=None, flipflop=None):
        """
        :param index: 0-indexed M/E number to control the preview bus of
        :param rate: Set new transition rate, or None
        :param style: Set new transition style, or None
        :param fill_source: Set new fill source, or None
        :param key_source: Set new key source, or None
        :param key_enable: Enable the keyer, or None
        :param key_premultiplied: Key is premultiplied alpha, or None
        :param key_clip: Key clip, or None
        :param key_gain: Key gain, or None
        :param key_invert: Invert the key source, or None
        :param reverse: Set the reverse flag for the transition, or None
        :param flipflop: Set the flipflop flag for the transition, or None
        """

        self.index = index
        self.rate = rate
        self.style = style
        self.fill_source = fill_source
        self.key_source = key_source
        self.key_enable = key_enable
        self.key_premultiplied = key_premultiplied
        self.key_clip = key_clip
        self.key_gain = key_gain
        self.key_invert = key_invert
        self.reverse = reverse
        self.flipflop = flipflop

    def get_command(self):
        mask = 0
        if self.rate is not None:
            mask |= 1 << 0
        if self.style is not None:
            mask |= 1 << 2
        if self.fill_source is not None:
            mask |= 1 << 3
        if self.key_source is not None:
            mask |= 1 << 4
        if self.key_enable is not None:
            mask |= 1 << 5
        if self.key_premultiplied is not None:
            mask |= 1 << 6
        if self.key_clip is not None:
            mask |= 1 << 7
        if self.key_gain is not None:
            mask |= 1 << 8
        if self.key_invert is not None:
            mask |= 1 << 9
        if self.reverse is not None:
            mask |= 1 << 10
        if self.flipflop is not None:
            mask |= 1 << 11

        rate = 0 if self.rate is None else self.rate
        style = 0 if self.style is None else self.style
        fill_source = 0 if self.fill_source is None else self.fill_source
        key_source = 0 if self.key_source is None else self.key_source
        key_enable = False if self.key_enable is None else self.key_enable
        key_premultiplied = False if self.key_premultiplied is None else self.key_premultiplied
        key_clip = 0 if self.key_clip is None else self.key_clip
        key_gain = 0 if self.key_gain is None else self.key_gain
        key_invert = False if self.key_invert is None else self.key_invert
        reverse = False if self.reverse is None else self.reverse
        flipflop = False if self.flipflop is None else self.flipflop
        data = struct.pack('>HBBx BHH ??HH? ?? x', mask, self.index, rate, style, fill_source, key_source, key_enable,
                           key_premultiplied, key_clip, key_gain, key_invert, reverse, flipflop)
        return self._make_command('CTDv', data)


class FairlightMasterPropertiesCommand(Command):
    """
    Implementation of the `CFMP` command. This sets the settings the master channel of fairlight audio.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask, see table below
    6      2    i16    EQ gain [-2000 - 2000]
    10     2    u16    Dynamics make-up gain [0 - 2000]
    12     4    i32    Master volume [-10000 - 1000]
    16     1    bool   Audio follow video
    17     1    bool   Enable master EQ
    18     2    ?      unknown
    ====== ==== ====== ===========

    === ==========
    Bit Mask value
    === ==========
    0   EQ Enable
    1   EQ Gain
    2   Dynamics gain
    3   Master volume
    4   AFV
    5   ?
    6   ?
    7   ?
    === ==========


    """

    def __init__(self, eq_gain=None, dynamics_gain=None, volume=None, afv=None, eq_enable=None):
        """
        :param index: 0-indexed M/E number to control the preview bus of
        """

        self.eq_gain = eq_gain
        self.dynamics_gain = dynamics_gain
        self.volume = volume
        self.afv = afv
        self.eq_enable = eq_enable

    def get_command(self):
        mask = 0
        if self.eq_enable is not None:
            mask |= 1 << 0
        if self.eq_gain is not None:
            mask |= 1 << 1
        if self.dynamics_gain is not None:
            mask |= 1 << 2
        if self.volume is not None:
            mask |= 1 << 3
        if self.afv is not None:
            mask |= 1 << 4

        eq_enable = False if self.eq_enable is None else self.eq_enable
        eq_gain = 0 if self.eq_gain is None else self.eq_gain
        dynamics_gain = 0 if self.dynamics_gain is None else self.dynamics_gain
        volume = 0 if self.volume is None else self.volume
        afv = False if self.afv is None else self.afv

        data = struct.pack('>B 5x h 2x Hi?? 2x', mask, eq_gain, dynamics_gain, volume, afv, eq_enable)
        return self._make_command('CFMP', data)


class FairlightStripPropertiesCommand(Command):
    """
    Implementation of the `CFSP` command. This sets the settings of a channel strip in fairlight audio.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Mask, see table below
    2      2    u16    Source index
    15     1    u8     Channel number
    16     1    u8     Delay in frames
    22     2    i16    Gain [-10000 - 600]
    30     2    i16    EQ Gain
    34     2    u16    Dynamics Gain
    36     2    i16    Pan [-10000 - 10000]
    40     4    i32    volume [-10000 - 1000]
    44     1    u8     State
    45     3    ?      unknown
    ====== ==== ====== ===========

    === ==========
    Bit Mask value
    === ==========
    0   Delay
    1   Gain
    2   ?
    3   EQ Enable
    4   EQ Gain
    5   Dynamics gain
    6   Balance
    7   Volume
    8   State
    === ==========


    """

    def __init__(self, source, channel, delay=None, gain=None, eq_gain=None, dynamics_gain=None, balance=None,
                 volume=None, state=None):
        """
        :param index: 0-indexed M/E number to control the preview bus of
        """
        self.source = source
        self.channel = channel
        self.delay = delay
        self.gain = gain
        self.eq_gain = eq_gain
        self.dynamics_gain = dynamics_gain
        self.balance = balance
        self.volume = volume
        self.state = state

    def get_command(self):
        mask = 0
        if self.delay is not None:
            mask |= 1 << 0
        if self.gain is not None:
            mask |= 1 << 1
        if self.eq_gain is not None:
            mask |= 1 << 4
        if self.dynamics_gain is not None:
            mask |= 1 << 5
        if self.balance is not None:
            mask |= 1 << 6
        if self.volume is not None:
            mask |= 1 << 7
        if self.state is not None:
            mask |= 1 << 8

        delay = 0 if self.delay is None else self.delay
        gain = 0 if self.gain is None else self.gain
        eq_gain = 0 if self.eq_gain is None else self.eq_gain
        dynamics_gain = 0 if self.dynamics_gain is None else self.dynamics_gain
        balance = 0 if self.balance is None else self.balance
        volume = 0 if self.volume is None else self.volume
        state = 0 if self.state is None else self.state

        split = 0xff if self.channel > -1 else 0x01
        self.channel = 0x00 if self.channel == -1 else self.channel
        pad = b'\xff\xff\xff\xff\xff\xff\xff'
        data = struct.pack('>H H4x6sBb B 5x h 6x h 2x Hh 2x iB 3x', mask, self.source, pad, split, self.channel, delay,
                           gain, eq_gain,
                           dynamics_gain, balance, volume, state)
        return self._make_command('CFSP', data)


class KeyOnAirCommand(Command):
    """
    Implementation of the `CKOn` command. This enables an upstream keyer without having a transition.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index, 0-indexed
    1      1    u8     Keyer index
    2      1    bool   Enabled
    4      1    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, index, keyer, enabled):
        """
        :param index: 0-indexed DSK number to trigger
        :param keyer: 0-indexed keyer number
        :param enabled: Set the keyer on-air or disabled
        """
        self.index = index
        self.keyer = keyer
        self.enabled = enabled

    def get_command(self):
        data = struct.pack('>BB?x', self.index, self.keyer, self.enabled)
        return self._make_command('CKOn', data)


class KeyFillCommand(Command):
    """
    Implementation of the `CKeF` command. This enables an upstream keyer without having a transition.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index, 0-indexed
    1      1    u8     Keyer index
    2      2    u16    Source index
    ====== ==== ====== ===========

    """

    def __init__(self, index, keyer, source):
        """
        :param index: 0-indexed DSK number to trigger
        :param keyer: 0-indexed keyer number
        :param source: Source index for the keyer fill
        """
        self.index = index
        self.keyer = keyer
        self.source = source

    def get_command(self):
        data = struct.pack('>BBH', self.index, self.keyer, self.source)
        return self._make_command('CKeF', data)


class LockCommand(Command):
    """
    Implementation of the `LOCK` command. This requests a new lock, used for data transfers.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u16    Store index
    2      1    bool   Lock state
    3      1    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, store, state):
        """
        :param index: 0-indexed DSK number to trigger
        :param keyer: 0-indexed keyer number
        :param source: Source index for the keyer fill
        """
        self.store = store
        self.state = state

    def get_command(self):
        data = struct.pack('>H?x', self.store, self.state)
        return self._make_command('LOCK', data)


class TransferDownloadRequestCommand(Command):
    """
    Implementation of the `FTSU` command. This requests download from the switcher to the client.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Tranfer id
    2      2    u16    Store
    4      2    u16    Slot
    8      4    u32    unknown
    ====== ==== ====== ===========

    """

    def __init__(self, transfer, store, slot):
        """
        :param transfer: Unique transfer number
        :param store: Store index
        :param slot: Slot index
        """
        self.transfer = transfer
        self.store = store
        self.slot = slot

    def get_command(self):
        data = struct.pack('>HHH2xI', self.transfer, self.store, self.slot, 0x00965340)
        return self._make_command('FTSU', data)


class TransferAckCommand(Command):
    """
    Implementation of the `FTUA` command. This is an acknowledgement for FTDa packets.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Tranfer id
    2      2    u16    Slot
    ====== ==== ====== ===========

    """

    def __init__(self, transfer, slot):
        """
        :param transfer: Unique transfer number
        :param slot: Slot index
        """
        self.transfer = transfer
        self.slot = slot

    def get_command(self):
        data = struct.pack('>HH', self.transfer, self.slot)
        return self._make_command('FTUA', data)
