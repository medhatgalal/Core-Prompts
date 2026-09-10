"""PUBLIC AUTHOR ANSWER: fixture integrity only; not a model-generated suite."""
import unittest
from sut import read_with_retry


class Stream:
    def __init__(self, value, events):
        self.value = value
        self.events = events
        self.closes = 0

    def read(self):
        self.events.append("read")
        if isinstance(self.value, Exception):
            raise self.value
        return self.value

    def close(self):
        self.closes += 1
        self.events.append("close")


class RetryContract(unittest.TestCase):
    def test_success_closes_including_empty_bytes(self):
        for value in (b"ok", b""):
            events = []
            stream = Stream(value, events)
            self.assertEqual(read_with_retry(lambda: stream), value)
            self.assertEqual(stream.closes, 1)
            self.assertEqual(events, ["read", "close"])

    def test_failed_read_closes_before_retry(self):
        events = []
        streams = [Stream(OSError("first"), events), Stream(b"ok", events)]
        pending = iter(streams)

        def factory():
            events.append("open")
            return next(pending)

        self.assertEqual(read_with_retry(factory), b"ok")
        self.assertEqual(events, ["open", "read", "close", "open", "read", "close"])
        self.assertEqual([s.closes for s in streams], [1, 1])

    def test_open_failure_then_success(self):
        calls = []
        stream = Stream(b"recovered", [])

        def factory():
            calls.append(1)
            if len(calls) == 1:
                raise OSError("open failed")
            return stream

        self.assertEqual(read_with_retry(factory, 2), b"recovered")
        self.assertEqual(len(calls), 2)
        self.assertEqual(stream.closes, 1)

    def test_non_oserror_from_open_is_not_retried(self):
        calls = []
        error = RuntimeError("configuration")

        def factory():
            calls.append(1)
            raise error

        with self.assertRaises(RuntimeError) as caught:
            read_with_retry(factory, 3)
        self.assertIs(caught.exception, error)
        self.assertEqual(len(calls), 1)

    def test_exhaustion_reraises_last_open_error_at_limit(self):
        errors = [OSError("first"), OSError("last")]
        calls = []

        def factory():
            calls.append(1)
            raise errors[min(len(calls) - 1, 1)]

        with self.assertRaises(OSError) as caught:
            read_with_retry(factory, 2)
        self.assertIs(caught.exception, errors[-1])
        self.assertEqual(len(calls), 2)

    def test_non_oserror_propagates_without_retry_and_closes(self):
        error = RuntimeError("do not retry")
        stream = Stream(error, [])
        calls = []

        def factory():
            calls.append(1)
            return stream

        with self.assertRaises(RuntimeError) as caught:
            read_with_retry(factory, 3)
        self.assertIs(caught.exception, error)
        self.assertEqual(len(calls), 1)
        self.assertEqual(stream.closes, 1)

    def test_invalid_budget_never_opens(self):
        calls = []
        for attempts in (0, -1):
            with self.assertRaises(ValueError):
                read_with_retry(lambda: calls.append(1), attempts)
        self.assertEqual(calls, [])

    def test_last_read_failure_closes_and_next_call_recovers(self):
        stream = Stream(OSError("failed"), [])
        with self.assertRaises(OSError):
            read_with_retry(lambda: stream, 1)
        self.assertEqual(stream.closes, 1)
        good = Stream(b"recovered", [])
        self.assertEqual(read_with_retry(lambda: good, 1), b"recovered")
        self.assertEqual(good.closes, 1)
