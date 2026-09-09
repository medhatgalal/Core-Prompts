"""PUBLIC AUTHOR ANSWER: fixture integrity only; not a model-generated suite."""
import unittest
from sut import LeaseBook


class LeaseContract(unittest.TestCase):
    def test_exact_expiry(self):
        book = LeaseBook()
        self.assertTrue(book.acquire("job", "alice", 10, 5))
        self.assertFalse(book.acquire("job", "bob", 14.5, 5))
        self.assertTrue(book.acquire("job", "bob", 15, 5))

    def test_failed_acquire_preserves_owner_and_expiry(self):
        book = LeaseBook()
        book.acquire("job", "alice", 0, 10)
        self.assertFalse(book.acquire("job", "bob", 1, 100))
        self.assertFalse(book.release("job", "bob"))
        self.assertFalse(book.acquire("job", "alice", 2, 100))
        self.assertTrue(book.acquire("job", "bob", 10, 1))

    def test_release_requires_owner_and_is_idempotent(self):
        book = LeaseBook()
        book.acquire("job", "alice", 0, 10)
        self.assertFalse(book.release("job", "bob"))
        self.assertTrue(book.release("job", "alice"))
        self.assertFalse(book.release("job", "alice"))

    def test_recorded_owner_can_release_after_expiry(self):
        book = LeaseBook()
        book.acquire("job", "alice", 0, 1)
        self.assertFalse(book.renew("job", "alice", 100, 1))
        self.assertTrue(book.release("job", "alice"))

    def test_renew_live_and_expired(self):
        book = LeaseBook()
        self.assertFalse(book.renew("job", "alice", 0, 5))
        book.acquire("job", "alice", 0, 5)
        self.assertFalse(book.renew("job", "bob", 1, 100))
        self.assertTrue(book.renew("job", "alice", 4, 2))
        self.assertFalse(book.acquire("job", "bob", 5, 5))
        self.assertFalse(book.renew("job", "alice", 6, 50))
        self.assertTrue(book.acquire("job", "bob", 6, 5))

    def test_invalid_duration_does_not_change_state(self):
        book = LeaseBook()
        book.acquire("job", "alice", 0, 10)
        for ttl in (0, -1):
            with self.subTest(ttl=ttl):
                with self.assertRaises(ValueError):
                    book.acquire("job", "bob", 1, ttl)
                with self.assertRaises(ValueError):
                    book.renew("job", "alice", 1, ttl)
                with self.assertRaises(ValueError):
                    book.renew("job", "bob", 1, ttl)
                with self.assertRaises(ValueError):
                    book.renew("absent", "bob", 1, ttl)
        self.assertFalse(book.acquire("job", "bob", 9, 2))
        self.assertTrue(book.acquire("job", "bob", 10, 2))

    def test_keys_and_instances_are_independent(self):
        book = LeaseBook()
        book.acquire("one", "alice", 0, 10)
        self.assertTrue(book.acquire("two", "bob", 0, 10))
        self.assertTrue(LeaseBook().acquire("one", "bob", 0, 10))
