import argparse
import os
from datetime import datetime
import itertools

import yaml

from pyatem.protocol import AtemProtocol
import pyatem.field as fieldmodule
import pyatem.command as commandmodule

switcher = None
current = None
send_time = None
in_prep = True
prepqueue = []
testqueue = []
rejectbuffer = []

stats_executed = 0
stats_start = None


def on_change(key, contents):
    global switcher
    global stats_executed
    global rejectbuffer
    delta = datetime.now() - send_time

    if in_prep:
        send_next()
        return

    expect = current['expect']

    if delta.total_seconds() > 2:
        print("\nTimeout while waiting for field response")
        print("Sent:")
        print(f"  {current['send']['cmd']}:")
        for arg in current['send']:
            if arg == 'cmd':
                continue
            print(f"    {arg} = {current['send'][arg]}")
        print(f"Expected: {expect['field']}")
        print("Received:")
        for k in rejectbuffer:
            print(f"  {k}")
        exit(2)

    if key != expect['field']:
        rejectbuffer.append(key)
        return

    rejectbuffer = []

    for argname in expect:
        if argname == 'field':
            continue

        if getattr(contents, argname) != expect[argname]:
            print("Sent:")
            print(f"  {current['send']['cmd']}:")
            for arg in current['send']:
                if arg == 'cmd':
                    continue
                print(f"    {arg} = {current['send'][arg]}")
            print(f"\nMismatch on {argname}: expected {expect[argname]}, got {getattr(contents, argname)}")
            exit(2)

    stats_executed += 1
    print(".", end='')
    send_next()


def send_next():
    global switcher
    global prepqueue
    global in_prep
    global testqueue
    global current
    global send_time


    if len(testqueue) == 0:
        print("\n")
        print(f"Executed tests: {stats_executed}")
        print(f"Test duration: {datetime.now() - stats_start}")
        print("Tests completed successfully")
        exit(0)

    if len(prepqueue) > 0:
        test = prepqueue.pop(0)
    else:
        if in_prep:
            print("Running tests...")
            in_prep = False
        test = testqueue.pop(0)
    current = test

    classname = test['send']['cmd'].title().replace('-', '') + "Command"
    arguments = test['send'].copy()
    del arguments['cmd']

    if hasattr(commandmodule, classname):
        cmd = getattr(commandmodule, classname)(**arguments)
    else:
        print(f"Unknown command: {classname}")
        exit(2)

    send_time = datetime.now()
    switcher.send_commands([cmd])


def on_connected():
    global switcher
    global testqueue
    global prepqueue
    global stats_start

    print("Connection successful")
    model = switcher.mixerstate['product-name']
    print(f"Detected hardware: {model.name}")

    switcher.on('change', on_change)

    testfile = f'testset/{model.name}.yml'
    if not os.path.isfile(testfile):
        print("No test set defined for this hardware")
        exit(1)

    with open(testfile) as handle:
        tests = yaml.load(handle.read(), yaml.Loader)
    print(f"Loaded {len(tests['tests'])} test definitions")
    print("Setting initial state...")

    for prep in tests['prepare']:
        prepqueue.append({
            'send': prep,
        })

    for test in tests['tests']:
        if 'parameter' in test:
            sets = []
            for pname in test['parameter']:
                s = []
                for val in test['parameter'][pname]:
                    s.append((pname, val))
                sets.append(s)
            for combo in itertools.product(*sets):
                parameters = {}
                for arg in combo:
                    parameters[arg[0]] = arg[1]

                expectparam = parameters.copy()
                parameters.update(test['send'])
                expectparam.update(test['expect'])

                testqueue.append({
                    'send': parameters,
                    'expect': expectparam
                })
        else:
            testqueue.append(test)

    stats_start = datetime.now()
    send_next()


def on_disconnected():
    print("Hardware has disconnected")


def run_tests(device):
    global switcher
    print(f"Connecting to {device}...")
    switcher = AtemProtocol(device)
    switcher.on('connected', on_connected)
    switcher.on('disconnected', on_disconnected)
    switcher.connect()
    while True:
        switcher.loop()


def main():
    parser = argparse.ArgumentParser(description="pyatem unit test tool")
    parser.add_argument('device', help="Device ip address or 'usb'")
    args = parser.parse_args()
    run_tests(args.device)


if __name__ == '__main__':
    main()
