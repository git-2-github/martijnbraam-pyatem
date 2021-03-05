import struct


def atem_to_image(data, width, height):
    data = rle_decode(data)

    with open('test.bin', 'wb') as handle:
        handle.write(data)


def is_rle_header(data, offset):
    if offset >= len(data):
        return True
    return


def rle_decode(data):
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
            block = data[offset:offset + 8]
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
    with open('download-0-0.bin', 'rb') as handle:
        raw = handle.read()
    atem_to_image(raw, 1920, 1080)
