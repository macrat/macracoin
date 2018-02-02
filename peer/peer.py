from wsgiref import simple_server

import falcon

import core
from peer.chainmanager import ChainManager
from peer import endpoint


class Peer:
    def __init__(self, manager: ChainManager) -> None:
        print('length={}, root={}'.format(len(manager.chain),
                                          manager.chain[0].signature.hex()))

        self.manager = manager
        self.app = falcon.API()

        self.app.add_route('/connection', endpoint.ConnectResource(manager))
        self.app.add_route('/block', endpoint.BlockResource(manager))
        self.app.add_route('/block/{index:int}', endpoint.SingleBlockResource(manager))
        self.app.add_route('/message', endpoint.MessageResource(manager))

    @classmethod
    def generate(cls, addr: str, rootuser: core.User) -> 'Peer':
        print('made origin server')
        return cls(ChainManager.generate(addr, rootuser))

    @classmethod
    def clone(cls, addr: str, remote: str) -> 'Peer':
        print('clone by {}'.format(remote))
        return cls(ChainManager.clone(addr, remote))

    def __call__(self, environment, start_response):
        return self.app(environment, start_response)

    def connect(self, addr: str) -> None:
        self.manager.connect(addr)

    def destroy(self) -> None:
        self.manager.disconnect_all()

    def run(self, addr='localhost', port=50000) -> None:
        server = simple_server.make_server(addr, port, self)

        print('listening on http://{}:{}...'.format(addr, port))

        try:
            server.serve_forever()
        except:
            self.destroy()
