import threading
import logging
import json
from .frontend_httpapi import FieldEncoder
try:
    import paho.mqtt.client as mqtt
except ModuleNotFoundError:
    mqtt = None


class MqttFrontendThread(threading.Thread):
    def __init__(self, config, threadlist):
        threading.Thread.__init__(self)
        if mqtt is None:
            raise NotImplementedError("The paho-mqtt library is not available")
        self.name = 'mqtt.' + str(config['host'])
        self.config = config
        self.threadlist = threadlist
        self.hw_name = self.config['hardware']
        self.switcher = self.threadlist['hardware'][self.hw_name].switcher
        self.client = None
        self.status = 'initializing...'

    def run(self):
        logging.info('MQTT frontend run')
        host, port = self.config['host'].split(':')
        port = int(port)
        self.client = mqtt.Client(client_id=f'atem-{self.name}', userdata=self)
        self.client.on_connect = lambda client, userdata, flags, rc: self.on_mqtt_connect(flags, rc)
        self.client.on_message = lambda client, userdata, msg: self.on_mqtt_message(msg)
        logging.info(f'connecting to {host}:{port}')
        self.client.connect(host, port, keepalive=3)
        self.switcher.on('change', lambda field, value: self.on_switcher_changed(field, value))
        # FIXME: this is racy, I've seen `RuntimeError: dictionary changed size during iteration` once
        for field, value in self.switcher.mixerstate.items():
            self.on_switcher_changed(field, value)
        self.client.loop_forever()

    def on_switcher_changed(self, field, value):
        raw = json.dumps(value, cls=FieldEncoder)
        self.client.publish(f'atem/{self.hw_name}/{field}', raw)

    def on_mqtt_connect(self, flags, rc):
        self.status = 'running'
        logging.info(f'MQTT: connected ({rc})')
        # TODO: enable once on_mqtt_message() works
        # client.subscribe(f'atem/{userdata.hw_name}/#')

    def on_mqtt_message(self, msg):
        # TODO: propagate to the switcher, eventually
        logging.debug(f'MQTT: msg: {msg.topic} {msg.payload}')

    def get_status(self):
        return self.status
