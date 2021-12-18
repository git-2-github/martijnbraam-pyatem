#!/usr/bin/env python3
import argparse
import json
import sys

import requests
from requests.auth import HTTPBasicAuth


def switcher(proxy, index, to_source, auto=False, username=None, password=None):
    auth = None
    if username is not None and password is not None:
        auth = HTTPBasicAuth(username, password)

    if to_source.isnumeric():
        to_source = int(to_source)

    if auto:
        r = requests.get(f'{proxy}/program-bus-input', auth=auth)
        try:
            reply = r.json()
            if reply[str(index)]['source'] != to_source:
                data = {'index': index, 'source': to_source}
                requests.post(f'{proxy}/preview-input', data, auth=auth)
                data = {'index': index}
                requests.post(f'{proxy}/auto', data, auth=auth)
            else:
                sys.exit(2)
        except json.decoder.JSONDecodeError:
            sys.exit(1)
    else:
        data = {'index': index, 'source': to_source}
        requests.post(f'{proxy}/program-input', data=data, auth=auth)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--proxy', '-s', required=True)
    parser.add_argument('--to-source', '-t', required=True)
    parser.add_argument('--username', '-u', required=False)
    parser.add_argument('--password', '-p', required=False)
    parser.add_argument('--auto', '-a', required=False, action='store_true')
    parser.add_argument('--index', '-i', type=int, required=False, default=0)
    args = parser.parse_args()

    switcher(args.proxy, args.index, args.to_source, args.auto, args.username, args.password)
