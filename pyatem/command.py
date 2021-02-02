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
        position = int(self.position * 9999)
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
