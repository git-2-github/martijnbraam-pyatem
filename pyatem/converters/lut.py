# Copyright 2022 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import struct


class Cube:
    def __init__(self):
        self.title = None
        self.table = []
        self.keywords = {}


def load_cube(path):
    with open(path, 'r') as handle:
        raw = handle.read()

    keywords = {}
    table = []
    domain_min = (0, 0, 0)
    domain_max = (1, 1, 1)
    for line in raw.splitlines(keepends=False):
        line = line.strip()
        if line == "" or line.startswith('#'):
            continue

        part = line.split()
        if part[0] in ['TITLE', 'LUT_1D_SIZE', 'LUT_3D_SIZE', 'DOMAIN_MIN', 'DOMAIN_MAX']:
            key, val = line.split(maxsplit=1)
            if val.startswith('"'):
                val = val[1:-1]
            elif key.startswith('LUT'):
                val = int(val)
            elif key.startswith('DOMAIN'):
                r = float(part[1])
                g = float(part[2])
                b = float(part[3])
                val = (r, g, b)
                if key == 'DOMAIN_MIN':
                    domain_min = val
                elif key == 'DOMAIN_MAX':
                    domain_max = val
            keywords[key] = val
            continue

        r = (float(part[0]) - domain_min[0]) * (domain_max[0] - domain_min[0])
        g = (float(part[1]) - domain_min[1]) * (domain_max[1] - domain_min[1])
        b = (float(part[2]) - domain_min[2]) * (domain_max[2] - domain_min[2])
        table.append((r, g, b))

    result = Cube()
    result.title = keywords['TITLE'] if 'TITLE' in keywords else 'Unnamed'
    result.keywords = keywords
    result.table = table
    return result


def lut_to_bmd17(lut):
    data = b''
    for i, row in enumerate(lut.table):
        value = 0
        for c in range(3):
            v = int(row[2 - c] * 1023)
            value = (value << 10) | (v & 0x3ff)
        drow = struct.pack('<I', value)
        data += drow
    return data
