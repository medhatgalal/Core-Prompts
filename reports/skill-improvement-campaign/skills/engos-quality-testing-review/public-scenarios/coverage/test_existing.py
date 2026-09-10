import unittest
from sut import can_cancel


class Existing(unittest.TestCase):
    def test_owner_pending(self):
        self.assertTrue(can_cancel(True, "pending"))

    def test_nonowner_pending(self):
        self.assertFalse(can_cancel(False, "pending"))
