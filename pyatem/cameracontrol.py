# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import math
import sys
import inspect

from pyatem.command import CameraControlCommand

_cache = {}

VOID = 0
BOOL = 0
INT8 = 1
INT16 = 2
INT32 = 3
INT64 = 4
UTF8 = 5
FIXED16 = 128


class CameraControlData:
    CATEGORY = -1
    PARAMETER = -1
    DATATYPE = -1
    DESCRIPTIONS = [""]
    KEYS = [""]

    def __init__(self, destination=None, **kwargs):
        self.data = None
        self.destination = destination

        if len(kwargs) > 0:
            self.data = [0] * len(self.DESCRIPTIONS)
            for key in kwargs:
                offset = self.KEYS.index(key)
                self.data[offset] = kwargs[key]

    @classmethod
    def from_data(cls, data):
        """
        :type data: pyatem.field.CameraControlDataPacketField
        """
        global _cache
        if len(_cache) == 0:
            current_module = sys.modules[__name__]
            for name, dcls in inspect.getmembers(current_module):
                if hasattr(dcls, 'CATEGORY') and dcls.CATEGORY > -1:
                    _cache[(dcls.CATEGORY, dcls.PARAMETER)] = dcls

        if (data.category, data.parameter) in _cache:
            instance = _cache[(data.category, data.parameter)]()
            instance.data = data.data
            instance.destination = data.destination
            instance.decode()
            return instance
        return None

    def to_command(self, relative=False):
        cmd = CameraControlCommand(self.destination, self.CATEGORY, self.PARAMETER, relative, self.DATATYPE, self.data)
        return cmd

    def decode(self):
        pass

    def __repr__(self):
        values = ""
        if self.data is not None:
            for i, value in enumerate(self.data):
                values += f' {self.KEYS[i]}={value}{self.DESCRIPTIONS[i]}'
        return f'<{self.__class__.__name__} dest={self.destination} id={self.CATEGORY}.{self.PARAMETER}{values}>'


class Focus(CameraControlData):
    CATEGORY = 0
    PARAMETER = 0
    DATATYPE = FIXED16
    KEYS = ["distance"]


class TriggerAutofocus(CameraControlData):
    CATEGORY = 0
    PARAMETER = 1
    DATATYPE = VOID
    DESCRIPTIONS = []


class ApertureFStop(CameraControlData):
    CATEGORY = 0
    PARAMETER = 2
    DATATYPE = FIXED16
    KEYS = ["fnumber"]

    def decode(self):
        self.data[0] = math.sqrt(2 ** self.data[0])


class ApertureNormalized(CameraControlData):
    CATEGORY = 0
    PARAMETER = 3
    DATATYPE = FIXED16
    KEYS = ["aperture"]


class ApertureOrdinal(CameraControlData):
    CATEGORY = 0
    PARAMETER = 3
    DATATYPE = FIXED16
    KEYS = ["aperture"]


class TriggerAutoaperture(CameraControlData):
    CATEGORY = 0
    PARAMETER = 5
    DATATYPE = VOID
    DESCRIPTIONS = []


class OIS(CameraControlData):
    CATEGORY = 0
    PARAMETER = 6
    DATATYPE = BOOL
    KEYS = ["enabled"]


class AbsoluteZoom(CameraControlData):
    CATEGORY = 0
    PARAMETER = 7
    DATATYPE = INT16
    KEYS = ["zoom"]
    DESCRIPTIONS = ["mm"]


class AbsoluteZoomNormalized(CameraControlData):
    CATEGORY = 0
    PARAMETER = 8
    DATATYPE = FIXED16
    KEYS = ["zoom"]


class ContinuousZoom(CameraControlData):
    CATEGORY = 0
    PARAMETER = 9
    DATATYPE = FIXED16
    KEYS = ["rate"]


class VideoMode(CameraControlData):
    CATEGORY = 1
    PARAMETER = 0
    DATATYPE = INT8
    KEYS = ["framerate", "mrate", "dimensions", "interlaced", "colorspace"]
    DESCRIPTIONS = ["fps", "", "", "", ""]


class Gain(CameraControlData):
    CATEGORY = 1
    PARAMETER = 1
    DATATYPE = INT8
    KEYS = ["ISO"]

    def decode(self):
        self.data = [self.data[0] * 100]


class WhiteBalance(CameraControlData):
    CATEGORY = 1
    PARAMETER = 2
    DATATYPE = INT16
    KEYS = ["temperature", "tint"]
    DESCRIPTIONS = ["k", ""]


class TriggerAutowhitebalance(CameraControlData):
    CATEGORY = 1
    PARAMETER = 3
    DATATYPE = VOID
    DESCRIPTIONS = []


