import json
import typing

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_PSS
from Crypto.Util import randpool

from core import errors


def _serialize(message: typing.Any) -> bytes:
    return json.dumps(
        message,
        separators=(',', ':'),
        sort_keys=True,
    ).encode('ascii')


class User:
    """
    >>> u = User.generate()

    >>> sig = u.sign('hello world')

    >>> u.verify('hello world', sig)
    True
    >>> u.verify('helloworld', sig)
    False

    >>> data = {'hello': 'world', 'foo': 'bar'}
    >>> u.verify(data, u.sign(data))
    True

    >>> u_pri = User.from_pem(u.private_pem)
    >>> u_pri.verify('hello world', sig)
    True

    >>> u_pub = User.from_pem(u.public_pem)
    >>> u_pub.verify('hello world', sig)
    True

    >>> u_pub = User.from_pem(u.public_pem)
    >>> u_pub.sign('foo bar')
    Traceback (most recent call last):
        ...
    core.errors.NoPrivateKeyError
    """

    def __init__(self, key: RSA._RSAobj) -> None:
        self.key = key

    @classmethod
    def generate(cls) -> 'User':
        return cls(RSA.generate(1024, randpool.RandomPool().get_bytes))

    @classmethod
    def from_pem(cls, data: str) -> 'User':
        return cls(RSA.importKey(data))

    def sign_raw(self, data: bytes) -> bytes:
        if not self.key.has_private():
            raise errors.NoPrivateKeyError()

        h = SHA256.new()
        h.update(data)
        sign = PKCS1_PSS.new(self.key).sign(h)
        return sign

    def sign(self, message: typing.Any) -> bytes:
        return self.sign_raw(_serialize(message))

    def verify_raw(self, data: bytes, signature: bytes) -> bool:
        h = SHA256.new()
        h.update(data)
        return PKCS1_PSS.new(self.key).verify(h, signature)

    def verify(self, message: typing.Any, signature: bytes) -> bool:
        return self.verify_raw(_serialize(message), signature)

    @property
    def private_pem(self) -> str:
        return self.key.exportKey().decode('ascii')

    @property
    def public_pem(self) -> str:
        return self.key.publickey().exportKey().decode('ascii')
