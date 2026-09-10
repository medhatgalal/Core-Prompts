"""PUBLIC AUTHOR ANSWER, not an experimental model output."""
import sqlite3
import tempfile
from pathlib import Path
import unittest
from sut import initialize, create_order


class Orders(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "orders.db"
        initialize(self.path)

    def rows(self):
        connection = sqlite3.connect(self.path)
        try:
            return connection.execute("SELECT key, cents FROM orders ORDER BY key").fetchall()
        finally:
            connection.close()

    def test_response_corresponds_to_persisted_row(self):
        create_order(self.path, "one", 100)
        self.assertEqual(self.rows(), [("one", 100)])

    def test_retry_is_idempotent_and_conflict_preserves_state(self):
        create_order(self.path, "one", 100)
        create_order(self.path, "one", 100)
        with self.assertRaises(ValueError):
            create_order(self.path, "one", 200)
        self.assertEqual(self.rows(), [("one", 100)])
        create_order(self.path, "two", 200)
        self.assertEqual(self.rows(), [("one", 100), ("two", 200)])

    def test_invalid_amount_does_not_insert(self):
        for cents in (0, -1):
            with self.assertRaises(ValueError):
                create_order(self.path, "bad", cents)
        self.assertEqual(self.rows(), [])
