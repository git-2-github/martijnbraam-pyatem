# Copyright 2022 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
from setuptools import setup, Extension

setup(
    name='pyatem',
    version='0.12.0',
    packages=['pyatem', 'pyatem.converters'],
    ext_modules=[Extension('pyatem.mediaconvert', ['pyatem/mediaconvertmodule.c'])],
    url='https://git.sr.ht/~martijnbraam/pyatem',
    license='LGPL3',
    author='Martijn Braam',
    author_email='martijn@brixit.nl',
    description='Library implementing the Blackmagic Design Atem switcher protocol',
    long_description=open("README.md").read(),
    classifiers=[
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: POSIX :: Linux',
    ],
)
