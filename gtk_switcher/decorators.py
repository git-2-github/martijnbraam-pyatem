# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only

# Needs to be a global for decorators
_callbacks = {}


def call_fields(name, self, data):
    if name in _callbacks:
        for f in _callbacks[name]:
            f(self, data)


def field(name):
    def wrapper(func):
        global _callbacks
        if name not in _callbacks:
            _callbacks[name] = []
        _callbacks[name].append(func)
        return func

    return wrapper
