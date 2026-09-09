"""Public safe control: helper plus while loop with no shared state."""


def _read(factory):
    resource = factory()
    try:
        return resource.read()
    finally:
        resource.close()


def read_with_retry(open_stream, attempts=2):
    if attempts <= 0:
        raise ValueError("at least one attempt required")
    remaining = attempts
    while remaining:
        remaining -= 1
        try:
            return _read(open_stream)
        except OSError:
            if remaining == 0:
                raise
