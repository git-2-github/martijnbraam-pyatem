from unittest import TestCase

from pyatem.media import rle_decode


class Test(TestCase):
    FRAME_1080_RED = b'\xfe\xfe\xfe\xfe\xfe\xfe\xfe\xfe\x00\x00\x00\x00\x00\x0f\xd2\x00:\x96d\xfa:\x9e\xfc\xfa'
    FRAME_1080_RED_PIXEL = b':\x96d\xfa:\x9e\xfc\xfa'

    def test_atem_to_image(self):
        YCbCrA10Bit422 = rle_decode(self.FRAME_1080_RED)


    def test_rle_decode_solid_color(self):
        result = rle_decode(self.FRAME_1080_RED)
        for index in range(0, len(result) - 8, 8):
            pixel = result[index:index + 8]
            self.assertEqual(pixel, self.FRAME_1080_RED_PIXEL)
