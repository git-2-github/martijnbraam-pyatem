# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
import queue
import socket
import os


class SocketQueue(queue.Queue):
    """
    This is a queue.Queue that's also a socket so it works with the select() call
    to await both a queue item and a network packet.
    """

    def __init__(self):
        super().__init__()

        if os.name == 'posix':
            self._putsocket, self._getsocket = socket.socketpair()
        else:
            # Compatibility on non-POSIX systems
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(('127.0.0.1', 0))
            server.listen(1)
            self._putsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._putsocket.connect(server.getsockname())
            self._getsocket, _ = server.accept()
            server.close()

    def fileno(self):
        return self._getsocket.fileno()

    def put(self, item, **kwargs):
        super().put(item, **kwargs)
        self._putsocket.send(b'x')

    def get(self, **kwargs):
        self._getsocket.recv(1)
        return super().get(**kwargs)
