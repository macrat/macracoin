import base64
import hashlib
import json
import time
import typing

from Crypto.Util import randpool

from core import errors
from core.message import Message
from core.user import User


DEFAULT_MAGIC_NUMBER = 'c105ed'


class DummyBlock:
    """ The dummy block for emulate chain. """

    def __init__(self, index: int, magicnumber: str, signature: bytes) -> None:
        self.index = index
        if magicnumber is None:
            self.magicnumber = DEFAULT_MAGIC_NUMBER
        else:
            self.magicnumber = magicnumber
        self.signature = signature


class Block():
    """ The block of chain. """

    def __init__(self,
                 parent: typing.Union['Block', DummyBlock, None],
                 magicnumber: str = None) -> None:

        self.parent = parent
        self.messages: typing.List[Message] = []
        self.key: bytes = None
        self.closer: User = None
        self.timestamp: int = None
        self.signature: bytes = None

        if parent is not None:
            self.index: int = parent.index + 1
            self.magicnumber: str = parent.magicnumber
        else:
            self.index: int = 0

            if magicnumber is None:
                self.magicnumber: str = DEFAULT_MAGIC_NUMBER
            else:
                self.magicnumber: str = magicnumber

        if not isinstance(self.magicnumber, str) or len(self.magicnumber) == 0:
            raise TypeError('magic number must be non empty string')

    @classmethod
    def make_root(cls, user: User, magicnumber: str = None) -> 'Block':
        """ Make root block

        The root block has no any messages and closed from the creating.
        The first closer is the administrator of the chain.

        >>> rootuser = User.generate()

        >>> root = Block.make_root(rootuser)
        >>> child = Block(root)

        >>> root.is_closed()
        True
        >>> root.verify()
        True
        >>> child.is_closed()
        False

        >>> root.messages
        []

        Index of the root block is 0.

        >>> root.index
        0
        >>> child.index
        1
        """

        result = cls(None, magicnumber)

        result.timestamp = int(time.time() * 1000)
        result.key = randpool.RandomPool().get_bytes(32)
        result.closer = user
        result.signature = user.sign_raw(
            result.timestamp.to_bytes(8, 'big') + result.key
        )

        return result

    def is_root(self) -> bool:
        """ Check this block is root block or not.


        >>> root = Block.make_root(User.generate())
        >>> child = Block(root)

        >>> root.is_root()
        True
        >>> child.is_root()
        False
        """

        return self.index == 0 and self.parent is None

    def is_closed(self) -> bool:
        """ Check this block is already closed.


        >>> user = User.generate()
        >>> root = Block.make_root(user, magicnumber='000')
        >>> child = Block(root)

        >>> root.is_closed()
        True
        >>> child.is_closed()
        False

        >>> leaf = child.close(user, mining(child))

        >>> child.is_closed()
        True

        >>> leaf.is_closed()
        False
        """

        return (self.key is not None
                and self.closer is not None
                and self.timestamp is not None
                and self.signature is not None)

    def pool(self, message: Message) -> None:
        """ Pooling new message into this block.


        >>> user = User.generate()
        >>> root = Block.make_root(user)

        The block is empty when created.

        >>> child = Block(root)
        >>> len(child.messages)
        0

        Pooling new message like this.

        >>> message = Message(user, 'namespace', 'hello')
        >>> child.pool(message)
        >>> len(child.messages)
        1
        >>> child.messages[0] == message
        True

        Can't pooling message into a closed block.

        >>> root.is_closed()
        True
        >>> root.pool(message)
        Traceback (most recent call last):
            ...
        core.errors.BlockAlreadyClosedError
        """

        if self.is_closed():
            raise errors.BlockAlreadyClosedError()

        if not message.verify():
            raise errors.InvalidSignatureError()

        self.messages.append(message)

    def verify(self) -> bool:
        """ Verify a closed block.


        >>> rootuser = User.generate()

        >>> root = Block.make_root(rootuser)
        >>> root.verify()
        True
        >>> root.timestamp += 1
        >>> root.verify()
        False

        Can't verify not closed block.

        >>> Block(root).verify()
        Traceback (most recent call last):
            ...
        core.errors.BlockNotClosedError
        """

        if not self.is_closed():
            raise errors.BlockNotClosedError()

        sign_correct = self.closer.verify_raw(
            self.timestamp.to_bytes(8, 'big') + self.key,
            self.signature,
        )
        if not sign_correct:
            return False

        if self.is_root():
            return len(self.messages) == 0
        elif self.parent.index + 1 != self.index:
            return False
        else:
            return self.verify_key(self.key)

    def verify_key(self, key: bytes) -> bool:
        """ Verify key for closing this block. """

        if len(key) != 32:
            return False

        if self.magicnumber != self.parent.magicnumber:
            return False

        h = hashlib.sha256()

        h.update(self.parent.signature)

        for m in self.messages:
            h.update(m.signature)

        h.update(key)

        hash_ = h.hexdigest()

        return hash_.endswith(self.magicnumber)

    def close(self,
              user: User,
              key: bytes,
              timestamp: int = None,
              signature: bytes = None) -> 'Block':

        """ Close this block and create next block.


        Can't close already closed block.

        >>> root = Block.make_root(User.generate())
        >>> root.is_closed()
        True
        >>> root.close(User.generate(), b'hello')
        Traceback (most recent call last):
            ...
        core.errors.BlockAlreadyClosedError
        """

        if self.is_closed():
            raise errors.BlockAlreadyClosedError()

        if not self.verify_key(key):
            raise errors.InvalidKeyError()

        if timestamp is None:
            timestamp = int(time.time() * 1000)

        if signature is not None:
            if not user.verify_raw(timestamp.to_bytes(8, 'big') + key,
                                   signature):
                raise errors.InvalidSignatureError()
            self.signature = signature
        else:
            self.signature = user.sign_raw(
                timestamp.to_bytes(8, 'big') + key
            )

        self.timestamp = timestamp
        self.key = key
        self.closer = user

        return Block(self)

    def as_dict(self) -> dict:
        """ Convert as dictionary for serialize. """

        parent = None
        if self.parent is not None:
            parent = base64.b64encode(self.parent.signature).decode('ascii')

        key = None
        if self.key is not None:
            key = base64.b64encode(self.key).decode('ascii')

        closer = None
        if self.closer is not None:
            closer = self.closer.public_pem

        signature = None
        if self.signature is not None:
            signature = base64.b64encode(self.signature).decode('ascii')

        return {
            'index': self.index,
            'parent': parent,
            'key': key,
            'closer': closer,
            'timestamp': self.timestamp,
            'signature': signature,
            'messages': [m.as_dict() for m in self.messages],
        }

    def as_json(self) -> str:
        """ Serialize as json.


        >>> root = Block.make_root(User.generate())

        >>> root2 = Block.from_json(root.as_json())
        >>> root2.verify()
        True
        >>> root.signature == root2.signature
        True


        >>> child = Block(root)
        >>> child.pool(Message(User.generate(), 'namespace', 'hello world'))

        >>> child2 = Block.from_json(child.as_json())
        >>> len(child.messages) == len(child2.messages) == 1
        True
        >>> child.messages[0].verify() == child2.messages[0].verify() == True
        True
        >>> child.messages[0].signature == child2.messages[0].signature
        True
        """

        return json.dumps(self.as_dict())

    @classmethod
    def from_dict(cls, data: dict, magicnumber: str = None) -> 'Block':
        """ Convert from dictionary for deserialize. """

        parent = None
        if data['parent'] is not None:
            parent = DummyBlock(
                data['index'] - 1,
                magicnumber,
                base64.b64decode(data['parent']),
            )

        result = cls(parent)

        if data['key'] is not None:
            result.key = base64.b64decode(data['key'])

        if data['closer'] is not None:
            result.closer = User.from_pem(data['closer'])

        result.timestamp = data['timestamp']

        if data['signature'] is not None:
            result.signature = base64.b64decode(data['signature'])

        result.messages = [Message.from_dict(m) for m in data['messages']]

        return result

    @classmethod
    def from_json(cls, data: str, magicnumber: str = None) -> 'Block':
        """ Deserialize from json. """

        return cls.from_dict(json.loads(data), magicnumber=magicnumber)


def mining(block: Block) -> bytes:
    """ Find key for closing block. """

    hash_ = hashlib.sha256()

    hash_.update(block.parent.signature)

    for m in block.messages:
        hash_.update(m.signature)

    for i in range(2<<32):
        key = i.to_bytes(32, 'big')

        h = hash_.copy()
        h.update(key)

        if h.hexdigest().endswith(block.magicnumber):
            return key

    raise ValueError('not found key')


if __name__ == '__main__':
    import datetime
    import functools


    user = User.generate()
    root = Block.make_root(user)
    child = Block(root)

    oldtime = datetime.datetime.now()
    timediffs = []
    print('{:5d}: {}({}) [{}]'.format(0, datetime.datetime.now(), datetime.timedelta(0), root.key.hex()))
    while True:
        key = mining(child)
        child = child.close(user, key)

        now = datetime.datetime.now()
        timediffs.append(now - oldtime)
        oldtime = now
        print('{:5d}: {}({}) [{}]'.format(len(timediffs), now, functools.reduce(lambda x, y: x + y, timediffs) / len(timediffs), key.hex()))
