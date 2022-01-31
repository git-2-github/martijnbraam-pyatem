import argparse
import time

import toml
import logging

from openswitcher_proxy.error import RecoverableError
from openswitcher_proxy.frontend_httpapi import HttpApiFrontendThread
from openswitcher_proxy.frontend_midi import MidiFrontendThread
from openswitcher_proxy.frontend_status import StatusFrontendThread
from openswitcher_proxy.frontend_tcp import TcpFrontendThread
from openswitcher_proxy.frontend_mqtt import MqttFrontendThread
from openswitcher_proxy.hardware import HardwareThread

logging.basicConfig(
    format="%(asctime)s [%(levelname)-8s %(threadName)-15s] %(message)s",
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
)

threads = []
nthreads = {}


def run(config_path):
    config = toml.load(config_path)
    logging.info('Loading config file ' + config_path)
    if 'hardware' in config:
        nthreads['hardware'] = {}
        for hardware in config['hardware']:
            logging.info(f'  hardware: {hardware["id"]} ({hardware["label"]})')
            t = HardwareThread(hardware)
            t.daemon = True
            threads.append(t)
            nthreads['hardware'][hardware['id']] = t
            t.start()

    if 'frontend' in config:
        nthreads['frontend'] = {}
        for frontend in config['frontend']:
            if 'host' in frontend:
                connection = frontend['host']
            elif 'bind' in frontend:
                connection = frontend['bind']
            else:
                connection = 'n/a'
                logging.error(f'  Frontend is missing bind or host option')
            logging.info(f'  frontend: {frontend["type"]} ({connection})')
            try:
                if frontend['type'] == 'status':
                    t = StatusFrontendThread(frontend, nthreads)
                elif frontend['type'] == 'http-api':
                    t = HttpApiFrontendThread(frontend, nthreads)
                elif frontend['type'] == 'tcp':
                    t = TcpFrontendThread(frontend, nthreads)
                elif frontend['type'] == 'mqtt':
                    t = MqttFrontendThread(frontend, nthreads)
                elif frontend['type'] == 'midi':
                    t = MidiFrontendThread(frontend, nthreads)
                else:
                    logging.error(f'  Unknown frontend type "{frontend["type"]}"')
                    continue
                t.daemon = True
                threads.append(t)
                nthreads['frontend'][t.name] = t
                t.start()
            except RecoverableError as e:
                logging.error(f'  Could not initialize the "{frontend["type"]}" frontend. {e}')

    while True:
        time.sleep(1)


def main():
    parser = argparse.ArgumentParser("OpenSwitcher proxy")
    parser.add_argument("--config", help="Config file to use", default="/etc/openswitcher/proxy.toml")
    args = parser.parse_args()

    run(args.config)


if __name__ == '__main__':
    main()
