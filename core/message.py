import base64
import json
import typing

from core.user import User


class Message:
    """ The message of macracoin.

    The Message has sender signature, namespace, and payload.

    >>> u = User.generate()
    >>> m = Message(u, 'my.space', {
    ...     'to': 'hogehoge',
    ...     'from': 'fugafuga',
    ...     'message': 'hello!',
    ... })
    ... 

    >>> m2 = Message.from_json(m.as_json())
    >>> m2.namespace == m.namespace
    True
    >>> m2.payload['to'] == m2.payload['to'] == 'hogehoge'
    True
    >>> m2.payload['from'] == m2.payload['from'] == 'fugafuga'
    True
    >>> m2.payload['message'] == m2.payload['message'] == 'hello!'
    True
    >>> m2.signature == m.signature
    True

    >>> Message(m.user, 'my.space', 'foobar', 'invalid signature')
    Traceback (most recent call last):
        ...
    message.InvalidSignatureError
    """

    def __init__(self,
                 user: User,
                 namespace: str,
                 payload: typing.Any,
                 signature: bytes = None) -> None:

        self.user = user
        self.namespace = namespace
        self.payload = payload

        if signature is None:
            self.signature = user.sign({
                'namespace': namespace,
                'payload': self.payload,
            })
        else:
            self.signature = signature

            if not self.verify():
                raise InvalidSignatureError()

    def verify(self) -> bool:
        """ Verify signature. """

        return self.user.verify({
            'namespace': self.namespace,
            'payload': self.payload,
        }, self.signature)

    def as_dict(self) -> dict:
        """ Convert to dictoinary for serialize. """

        return {
            'user': self.user.public_pem,
            'namespace': self.namespace,
            'payload': self.payload,
            'signature': base64.b64encode(self.signature).decode('ascii'),
        }

    def as_json(self) -> str:
        """ Serialize to json. """

        return json.dumps(self.as_dict())

    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        """ Convert from dictionary for deserialize. """

        return cls(
            User.from_pem(data['user']),
            data['namespace'],
            data['payload'],
            base64.b64decode(data['signature']),
        )

    @classmethod
    def from_json(cls, data: str) -> 'Message':
        """ Deserialize from json. """

        return cls.from_dict(json.loads(data))


class InvalidSignatureError(ValueError):
    pass
