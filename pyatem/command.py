import colorsys
import struct


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
    Implementation of the `DAut` command. This is equivalent to pressing the AUTO button in the UI

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


class AuxSourceCommand(Command):
    """
    Implementation of the `CAuS` command. This selects the source that will be sent to a specific AUX output

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask, always 1
    1      1    u8     AUX index
    2      2    u16    Source index
    ====== ==== ====== ===========

    """

    def __init__(self, index, source):
        """
        :param index: 0-indexed AUX output number
        :param source: Source index to send to the aux output
        """
        self.index = index
        self.source = source

    def get_command(self):
        data = struct.pack('>BBH', 1, self.index, self.source)
        return self._make_command('CAuS', data)


class TransitionPositionCommand(Command):
    """
    Implementation of the `CTPs` command. This sets the state and position for the transition T-bar control.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    ?      unknown
    2      2    u16    Position [0-10000]
    ====== ==== ====== ===========

    """

    def __init__(self, index, position):
        """
        :param index: 0-indexed M/E number to control the transition of
        :param position: New position for the T-bar [0-10000]
        """
        self.index = index
        self.position = position

    def get_command(self):
        position = self.position
        data = struct.pack('>BxH', self.index, position)
        return self._make_command('CTPs', data)


class TransitionSettingsCommand(Command):
    """
    Implementation of the `CTTp` command. This is setting the transition style for the M/E unit between the
    Mix, Dip, Wipe, String and DVE transition style.

    The style argument takes one of the values from the TransitionSettingsField constants:
    TransitionSettingsField.STYLE_MXI
    TransitionSettingsField.STYLE_DIP
    TransitionSettingsField.STYLE_WIPE
    TransitionSettingsField.STYLE_STING
    TransitionSettingsField.STYLE_DVE

    The next_transition argument is a bitfield that sets the state of the "Next Transition" buttons, the row
    with the BKGD button.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask, bit0=set style, bit1=set next transition
    1      1    u8     M/E index
    2      1    u8     Style
    3      1    u8     Next transition
    ====== ==== ====== ===========

    ===== =============
    bit   Next transition button
    ===== =============
    0     BKGD
    1     Key 1
    2     Key 2
    3     Key 3
    4     Key 4
    ===== =============

    """

    def __init__(self, index, style=None, next_transition=None):
        """
        :param index: 0-indexed M/E number to control the preview bus of
        :param style: Set new transition style, or None
        :param next_transition: Set next transition active layers, or None
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


class MediaplayerSelectCommand(Command):
    """
    Implementation of the `MPSS` command. This sets the still or clip from the media pool to load into a mediaplayer

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask
    1      1    u8     Mediaplayer index
    2      1    u8     Source type, 1=still, 2=clip
    3      1    u8     Still index
    4      1    u8     Clip index
    5      3    ?      padding
    ====== ==== ====== ===========

    """

    def __init__(self, index, still=None, clip=None):
        """
        :param index: Mediaplayer index
        :param still: Still index to load
        :param clip: Clip index to load
        """
        self.index = index
        self.still = still
        self.clip = clip
        if still is not None and clip is not None:
            raise ValueError("Can only set still= or clip=, not both")
        if still is None and clip is None:
            raise ValueError("Either still or clip is required")
        if clip is None:
            self.source_type = 1
        else:
            self.source_type = 2

    def get_command(self):
        mask = 1
        if self.still is not None:
            mask |= 1 << 1
        if self.clip is not None:
            mask |= 1 << 2

        still = self.still if self.still is not None else 0
        clip = self.clip if self.clip is not None else 0

        data = struct.pack('>BBBBBxxx', mask, self.index, self.source_type, still, clip)
        return self._make_command('MPSS', data)


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


class DkeySetFillCommand(Command):
    """
    Implementation of the `CDsF` command. This sets the fill source on a downstream keyer
    panel.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Keyer index, 0-indexed
    1      1    ?      unknown
    2      2    u16    Fill source index
    ====== ==== ====== ===========

    """

    def __init__(self, index, source):
        """
        :param index: 0-indexed DSK number to control
        :param source: The source index to set on the keyer
        """
        self.index = index
        self.source = source

    def get_command(self):
        data = struct.pack('>BxH', self.index, self.source)
        return self._make_command('CDsF', data)


class DkeySetKeyCommand(Command):
    """
    Implementation of the `CDsC` command. This sets the key source on a downstream keyer
    panel.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Keyer index, 0-indexed
    1      1    ?      unknown
    2      2    u16    Key source index
    ====== ==== ====== ===========

    """

    def __init__(self, index, source):
        """
        :param index: 0-indexed DSK number to control
        :param source: The source index to set on the keyer
        """
        self.index = index
        self.source = source

    def get_command(self):
        data = struct.pack('>BxH', self.index, self.source)
        return self._make_command('CDsC', data)


class DkeyGainCommand(Command):
    """
    Implementation of the `CDsG` command. This controls the gain, clip, premultiplied and invert settings for a
    downstream keyer.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask
    1      1    u8     Downstream keyer index
    2      1    bool   Premultiplied
    3      1    ?      unknown
    4      2    u16    Clip
    6      2    u16    Gain
    8      1    bool   Invert
    9      3    ?      unknown
    ====== ==== ====== ===========

    === ==========
    Bit Mask value
    === ==========
    0   Pre-multiplied
    1   Clip
    2   Gain
    3   Invert key
    === ==========

    """

    def __init__(self, index, premultiplied=None, clip=None, gain=None, invert=None):
        """
        :param index: 0-indexed DSK number to control
        :param premultipled: The new premultiplied state for the keyer, or None
        :param clip: The new clip value for the keyer, or None
        :param gain: The new gain value for the keyer, or None
        :param invert: The new invert state for the keyer, or None
        """
        self.index = index
        self.premultiplied = premultiplied
        self.clip = clip
        self.gain = gain
        self.invert = invert

    def get_command(self):
        mask = 0
        if self.premultiplied is not None:
            mask |= 0x01
        if self.clip is not None:
            mask |= 0x02
        if self.gain is not None:
            mask |= 0x04
        if self.invert is not None:
            mask |= 0x08

        premultiplied = False if self.premultiplied is None else self.premultiplied
        invert = False if self.invert is None else self.invert
        clip = 0 if self.clip is None else self.clip
        gain = 0 if self.gain is None else self.gain
        data = struct.pack('>BB ?x H H ?3x', mask, self.index, premultiplied, clip, gain, invert)
        return self._make_command('CDsG', data)


class DkeyMaskCommand(Command):
    """
    Implementation of the `CDsM` command. This controls the mask values for a downstream keyer.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask
    1      1    u8     Downstream keyer index
    2      1    bool   Mask enabled
    3      1    ?      unknown
    4      2    i16    Mask Top
    6      2    i16    Mask bottom
    8      2    i16    Mask left
    10     2    i16    Mask right
    ====== ==== ====== ===========

    === ==========
    Bit Mask value
    === ==========
    0   Mask enabled
    1   Top
    2   Bottom
    3   Left
    4   Right
    === ==========

    """

    def __init__(self, index, enabled=None, top=None, bottom=None, left=None, right=None):
        """
        :param index: 0-indexed DSK number to control
        :param enabled: Enable or disable the mask, or None
        :param top: The new top offset for the mask, or None
        :param bottom: The new bottom offset for the mask, or None
        :param left: The new left offset for the mask, or None
        :param right: The new right offset for the mask, or None
        """
        self.index = index
        self.enabled = enabled
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right

    def get_command(self):
        mask = 0
        if self.enabled is not None:
            mask |= 0x01
        if self.top is not None:
            mask |= 0x02
        if self.bottom is not None:
            mask |= 0x04
        if self.left is not None:
            mask |= 0x08
        if self.right is not None:
            mask |= 0x10

        enabled = False if self.enabled is None else self.enabled
        top = 0 if self.top is None else self.top
        bottom = 0 if self.bottom is None else self.bottom
        left = 0 if self.left is None else self.left
        right = 0 if self.right is None else self.right
        data = struct.pack('>BB ?x 4h', mask, self.index, enabled, top, bottom, left, right)
        return self._make_command('CDsM', data)


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


class AudioMasterPropertiesCommand(Command):
    """
    Implementation of the `CAMM` command. This sets the settings the master channel of legacy audio.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask, see table below
    1      1    u8     unknown
    2      2    u16    Master volume [0 - 65381]
    4      2    ?      unknown
    6      1    bool   AFV
    7      1    ?      unknown
    ====== ==== ====== ===========

    === ==========
    Bit Mask value
    === ==========
    0   Volume
    1   ?
    2   AFV On/Off
    === ==========
    """

    def __init__(self, volume=None, afv=None):
        """
        :param volume: New volume of the master channel, or None
        :param afv: Enable AFV for master, following the Fade-to-black, or None
        """
        self.volume = volume
        self.afv = afv

    def get_command(self):
        mask = 0
        if self.volume is not None:
            mask |= 1 << 0
        if self.afv is not None:
            mask |= 1 << 2

        afv = False if self.afv is None else self.afv
        volume = 0 if self.volume is None else self.volume

        data = struct.pack('>B x H 2x ?x', mask, volume, afv)
        return self._make_command('CAMM', data)


class AudioMonitorPropertiesCommand(Command):
    """
    Implementation of the `CAMm` command. This sets the settings the monitor bus of legacy audio.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask, see table below
    1      1    bool   Enabled
    2      2    u16    Monitor volume [0 - 65381]
    4      1    bool   Mute
    5      1    bool   Solo
    6      2    u16    Solo source
    8      1    bool   Dim
    9      1    ?      unknown
    10     2    u16    Dim volume
    ====== ==== ====== ===========

    === ==========
    Bit Mask value
    === ==========
    0   Enabled
    1   Gain
    2   Mute
    3   Solo
    4   Solo source
    5   Dim
    6   Dim volume
    === ==========
    """

    def __init__(self, enabled=None, volume=None, mute=None, solo=None, solo_source=None, dim=None, dim_volume=None):
        """
        :param volume: New volume of the master channel, or None
        :param afv: Enable AFV for master, following the Fade-to-black, or None
        """
        self.enabled = enabled
        self.volume = volume
        self.mute = mute
        self.solo = solo
        self.solo_source = solo_source
        self.dim = dim
        self.dim_volume = dim_volume

    def get_command(self):
        mask = 0
        if self.enabled is not None:
            mask |= 1 << 0
        if self.volume is not None:
            mask |= 1 << 1
        if self.mute is not None:
            mask |= 1 << 2
        if self.solo is not None:
            mask |= 1 << 3
        if self.solo_source is not None:
            mask |= 1 << 4
        if self.dim is not None:
            mask |= 1 << 5
        if self.dim_volume is not None:
            mask |= 1 << 6

        enabled = False if self.enabled is None else self.enabled
        volume = 0 if self.volume is None else self.volume
        mute = False if self.mute is None else self.mute
        solo = False if self.solo is None else self.solo
        solo_source = 0 if self.solo_source is None else self.solo_source
        dim = False if self.dim is None else self.dim
        dim_volume = 0 if self.dim_volume is None else self.dim_volume

        data = struct.pack('>BB H ?? H ?x H', mask, enabled, volume, mute, solo, solo_source, dim, dim_volume)
        return self._make_command('CAMm', data)


class AudioInputCommand(Command):
    """
    Implementation of the `CAMI` command. This sets the settings of a channel strip in legacy audio.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask, see table below
    2      2    u16    Source index
    4      1    u8     Mix Option [0: Off, 1: On, 2: AFV]
    5      1    u8     unknown
    6      2    u16    Volume [0 - 65381]
    8      2    i16    Balance [-10000 - 10000]
    10     2    u16    unknown
    ====== ==== ====== ===========

    === ==========
    Bit Mask value
    === ==========
    0   Mix Option
    1   Volume
    2   Balance
    3   ?
    4   ?
    5   ?
    6   ?
    7   ?
    8   ?
    === ==========


    """

    def __init__(self, source, balance=None, volume=None, on=None, afv=None):
        """
        :param index: 0-indexed M/E number to control the preview bus of
        """
        self.source = source
        self.balance = balance
        self.volume = volume
        self.on = on
        self.afv = afv

    def get_command(self):
        mask = 0
        if self.on is not None or self.afv is not None:
            mask |= 1 << 0
        if self.volume is not None:
            mask |= 1 << 1
        if self.balance is not None:
            mask |= 1 << 2

        state = 0
        if self.on is not None:
            state = int(bool(self.on))
        elif self.afv is not None:
            state = int(bool(self.afv)) * 2

        balance = 0 if self.balance is None else self.balance
        volume = 0 if self.volume is None else self.volume

        data = struct.pack('>B x H B x H h x x', mask, self.source, state, volume, balance)
        return self._make_command('CAMI', data)


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
    22     4    i32    Gain [-10000 - 600]
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

    def __init__(self, source, channel, delay=None, gain=None, eq_gain=None, eq_enable=None, dynamics_gain=None,
                 balance=None, volume=None, state=None):
        """
        :param index: 0-indexed M/E number to control the preview bus of
        """
        self.source = source
        self.channel = channel
        self.delay = delay
        self.gain = gain
        self.eq_gain = eq_gain
        self.eq_enable = eq_enable
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
        if self.eq_enable is not None:
            mask |= 1 << 3
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
        eq_enable = False if self.eq_enable is None else self.eq_enable
        eq_gain = 0 if self.eq_gain is None else self.eq_gain
        dynamics_gain = 0 if self.dynamics_gain is None else self.dynamics_gain
        balance = 0 if self.balance is None else self.balance
        volume = 0 if self.volume is None else self.volume
        state = 0 if self.state is None else self.state

        split = 0xff if self.channel > -1 else 0x01
        self.channel = 0x00 if self.channel == -1 else self.channel
        pad = b'\xff\xff\xff\xff\xff\xff\xff'
        data = struct.pack('>H H4x6sBb B 3x i ? 5x h 2x Hh 2x iB 3x', mask, self.source, pad, split, self.channel,
                           delay,
                           gain, eq_enable, eq_gain,
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


class KeyCutCommand(Command):
    """
    Implementation of the `CKeC` command. This sets the key source for an upstream keyer.

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
        return self._make_command('CKeC', data)


