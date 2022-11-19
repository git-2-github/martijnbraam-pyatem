# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import struct
import pyatem.mediaconvert as mc


def atem_to_image(data, width, height):
    """Decompress and decode an atem frame to RGBA8888"""
    data = rle_decode(data)
    data = mc.atem_to_rgb(data, width, height)
    return data


def image_to_atem(data, width, height):
    """Convert a frame to atem format and compress it"""
    data = mc.rgb_to_atem(data, width, height)
    return rle_encode(data)


def atem_to_rgb(data, width, height):
    """Wrapper for the native function"""
    return mc.atem_to_rgb(data, width, height)


def rgb_to_atem(data, width, height, premultiply=False):
    """Wrapper for the native function"""
    return mc.rgb_to_atem(data, width, height, premultiply)


def rle_encode_slow(data):
    """
    See rle_decode for format description
    :param data:
    :return:
    """
    result = bytearray()
    lastblock = None
    lastcount = 0
    offset = 0
    while True:
        block = data[offset:offset + 8]
        offset += 8
        if len(block) < 8:
            break
        if block != lastblock:
            if lastcount > 2:
                result += b'\xfe\xfe\xfe\xfe\xfe\xfe\xfe\xfe'
                result += struct.pack('>Q', lastcount)
                result += lastblock
            elif lastcount > 0:
                result += lastblock * lastcount

            result += block
            lastblock = block
            lastcount = 0
            continue
        lastcount += 1
        lastblock = block
    if lastcount > 0:
        result += b'\xfe\xfe\xfe\xfe\xfe\xfe\xfe\xfe'
        result += struct.pack('>Q', lastcount)
        result += lastblock
    return result


def rle_encode(data):
    return mc.rle_encode(data)


def rle_decode(data):
    """
    ATEM frames are compressed with a custom RLE encoding. Data in the frame is grouped in 8 byte chunks since
    that is exactly 2 pixels in the 10-bit YCbCr 4:2:2 data. Most of the data is sent without compression but
    if a 8 byte chunk is fully 0xfe then the following chunk is RLE compressed.

    An RLE compressed part is an 64 bit integer setting the repeat count following the 8-byte block of data
    to be repeated. This seems mainly useful to compress solid colors.

    :param data:
    :return:
    """
    result = bytearray()
    offset = 0
    in_size = len(data)

    while offset < in_size:
        block = data[offset:offset + 8]
        if data[offset] == 0xfe \
                and data[offset + 1] == 0xfe \
                and data[offset + 2] == 0xfe \
                and data[offset + 3] == 0xfe \
                and data[offset + 4] == 0xfe \
                and data[offset + 5] == 0xfe \
                and data[offset + 6] == 0xfe \
                and data[offset + 7] == 0xfe:
            # Got an RLE block
            offset += 8
            count, = struct.unpack_from('>Q', data, offset)
            offset += 8
            block = data[offset:offset + 8]
            result += block * count
            offset += 8
        else:
            # Raw data block
            result += block
            offset += 8
    return result


if __name__ == '__main__':
    with open('/workspace/test.bin', 'wb') as handle:
        handle.write(
            rle_decode(b'\xfe\xfe\xfe\xfe\xfe\xfe\xfe\xfe\x00\x00\x00\x00\x00\x0f\xd2\x00:\x96d\xfa:\x9e\xfc\xfa'))
    exit(0)

    with open('/workspace/usb-0-0.bin', 'rb') as handle:
        raw = handle.read()
    atem_to_image(raw, 1920, 1080)
