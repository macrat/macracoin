import sys
import random

import core
import peer


port = random.randint(50000, 60000)
addr = 'http://localhost:{}'.format(port)


if len(sys.argv) > 1:
    app = peer.Peer.clone(addr, sys.argv[1])
    for remote in sys.argv[1:]:
        app.connect(remote)
else:
    rootuser = core.User.generate()
    print('user generated')
    print(rootuser.public_pem)
    print()
    app = peer.Peer.generate(addr, rootuser)


if __name__ == '__main__':
    app.run(port=port)
