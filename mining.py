import sys

import core
import peer


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('$ mining.py [server address]', file=sys.stderr)
        sys.exit(1)

    user = core.User.generate()
    print('user generated')
    print(user.public_pem)

    client = peer.Client()

    while True:
        leaf = client.get_block(sys.argv[1], -1)

        print('leaf got: index={} parent-signature={}'.format(
            leaf.index,
            leaf.parent.signature.hex(),
        ))

        while True:
            key = core.mining(leaf)
            print('found key: {}'.format(key.hex()))

            next_ = leaf.close(user, key)

            client.post_close_block(sys.argv[1], leaf)

            print('yeah!  index={} signature={}'.format(
                leaf.index,
                leaf.signature.hex(),
            ))

            leaf = next_
