import struct


def atem_to_image(data, width, height):
    data = rle_decode(data)
    return data


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
    with open('/workspace/usb-0-0.bin', 'rb') as handle:
        raw = handle.read()
    atem_to_image(raw, 1920, 1080)