class TriggerRestorewhitebalance(CameraControlData):
    CATEGORY = 1
    PARAMETER = 4
    DATATYPE = VOID
    DESCRIPTIONS = []


class Exposure(CameraControlData):
    CATEGORY = 1
    PARAMETER = 5
    DATATYPE = INT32
    KEYS = ["time"]
    DESCRIPTIONS = ["us"]


class DynamicRangeMode(CameraControlData):
    CATEGORY = 1
    PARAMETER = 7
    DATATYPE = INT8
    KEYS = ["mode"]


class VideoSharpening(CameraControlData):
    CATEGORY = 1
    PARAMETER = 8
    DATATYPE = INT8
    KEYS = ["level"]


class RecordingFormat(CameraControlData):
    CATEGORY = 1
    PARAMETER = 9
    DATATYPE = INT16
    KEYS = ["file-fps", "sensor-fps", "width", "height", "flags"]
    DESCRIPTIONS = ["", "", "", "", ""]


class AutoExposureMode(CameraControlData):
    CATEGORY = 1
    PARAMETER = 10
    DATATYPE = INT8
    KEYS = ["mode"]


class ShutterAngle(CameraControlData):
    CATEGORY = 1
    PARAMETER = 11
    DATATYPE = INT32
    KEYS = ["angle"]
    DESCRIPTIONS = ["deg"]

    def decode(self):
        self.data = [self.data[0] / 100]


class ShutterSpeed(CameraControlData):
    CATEGORY = 1
    PARAMETER = 12
    DATATYPE = INT32
    KEYS = ["speed"]


class GainDB(CameraControlData):
    CATEGORY = 1
    PARAMETER = 13
    DATATYPE = INT8
    KEYS = ["gain"]
    DESCRIPTIONS = ["dB"]


class ISO(CameraControlData):
    CATEGORY = 1
    PARAMETER = 14
    DATATYPE = INT32
    KEYS = ["iso"]
    DESCRIPTIONS = ["ISO"]


class MicLevel(CameraControlData):
    CATEGORY = 2
    PARAMETER = 0
    DATATYPE = FIXED16
    KEYS = ["level"]


class HeadphoneLevel(CameraControlData):
    CATEGORY = 2
    PARAMETER = 1
    DATATYPE = FIXED16
    KEYS = ["level"]


class HeadphoneProgramMix(CameraControlData):
    CATEGORY = 2
    PARAMETER = 2
    DATATYPE = FIXED16
    KEYS = ["mix"]


class SpeakerLevel(CameraControlData):
    CATEGORY = 2
    PARAMETER = 3
    DATATYPE = FIXED16
    KEYS = ["level"]


class AudioInputType(CameraControlData):
    CATEGORY = 2
    PARAMETER = 4
    DATATYPE = INT8
    KEYS = ["type"]


class AudioInputLevels(CameraControlData):
    CATEGORY = 2
    PARAMETER = 5
    DATATYPE = FIXED16
    KEYS = ["left", "right"]


class PhantomPower(CameraControlData):
    CATEGORY = 2
    PARAMETER = 6
    DATATYPE = BOOL
    KEYS = ["enabled"]


class OutputOverlay(CameraControlData):
    CATEGORY = 3
    PARAMETER = 0
    DATATYPE = INT16
    KEYS = "flag"


class OutputFrameGuideStyle(CameraControlData):
    CATEGORY = 3
    PARAMETER = 1
    DATATYPE = INT8
    KEYS = "style"


class OutputFrameGuideOpacity(CameraControlData):
    CATEGORY = 3
    PARAMETER = 2
    DATATYPE = FIXED16
    KEYS = "opacity"


class OutputOverlays(CameraControlData):
    CATEGORY = 3
    PARAMETER = 3
    DATATYPE = INT8
    KEYS = ["style", "opacity", "safearea", "gridstyle"]
    DESCRIPTIONS = ["", "%", "%", ""]


class DisplayBrightness(CameraControlData):
    CATEGORY = 4
    PARAMETER = 0
    DATATYPE = FIXED16
    KEYS = ["brightness"]


class DisplayOverlay(CameraControlData):
    CATEGORY = 4
    PARAMETER = 1
    DATATYPE = INT16
    KEYS = ["bitfield"]


class DisplayZebraLevel(CameraControlData):
    CATEGORY = 4
    PARAMETER = 2
    DATATYPE = FIXED16
    KEYS = ["level"]


class DisplayPeakingLevel(CameraControlData):
    CATEGORY = 4
    PARAMETER = 3
    DATATYPE = FIXED16
    KEYS = ["level"]


class DisplayColorBarsTime(CameraControlData):
    CATEGORY = 4
    PARAMETER = 4
    DATATYPE = INT8
    KEYS = ["seconds"]


