from setuptools import setup

setup(
    name='pyatem',
    version='0.1.0',
    packages=['pyatem'],
    url='https://git.sr.ht/~martijnbraam/pyatem',
    license='LGPL3',
    author='Martijn Braam',
    author_email='martijn@brixit.nl',
    description='Library implementing the Blackmagic Design Atem switcher protocol',
    long_description=open("README").read(),
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Operating System :: POSIX :: Linux',
    ],
    install_requires=[
        'hexdump',
    ],
)
