import core
from peer.client import Client


class ChainManager:
    def __init__(self, addr: str, chain: core.Chain) -> None:
        self.addr = addr
        self.chain = chain
        self.client = Client(addr)

    @classmethod
    def clone(cls, local: str, remote: str) -> 'ChainManager':
        result = cls(local, Client().get_chain(remote))
        result.connect(remote)

        return result

    @classmethod
    def generate(cls, addr: str, rootuser: core.User) -> 'ChainManager':
        return cls(addr, core.Chain.generate(rootuser))

    def connected(self, addr: str) -> None:
        self.client.connected(addr)

    def disconnected(self, addr: str) -> None:
        self.client.disconnected(addr)

    def connect(self, addr: str) -> None:
        self.client.connect_request(addr)

    def disconnect_all(self) -> None:
        self.client.disconnect_all()

    def add_block(self, block: core.Block, origin: str = None) -> bool:
        if block in self.chain:
            return False

        self.chain.join(block)
        self.client.put_block(self.chain[-2], origin)

        return True

    def close_block(self,
                    closer: core.User,
                    timestamp: int,
                    key: bytes,
                    signature: bytes,
                    host: str = None) -> bool:

        try:
            next_ = self.chain[-1].close(closer, key, timestamp, signature)
        except Exception as e:
            print(e)
            return False

        self.add_block(next_, host)

        return True

    def add_message(self, message: core.Message) -> None:
        self.chain[-1].pool(message)