class KeyTypeCommand(Command):
    """
    Implementation of the `CKTp` command. This sets the type of an upstream keyer.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask
    1      1    u8     M/E index, 0-indexed
    2      1    u8     Keyer index
    3      1    u8     Keyer type
    4      1    bool   Fly enabled
    5      3    ?      unknown
    ====== ==== ====== ===========

    === ==========
    Bit Mask value
    === ==========
    0   Key type
    1   Fly enabled
    === ==========

    """

    LUMA = 0
    CHROMA = 1
    PATTERN = 2
    DVE = 3

    def __init__(self, index, keyer, type=None, fly_enabled=None):
        """
        :param index: 0-indexed DSK number to trigger
        :param keyer: 0-indexed keyer number
        :param source: Source index for the keyer fill
        """
        self.index = index
        self.keyer = keyer
        self.type = type
        self.fly_enabled = fly_enabled

    def get_command(self):
        mask = 0
        if self.type is not None:
            mask |= 1 << 0
        if self.fly_enabled is not None:
            mask |= 1 << 1

        key_type = 0 if self.type is None else self.type
        fly_enabled = 0 if self.fly_enabled is None else self.fly_enabled

        data = struct.pack('>BBB B? 3x', mask, self.index, self.keyer, key_type, fly_enabled)
        return self._make_command('CKTp', data)


