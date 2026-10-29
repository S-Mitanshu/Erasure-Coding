"""Full Scale-Out Experiment Sweep (100 KB to 20 MB)

Evaluates:
- RS (4+2), RS (8+2), RS (8+4)
- XOR (4+2)
- 3-Way Replication
Across failure counts (0, 1, 2) and file sizes (100 KB, 500 KB, 1 MB, 5 MB, 10 MB, 20 MB).

Outputs:
- results/summary.csv
- results/summary.md
"""

from __future__ import annotations

import os
from pathlib import Path
import pandas as pd

from erasure_storage.codec.rs_codec import CodecType, get_codec
from erasure_storage.experiment_runner import run_experiment
from erasure_storage.replication.replication_runner import run_replication_experiment


def df_to_markdown(df: pd.DataFrame) -> str:
    headers = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(val) for val in row.values) + " |")
    return "\n".join(lines)


def run_full_sweep():
    # Warmup Galois Field JIT compiler
    print("Warming up Galois Field JIT compiler...")
    for (k, m) in [(4, 2), (8, 2), (8, 4)]:
        codec = get_codec(CodecType.REED_SOLOMON, k, m)
        _frags = codec.encode_data(b"x" * 1024)
        codec.recover_missing(_frags[:k], k, m, list(range(k, k + m)))

    test_sizes = [
        ("100 KB", 100 * 1024),
        ("500 KB", 500 * 1024),
        ("1 MB", 1024 * 1024),
        ("5 MB", 5 * 1024 * 1024),
        ("10 MB", 10 * 1024 * 1024),
        ("20 MB", 20 * 1024 * 1024),
    ]

    ec_configs = [
        {"name": "RS (4+2)", "type": CodecType.REED_SOLOMON, "k": 4, "m": 2, "nodes": 6},
        {"name": "RS (8+2)", "type": CodecType.REED_SOLOMON, "k": 8, "m": 2, "nodes": 10},
        {"name": "RS (8+4)", "type": CodecType.REED_SOLOMON, "k": 8, "m": 4, "nodes": 12},
        {"name": "XOR (4+2)", "type": CodecType.XOR, "k": 4, "m": 2, "nodes": 6},
    ]

    results = []
    print("Starting Scale-Out Experiments Sweep (100 KB to 20 MB)...")

    for label, size_bytes in test_sizes:
        size_mb = size_bytes / (1024 * 1024)
        print(f"--> Benchmarking payload: {label} ({size_mb:.2f} MB)...")
        payload = os.urandom(size_bytes)

        # 1. EC Configurations
        for cfg in ec_configs:
            k, m, nodes = cfg["k"], cfg["m"], cfg["nodes"]
            # Test failure scenarios: 0, 1, 2 failures
            for fail_count in [0, 1, 2]:
                # If XOR and 2 failures, XOR cannot recover if data shards fail
                # But let's test node failures: [1] for 1, [1, 2] for 2
                failed = list(range(1, fail_count + 1)) if fail_count > 0 else []

                try:
                    rep = run_experiment(
                        payload=payload,
                        data_shards=k,
                        parity_shards=m,
                        node_count=nodes,
                        failed_nodes=failed,
                        codec_type=cfg["type"],
                    )
                    enc_m = rep["metrics"]["encoding"]
                    rec_m = rep["metrics"]["recovery"]
                    success = rep["recovery_success"]
                    repair_bytes = rec_m.get("bytes_transferred", 0)
                    rec_time = rec_m.get("duration_s", 0) * 1000
                    mem_peak = rec_m.get("memory_peak_mb", 0)
                except Exception:
                    enc_m = {"duration_s": 0}
                    repair_bytes = 0
                    rec_time = 0
                    mem_peak = 0
                    success = False

                results.append({
                    "Scheme": cfg["name"],
                    "File Size": label,
                    "Size (MB)": round(size_mb, 2),
                    "Data Shards (k)": k,
                    "Parity Shards (m)": m,
                    "Storage Nodes": nodes,
                    "Failures Tested": fail_count,
                    "Total Stored (MB)": round((size_bytes * (k + m) / k) / (1024 * 1024), 2),
                    "Overhead Ratio": f"{(k + m) / k:.2f}x",
                    "Repair Bandwidth (MB)": round(repair_bytes / (1024 * 1024), 2),
                    "Encode Time (ms)": round(enc_m.get("duration_s", 0) * 1000, 2),
                    "Recovery Time (ms)": round(rec_time, 2),
                    "Peak Memory (MB)": round(mem_peak, 2),
                    "Recovery Success": success,
                })

        # 2. 3-Way Replication
        for fail_count in [0, 1, 2]:
            failed = list(range(1, fail_count + 1)) if fail_count > 0 else []
            rep = run_replication_experiment(
                payload=payload,
                replication_factor=3,
                node_count=6,
                failed_nodes=failed,
            )
            enc_m = rep["metrics"]["encoding"]
            rec_m = rep["metrics"]["recovery"]

            results.append({
                "Scheme": "3-Way Replication",
                "File Size": label,
                "Size (MB)": round(size_mb, 2),
                "Data Shards (k)": 1,
                "Parity Shards (m)": 2,
                "Storage Nodes": 6,
                "Failures Tested": fail_count,
                "Total Stored (MB)": round((size_bytes * 3) / (1024 * 1024), 2),
                "Overhead Ratio": "3.00x",
                "Repair Bandwidth (MB)": round(rec_m.get("bytes_transferred", 0) / (1024 * 1024), 2),
                "Encode Time (ms)": round(enc_m.get("duration_s", 0) * 1000, 2),
                "Recovery Time (ms)": round(rec_m.get("duration_s", 0) * 1000, 2),
                "Peak Memory (MB)": round(rec_m.get("memory_peak_mb", 0), 2),
                "Recovery Success": rep["recovery_success"],
            })

    df = pd.DataFrame(results)

    out_dir = Path("results")
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "summary.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved dataset: {csv_path}")

    md_path = out_dir / "summary.md"
    md_content = "# Full Scale-Out Controlled Experiment Summary\n\n"
    md_content += f"**Total Experiment Runs**: {len(df)}\n\n"
    md_content += df_to_markdown(df)
    md_path.write_text(md_content, encoding="utf-8")
    print(f"Saved summary: {md_path}")

    print("\nScale-out experiment sweep completed successfully!")
    return df


if __name__ == "__main__":
    run_full_sweep()
