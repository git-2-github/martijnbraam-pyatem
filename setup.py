from setuptools import setup, Extension

setup(
    name='pyatem',
    version='0.5.1',
    packages=['pyatem'],
    ext_modules=[Extension('pyatem.mediaconvert', ['pyatem/mediaconvertmodule.c'])],
    url='https://git.sr.ht/~martijnbraam/pyatem',
    license='LGPL3',
    author='Martijn Braam',
    author_email='martijn@brixit.nl',
    description='Library implementing the Blackmagic Design Atem switcher protocol',
    long_description=open("README.md").read(),
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Operating System :: POSIX :: Linux',
    ],
)
