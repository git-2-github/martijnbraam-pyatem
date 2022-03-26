class TransferTask:
    def __init__(self, store, slot, upload=False):
        self.tid = None
        self.state = None
        self.upload = upload

        self.store = store
        self.slot = slot

        self.data = None
