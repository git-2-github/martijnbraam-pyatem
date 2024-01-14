import threading
import logging
from functools import partial
from time import sleep

from .error import DependencyError
import pyatem.command as commandmodule

try:
    import rtmidi
    from rtmidi.midiutil import open_midiinput, open_midioutput, list_available_ports
    from rtmidi.midiconstants import NOTE_ON, NOTE_OFF, PITCH_BEND
except ModuleNotFoundError:
    rtmidi = None


class MidiFrontendThread(threading.Thread):
    def __init__(self, config, threadlist):
        threading.Thread.__init__(self)
        if rtmidi is None:
            raise DependencyError("The rtmidi library is not available")
        self.name = 'midi.' + str(config['bind'])
        self.bind = str(config['bind'])
        self.config = config
        self.threadlist = threadlist
        self.status = 'initializing...'
        self.error = None

        self.port = None
        self.output = None
        self.input = None
        self.map = {}
        self.reverse = {}
        self.dump = config['dump'] if 'dump' in config else False

        self.eventname = {
            'CC': 11,
            'NOTE-ON': 9,
            'NOTE-OFF': 8,
            'PITCH-BEND': 14,
        }

        # Parse the configured midi events and create the midi->switcher mapping
        for ckey in config:
            if '/' not in ckey:
                continue
            part = ckey.split('/')
            if part[0] == '*':
                channel = None
            else:
                channel = int(part[0])
            event = part[1]
            if event.isnumeric():
                event = int(part[1])
            else:
                event = self.eventname[event]
            key = None
            if len(part) > 2:
                key = int(part[2])
            if len(part) > 3:
                value = int(part[3])
            else:
                value = None
            mkey = (channel, event, key, value)

            fieldname = config[ckey]['field']
            classname = fieldname.title().replace('-', '') + "Command"
            if not hasattr(commandmodule, classname):
                logging.error(f'unrecognized command {fieldname}')
                self.status = 'error'
                self.error = 'config error'
                return
            arguments = {}
            for argname in config[ckey]:
                if argname in ['hardware', 'field']:
                    continue
                arguments[argname] = config[ckey][argname]
            cmd = getattr(commandmodule, classname)(**arguments)
            action = (config[ckey]['hardware'], cmd)

            if mkey not in self.map:
                self.map[mkey] = []
            self.map[mkey].append(action)

        # Parse the switcher events and create the switcher->midi mapping
        for ckey in config:
            if ':' not in ckey:
                continue

            name, field, raw = ckey.split(':', maxsplit=2)
            filters = {}
            raw = raw.split(':')
            for i, f in enumerate(raw):
                if '=' in f:
                    k, v = f.split('=', maxsplit=1)
                    v = int(v)
                else:
                    k = f
                    v = None
                filters[k] = v
                if i == len(raw) - 1:
                    filters['_val'] = k

            if name not in self.reverse:
                self.reverse[name] = {}

            if field not in self.reverse[name]:
                self.reverse[name][field] = []
            filters['_action'] = config[ckey]
            self.reverse[name][field].append(filters)

        # Subscribe to all requested switchers
        hw_names = set()
        for ckey in config:
            if ':' not in ckey:
                continue
            name, _ = ckey.split(':', maxsplit=1)
            hw_names.add(name)
        sleep(0.1)
        for hw in hw_names:
            sw = self.threadlist['hardware'][hw].switcher
            sw.on('change', partial(self.on_switcher_changed, hw))
            sw.on('connected', partial(self.on_switcher_connected, hw))

    def run(self):
        logging.info('MIDI frontend run')

        temp = rtmidi.MidiIn()
        ports = temp.get_ports()
        options = []
        for port in ports:
            if 'Midi Through' in port:
                continue
            options.append(port)
            if self.bind == 'any':
                break
            if self.bind == port:
                break
        else:
            if self.bind == 'any':
                logging.error(f'Could not find any midi devices to bind to')
            else:
                logging.error(f'Could not bind to midi device "{self.bind}"')
                devices = '", "'.join(options)
                logging.error(f'Midi devices present: ["{devices}"]')
            self.status = "error"
            self.error = "hardware not present"
            return

        self.port = port
        midiin, port_name = open_midiinput(self.port, client_name="OpenSwitcher Proxy")
        midiout, port_name = open_midioutput(self.port, client_name="OpenSwitcher Proxy")

        self.output = midiout
        self.input = midiin
        midiin.set_callback(self.on_midi_in)

        hw_names = set()
        for ckey in self.config:
            if ':' not in ckey:
                continue
            name, _ = ckey.split(':', maxsplit=1)
            hw_names.add(name)

        for hw in hw_names:
            sw = self.threadlist['hardware'][hw].switcher
            sw.on('change', partial(self.on_switcher_changed, hw))
            sw.on('connected', partial(self.on_switcher_connected, hw))

            if self.threadlist['hardware'][hw].status == 'connected':
                # Hardware is already connected at this point, re-generate the initial data
                self.on_switcher_connected(hw)

        self.status = 'running'

    def get_events(self, channel, event, key, value):
        result = []
        mkey = (channel, event, key, value)
        if mkey in self.map:
            result.extend(self.map[mkey])
        mkey = (channel, event, key, None)
        if mkey in self.map:
            result.extend(self.map[mkey])
        mkey = (None, event, key, value)
        if mkey in self.map:
            result.extend(self.map[mkey])
        mkey = (None, event, key, None)
        if mkey in self.map:
            result.extend(self.map[mkey])
        return result

    def on_midi_in(self, raw, data=None):
        event_raw, key, value = raw[0]
        event = event_raw >> 4
        channel = event_raw & 0b00001111

        if event == 14:
            value = (value << 7) | key
            key = None

        if self.dump:
            ename = f'EVENT-{event}'
            for e in self.eventname:
                if event == self.eventname[e]:
                    ename = e
            if ename == 'PITCH-BEND':
                print(f'{channel}/{ename} = {value}')
            else:
                print(f'{channel}/{ename}/{key} = {value}')
        for action in self.get_events(channel, event, key, value):
            command = action[1]
            if event == 14:
                command.position = int(value / (2 ** 14) * 10000)
            self.threadlist['hardware'][action[0]].switcher.send_commands([command])

    def on_switcher_changed(self, hw, field, value):
        if hw not in self.reverse:
            return
        if field not in self.reverse[hw]:
            return
        for f in self.reverse[hw][field]:
            match = True
            state = False
            for filter_field in f:
                if filter_field in ["_action", "_val"]:
                    continue
                filter_value = f[filter_field]
                real_value = getattr(value, filter_field)

                if filter_field == f['_val'] and filter_value is not None:
                    state = real_value == filter_value
                    continue
                elif filter_field == f['_val'] and filter_value is None:
                    state = real_value
                elif real_value != filter_value:
                    match = False
                    break

            if match:
                action = f['_action']

                if action['event'] == 'note-on':
                    channel = (action['channel'] if 'channel' in action else 1) - 1
                    message = [
                        NOTE_ON | channel,
                        action['key'],
                        action['on'] if state else action['off']
                    ]
                elif action['event'] == 'pitch-bend':
                    channel = (action['channel'] if 'channel' in action else 1) - 1
                    midivalue = (state - action['min']) / (action['max'] - action['min'])
                    midivalue = int(midivalue * (2 ** 14))
                    lsb = midivalue & 0b01111111
                    msb = (midivalue >> 7) & 0b01111111
                    message = [
                        PITCH_BEND | channel,
                        lsb,
                        msb
                    ]
                else:
                    raise ValueError(f"Unknown action '{action['event']}'")
                self.output.send_message(message)

    def on_switcher_connected(self, hw):
        sw = self.threadlist['hardware'][hw].switcher
        items = list(sw.mixerstate.items())
        for field, value in items:
            if isinstance(value, dict):
                for k in value:
                    v = value[k]
                    self.on_switcher_changed(hw, field, v)
            else:
                self.on_switcher_changed(hw, field, value)

    def get_status(self):
        if self.status == 'error':
            return f'{self.status}, {self.error}'
        else:
            return f'{self.status} ({self.port})'
