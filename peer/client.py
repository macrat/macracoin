import base64
import json
import typing
import urllib.parse

import requests

import core


class Client:
    def __init__(self, addr: str = None) -> None:
        self.addr = addr
        self.hosts: typing.Set[str] = set()

    def connected(self, addr: str) -> None:
        print('connect with {}'.format(addr))

        self.hosts.add(addr)

    def disconnected(self, addr: str) -> None:
        print('disconnect with {}'.format(addr))

        self.hosts.remove(addr)

    def connect_request(self, addr: str) -> typing.Tuple[str]:
        if self.addr is None:
            raise TypeError('address is not set')

        data = json.dumps({'addr': self.addr}).encode('ascii')
        headers = {'Content-Type': 'application/json'}

        resp = requests.put(urllib.parse.urljoin(addr, 'connection'),
                            data=data,
                            headers=headers)
        resp.raise_for_status()

        self.connected(addr)

        return resp.json()

    def disconnect_all(self) -> None:
        if self.addr is None:
            raise TypeError('address is not set')

        for addr in self.hosts:
            print('disconnect with {}'.format(addr))

            url = urllib.parse.urljoin(addr, 'connection')
            requests.delete(
                url,
                data=json.dumps({'addr': self.addr}).encode('ascii'),
                headers={'Content-Type': 'application/json'},
            ).raise_for_status()

        self.hosts = set()

    def put_block(self, block: core.Block, origin: str = None) -> None:
        if not block.verify():
            raise TypeError('invalid block')

        data = json.dumps({
            'host': self.addr,
            'block': block.as_dict(),
        }).encode('ascii')
        headers = {'Content-Type': 'application/json'}

        for addr in self.hosts:
            if addr != origin:
                print('notify to {}'.format(addr))
                url = urllib.parse.urljoin(addr, 'block')
                requests.put(url,
                             data=data,
                             headers=headers).raise_for_status()

    def get_block(self, addr: str, index: int) -> core.Block:
        url = urllib.parse.urljoin(addr, '/block/{}'.format(index))
        resp = requests.get(url)
        resp.raise_for_status()

        block = core.Block.from_json(resp.text)
        if block.is_closed() and not block.verify():
            raise TypeError('invalid block')

        return block

    def post_close_block(self, addr: str, block: core.Block) -> None:
        if not block.verify():
            raise TypeError('invalid block')

        data = json.dumps({
            'user': block.closer.public_pem,
            'key': base64.b64encode(block.key).decode('ascii'),
            'timestamp': block.timestamp,
            'signature': base64.b64encode(block.signature).decode('ascii'),
        }).encode('ascii')
        header = {'Content-Type': 'application/json'}

        url = urllib.parse.urljoin(addr, '/block')
        requests.post(url, data=data, headers=header).raise_for_status()

    def get_chain(self, addr: str) -> core.Chain:
        url = urllib.parse.urljoin(addr, 'block')
        resp = requests.get(url)
        resp.raise_for_status()

        return core.Chain.from_json(resp.text)

    def post_message(self, addr: str, message: core.Message) -> None:
        url = urllib.parse.urljoin(addr, 'message')

        requests.post(
            url,
            data=message.as_json().encode('ascii'),
            headers={'Content-Type': 'application/json'},
        ).raise_for_status()
