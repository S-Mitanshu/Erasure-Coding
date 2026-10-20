from __future__ import annotations

import argparse
from pathlib import Path

from erasure_storage.experiment_runner import run_experiment


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a small erasure-coded storage experiment.")
    parser.add_argument("--input", type=str, required=True, help="Path to the file to store and recover.")
    parser.add_argument("--output-dir", type=str, default="runs", help="Directory for JSON and Markdown reports.")
    parser.add_argument("--codec", type=str, choices=["reed_solomon", "xor"], default="reed_solomon", help="Codec algorithm to use.")
    parser.add_argument("--data-shards", type=int, default=4)
    parser.add_argument("--parity-shards", type=int, default=2)
    parser.add_argument("--node-count", type=int, default=6)
    parser.add_argument("--failed-nodes", type=int, nargs="*", default=[2, 5], help="Node IDs to mark unavailable.")
    args = parser.parse_args()

    input_path = Path(args.input)
    payload = input_path.read_bytes()
    report = run_experiment(
        payload,
        data_shards=args.data_shards,
        parity_shards=args.parity_shards,
        node_count=args.node_count,
        failed_nodes=args.failed_nodes,
        output_dir=args.output_dir,
        codec_type=args.codec,
    )

    print(f"codec={report['codec']}")
    print(f"recovery_success={report['recovery_success']}")
    print(f"file_id={report['file_id']}")
    print(f"recovered_hash={report['recovered_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
