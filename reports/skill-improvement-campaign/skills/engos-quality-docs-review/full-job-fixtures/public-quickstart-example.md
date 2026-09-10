# First event report

Use Python 3.11 or newer. From the repository root, initialize a new local workspace:

```sh
python3 cli.py init --workspace demo
```

Expected output: `Workspace ready`.

Summarize the supplied sample:

```sh
python3 cli.py summarize --workspace demo --input samples/events.csv
```

Expected output: `events=3`. If the tool reports an uninitialized workspace, run the init command for the same workspace path.

See [reference](REFERENCE.md) for flags and [team preferences](LOCAL.md) for custom workspace choices.
