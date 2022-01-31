import threading
import logging
import json

from .error import DependencyError
from .frontend_httpapi import FieldEncoder
import pyatem.command as commandmodule

try:
    import rtmidi
    from rtmidi.midiutil import open_midiinput, open_midioutput, list_available_ports
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
        self.map = {}
        self.reverse = {}

        eventname = {
            'CC': 11,
            'NOTE-ON': 9,
            'NOTE-OFF': 8,
        }

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
                event = eventname[event]
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
        midiin.set_callback(self.on_midi_in)
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
        print(channel, event, key, value)
        for action in self.get_events(channel, event, key, value):
            print(action)
            self.threadlist['hardware'][action[0]].switcher.send_commands([action[1]])

    def on_switcher_changed(self, hw, field, value):
        raw = json.dumps(value, cls=FieldEncoder)
        topic = self.topic.format(hardware=hw, field=field)
        self.client.publish(topic, raw)

    def on_switcher_connected(self, hw):
        return
        self.on_switcher_changed(hw, 'status', {'upstream': True})
        sw = self.threadlist['hardware'][hw].switcher
        items = list(sw.mixerstate.items())
        for field, value in items:
            self.on_switcher_changed(hw, field, value)

    def on_switcher_disconnected(self, hw):
        return
        self.on_switcher_changed(hw, 'status', {'upstream': False})

    def on_mqtt_message(self, msg):
        return

        match = self.topic_re.match(msg.topic)
        if not match:
            logging.error(f'MQTT: malformed command topic: {msg.topic}')

        hw = match.group('hardware')
        fieldname = match.group('field')

        if hw not in self.hw_name:
            logging.error(f'MQTT: not handling writes for "{hw}"')
            return

        classname = fieldname.title().replace('-', '') + "Command"
        if not hasattr(commandmodule, classname):
            logging.error(f'MQTT: unrecognized command {fieldname}')
            return
        try:
            arguments = json.loads(msg.payload)
        except JSONDecodeError as e:
            logging.error('received malformed payload, need a JSON dict')
            return
        if not isinstance(arguments, dict):
            logging.error(f'MQTT: mailformed payload, needs a JSON dict')
            return
        for key in arguments:
            try:
                arguments[key] = int(arguments[key])
            except:
                pass
        if 'source' in arguments:
            inputs = self.threadlist['hardware'][hw].switcher.inputs
            if arguments['source'] in inputs:
                arguments['source'] = inputs[arguments['source']]
        try:
            cmd = getattr(commandmodule, classname)(**arguments)
            self.threadlist['hardware'][hw].switcher.send_commands([cmd])
        except Exception as e:
            logging.error(f'MQTT: cannot write {fieldname}: {str(e)}')

    def get_status(self):
        if self.status == 'error':
            return f'{self.status}, {self.error}'
        else:
            return self.status
