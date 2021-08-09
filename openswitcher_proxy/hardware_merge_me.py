import threading
import logging
import time
from functools import partial

from pyatem.protocol import AtemProtocol


class SwitcherDummy:
    def __init__(self):
        self.mixerstate = {}
        self.me_map = []


class HardwareMergeMEThread(threading.Thread):
    def __init__(self, config, namedthreads):
        self.namedthreads = namedthreads
        threading.Thread.__init__(self)
        self.name = 'hw.' + str(config['id'])
        self.switcher = SwitcherDummy()
        self.config = config
        self.stop = False
        self.status = 'init'
        self.downstreams = config['hardware'].split(',')
        self.state = {}

    def run(self):
        self.status = 'waiting for downstream device sync...'
        logging.info('Waiting for downstream device sync')
        for ds in self.downstreams:
            self.state[ds] = False
            self.namedthreads['hardware'][ds].switcher.on('connected', partial(self.on_connected, ds))
            self.namedthreads['hardware'][ds].switcher.on('change', partial(self.on_change, ds))
            self.namedthreads['hardware'][ds].switcher.on('disconnected', partial(self.on_disconnected, ds))

        while not self.stop:
            time.sleep(1)

    def get_status(self):
        return self.status

    def on_connected(self, subdev):
        self.state[subdev] = True
        connected = 0
        for ds in self.state:
            if self.state[ds]:
                connected += 1
        if connected != len(self.state):
            self.status = 'connecting [{}/{}]'.format(connected, len(self.state))
        else:
            self.status = 'connected'
            logging.info("connected to all downstreams, building initial state")
            self.build_initial_state()

    def on_disconnected(self, subdev):
        self.state[subdev] = False
        self.status = 'lost connection'
        logging.error('Lost connection with subdevice ' + subdev)

    def on_change(self, subdev, key, value):
        if key == 'mixer-effect-config':
            self.switcher.me_map

    def build_initial_state(self):
        count_mediaplayers = 0
        count_aux = 0
        count_multiviewers = 0
        count_hyperdecks = 0
        count_dve = 0
        count_stingers = 0
        count_supersources = 0
        count_rs485 = 0

        for ds in self.downstreams:
            topology = self.namedthreads['hardware'][ds].switcher.mixerstate['topology']
            me_count = topology.me_units
            for i in range(0, me_count):
                self.switcher.me_map.append((ds, i))
            count_mediaplayers += topology.mediaplayers
            count_multiviewers += topology.multiviewers
            count_hyperdecks += topology.hyperdecks
            count_dve += topology.dve
            count_stingers += topology.stingers
            count_supersources += topology.supersources
            count_rs485 += topology.rs485
            count_aux += topology.aux_outputs

        self.switcher.mixerstate['topology'] = self.namedthreads['hardware'][self.downstreams[0]].switcher.mixerstate[
            'topology']
        self.switcher.mixerstate['topology'].me_units = len(self.switcher.me_map)
        self.switcher.mixerstate['topology'].aux_outputs = count_aux
        self.switcher.mixerstate['topology'].mediaplayers = count_mediaplayers
        self.switcher.mixerstate['topology'].multiviewers = count_multiviewers
        self.switcher.mixerstate['topology'].rs485 = count_rs485
        self.switcher.mixerstate['topology'].hyperdecks = count_hyperdecks
        self.switcher.mixerstate['topology'].dve = count_dve
        self.switcher.mixerstate['topology'].stingers = count_stingers
        self.switcher.mixerstate['topology'].supersources = count_supersources
        self.switcher.mixerstate['topology'].update()

        for ds in self.downstreams:
            ds_mixerstate = self.namedthreads['hardware'][ds].switcher.mixerstate
            for key in ds_mixerstate:
                if key in ['topology']:
                    continue
                if isinstance(ds_mixerstate[key], dict):
                    for field in self.ds_mixerstate[key]:
                        if isinstance(ds_mixerstate[key][field], dict):
                            self.switcher.mixerstate[key][field] = ds_mixerstate[key][field]
                        elif hasattr(ds_mixerstate[key][field].__class__, 'ME'):

                    if key not in self.switcher.mixerstate:
                        self.switcher.mixerstate[key] = {}
