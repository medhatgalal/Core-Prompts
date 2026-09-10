"""PUBLIC AUTHOR ANSWER: small semantic gap despite full measured branch coverage."""
import unittest
from sut import can_cancel


class Cancellation(unittest.TestCase):
    def test_owner_cannot_cancel_settled_order(self):
        self.assertFalse(can_cancel(True, "settled"))

    def test_nonowner_cannot_cancel_settled_order(self):
        self.assertFalse(can_cancel(False, "settled"))
