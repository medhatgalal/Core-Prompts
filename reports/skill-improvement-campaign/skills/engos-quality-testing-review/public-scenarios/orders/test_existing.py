import tempfile
from pathlib import Path
import unittest
from sut import initialize, create_order


class Existing(unittest.TestCase):
    def test_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "orders.db"
            initialize(path)
            self.assertEqual(create_order(path, "one", 100), {"key": "one", "cents": 100})
