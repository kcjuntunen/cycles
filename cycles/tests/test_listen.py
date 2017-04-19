from unittest import TestCase
from ..listen import *


class TestCreate(TestCase):
    def test_print_devlist(self):
        # nothing comes out unless you're root
        print_devlist()

    def test_devlist(self):
        # empty list unless you're root
        self.assertIsInstance(devlist(), list)

    def test_get_device(self):
        self.assertIn('/dev/input/event', get_device('Barcode Reader '))
