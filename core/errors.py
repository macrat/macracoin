class BlockAlreadyClosedError(Exception):
    pass


class BlockNotClosedError(Exception):
    pass


class InvalidChainError(ValueError):
    pass


class InvalidKeyError(ValueError):
    pass


class InvalidSignatureError(ValueError):
    pass


class NoPrivateKeyError(ValueError):
    pass