class KeyPropertiesDveCommand(Command):
    """
    Implementation of the `CKDV` command. This sets the settings of the DVE in an upstream keyer

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u32    Mask
    4      1    u8     M/E index, 0-indexed
    5      1    u8     Keyer index
    6      2    ?      unknown
    8      4    i32    Size x [0 - 9900]
    12     4    i32    Size y [0 - 9900]
    16     4    i32    Position x [-16000 - 16000]
    20     4    i32    Position y [-9000 - 9000]
    24     4    i32    Rotation
    28     1    bool   Border enabled
    29     1    bool   Shadow enabled
    30     1    u8     Border bevel mode
    31     1    ?      unknown
    32     2    u16    Border outer width [0 - 1600]
    34     2    u16    Border inner width [0 - 1600]
    36     1    u8     Border outer softness [0 - 100]
    37     1    u8     Border inner softness [0 - 100]
    38     1    u8     Border bevel softness [0 - 100]
    39     1    u8     Border bevel position [0 - 100]
    40     1    u8     Border opacity [0-100]
    41     1    ?      unknown
    42     2    u16    Border color hue [0 - 3599]
    44     2    u16    Border color saturation [0 - 1000]
    46     2    u16    Border color luma [0 - 1000]
    48     2    u16    Shadow light source angle [0 - 3590]
    50     1    u8     Shadow light source altitude [10-100]
    51     1    bool   Mask enabled
    52     2    i16    Mask top [-9000 - 9000]
    54     2    i16    Mask bottom [-9000 - 9000]
    56     2    i16    Mask left [-16000 - 16000]
    58     2    i16    Mask right [-16000 - 16000]
    60     1    u8     Rate
    61     3    ?      unknown
    ====== ==== ====== ===========

    === ==========
    Bit Mask value
    === ==========
    0   Size x
    1   Size y
    2   Position x
    3   Position y
    4   Rotation
    5   Border enabled
    6   Shadow enabled
    7   Border bevel mode
    8   Outer width
    9   Inner width
    10  Outer softness
    11  Inner softness
    12  Bevel softness
    13  Bevel position
    14  Border opacity
    15  Border hue
    16  Border saturation
    17  Border luma
    18  Shadow angle
    19  Shadow altitude
    20  Mask enabled
    21  Mask top
    22  Mask bottom
    23  Mask left
    24  Mask right
    25  Rate
    === ==========

    """

    def __init__(self, index, keyer, size_x=None, size_y=None, pos_x=None, pos_y=None, rotation=None,
                 border_enabled=None, shadow_enabled=None, border_bevel_enabled=None, outer_width=None,
                 inner_width=None, outer_softness=None, inner_softness=None, bevel_softness=None, bevel_position=None,
                 border_opacity=None, border_hue=None, border_saturation=None, border_luma=None, angle=None,
                 altitude=None, mask_enabled=None, mask_top=None, mask_bottom=None, mask_left=None, mask_right=None,
                 rate=None):
        """
        :param index: 0-indexed M/E number to control the preview bus of
        """
        self.index = index
        self.keyer = keyer
        self.size_x = size_x
        self.size_y = size_y
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.rotation = rotation
        self.border_enabled = border_enabled
        self.shadow_enabled = shadow_enabled
        self.border_bevel_enabled = border_bevel_enabled
        self.outer_width = outer_width
        self.inner_width = inner_width
        self.outer_softness = outer_softness
        self.inner_softness = inner_softness
        self.bevel_softness = bevel_softness
        self.bevel_position = bevel_position
        self.border_opacity = border_opacity
        self.border_hue = border_hue
        self.border_saturation = border_saturation
        self.border_luma = border_luma
        self.angle = angle
        self.altitude = altitude
        self.mask_enabled = mask_enabled
        self.mask_top = mask_top
        self.mask_bottom = mask_bottom
        self.mask_left = mask_left
        self.mask_right = mask_right
        self.rate = rate

    def set_border_color_rgb(self, red, green, blue):
        h, l, s = colorsys.rgb_to_hls(red, green, blue)
        self.border_hue = int(h * 3590)
        self.border_saturation = int(s * 1000)
        self.border_luma = int(l * 1000)

    def get_command(self):
        mask = 0
        if self.size_x is not None:
            mask |= 1 << 0
        if self.size_y is not None:
            mask |= 1 << 1
        if self.pos_x is not None:
            mask |= 1 << 2
        if self.pos_y is not None:
            mask |= 1 << 3
        if self.rotation is not None:
            mask |= 1 << 4
        if self.border_enabled is not None:
            mask |= 1 << 5
        if self.shadow_enabled is not None:
            mask |= 1 << 6
        if self.border_bevel_enabled is not None:
            mask |= 1 << 7
        if self.outer_width is not None:
            mask |= 1 << 8
        if self.inner_width is not None:
            mask |= 1 << 9
        if self.outer_softness is not None:
            mask |= 1 << 10
        if self.inner_softness is not None:
            mask |= 1 << 11
        if self.bevel_softness is not None:
            mask |= 1 << 12
        if self.bevel_position is not None:
            mask |= 1 << 13
        if self.border_opacity is not None:
            mask |= 1 << 14
        if self.border_hue is not None:
            mask |= 1 << 15
        if self.border_saturation is not None:
            mask |= 1 << 16
        if self.border_luma is not None:
            mask |= 1 << 17
        if self.angle is not None:
            mask |= 1 << 18
        if self.altitude is not None:
            mask |= 1 << 19
        if self.mask_enabled is not None:
            mask |= 1 << 20
        if self.mask_top is not None:
            mask |= 1 << 21
        if self.mask_bottom is not None:
            mask |= 1 << 22
        if self.mask_left is not None:
            mask |= 1 << 23
        if self.mask_right is not None:
            mask |= 1 << 24
        if self.rate is not None:
            mask |= 1 << 25

        index = 0 if self.index is None else self.index
        keyer = 0 if self.keyer is None else self.keyer
        size_x = 0 if self.size_x is None else self.size_x
        size_y = 0 if self.size_y is None else self.size_y
        pos_x = 0 if self.pos_x is None else self.pos_x
        pos_y = 0 if self.pos_y is None else self.pos_y
        rotation = 0 if self.rotation is None else self.rotation
        border_enabled = 0 if self.border_enabled is None else self.border_enabled
        shadow_enabled = 0 if self.shadow_enabled is None else self.shadow_enabled
        border_bevel_enabled = 0 if self.border_bevel_enabled is None else self.border_bevel_enabled
        outer_width = 0 if self.outer_width is None else self.outer_width
        inner_width = 0 if self.inner_width is None else self.inner_width
        outer_softness = 0 if self.outer_softness is None else self.outer_softness
        inner_softness = 0 if self.inner_softness is None else self.inner_softness
        bevel_softness = 0 if self.bevel_softness is None else self.bevel_softness
        bevel_position = 0 if self.bevel_position is None else self.bevel_position
        border_opacity = 0 if self.border_opacity is None else self.border_opacity
        border_hue = 0 if self.border_hue is None else self.border_hue
        border_saturation = 0 if self.border_saturation is None else self.border_saturation
        border_luma = 0 if self.border_luma is None else self.border_luma
        angle = 0 if self.angle is None else self.angle
        altitude = 0 if self.altitude is None else self.altitude
        mask_enabled = 0 if self.mask_enabled is None else self.mask_enabled
        mask_top = 0 if self.mask_top is None else self.mask_top
        mask_bottom = 0 if self.mask_bottom is None else self.mask_bottom
        mask_left = 0 if self.mask_left is None else self.mask_left
        mask_right = 0 if self.mask_right is None else self.mask_right
        rate = 0 if self.rate is None else self.rate

        data = struct.pack('>I BBxx 5i ??Bx HH5Bx 4HB?hhhhBxxx', mask, index,
                           keyer,

                           size_x,
                           size_y,
                           pos_x,
                           pos_y,
                           rotation,

                           border_enabled,
                           shadow_enabled,
                           border_bevel_enabled,

                           outer_width,
                           inner_width,
                           outer_softness,
                           inner_softness,
                           bevel_softness,
                           bevel_position,
                           border_opacity,

                           border_hue,
                           border_saturation,
                           border_luma,
                           angle,

                           altitude,
                           mask_enabled,
                           mask_top,
                           mask_bottom,
                           mask_left,
                           mask_right,
                           rate)
        return self._make_command('CKDV', data)


