import argparse
import os
import logging
import time
import math
import functools

import usb
import tqdm

DFU_DETACH = 0
DFU_DOWNLOAD = 1
DFU_STATUS = 3


class DfuMatcher:
    def __init__(self, pid):
        self.pid = pid

    def __call__(self, device: usb.core.Device):
        if device.idVendor != 0x1edb:
            return False
        if device.idProduct != self.pid:
            return False
        return True


def get_dfu_interface(device):
    for cfg in device:
        for intf in cfg:
            if intf.bInterfaceClass != 0xFE:
                continue
            if intf.bInterfaceSubClass != 0x01:
                continue
            return intf
    return None


def get_dfu_status(device, intf):
    status = device.ctrl_transfer(bmRequestType=0xA1, bRequest=DFU_STATUS, wValue=0, wIndex=intf.index,
                                  data_or_wLength=6)
    return status[4]


def dfu_detach(device, intf):
    device.ctrl_transfer(bmRequestType=0x21, bRequest=DFU_DETACH, wValue=1000, wIndex=intf.index, data_or_wLength=0)


def dfu_download(device, intf, firmware):
    chunk_size = 32768
    with open(firmware, "rb") as handle:
        handle.seek(0, os.SEEK_END)
        firmware_size = handle.tell()
        handle.seek(0, os.SEEK_SET)
        chunk_count = math.ceil(firmware_size / chunk_size)
        chunker = functools.partial(handle.read, chunk_size)
        block_num = 0
        for chunk in tqdm.tqdm(iter(chunker, b''), total=chunk_count):
            device.ctrl_transfer(bmRequestType=0x21, bRequest=DFU_DOWNLOAD, wValue=block_num, wIndex=intf.index,
                                 data_or_wLength=chunk, timeout=1000)
            block_num += 1
            status = get_dfu_status(device, intf)
            if status != 5:
                raise RuntimeError(f"Something wrong: status is {status}")


def main():
    logging.basicConfig(format="%(message)s", datefmt="%H:%M:%S.%f", level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="be16")
    parser.add_argument("--firmware", default="/workspace/pocket4k-firmware.bin")
    args = parser.parse_args()

    pid = int(args.device, 16)
    devices = list(usb.core.find(find_all=True, custom_match=DfuMatcher(pid)))
    if len(devices) != 1:
        print("No camera found")
        exit(1)
    device = devices[0]
    intf = get_dfu_interface(device)
    in_recovery = 'Recovery' in device.product
    if not in_recovery:
        print("Device not in recovery mode, resetting...")
        # DFU_DETACH
        dfu_detach(device, intf)

        time.sleep(3)
        devices = list(usb.core.find(find_all=True, custom_match=DfuMatcher(pid)))
        if len(devices) != 1:
            print("Doeidoei device")
            exit(1)
        in_recovery = 'Recovery' in device.product
        if in_recovery:
            print("Switch success!")
        else:
            print("Failed to switch")
            exit(1)
    print("Device in recovery mode... starting firmware upload")
    status = get_dfu_status(device, intf)
    if status == 0:
        print("Detaching...")
        dfu_detach(device, intf)
    status = get_dfu_status(device, intf)
    if status == 2:
        dfu_download(device, intf, args.firmware)
    else:
        print("Device did not detach")


if __name__ == '__main__':
    main()
