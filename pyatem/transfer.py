import hashlib

from pyatem.media import rle_encode


class TransferTask:
    def __init__(self, store, slot, upload=False):
        self.tid = None
        self.state = None
        self.upload = upload

        self.store = store
        self.slot = slot

        self.data = None
        self.data_length = None
        self.hash = None

        self.send_length = None
        self.send_done = 0

        self.name = None
        self.description = None

    def calculate_hash(self):
        hasher = hashlib.md5(self.data)
        self.hash = hasher.digest()
        self.data_length = len(self.data)

    def compress(self):
        compressed = rle_encode(self.data)
        self.data = compressed
        self.send_length = len(self.data)

    def __repr__(self):
        direction = 'upload' if self.upload else 'download'
        return f'<TransferTask {direction} store={self.store} slot={self.slot}>'


class TransferQueueFlushed:
    def __init__(self):
        pass
