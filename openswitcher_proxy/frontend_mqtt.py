import threading
import logging
import json
from functools import partial

from .error import DependencyError
from .frontend_httpapi import FieldEncoder

try:
    import paho.mqtt.client as mqtt
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

    def run(self):
        logging.info('MQTT frontend run')
        host, port = self.config['host'].split(':')
        port = int(port)
        self.client = mqtt.Client(client_id=f'atem-{self.name}', userdata=self)
        self.client.on_connect = lambda client, userdata, flags, rc: self.on_mqtt_connect(flags, rc)
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

    def on_mqtt_connect(self, flags, rc):
        self.status = 'running'
        logging.info(f'MQTT: connected ({rc})')
        # TODO: enable once on_mqtt_message() works
        # client.subscribe(f'atem/{userdata.hw_name}/#')

    def on_mqtt_message(self, msg):
        # TODO: propagate to the switcher, eventually
        logging.debug(f'MQTT: msg: {msg.topic} {msg.payload}')

    def get_status(self):
        if self.status == 'error':
            return f'{self.status}, {self.error}'
        return self.status
