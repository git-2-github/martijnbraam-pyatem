import struct


class Command:
    def get_command(self):
        pass

    def _make_command(self, name, data):
        header = struct.pack('>H 2x 4s', len(data) + 8, name.encode())
        return header + data


class CutCommand(Command):
    def __init__(self, index):
        self.index = index

    def get_command(self):
        data = struct.pack('>B 3x', self.index)
        return self._make_command('DCut', data)


class TransitionPositionCommand(Command):
    def __init__(self, index, position):
        self.index = index
        self.position = position

    def get_command(self):
        position = int(self.position * 9999)
        data = struct.pack('>BxH', self.index, position)
        return self._make_command('CTPs', data)
