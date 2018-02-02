import json
import typing

from core.block import Block, BlockNotClosedError
from core.user import User


class Chain(typing.Iterable[Block], typing.Sized):
    """ The block chain.


    >>> user = User.generate()

    >>> chain = Chain.generate(user, magicnumber='000')

    >>> from block import mining
    >>> len(chain)
    2
    >>> chain.join(chain[-1].close(user, mining(chain[-1])))
    >>> len(chain)
    3
    """

    def __init__(self, chain: typing.List[Block]) -> None:
        self._chain = chain

        if not self.verify():
            raise InvalidChainError()

    @classmethod
    def generate(cls, user: User, magicnumber: str = None) -> 'Chain':
        """ Generate new chain.


        New chain has 2 block; first element is closed, and second element is
        not closed.

        >>> chain = Chain.generate(User.generate())

        >>> len(chain)
        2

        >>> chain[0].is_closed()
        True
        >>> chain[1].is_closed()
        False

        >>> chain[0].verify()
        True
        """

        root = Block.make_root(user, magicnumber)
        return cls([root, Block(root)])

    def __len__(self) -> int:
        return len(self._chain)

    @typing.overload
    def __getitem__(self, idx: int) -> Block:
        ...

    @typing.overload
    def __getitem__(self, idx: slice) -> typing.Iterable[Block]:
        ...

    def __getitem__(self, idx: typing.Union[int, slice]) \
             -> typing.Union[Block, typing.Iterable[Block]]:

        return self._chain[idx]

    def __iter__(self) -> typing.Iterator[Block]:
        return iter(self._chain)

    def __in__(self, block: Block) -> bool:
        return any(x.signature == block.signature for x in self)

    def verify(self) -> bool:
        """ Verify chain and all elements. """

        if (len(self._chain) == 0
            or not self[0].is_root()
            or not self[0].verify()):

            return False

        if len(self._chain) == 1:
            return True

        parent = self[0]

        for block in self[1:-1]:
            if (block.is_root()
                or block.parent.signature != parent.signature
                or block.index != parent.index + 1):

                return False

            try:
                if not block.verify():
                    return False
            except BlockNotClosedError:
                return False

            parent = block

        if (self[-1].is_root()
            or self[-1].parent.signature != self[-2].signature
            or self[-1].index != self[-2].index + 1):

            return False

        try:
            return self[-1].verify()
        except BlockNotClosedError:
            return True

    def join(self, block: Block) -> None:
        """ Join new block. """

        if (block.is_root() or (block.is_closed() and not block.verify())):
            raise InvalidChainError()

        leaf = self[-1]

        if (leaf.is_closed()
            and leaf.signature == block.parent.signature
            and leaf.index + 1 == block.index):

            self._chain.append(block)
        elif (block.is_closed()
              and not leaf.is_closed()
              and block.index == leaf.index):

            self._chain.insert(-1, block)
            self[-1].parent = block
            self[-1].index += 1
        else:
            raise InvalidChainError()

        if not self.verify():
            raise InvalidChainError()

    def as_dict(self) -> typing.Tuple[dict, ...]:
        """ Convert to dictoinary for serialize. """

        return tuple(block.as_dict() for block in self)

    def as_json(self) -> str:
        """ Serialize to json. """

        return json.dumps(self.as_dict())

    @classmethod
    def from_dict(cls, data: typing.Tuple[dict]) -> 'Chain':
        """ Convert from dictoinary for deserialize. """

        return cls([Block.from_dict(b) for b in data])

    @classmethod
    def from_json(cls, data: str) -> 'Chain':
        """ Deserialize from json. """

        return cls.from_dict(json.loads(data))


class InvalidChainError(ValueError):
    pass