class DisplayFocusAssist(CameraControlData):
    CATEGORY = 4
    PARAMETER = 5
    DATATYPE = INT8
    KEYS = ["method", "color"]
    DESCRIPTIONS = ["", ""]


class TallyBrightness(CameraControlData):
    CATEGORY = 5
    PARAMETER = 0
    DATATYPE = FIXED16
    KEYS = ["brightness"]


class TallyFrontBrightness(CameraControlData):
    CATEGORY = 5
    PARAMETER = 1
    DATATYPE = FIXED16
    KEYS = ["brightness"]


class TallyRearBrightness(CameraControlData):
    CATEGORY = 5
    PARAMETER = 2
    DATATYPE = FIXED16
    KEYS = ["brightness"]


class ReferenceSource(CameraControlData):
    CATEGORY = 6
    PARAMETER = 0
    DATATYPE = INT8
    KEYS = ["source"]


class ReferenceOffset(CameraControlData):
    CATEGORY = 6
    PARAMETER = 1
    DATATYPE = INT32
    KEYS = ["offset"]
    DESCRIPTIONS = ["px"]


class RealtimeClock(CameraControlData):
    CATEGORY = 7
    PARAMETER = 0
    DATATYPE = INT32
    KEYS = ["time", "date"]
    DESCRIPTIONS = ["", " as BCD"]


class SystemLanguage(CameraControlData):
    CATEGORY = 7
    PARAMETER = 1
    DATATYPE = UTF8
    KEYS = ["lang"]


class Timezone(CameraControlData):
    CATEGORY = 7
    PARAMETER = 2
    DATATYPE = INT32
    KEYS = ["offset"]
    DESCRIPTIONS = [" minutes"]


class Location(CameraControlData):
    CATEGORY = 7
    PARAMETER = 3
    DATATYPE = INT64
    KEYS = ["latitude", "longitude"]
    DESCRIPTIONS = ["", " as BCD"]


class LiftAdjust(CameraControlData):
    CATEGORY = 8
    PARAMETER = 0
    DATATYPE = FIXED16
    KEYS = ["red", "green", "blue", "luma"]
    DESCRIPTIONS = ["", "", "", ""]


class GammaAdjust(CameraControlData):
    CATEGORY = 8
    PARAMETER = 1
    DATATYPE = FIXED16
    KEYS = ["red", "green", "blue", "luma"]
    DESCRIPTIONS = ["", "", "", ""]


class GainAdjust(CameraControlData):
    CATEGORY = 8
    PARAMETER = 2
    DATATYPE = FIXED16
    KEYS = ["red", "green", "blue", "luma"]
    DESCRIPTIONS = ["", "", "", ""]


class OffsetAdjust(CameraControlData):
    CATEGORY = 8
    PARAMETER = 3
    DATATYPE = FIXED16
    KEYS = ["red", "green", "blue", "luma"]
    DESCRIPTIONS = ["", "", "", ""]


class ContrastAdjust(CameraControlData):
    CATEGORY = 8
    PARAMETER = 4
    DATATYPE = FIXED16
    KEYS = ["pivot", "adjust"]
    DESCRIPTIONS = ["", ""]


class LumaMix(CameraControlData):
    CATEGORY = 8
    PARAMETER = 5
    DATATYPE = FIXED16
    KEYS = ["mix"]


class ColorAdjust(CameraControlData):
    CATEGORY = 8
    PARAMETER = 6
    DATATYPE = FIXED16
    KEYS = ["hue", "saturation"]
    DESCRIPTIONS = ["", ""]


class TriggerColorReset(CameraControlData):
    CATEGORY = 8
    PARAMETER = 7
    DATATYPE = VOID
    DESCRIPTIONS = []


class Codec(CameraControlData):
    CATEGORY = 10
    PARAMETER = 0
    DATATYPE = INT8
    KEYS = ["codec", "variant"]
    DESCRIPTIONS = ["", ""]


class TransportMode(CameraControlData):
    CATEGORY = 10
    PARAMETER = 1
    DATATYPE = INT8
    KEYS = ["mode", "speed", "flags", "storage"]
    DESCRIPTIONS = ["", "x", "", ""]


class PanTiltVelocity(CameraControlData):
    CATEGORY = 11
    PARAMETER = 0
    DATATYPE = FIXED16
    KEYS = ["pan", "tilt"]
    DESCRIPTIONS = ["", ""]


class PositionPreset(CameraControlData):
    CATEGORY = 11
    PARAMETER = 1
    DATATYPE = INT8
    KEYS = ["command", "slot"]
    DESCRIPTIONS = ["", ""]