class KeyPropertiesAdvancedChromaColorpickerCommand(Command):
    """
    Implementation of the `CACC` command. This sets the state of the colorpicker for the advanced chroma keyer

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask
    1      1    u8     M/E index, 0-indexed
    2      1    u8     Keyer index
    3      1    bool   Enable cursor
    4      1    bool   Enable preview
    5      1    ?      padding
    6      2    i16    Cursor X [-16000 - 16000]
    8      2    i16    Cursor Y [-9000 - 9000]
    10     2    u16    Cursor size [620 - 9925]
    12     2    u16    Color Y
    14     2    i16    Color Cb
    16     2    i16    Color Cr
    18     2    ?      padding
    ====== ==== ====== ===========

    === ==========
    Bit Mask value
    === ==========
    0   Enable cursor
    1   Enable preview
    2   Cursor X
    3   Cursor Y
    4   Cursor size
    5   Color Y
    6   Color Cb
    7   color Cr
    === ==========

    """

    def __init__(self, index, keyer, cursor=None, preview=None, x=None, y=None, size=None, Y=None, Cb=None, Cr=None):
        """
        :param index: 0-indexed M/E number to control the preview bus of
        """
        self.index = index
        self.keyer = keyer
        self.cursor = cursor
        self.preview = preview
        self.x = x
        self.y = y
        self.size = size
        self.Y = Y
        self.Cb = Cb
        self.Cr = Cr

    def get_command(self):
        mask = 0
        if self.cursor is not None:
            mask |= 1 << 0
        if self.preview is not None:
            mask |= 1 << 1
        if self.x is not None:
            mask |= 1 << 2
        if self.y is not None:
            mask |= 1 << 3
        if self.size is not None:
            mask |= 1 << 4
        if self.Y is not None:
            mask |= 1 << 5
        if self.Cb is not None:
            mask |= 1 << 6
        if self.Cr is not None:
            mask |= 1 << 7

        index = 0 if self.index is None else self.index
        keyer = 0 if self.keyer is None else self.keyer
        cursor = False if self.cursor is None else self.cursor
        preview = False if self.preview is None else self.preview
        x = 0 if self.x is None else self.x
        y = 0 if self.y is None else self.y
        size = 0 if self.size is None else self.size
        Y = 0 if self.Y is None else self.Y
        Cb = 0 if self.Cb is None else self.Cb
        Cr = 0 if self.Cr is None else self.Cr

        data = struct.pack('>BBB? ?x hhH Hhh xx', mask, index, keyer,
                           cursor, preview, x, y, size, Y, Cb, Cr)

        return self._make_command('CACC', data)


