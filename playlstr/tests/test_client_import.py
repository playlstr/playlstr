from django.test import TestCase
import playlstr.models
import random
import string

from playlstr.util.client import *

NUM_CODES_GENERATED = 1000


class ClientLinkTestCase(TestCase):
    user = None

    def setUp(self):
        # Create a user
        if self.user:
            self.user.delete()
        self.user = playlstr.models.PlaylstrUser.objects.create()

    def test_link_code_quality(self):
        codes = [self.user.get_link_code() for i in range(NUM_CODES_GENERATED)]
        codes.sort()
        last_c = None
        expected_len = len(codes[0])
        for c in codes:
            self.assertNotEqual(
                c,
                last_c,
                "Duplicate code generated out of {} - probabilistically this shouldn't happen".format(
                    NUM_CODES_GENERATED
                ),
            )
            if len(c) != expected_len:
                self.assertEqual(expected_len, len(c), "Differing code lengths")
            last_c = c

    def test_linking_client_invalid(self):
        client_id = "".join(
            random.choice(string.ascii_lowercase + string.digits) for i in range(20)
        )
        # Invalid link code
        with self.assertRaises(ValueError):
            link_client_code("123456", client_id)
        # Invalid client id
        with self.assertRaises(ValueError):
            link_client_code(self.user.get_link_code(), "asdf")

    def test_linking_client(self):
        link_code = self.user.get_link_code()
        client_id = "".join(
            random.choice(string.ascii_lowercase + string.digits) for i in range(20)
        )
        link_client_code(link_code, client_id)
        self.user.refresh_from_db()
        self.assertIn(
            client_id, self.user.linked_clients, "Link valid client id and link code"
        )
