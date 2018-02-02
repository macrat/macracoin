import base64
import json
import urllib.parse

import falcon

import core
from peer.chainmanager import ChainManager


class BaseResource:
    def __init__(self, manager: ChainManager) -> None:
        self.manager = manager


class ConnectResource(BaseResource):
    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.body = json.dumps(tuple(self.manager.client.hosts))

    def on_put(self, req: falcon.Request, resp: falcon.Response) -> None:
        msg = json.loads(req.stream.read())

        print('connected {}'.format(msg['addr']))

        resp.body = json.dumps(tuple(self.manager.client.hosts))
        self.manager.connected(msg['addr'])

    def on_delete(self, req: falcon.Request, resp: falcon.Response) -> None:
        msg = json.loads(req.stream.read())

        print('disconnected {}'.format(msg['addr']))

        self.manager.disconnected(msg['addr'])
        resp.status = falcon.HTTP_201


class BlockResource(BaseResource):
    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.body = self.manager.chain.as_json()

    def on_put(self, req: falcon.Request, resp: falcon.Response) -> None:
        msg = json.loads(req.stream.read())

        print('receive block {}'.format(msg['block']['signature']))

        self.manager.add_block(core.Block.from_dict(msg['block']),
                               msg.get('host'))

        resp.status = falcon.HTTP_201

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
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


class SingleBlockResource(BaseResource):
    def on_get(self,
               req: falcon.Request,
               resp: falcon.Response,
               index: int) -> None:

        try:
            resp.body = self.manager.chain[index].as_json()
        except IndexError:
            resp.status = falcon.HTTP_404


class MessageResource(BaseResource):
    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        msg = json.loads(req.stream.read())

        print('send message of {}'.format(msg['namespace']))

        message = core.Message.from_dict(msg)
        self.manager.add_message(message)
        resp.status = falcon.HTTP_201
