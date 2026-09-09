import unittest
from sut import read_with_retry


class Stream:
    def read(self):
        return b"ok"

    def close(self):
        pass


class Existing(unittest.TestCase):
    def test_reads_bytes(self):
        self.assertEqual(read_with_retry(Stream), b"ok")
