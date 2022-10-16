# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
from unittest import TestCase

from pyatem.hexdump import hexdump
from pyatem.media import rle_decode, rle_encode, atem_to_image, image_to_atem, rgb_to_atem
from pyatem.mediaconvert import atem_to_rgb


class Test(TestCase):
    FRAME_1080_RED = b'\xfe\xfe\xfe\xfe\xfe\xfe\xfe\xfe\x00\x00\x00\x00\x00\x0f\xd2\x00:\x96d\xfa:\x9e\xfc\xfa'
    FRAME_1080_RED_PIXEL = b':\x96d\xfa:\x9e\xfc\xfa'
    RED_PIXEL_8888 = b'\xff\0\0\xff'

    def test_rle_decode(self):
        decompressed = rle_decode(self.FRAME_1080_RED)
        for index in range(0, len(decompressed), 8):
            pixel = decompressed[index:index + 8]
            self.assertEqual(self.FRAME_1080_RED_PIXEL, pixel, msg='index {}'.format(index))

    def test_atem_to_image(self):
        decompressed = rle_decode(self.FRAME_1080_RED)
        result = atem_to_rgb(decompressed, 1920, 1080)
        for index in range(0, len(result), 4):
            pixel = result[index:index + 4]
            self.assertEqual(self.RED_PIXEL_8888, pixel, msg='index {}'.format(index))

    def test_image_to_atem(self):
        frame = atem_to_image(self.FRAME_1080_RED, 1920, 1080)
        result = rgb_to_atem(frame, 1920, 1080)
        compressed = rle_encode(result)
        hexdump(compressed)
        test = atem_to_rgb(result, 1920, 1080)

    def test_rle_decode_solid_color(self):
        result = rle_decode(self.FRAME_1080_RED)
        for index in range(0, len(result) - 8, 8):
            pixel = result[index:index + 8]
            self.assertEqual(self.FRAME_1080_RED_PIXEL, pixel)

    def test_rle_encode_solid_color(self):
        testframe = rle_decode(self.FRAME_1080_RED)
        compressed = rle_encode(testframe)
        decompressed = rle_decode(compressed)
        self.assertEqual(testframe, decompressed)