class KeyPropertiesAdvancedChromaCommand(Command):
    """
    Implementation of the `CACK` command. This sets the state for the advanced chroma keyer

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Mask
    2      1    u8     M/E index, 0-indexed
    3      1    u8     Keyer index
    4      2    u16    Foreground [0 - 1000]
    6      2    u16    Background [0 - 1000]
    8      2    u16    Key edge [0 - 1000]
    10     2    u16    Spill suppress [0 - 1000]
    12     2    u16    Flare suppress [0 - 1000]
    14     2    i16    Brightness [-1000 - 1000]
    16     2    i16    Contrast [-1000 - 1000]
    18     2    u16    Saturation [0 - 2000]
    20     2    i16    Red [-1000 - 1000]
    22     2    i16    Green [-1000 - 1000]
    24     2    i16    Blue [-1000 - 1000]
    26     2    ?      padding
    ====== ==== ====== ===========

    === ==========
    Bit Mask value
    === ==========
    0   Foreground
    1   Background
    2   Key edge
    3   Spill suppress
    4   Flare suppress
    5   Brightness
    6   Contrast
    7   Saturation
    8   Red
    9   Green
    10  Blue
    === ==========

    """

    def __init__(self, index, keyer, foreground=None, background=None, key_edge=None, spill=None, flare=None,
                 brightness=None, contrast=None, saturation=None, red=None, green=None, blue=None):
        """
        :param index: 0-indexed M/E number to control the preview bus of
        """
        self.index = index
        self.keyer = keyer
        self.foreground = foreground
        self.background = background
        self.key_edge = key_edge
        self.spill = spill
        self.flare = flare
        self.brightness = brightness
        self.contrast = contrast
        self.saturation = saturation
        self.red = red
        self.green = green
        self.blue = blue

    def get_command(self):
        mask = 0
        if self.foreground is not None:
            mask |= 1 << 0
        if self.background is not None:
            mask |= 1 << 1
        if self.key_edge is not None:
            mask |= 1 << 2
        if self.spill is not None:
            mask |= 1 << 3
        if self.flare is not None:
            mask |= 1 << 4
        if self.brightness is not None:
            mask |= 1 << 5
        if self.contrast is not None:
            mask |= 1 << 6
        if self.saturation is not None:
            mask |= 1 << 7
        if self.red is not None:
            mask |= 1 << 8
        if self.green is not None:
            mask |= 1 << 9
        if self.blue is not None:
            mask |= 1 << 10

        foreground = 0 if self.foreground is None else self.foreground
        background = 0 if self.background is None else self.background
        key_edge = 0 if self.key_edge is None else self.key_edge
        spill = 0 if self.spill is None else self.spill
        flare = 0 if self.flare is None else self.flare
        brightness = 0 if self.brightness is None else self.brightness
        contrast = 0 if self.contrast is None else self.contrast
        saturation = 0 if self.saturation is None else self.saturation
        red = 0 if self.red is None else self.red
        green = 0 if self.green is None else self.green
        blue = 0 if self.blue is None else self.blue

        data = struct.pack('>HBB HHH HH hhHhhh xx', mask, self.index, self.keyer, foreground, background, key_edge, spill,
                           flare, brightness, contrast, saturation, red, green, blue)

        return self._make_command('CACK', data)


