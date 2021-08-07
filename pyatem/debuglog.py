import struct


class DebugLog:
    def __init__(self, filename):
        self.filename = filename
        with open(filename, 'w') as handle:
            handle.write('<style>\n')
            handle.write('tr.packet {\n')
            handle.write('  font-family: monospace;\n')
            handle.write('}\n')
            handle.write('tr.packet.sending {\n')
            handle.write('  background: #ddd;\n')
            handle.write('}\n')
            handle.write('td.header {\n')
            handle.write('  white-space: nowrap;\n')
            handle.write('}\n')
            handle.write('td {\n')
            handle.write('  vertical-align: top;\n')
            handle.write('  font-size: 12px;\n')
            handle.write('}\n')
            handle.write('span {\n')
            handle.write('  padding-right: 10px;\n')
            handle.write('}\n')
            handle.write('span.sep {\n')
            handle.write('  padding-right: 20px;\n')
            handle.write('}\n')
            handle.write('span.data {\n')
            handle.write('  display: inline-block;\n')
            handle.write('}\n')
            handle.write('</style>\n\n<table style="width: 100%">')

    def add_packet(self, sending, raw):
        dc = 'receiving'
        if sending:
            dc = 'sending'
        row = '<tr class="packet {}"><td class="header">\n'.format(dc)
        row += '<span class="flags">{:02x} {:02x}</span>\n'.format(raw[0], raw[1])
        row += '<span class="session">{:02x} {:02x}</span>\n'.format(raw[2], raw[3])
        row += '<span class="acknr">{:02x} {:02x}</span>\n'.format(raw[4], raw[5])
        row += '<span class="hdrunkwn">{:02x} {:02x}</span>\n'.format(raw[6], raw[7])
        row += '<span class="remseq">{:02x} {:02x}</span>\n'.format(raw[8], raw[9])
        row += '<span class="locseq">{:02x} {:02x}</span>\n'.format(raw[10], raw[11])
        row += '<span class="sep"></span></td><td>\n'
        row += '<span class="data">\n'
        data = raw[12:]
        if len(data) > 8:
            row += '<table class="fields">\n'
            offset = 0
            while offset < len(data):
                l1, l2, l3, l4, cmd = struct.unpack_from('!4B 4s', data, offset)
                datalen, _ = struct.unpack_from('!H2x 4s', data, offset)
                raw = data[offset + 8:offset + datalen]
                offset += datalen
                row += '<tr><td class="header">\n'
                row += '{:02x} {:02x} {:02x} {:02x} {} <span class="sep"></span>'.format(l1, l2, l3, l4, cmd.decode())
                row += '</td><td>\n'
                for b in raw:
                    row += '{:02x} '.format(b)
                row += '</tr>\n'
            row += '</table>\n'

        else:
            for b in data:
                row += '{:02x} '.format(b)
        row += '</span>\n'
        row += '</td></tr>\n'
        with open(self.filename, 'a') as handle:
            handle.write(row)
