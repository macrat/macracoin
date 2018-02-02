import json
import base64

import requests

import core


if __name__ == '__main__':
    user = core.User.generate()
    print('user generated')
    print(user.public_pem)

    while True:
        resp = requests.get('http://localhost:54321/block/-1')
        leaf = core.Block.from_json(resp.text)

        print('leaf got: index={} parent-signature={}'.format(
            leaf.index,
            leaf.parent.signature.hex(),
        ))

        while True:
            key = core.mining(leaf)
            print('found key: {}'.format(key.hex()))

            next_ = leaf.close(user, key)

            data = json.dumps({
                'user': user.public_pem,
                'key': base64.b64encode(key).decode('ascii'),
                'timestamp': leaf.timestamp,
                'signature': base64.b64encode(leaf.signature).decode('ascii'),
            }).encode('ascii')
            header = {'Content-Type': 'application/json'}

            requests.post('http://localhost:54321/block',
                          data=data,
                          headers=header)

            print('yeah!  index={} signature={}'.format(
                leaf.index,
                leaf.signature.hex(),
            ))

            leaf = next_
