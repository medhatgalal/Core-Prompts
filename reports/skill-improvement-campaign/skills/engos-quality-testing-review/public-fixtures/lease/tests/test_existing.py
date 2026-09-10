import unittest
from sut import LeaseBook


class Existing(unittest.TestCase):
    def test_basic_acquire_release(self):
        book = LeaseBook()
        self.assertTrue(book.acquire("job", "alice", 0, 10))
        self.assertTrue(book.release("job", "alice"))
