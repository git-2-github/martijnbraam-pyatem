# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import os
from unittest import TestCase
import gzip

import pyatem.media
from PIL import Image


class Test(TestCase):

    def setUp(self):
        fixtures_dir = os.environ.get('TEST_FIXTURES', os.path.join(os.path.dirname(__file__), 'fixtures'))
        fixture = self._encode_test(os.path.join(fixtures_dir, 'ramps.png'))
        self.encoded = pyatem.media.rgb_to_atem(fixture, 1920, 1080)

        with gzip.open(os.path.join(fixtures_dir, 'ramps-atemsc.data.gz'), 'rb') as handle:
            self.reference = handle.read()

    def _encode_test(self, path):
        """
        Load a test fixture image with pillow and run through the atem frame encoder without compression
        """
        im = Image.open(path)
        pixels = im.getdata()
        flat = [item for sublist in pixels for item in sublist]
        return bytes(flat)

    def _decompose(self, raw):
        """
        Converts 8 packed pixels to a list of values
        """
        a = int.from_bytes(raw[0:4], byteorder='big', signed=False)
        b = int.from_bytes(raw[4:8], byteorder='big', signed=False)

        a1 = a >> 20
        cb = (a >> 10) & 0b1111111111
        y1 = a & 0b1111111111
        a2 = b >> 20
        cr = (b >> 10) & 0b1111111111
        y2 = b & 0b1111111111
        return {
            "y1": y1,
            "y2": y2,
            "cr": cr,
            "cb": cb,
            "a1": a1,
            "a2": a2,
        }

    def _test_primary(self, name, rgb, expect):
        sequence = rgb + b'\xff' + rgb + b'\xff'
        encoded = pyatem.media.rgb_to_atem(sequence, 2, 1)
        dec = self._decompose(encoded)
        self.assertAlmostEqual(expect[0], dec['y1'], msg=f'{name} Y', delta=2)
        self.assertAlmostEqual(expect[1], dec['cb'], msg=f'{name} Cb', delta=2)
        self.assertAlmostEqual(expect[2], dec['cr'], msg=f'{name} Cr', delta=2)

    def _assertClose(self, a, b, msg):
        for key in a:
            self.assertAlmostEqual(a[key], b[key], msg=f'{msg} [{key}]', delta=5)

    def _compare_row(self, test, reference, row):
        stride = 1920 * 4
        offset = row * stride

        test = test[offset:offset + stride]
        reference = reference[offset:offset + stride]
        for i in range(0, stride, 8):
            testpixels = test[0:8]
            test = test[8:]
            referencepixels = reference[0:8]
            reference = reference[8:]

            r = self._decompose(referencepixels)
            t = self._decompose(testpixels)
            self._assertClose(r, t, f'chunk {i}')

    def test_greyramp(self):
        self._compare_row(self.encoded, self.reference, 1042)

    def test_redramp(self):
        self._compare_row(self.encoded, self.reference, 963)

    def test_greenramp(self):
        self._compare_row(self.encoded, self.reference, 885)

    def test_blueramp(self):
        self._compare_row(self.encoded, self.reference, 800)

    def test_hues(self):
        self._compare_row(self.encoded, self.reference, 0)

    def test_primaries(self):
        self._test_primary('red', b'\xff\x00\x00', (63 * 4, 102 * 4, 240 * 4))
        self._test_primary('green', b'\x00\xFF\x00', (173 * 4, 42 * 4, 26 * 4))
        self._test_primary('blue', b'\x00\x00\xFF', (32 * 4, 240 * 4, 118 * 4))
        self._test_primary('white', b'\xFF\xFF\xFF', (235 * 4, 128 * 4, 128 * 4))
        self._test_primary('black', b'\x00\x00\x00', (16 * 4, 128 * 4, 128 * 4))
        self._test_primary('yellow', b'\xFF\xFF\x00', (219 * 4, 16 * 4, 138 * 4))
        self._test_primary('cyan', b'\x00\xFF\xFF', (188 * 4, 154 * 4, 16 * 4))
        self._test_primary('magenta', b'\xFF\x00\xFF', (78 * 4, 214 * 4, 230 * 4))
