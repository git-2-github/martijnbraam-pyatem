# Copyright 2022 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
from pyatem.converters.lut import load_cube, lut_to_bmd17


def test_load_cube():
    result = load_cube('../fixtures/linear-17.cube')
    assert result.title == "Generated by Resolve"
    assert result.keywords['LUT_3D_SIZE'] == 17
    assert len(result.table) == 4913


def test_generate_bmd17():
    lut = load_cube('../fixtures/linear-17.cube')
    result = lut_to_bmd17(lut)

    with open('../fixtures/linear-17.bin', 'rb') as handle:
        reference = handle.read()

    assert result == reference
