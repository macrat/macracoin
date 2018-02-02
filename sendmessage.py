import sys

import core
import peer


if __name__ == '__main__':
    if len(sys.argv) <= 2:
        print('./sendmessage.py [server address] [message]', file=sys.stderr)
        sys.exit(1)

    user = core.User.generate()
    print('user generated')
    print(user.public_pem)

    message = core.Message(user, 'messaging', sys.argv[2])

    peer.Client().post_message(sys.argv[1], message)

    print('sent message to {}'.format(sys.argv[1]))
    print(message.as_json())
