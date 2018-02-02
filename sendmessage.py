import sys

import requests

import core


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('./sendmessage.py [message]', file=sys.stderr)
        sys.exit(1)

    user = core.User.generate()
    print('user generated')
    print(user.public_pem)

    message = core.Message(user, 'messaging', sys.argv[1])
    headers = {
        'Content-Type': 'application/json',
    }

    requests.post('http://localhost:54321/message',
                  data=message.as_json().encode('ascii'),
                  headers=headers)

    print('sent message')
    print(message.as_json())
