import argparse
import os
import sys
import logging
import tqdm
from pathlib import Path

from PIL import Image

from pyatem.command import CutCommand, TimeRequestCommand
import pyatem.mediaconvert
import pyatem.media
from pyatem.cameracontrol import CameraControlData
from pyatem.protocol import AtemProtocol
import pyatem.field as fieldmodule

connection = None
slot_index = None
image_path = None
args = None
pbar = None
logging.basicConfig(level=logging.INFO)


def prepare_image(path, resolution):
    im = Image.open(path)
    frame = Image.new('RGBA', resolution)
    im.thumbnail(resolution, Image.Resampling.LANCZOS)
    frame.paste(im)
    pixels = frame.getdata()

    flat = [item for sublist in pixels for item in sublist]
    return bytes(flat)


def save_image(path, resolution, data):
    im = Image.frombytes('RGBA', resolution, data)
    im.save(path)


def changed(key, contents):
    if key == 'time':
        return
    if not args.debug:
        return
    if isinstance(contents, fieldmodule.FieldBase):
        print(contents)
    else:
        print(key)


def connected():
    if not isinstance(connection, AtemProtocol):
        raise ValueError()

    product = connection.mixerstate['product-name']
    slots = connection.mixerstate['mediaplayer-slots']
    mode = connection.mixerstate['video-mode']

    logging.info(f'Connected to {product.name} at {mode.get_label()}')

    if slot_index < 0 or slot_index > slots.stills:
        logging.fatal(f'Slot index out of range, This hardware supports slot 1-{slots.stills}')

    if args.action == "upload":
        frame = prepare_image(image_path, mode.get_resolution())
        connection.send_commands([TimeRequestCommand()])
        logging.basicConfig(level=logging.DEBUG)
        frame_atem = pyatem.media.rgb_to_atem(frame, *mode.get_resolution())
        if args.name:
            name = args.name
        else:
            name = Path(args.file).stem
        connection.upload(0, slot_index, frame_atem, name=name, compress=True)
    elif args.action == "download":
        connection.download(0, slot_index)


def uploaded(store, slot):
    logging.info("Upload completed")
    exit(0)


def downloaded(store, slot, data):
    logging.info(f'Download complete, received {len(data)} bytes')
    if args.raw:
        logging.info(f'Saving raw data to {args.file}')
        with open(args.file, 'wb') as handle:
            handle.write(data)
    else:
        mode = connection.mixerstate['video-mode']
        image = pyatem.media.atem_to_image(data, *mode.get_resolution())
        save_image(args.file, mode.get_resolution(), image)
    exit(0)


def progress(store, slot, factor):
    print(factor * 100)


def upload_progress(store, slot, percent, done, size):
    global pbar
    if pbar is None:
        pbar = tqdm.tqdm(total=size, unit='B', unit_scale=True)
        pbar.last_done = 0
    block = done - pbar.last_done
    pbar.update(block)
    pbar.last_done = done
    if done == size:
        pbar.close()


def main():
    global connection, slot_index, image_path, args
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', help="More debug output", action="store_true")
    subparsers = parser.add_subparsers(dest="action")
    subparsers.required = True
    upload_parser = subparsers.add_parser('upload')
    upload_parser.add_argument('ip', help='ATEM IP address')
    upload_parser.add_argument('index', help='Media store slot number', type=int)
    upload_parser.add_argument('file', help='Still to upload')
    upload_parser.add_argument('--name', help='Still name')
    download_parser = subparsers.add_parser('download')
    download_parser.add_argument('ip', help='ATEM IP address')
    download_parser.add_argument('index', help='Media store slot number', type=int)
    download_parser.add_argument('file', help='Local filename for the still')
    download_parser.add_argument('--raw', help='Don\'t decode', action='store_true')

    args = parser.parse_args()

    if args.action == "upload" and not os.path.isfile(args.file):
        sys.stderr.write('File not found\n')
        exit(1)

    slot_index = args.index - 1
    image_path = args.file

    logging.info(f'Connecting to ATEM at {args.ip}...')
    if args.ip == 'usb':
        connection = AtemProtocol(usb=True)
    else:
        connection = AtemProtocol(args.ip)
    connection.on('connected', connected)
    connection.on('upload-done', uploaded)
    connection.on('download-done', downloaded)
    connection.on('transfer-progress', progress)
    connection.on('upload-progress', upload_progress)
    connection.on('change', changed)

    connection.connect()
    while True:
        connection.loop()


if __name__ == '__main__':
    main()