class KeyPropertiesLumaCommand(Command):
    """
    Implementation of the `CKLm` command. This sets the key source for an upstream keyer.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask
    1      1    u8     M/E index, 0-indexed
    2      1    u8     Keyer index
    3      1    bool   Pre-multiplied
    4      2    u16    Clip
    6      2    u16    Gain
    8      1    bool   Invert key
    9      3    ?      unknown
    ====== ==== ====== ===========

    === ==========
    Bit Mask value
    === ==========
    0   Pre-multiplied
    1   Clip
    2   Gain
    3   Invert key
    === ==========

    """

    def __init__(self, index, keyer, premultiplied=None, clip=None, gain=None, invert_key=None):
        """
        :param index: 0-indexed DSK number to trigger
        :param keyer: 0-indexed keyer number
        :param source: Source index for the keyer fill
        """
        self.index = index
        self.keyer = keyer
        self.premultiplied = premultiplied
        self.clip = clip
        self.gain = gain
        self.invert_key = invert_key

    def get_command(self):
        mask = 0
        if self.premultiplied is not None:
            mask |= 1 << 0
        if self.clip is not None:
            mask |= 1 << 1
        if self.gain is not None:
            mask |= 1 << 2
        if self.invert_key is not None:
            mask |= 1 << 3

        premultiplied = 0 if self.premultiplied is None else self.premultiplied
        clip = 0 if self.clip is None else self.clip
        gain = 0 if self.gain is None else self.gain
        invert_key = 0 if self.invert_key is None else self.invert_key

        data = struct.pack('>BBB?HH?3x', mask, self.index, self.keyer, premultiplied, clip, gain, invert_key)
        return self._make_command('CKLm', data)


class KeyerKeyframeSetCommand(Command):
    """
    Implementation of the `SFKF` command. This sets the A or B keyframe for the flying key in the keyer.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index, 0-indexed
    1      1    u8     Keyer index
    2      1    u8     keyframe, A = 1, B = 2
    3      1    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, index, keyer, keyframe):
        """
        :param index: M/E index
        :param keyer: 0-indexed keyer number
        :param keyframe: wether to store the A or B frame, set to 'A' or 'B'
        """
        self.index = index
        self.keyer = keyer
        self.keyframe = keyframe

    def get_command(self):
        keyframe = 1 if self.keyframe == 'A' else 2
        data = struct.pack('>BBBx', self.index, self.keyer, keyframe)
        return self._make_command('SFKF', data)


class KeyerKeyframeRunCommand(Command):
    """
    Implementation of the `RFlK` command. This makes the flying key run to full, A or B

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask
    1      1    u8     M/E index, zero indexed
    2      1    u8     Keyer index, zero indexed
    3      1    ?      unknown
    4      1    u8     Keyframe, 1=A, 2=B, 3=Full, 4=Infinite
    5      1    u8     Ininite run index
    6      2    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, index, keyer, run_to=None, set_infinite=None):
        """
        :param index: M/E index
        :param keyer: 0-indexed keyer number
        :param slot: wether to store the A or B frame, set to 'A' or 'B'
        """
        self.index = index
        self.keyer = keyer
        self.run_to = run_to
        self.set_infinite = set_infinite

    def get_command(self):
        run_to_lut = {
            'A': 1,
            'B': 2,
            'Full': 3,
            'Infinite': 4,
        }
        run_to = run_to_lut[self.run_to]
        set_infinite = self.set_infinite or 0

        mask = 0
        if self.set_infinite is not None:
            mask |= 1 << 1

        data = struct.pack('>BBBxBB2x', mask, self.index, self.keyer, run_to, set_infinite)
        return self._make_command('RFlK', data)


class RecorderStatusCommand(Command):
    """
    Implementation of the `RcTM` command. This starts and stops the stream recorder.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    bool   Recording state
    1      3    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, recording):
        """
        :param recording: Wether the hardware should be recording
        """
        self.recording = recording

    def get_command(self):
        data = struct.pack('>?3x', self.recording)
        return self._make_command('RcTM', data)


class RecordingSettingsSetCommand(Command):
    """
    Implementation of the `CRMS` command. This sets the parameters for the stream recorder.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask
    1      128  str    Filename
    132    4    u32    Disk 1 id
    136    4    i32    Disk 2 id
    140    1    bool   Record in all cameras
    ====== ==== ====== ===========

    """

    def __init__(self, filename=None, disk1=None, disk2=None, record_in_camera=None):
        """
        :param filename: Filename for recording, or None
        :param disk1: ID for disk 1, or None
        :param disk2: ID for disk 2, or None
        :param record_in_camera: Trigger recording on attached cameras, or None
        """
        self.filename = filename
        self.disk1 = disk1
        self.disk2 = disk2
        self.record_in_camera = record_in_camera

    def get_command(self):
        mask = 0
        if self.filename is not None:
            mask |= 1 << 0
        if self.disk1 is not None:
            mask |= 1 << 1
        if self.disk2 is not None:
            mask |= 1 << 2
        if self.record_in_camera is not None:
            mask |= 1 << 3

        filename = self.filename.encode() if self.filename is not None else b''
        ric = self.record_in_camera if self.record_in_camera is not None else False

        data = struct.pack('>B 128s xxx II ?xxx', mask, filename, self.disk1 or 0, self.disk2 or 0, ric)
        return self._make_command('CRMS', data)


class StreamingServiceSetCommand(Command):
    """
    Implementation of the `CRSS` command. This sets the parameters for the live stream output.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask
    1      64   str    Service name
    65     512  str    Url
    577    512  str    Streaming key
    1089   3    ?      padding bytes
    1092   4    u32    Minimum bitrate (Bps)
    1096   4    u32    Maximum bitrate (Bps)
    ====== ==== ====== ===========

    === ==========
    Bit Mask value
    === ==========
    0   Service name
    1   Url
    2   Key
    3   Min/Max bitrate
    === ==========

    """

    def __init__(self, name=None, url=None, key=None, bitrate_min=None, bitrate_max=None):
        """
        :param name: New streaming service name, or None
        :param url: RTMP url, or None
        :param key: Stream key, or None
        :param bitrate_min: Minimum bitrate, or None
        :param bitrate_max: Maximum bitrate, or None
        """
        self.name = name
        self.url = url
        self.key = key
        self.bitrate_min = bitrate_min
        self.bitrate_max = bitrate_max

    def get_command(self):
        if self.bitrate_min is None and self.bitrate_max is not None:
            return ValueError("Both min and max bitrate required")
        if self.bitrate_max is None and self.bitrate_min is not None:
            return ValueError("Both min and max bitrate required")
        mask = 0
        if self.name is not None:
            mask |= 1 << 0
        if self.url is not None:
            mask |= 1 << 1
        if self.key is not None:
            mask |= 1 << 2
        if self.bitrate_min is not None:
            mask |= 1 << 3

        name = self.name.encode() if self.name is not None else b''
        url = self.url.encode() if self.url is not None else b''
        key = self.key.encode() if self.key is not None else b''

        data = struct.pack('>B 64s 512s 512s 3x II', mask, name, url, key,
                           self.bitrate_min or 0, self.bitrate_max or 0)
        return self._make_command('CRSS', data)


class StreamingStatusSetCommand(Command):
    """
    Implementation of the `StrR` command. This starts and stops the live stream

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    bool   Stream enable
    1      3    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, streaming):
        """
        :param streaming: True to start streaming, False to stop streaming
        """
        self.streaming = streaming

    def get_command(self):
        data = struct.pack('>?xxx', self.streaming)
        return self._make_command('StrR', data)


