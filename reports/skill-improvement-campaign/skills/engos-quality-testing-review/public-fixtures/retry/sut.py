"""Public reference: bounded retries with stream cleanup."""


def read_with_retry(open_stream, attempts=2):
    if attempts < 1:
        raise ValueError("attempts must be positive")
    for attempt in range(attempts):
        stream = None
        try:
            stream = open_stream()
            return stream.read()
        except OSError:
            if attempt == attempts - 1:
                raise
        finally:
            if stream is not None:
                stream.close()
