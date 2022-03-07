import re
import threading
import logging
import json
from functools import partial
from json import JSONDecodeError

from .error import DependencyError
from .frontend_httpapi import FieldEncoder
import pyatem.command as commandmodule

try:
    import paho.mqtt.client as mqtt
    from paho.mqtt.subscribeoptions import SubscribeOptions
except ModuleNotFoundError:
    mqtt = None


class MqttFrontendThread(threading.Thread):
    def __init__(self, config, threadlist):
        threading.Thread.__init__(self)
        if mqtt is None:
            raise DependencyError("The paho-mqtt library is not available")
        self.name = 'mqtt.' + str(config['host'])
        self.config = config
        self.threadlist = threadlist
        self.hw_name = self.config['hardware'].split(',')
        self.topic = self.config['topic'] if 'topic' in self.config else "atem/{hardware}/{field}"
        self.client = None
        self.status = 'initializing...'
        self.error = None
        self.readonly = not self.config.get('allow-writes', False)
        self.subscribe = self.config['topic-subscribe'] if 'topic-subscribe' in self.config else self.topic

        regex = self.subscribe.replace('{hardware}', r'(?P<hardware>[^/]+)')
        regex = regex.replace('{field}', r'(?P<field>.+)')
        self.topic_re = re.compile(regex)

    def run(self):
        logging.info('MQTT frontend run')
        host, port = self.config['host'].split(':')
        port = int(port)
        self.client = mqtt.Client(client_id=f'atem-{self.name}', userdata=self, protocol=mqtt.MQTTv5)
        self.client.on_connect = lambda client, userdata, flags, rc, props: self.on_mqtt_connect(flags, rc, props)
        self.client.on_message = lambda client, userdata, msg: self.on_mqtt_message(msg)
        logging.info(f'connecting to {host}:{port}')
        try:
            self.client.connect(host, port, keepalive=3)
        except Exception as e:
            logging.error(f'Could not connect to the MQTT server at {host}:{port}')
            logging.error(e)
            self.error = f'could not connect to {host}:{port}'
            self.status = 'error'
            return
        for hw in self.hw_name:
            sw = self.threadlist['hardware'][hw].switcher

            # Hook into the events for the registered switchers and update the mqtt topic
            sw.on('connected', partial(self.on_switcher_connected, hw))
            sw.on('disconnected', partial(self.on_switcher_disconnected, hw))
            sw.on('change', partial(self.on_switcher_changed, hw))

            if self.threadlist['hardware'][hw].status == 'connected':
                # Hardware is already connected at this point, re-generate the initial data
                self.on_switcher_connected(hw)

        self.client.loop_forever()

    def on_switcher_changed(self, hw, field, value):
        raw = json.dumps(value, cls=FieldEncoder)
        topic = self.topic.format(hardware=hw, field=field)
        self.client.publish(topic, raw)

    def on_switcher_connected(self, hw):
        self.on_switcher_changed(hw, 'status', {'upstream': True})
        sw = self.threadlist['hardware'][hw].switcher
        items = list(sw.mixerstate.items())
        for field, value in items:
            self.on_switcher_changed(hw, field, value)

    def on_switcher_disconnected(self, hw):
        self.on_switcher_changed(hw, 'status', {'upstream': False})

    def on_mqtt_connect(self, flags, rc, properties):
        self.status = 'running'
        logging.info(f'MQTT: connected ({rc})')
        if not self.readonly:
            sub = self.subscribe.replace('{hardware}', '+').replace('{field}', '#')
            logging.info(f'Subscribing to topic {sub}')
            self.client.subscribe((sub, SubscribeOptions(noLocal=True)))

    def on_mqtt_message(self, msg):
        if self.readonly:
            logging.error('MQTT writes disabled')
            return

        match = self.topic_re.match(msg.topic)
        if not match:
            logging.error(f'MQTT: malformed command topic: {msg.topic}')

        hw = match.group('hardware')
        fieldname = match.group('field')

        if hw not in self.hw_name:
            logging.error(f'MQTT: not handling writes for "{hw}"')
            return

        if self.threadlist['hardware'][hw].status != "connected":
            logging.error(f'MQTT: writing to disconnected device "{hw}"')
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

        source_name_fault = False
        if 'source' in arguments:
            inputs = self.threadlist['hardware'][hw].switcher.inputs
            if not isinstance(arguments['source'], int) and arguments['source'] not in inputs:
                source_name_fault = True
            if arguments['source'] in inputs:
                arguments['source'] = inputs[arguments['source']]
        try:
            cmd = getattr(commandmodule, classname)(**arguments)
            self.threadlist['hardware'][hw].switcher.send_commands([cmd])
        except Exception as e:
            if source_name_fault:
                logging.error(f'MQTT: invalid source name: {arguments["source"]}')
            else:
                logging.error(f'MQTT: cannot write {fieldname}: {str(e)}')

    def get_status(self):
        if self.status == 'error':
            return f'{self.status}, {self.error}'
        if self.readonly:
            return self.status + ' (readonly)'
        else:
            return self.status + ' (writable)'