class MultiviewPropertiesCommand(Command):
    """
    Implementation of the `CMvP` command. This sets the layout of a multiview output and can set a flag for
    swapping the program and preview window.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask, see table below
    1      1    u8     Multiviewer index
    2      1    u8     Layout
    3      1    bool   Swap program/preview
    ====== ==== ====== ===========

    See the MultiviewPropertiesField for the description of the layout value.

    """

    def __init__(self, index, layout=None, swap=None):
        """
        :param index: 0-indexed multiview output number
        :param layout: The layout number to use, or None
        :param swap: Make the program/preview swapped or not, or None
        """
        self.index = index
        self.layout = layout
        self.swap = swap

    def get_command(self):
        mask = 0
        if self.layout is not None:
            mask |= 1 << 0
        if self.swap is not None:
            mask |= 1 << 1

        layout = 0 if self.layout is None else self.layout
        swap = False if self.swap is None else self.swap
        data = struct.pack('>BBB?', mask, self.index, layout, swap)
        return self._make_command('CMvP', data)


class MultiviewInputCommand(Command):
    """
    Implementation of the `CMvI` command. This routes a source to one of the windows in a multiview output

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Multiviewer index
    1      1    u8     Window index
    2      2    u16    Source index
    ====== ==== ====== ===========

    """

    def __init__(self, index, window, source):
        """
        :param index: 0-indexed multiview output number
        :param window: The window number on the multiview
        :param source: The source index index to route to the window
        """
        self.index = index
        self.window = window
        self.source = source

    def get_command(self):
        data = struct.pack('>BBH', self.index, self.window, self.source)
        return self._make_command('CMvI', data)


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
        :param store: Store number to get the lock for
        :param state: True to request the lock, False to release it
        """
        self.store = store
        self.state = state

    def get_command(self):
        data = struct.pack('>H?x', self.store, self.state)
        return self._make_command('LOCK', data)


class PartialLockCommand(Command):
    """
    Implementation of the `PLCK` command. This requests a new lock, used for data transfers.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u16    Store index
    2      2    u16    Slot
    4      4    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, store, slot):
        """
        :param store: Store number to request a lock for
        :param slot: Slot number inside the store to get the partial lock for
        """
        self.store = store
        self.slot = slot

    def get_command(self):
        data = struct.pack('>HH BBxx', self.store, self.slot, 0xff, 0x01)
        return self._make_command('PLCK', data)


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
        # Special case for macro downloads, not sure why
        if self.store == 0xffff:
            u1 = 0x03
        else:
            u1 = 0x00
        u2 = 0xd0
        u3 = 0x9b
        u4 = 0x8c
        data = struct.pack('>HHI 4B', self.transfer, self.store, self.slot, u1, u2, u3, u4)
        return self._make_command('FTSU', data)


class TransferUploadRequestCommand(Command):
    """
    Implementation of the `FTSD` command. This requests an upload from the client to the switcher.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Tranfer id
    2      2    u16    Store
    4      2    ?      unknown
    6      2    u16    Slot
    8      2    u32    Data length
    12     2    u16    Mode bitfield
    14     2    ?      unknown
    ====== ==== ====== ===========

    === ==========
    bit Mode
    === ==========
    0   Unknown
    1   Write RLE
    2   Clear
    256 Write uncompressed
    512 Pre-erase
    === ==========

    """

    MODE_WRITE_RLE = 1
    MODE_WRITE = 256
    MODE_ERASE = 512

    def __init__(self, transfer, store, slot, length, mode):
        """
        :param transfer: Unique transfer number
        :param store: Store index
        :param slot: Slot index
        """
        self.transfer = transfer
        self.store = store
        self.slot = slot
        self.length = length
        self.mode = mode

    def get_command(self):
        data = struct.pack('>HHxxHIHxx', self.transfer, self.store, self.slot, self.length, self.mode)
        return self._make_command('FTSD', data)


class TransferDataCommand(Command):
    """
    Implementation of the `FTDa` command. This is a chunk of data being sent from the client to the hardware.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Tranfer id
    2      2    u16    Size
    4      ?    u8[]   Chunk of data
    ====== ==== ====== ===========

    """

    def __init__(self, transfer, data):
        """
        :param transfer: Unique transfer number
        :param data: Chunk of data to send
        """
        self.transfer = transfer
        self.data = data

    def get_command(self):
        data = struct.pack('>HH', self.transfer, len(self.data))
        return self._make_command('FTDa', data + self.data)


class TransferFileDataCommand(Command):
    """
    Implementation of the `FTFD` command. This is the file metadata for the uploaded file and should be sent to the
    hardware after all the FTDa commands have been sent. It contains the name and MD5 hash of the uploaded data.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Tranfer id
    2      64   str    Name
    66     128  str    Description
    194    16   u8[]   MD5 hash
    210    2    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, transfer, hash, name=None, description=None):
        """
        :param transfer: Unique transfer number
        :param name: Filename
        :param description: File description
        :param hash: Data MD5 hash
        """
        self.transfer = transfer
        self.name = name
        self.description = description
        self.hash = hash

    def get_command(self):
        name = self.name.encode() if self.name is not None else b''
        description = self.description.encode() if self.description is not None else b''

        data = struct.pack('>H 64s 128s 16s 2x', self.transfer, name, description, self.hash)
        return self._make_command('FTFD', data)


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


class SendAudioLevelsCommand(Command):
    """
    Implementation of the `SALN` command. This is an acknowledgement for FTDa packets.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    bool   Enable sending levels
    1      3    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, enable):
        """
        :param transfer: Unique transfer number
        :param slot: Slot index
        """
        self.enable = enable

    def get_command(self):
        data = struct.pack('>? 3x', self.enable)
        return self._make_command('SALN', data)


