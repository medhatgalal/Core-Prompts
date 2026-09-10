# Public integration contract

`initialize(path)` creates a new local SQLite store. `create_order(path, key, cents)`
returns key and cents after durable commit. A retry with the same key and cents
returns that order without a second row; the same key with a different amount
raises ValueError and leaves the old row unchanged. Nonpositive cents raises
ValueError without inserting. Inputs are caller-provided nonempty keys and integer
cents. No external payment service, concurrent-call behavior or network contract
is promised. A new connection must observe successful effects after the call ends.

The repository uses Python 3.11+ `unittest`, SQLite and temporary local files.
Existing coverage only checks the returned response. Generate requested test files
in `tests/test_orders.py`; report them as unrun and provide the command. An input
packet may flatten these fixture files into a miniature repo with `sut.py` and
`tests/test_existing.py`; preserve that declared layout.
