# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
from unittest import TestCase

from pyatem.hexdump import hexdump
from pyatem.media import rle_decode, rle_encode


class Test(TestCase):
    def _rle_loop_check(self, label, testdata):
        compressed = rle_encode(testdata)
        decoded = rle_decode(compressed)
        if decoded != testdata:
            print("Original:")
            hexdump(testdata)
            print("Compressed:")
            hexdump(compressed)
            print("Result:")
            hexdump(decoded)

        self.assertEqual(testdata, decoded, label)

    def test_rle_uncompressable(self):
        testdata = b'\x01\x01\x01\x01\x01\x01\x01\x01'
        testdata += b'\x02\x02\x02\x02\x02\x02\x02\x02'
        testdata += b'\x03\x03\x03\x03\x03\x03\x03\x03'
        testdata += b'\x04\x04\x04\x04\x04\x04\x04\x04'
        self._rle_loop_check('uncompressable', testdata)

    def test_rle_single_block(self):
        testdata = b''
        for i in range(1, 10):
            testdata += b'\x01\x01\x01\x01\x01\x01\x01\x01'
            self._rle_loop_check(f'single block {i}', testdata)

    def test_rle_double_block(self):
        testdata1 = b''
        testdata2 = b''
        for i in range(1, 10):
            testdata1 += b'\x01\x01\x01\x01\x01\x01\x01\x01'
            testdata2 += b'\x02\x02\x02\x02\x02\x02\x02\x02'
            self._rle_loop_check(f'double block {i}', testdata1 + testdata2)

    def test_rle_block_purge(self):
        testdata = b'\x01\x01\x01\x01\x01\x01\x01\x01'
        testdata += b'\x01\x01\x01\x01\x01\x01\x01\x01'
        testdata += b'\x01\x01\x01\x01\x01\x01\x01\x01'
        testdata += b'\x02\x02\x02\x02\x02\x02\x02\x02'
        self._rle_loop_check('end block purge', testdata)

    def test_rle_block_purge_double(self):
        testdata = b'\x01\x01\x01\x01\x01\x01\x01\x01'
        testdata += b'\x01\x01\x01\x01\x01\x01\x01\x01'
        testdata += b'\x01\x01\x01\x01\x01\x01\x01\x01'
        testdata += b'\x02\x02\x02\x02\x02\x02\x02\x02'
        testdata += b'\x02\x02\x02\x02\x02\x02\x02\x02'
        self._rle_loop_check('double end block purge', testdata)

    def test_rle_two_compressable_gap(self):
        testdata = b'\x01\x01\x01\x01\x01\x01\x01\x01'
        testdata += b'\x01\x01\x01\x01\x01\x01\x01\x01'
        testdata += b'\x01\x01\x01\x01\x01\x01\x01\x01'
        testdata += b'\x01\x01\x01\x01\x01\x01\x01\x01'
        testdata += b'\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa'
        testdata += b'\x02\x02\x02\x02\x02\x02\x02\x02'
        testdata += b'\x02\x02\x02\x02\x02\x02\x02\x02'
        testdata += b'\x02\x02\x02\x02\x02\x02\x02\x02'
        testdata += b'\x02\x02\x02\x02\x02\x02\x02\x02'
        self._rle_loop_check('third block', testdata)
