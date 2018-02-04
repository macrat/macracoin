import doctest
import unittest

import core.block
import core.chain
import core.errors
import core.message
import core.user
import peer.chainmanager
import peer.client
import peer.endpoint
import peer.peer


class DocTest(unittest.TestCase):
    def test_doctest_core_block(self):
        failure, _ = doctest.testmod(core.block)
        self.assertEqual(failure, 0)

    def test_doctest_core_chain(self):
        failure, _ = doctest.testmod(core.chain)
        self.assertEqual(failure, 0)

    def test_doctest_core_errors(self):
        failure, _ = doctest.testmod(core.errors)
        self.assertEqual(failure, 0)

    def test_doctest_core_message(self):
        failure, _ = doctest.testmod(core.message)
        self.assertEqual(failure, 0)

    def test_doctest_core_user(self):
        failure, _ = doctest.testmod(core.user)
        self.assertEqual(failure, 0)

    def test_doctest_peer_chainmanager(self):
        failure, _ = doctest.testmod(peer.chainmanager)
        self.assertEqual(failure, 0)

    def test_doctest_peer_client(self):
        failure, _ = doctest.testmod(peer.client)
        self.assertEqual(failure, 0)

    def test_doctest_peer_endpoint(self):
        failure, _ = doctest.testmod(peer.endpoint)
        self.assertEqual(failure, 0)

    def test_doctest_peer_peer(self):
        failure, _ = doctest.testmod(peer.peer)
        self.assertEqual(failure, 0)