class SendFairlightLevelsCommand(Command):
    """
    Implementation of the `SFLN` command. This enables or disables receiving the 10Hz audio level update packets for
    the Audio page.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    bool   Enable sending levels
    1      3    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, enable):
        """
        :param enable: Enable or disable receiving audio level data
        """
        self.enable = enable

    def get_command(self):
        data = struct.pack('>? 3x', self.enable)
        return self._make_command('SFLN', data)


class CameraControlCommand(Command):
    """
    Implementation of the `CCmd` command. This sends a camera control command to an attached blackmagic design camera.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    int8   Destination
    1      1    int8   Category
    2      1    int8   Parameter
    3      1    int8   Relative 0=off 1=on
    4      1    int8   Datatype
    5      4    ?      unknown
    8      1    int8   Number of elements
    9      6    ?      unknown
    ...    ...  ...    data depending on command
    ====== ==== ====== ===========
    """

    def __init__(self, destination, category, parameter, relative=False, datatype=None, data=None):
        """
        :param destination: Camera index, or 255 for broadcast
        :param category: Command category
        :param parameter: Command parameter
        :param relative: Relative adjustment enable
        :param datatype: Data type index
        :param data: Data elements for command
        """
        self.destination = destination
        self.category = category
        self.parameter = parameter
        self.relative = relative
        self.datatype = datatype if datatype is not None else 0
        self.data = data

    def get_command(self):
        count = 0
        if self.data is not None:
            count = len(self.data)
        data = struct.pack('>5B', self.destination, self.category, self.parameter, self.relative, self.datatype)
        elements = [0] * 11
        countoffset = {
            0: 2,
            1: 2,
            2: 2,
            3: 4,
            4: 2,
            5: 2,
            128: 4
        }
        elements[countoffset[self.datatype]] = count
        data += struct.pack('>11B', *elements)
        if self.data is not None:
            fmt = '>{}'.format(count)
            if self.datatype == 5:
                fmt = '>{}s'.format(len(self.data[0]))
            fmtmap = {
                0: '?',
                1: 'b',
                2: 'h',
                3: 'i',
                4: 'q',
                5: '',
                128: 'h'
            }
            fmt += fmtmap[self.datatype]
            if self.datatype == 128:
                for i in range(0, len(self.data)):
                    self.data[i] = int(self.data[i] * (2 ** 11))
            elif self.datatype == 5:
                for i in range(0, len(self.data)):
                    self.data[i] = self.data[i].encode()
            packed_data = struct.pack(fmt, *self.data)
            packed_data += b'\0' * (8 - len(packed_data))
            data += packed_data
        return self._make_command('CCmd', data)


class VideoModeCommand(Command):
    """
    Implementation of the `CVdM` command. This sets the main video mode for the hardware

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     M/E index
    1      1    bool   Preview enabled
    2      2    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, mode):
        """
        :param mode: The new video mode ID
        """
        self.mode = mode

    def get_command(self):
        data = struct.pack('>B3x', self.mode)
        return self._make_command('CVdM', data)


class AutoInputVideoModeCommand(Command):
    """
    Implementation of the `AiVM` command. This enables or disables automatic video mode detection based on the video
    signal.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    bool   Enable
    1      3    ?      unknown
    ====== ==== ====== ===========

    """

    def __init__(self, enable):
        """
        :param enable: Set auto mode enabled or disabled
        """
        self.enable = enable

    def get_command(self):
        data = struct.pack('>?3x', self.enable)
        return self._make_command('AiVM', data)


class InputPropertiesCommand(Command):
    """
    Implementation of the `CInL` command. This sets labels and routing for video inputs

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      1    u8     Mask
    1      1    ?      unknown
    2      2    u16    Source index
    4      20   str[]  Label
    24     4    str[]  Short label
    28     2    u16    Port type
    ====== ==== ====== ===========

    """

    def __init__(self, source_index, label=None, short_label=None, port_type=None):
        """
        :param source_index: Input index to change the properties for
        :param label: Long display label for the input
        :param short_label: Short display label for the button of the input, 4 letter code
        :param port_type: Port type enum
        """
        self.source_index = source_index
        self.label = label
        self.short_label = short_label
        self.port_type = port_type

    def get_command(self):
        mask = 0
        if self.label is not None:
            mask |= 1 << 0
        if self.short_label is not None:
            mask |= 1 << 1
        if self.port_type is not None:
            mask |= 1 << 2

        label = self.label.encode() if self.label is not None else b''
        short = self.short_label.encode() if self.short_label is not None else b''
        port_type = self.port_type if self.port_type is not None else 0

        data = struct.pack('>Bx H 20s 4s Hxx', mask, self.source_index, label, short, port_type)
        return self._make_command('CInL', data)


class TimeRequestCommand(Command):
    """
    Request the system time of the hardware, this is also used as a NOP command
    This command has no arguments
    """

    def get_command(self):
        return self._make_command('TiRq', b'')


class TransferCompleteCommand(Command):
    """
    Implementation of the `*XFC` command. This is an command that's part of OpenSwitcher for the TCP protocol and not part
    of the actual ATEM protocol.

    ====== ==== ====== ===========
    Offset Size Type   Description
    ====== ==== ====== ===========
    0      2    u16    Store
    2      2    u16    Slot
    4      1    bool   Is upload
    5      3    x      padding
    ====== ==== ====== ===========

    """

    def __init__(self, store, slot, upload):
        """
        :param store: Transfer store index
        :param slot: Transfer slot index
        :param upload: True if an upload was completed, False if a download was completed
        """
        self.store = store
        self.slot = slot
        self.upload = upload

    def get_command(self):
        data = struct.pack('>HH ?xxx', self.store, self.slot, self.upload)
        return self._make_command('*XFC', data)
