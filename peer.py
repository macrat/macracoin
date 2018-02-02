import base64
import json
import urllib.parse

import falcon
import requests

import core


class ChainManager:
    def __init__(self, addr, chain):
        self.addr = addr
        self.chain = chain
        self.other_hosts = set()

    @classmethod
    def clone(cls, local, remote):
        url = urllib.parse.urljoin(remote, 'block')
        with requests.get(url) as resp:
            result = cls(local, core.Chain.from_json(resp.text))

        result.connect(remote)

        return result

    def connected(self, addr):
        self.other_hosts.add(addr)

    def disconnected(self, addr):
        self.other_hosts.remove(addr)

    def connect(self, addr):
        print('connect to {}'.format(addr))

        data = json.dumps({'addr': self.addr})

        headers = {'Content-Type': 'application/json'}

        url = urllib.parse.urljoin(addr, 'connection')
        with requests.put(url, data=data, headers=headers) as resp:
            host = urllib.parse.urlparse(addr).netloc
            if ':' in host:
                host = host.split(':')[0]

            self.other_hosts.add(addr)

    def disconnect(self, addr):
        print('disconnect by {}'.format(addr))

        url = urllib.parse.urljoin(addr, 'connection')
        requests.delete(
            url,
            data=json.dumps({'addr': self.addr}),
            headers={'Content-Type': 'application/json'},
        )

        self.other_hosts.remove(addr)

    def disconnect_all(self):
        for addr in self.other_hosts:
            print('disconnect by {}'.format(addr))

            url = urllib.parse.urljoin(addr, 'connection')
            requests.post(
                url,
                data=json.dumps({'addr': self.addr}),
                headers={'Content-Type': 'application/json'},
            )

        self.other_hosts = set()

    def add_block(self, block, origin=None):
        if block in self.chain:
            return False

        self.chain.join(block)

        data = json.dumps({
            'host': self.addr,
            'block': self.chain[-2].as_dict(),
        })
        headers = {'Content-Type': 'application/json'}

        for addr in self.other_hosts:
            if addr != origin:
                print('notify to {}'.format(addr))
                url = urllib.parse.urljoin(addr, 'block')
                requests.put(url, data=data, headers=headers)

        return True

    def close_block(self, closer, timestamp, key, signature, host=None):
        self.chain[-1].closer = closer
        self.chain[-1].timestamp = timestamp
        self.chain[-1].key = key
        self.chain[-1].signature = signature

        if not self.chain[-1].verify():
            self.chain[-1].timestamp = None
            self.chain[-1].key = None
            self.chain[-1].closer = None
            self.chain[-1].signature = None
            return False

        self.add_block(core.Block(self.chain[-1]), host)

        return True

    def add_message(self, message):
        self.chain[-1].pool(message)


class ConnectResource:
    def __init__(self, manager):
        self.manager = manager

    def on_get(self, req, resp):
        resp.body = json.dumps(tuple(self.manager.other_hosts))

    def on_put(self, req, resp):
        msg = json.loads(req.stream.read())

        print('connected {}'.format(msg['addr']))

        resp.body = json.dumps(tuple(self.manager.other_hosts))
        self.manager.connected(msg['addr'])

    def on_delete(self, req, resp):
        msg = json.loads(req.stream.read())

        print('disconnected {}'.format(msg['addr']))

        self.manager.disconnected(msg['addr'])
        resp.status = falcon.HTTP_201


class BlockResource:
    def __init__(self, manager):
        self.manager = manager

    def on_get(self, req, resp):
        resp.body = self.manager.chain.as_json()

    def on_put(self, req, resp):
        msg = json.loads(req.stream.read())

        print('receive block {}'.format(msg['block']['signature']))

        self.manager.add_block(core.Block.from_dict(msg['block']),
                               msg.get('host'))

        resp.status = falcon.HTTP_201

    def on_post(self, req, resp):
        msg = json.loads(req.stream.read())

        print('close block with {}'.format(msg['key']))

        ok = self.manager.close_block(
            core.User.from_pem(msg['user']),
            msg['timestamp'],
            base64.b64decode(msg['key']),
            base64.b64decode(msg['signature']),
            msg.get('host'),
        )

        if ok:
            resp.status = falcon.HTTP_201
        else:
            resp.status = falcon.HTTP_401


class SingleBlockResource:
    def __init__(self, manager):
        self.manager = manager

    def on_get(self, req, resp, index):
        try:
            resp.body = self.manager.chain[index].as_json()
        except IndexError:
            resp.status = falcon.HTTP_404


class MessageResource:
    def __init__(self, manager):
        self.manager = manager

    def on_post(self, req, resp):
        msg = json.loads(req.stream.read())

        print('send message of {}'.format(msg['namespace']))

        message = core.Message.from_dict(msg)
        self.manager.add_message(message)
        resp.status = falcon.HTTP_201


if __name__ == '__main__':
    import sys
    from wsgiref import simple_server

    app = falcon.API()

    if len(sys.argv) == 1:
        print('made origin server')
        rootuser = core.User.generate()
        manager = ChainManager('http://localhost:54321',
                               core.Chain.generate(rootuser))
        port = 54321
    else:
        print('clone by {}'.format(sys.argv[1]))
        manager = ChainManager.clone('http://localhost:54320', sys.argv[1])
        port = 54320

    print('length={}, root={}'.format(len(manager.chain),
                                      manager.chain[0].signature.hex()))

    app.add_route('/connection', ConnectResource(manager))
    app.add_route('/block', BlockResource(manager))
    app.add_route('/block/{index:int}', SingleBlockResource(manager))
    app.add_route('/message', MessageResource(manager))

    print('listening on {}...'.format(port))
    try:
        simple_server.make_server('localhost', port, app).serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        manager.disconnect_all()
