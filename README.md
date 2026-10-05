# Erasure Coding for Fault-Tolerant Distributed Storage

This project implements a small, research-oriented prototype for erasure-coded storage across simulated nodes. The goal is to demonstrate file ingestion, fragment encoding, failure simulation, recovery, and metric collection while keeping the implementation compact and reproducible.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]
pytest -q
```

## Run a local experiment

```bash
mkdir data
python -c "open('data/test.bin', 'wb').write(b'A sample file for erasure-coded recovery and checksum verification.')"
python -m erasure_storage.cli --input data/test.bin --output-dir runs --failed-nodes 2 5
```

This writes a JSON report and a Markdown summary to `runs/`.

## Research focus

The core research comparison is between replication and erasure coding, emphasizing:

- storage overhead;
- recovery time;
- bytes transferred during repair;
- fault tolerance under node loss.

## Project layout

- `src/erasure_storage/` — implementation modules
- `tests/` — regression tests
- `configs/` — experiment configuration
- `runs/` — experiment outputs

## MVP flow

1. ingest file
2. hash the file
3. split into data shards
4. generate parity shards
5. place fragments across nodes
6. simulate node failures
7. recover missing fragments
8. reconstruct original file and verify checksum

## Notes

This is intentionally a local prototype; it does not attempt a production distributed filesystem.
