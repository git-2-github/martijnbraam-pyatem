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
        self.me, self.keyers = struct.unpack('>2H', raw)

    def __repr__(self):
        return '<mixer-effect-config m/e {}: keyers={}>'.format(self.me, self.keyers)
