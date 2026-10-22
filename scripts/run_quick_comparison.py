"""Runs a comparative evaluation between Reed-Solomon Erasure Coding, XOR Parity, and 3-Way Replication.

Outputs:
1. Terminal summary table
2. results/quick_comparison.csv
3. results/quick_comparison.md
4. Initial plots in results/plots/
"""

from __future__ import annotations

import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from erasure_storage.codec.rs_codec import CodecType
from erasure_storage.experiment_runner import run_experiment
from erasure_storage.replication.replication_runner import run_replication_experiment


def df_to_markdown(df: pd.DataFrame) -> str:
    headers = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(val) for val in row.values) + " |")
    return "\n".join(lines)


def run_benchmarks():
    results = []
    # Test payloads: 100 KB, 500 KB, 1 MB, 2 MB
    test_sizes = [
        ("100 KB", 100 * 1024),
        ("500 KB", 500 * 1024),
        ("1 MB", 1024 * 1024),
        ("2 MB", 2 * 1024 * 1024),
    ]

    print("Warming up Galois Field JIT engines...")
    from erasure_storage.codec.rs_codec import get_codec
    _warmup_codec = get_codec(CodecType.REED_SOLOMON, 4, 2)
    _w_frags = _warmup_codec.encode_data(b"x" * 1024)
    _warmup_codec.recover_missing(_w_frags[:4], 4, 2, [4, 5])

    print("Running comparative benchmark across storage schemes...")

    for label, size_bytes in test_sizes:
        payload = os.urandom(size_bytes)

        # 1. Reed-Solomon (4+2)
        rs_rep = run_experiment(
            payload=payload,
            data_shards=4,
            parity_shards=2,
            node_count=6,
            failed_nodes=[1],
            codec_type=CodecType.REED_SOLOMON,
        )
        rs_enc = rs_rep["metrics"]["encoding"]
        rs_rec = rs_rep["metrics"]["recovery"]
        results.append({
            "Scheme": "RS (4+2)",
            "File Size": label,
            "Raw Size (KB)": round(size_bytes / 1024, 1),
            "Total Stored (KB)": round(rs_rep["total_stored_bytes"] / 1024, 1),
            "Overhead Ratio": f"{rs_rep['storage_overhead_ratio']:.2f}x",
            "Repair Transfer (KB)": round(rs_rec["bytes_transferred"] / 1024, 1),
            "Encode Time (ms)": round(rs_enc["duration_s"] * 1000, 2),
            "Recovery Time (ms)": round(rs_rec["duration_s"] * 1000, 2),
            "Max Fault Tolerance": "2 Nodes (MDS)",
        })

        # 2. XOR Parity (4+2)
        xor_rep = run_experiment(
            payload=payload,
            data_shards=4,
            parity_shards=2,
            node_count=6,
            failed_nodes=[1],
            codec_type=CodecType.XOR,
        )
        xor_enc = xor_rep["metrics"]["encoding"]
        xor_rec = xor_rep["metrics"]["recovery"]
        results.append({
            "Scheme": "XOR Parity (4+2)",
            "File Size": label,
            "Raw Size (KB)": round(size_bytes / 1024, 1),
            "Total Stored (KB)": round(xor_rep["total_stored_bytes"] / 1024, 1),
            "Overhead Ratio": f"{xor_rep['storage_overhead_ratio']:.2f}x",
            "Repair Transfer (KB)": round(xor_rec["bytes_transferred"] / 1024, 1),
            "Encode Time (ms)": round(xor_enc["duration_s"] * 1000, 2),
            "Recovery Time (ms)": round(xor_rec["duration_s"] * 1000, 2),
            "Max Fault Tolerance": "1 Node (Single Parity)",
        })

        # 3. 3-Way Replication
        rep_rep = run_replication_experiment(
            payload=payload,
            replication_factor=3,
            node_count=6,
            failed_nodes=[1],
        )
        rep_enc = rep_rep["metrics"]["encoding"]
        rep_rec = rep_rep["metrics"]["recovery"]
        results.append({
            "Scheme": "3-Way Replication",
            "File Size": label,
            "Raw Size (KB)": round(size_bytes / 1024, 1),
            "Total Stored (KB)": round(rep_rep["total_stored_bytes"] / 1024, 1),
            "Overhead Ratio": f"{rep_rep['storage_overhead_ratio']:.2f}x",
            "Repair Transfer (KB)": round(rep_rec["bytes_transferred"] / 1024, 1),
            "Encode Time (ms)": round(rep_enc["duration_s"] * 1000, 2),
            "Recovery Time (ms)": round(rep_rec["duration_s"] * 1000, 2),
            "Max Fault Tolerance": "2 Nodes (Replica Copy)",
        })

    df = pd.DataFrame(results)

    # Save CSV
    out_dir = Path("results")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "quick_comparison.csv"
    df.to_csv(csv_path, index=False)

    # Save Markdown table
    md_path = out_dir / "quick_comparison.md"
    md_content = "# Storage Scheme Comparison: Erasure Coding vs Replication\n\n"
    md_content += df_to_markdown(df)
    md_path.write_text(md_content, encoding="utf-8")

    print("\n" + "=" * 105)
    print("EMPIRICAL COMPARISON TABLE (TODAY'S WORKING MODEL)")
    print("=" * 105)
    print(df.to_string(index=False))
    print("=" * 105 + "\n")

    generate_plots(df)


def generate_plots(df: pd.DataFrame):
    plots_dir = Path("results/plots")
    plots_dir.mkdir(parents=True, exist_ok=True)

    # Filter for 1 MB file size for clean comparative bar charts
    df_1mb = df[df["File Size"] == "1 MB"].copy()

    # 1. Storage Overhead Comparison (Bar Chart)
    plt.figure(figsize=(8, 5))
    schemes = list(df_1mb["Scheme"])
    overheads = [1.5, 1.5, 3.0]
    colors = ["#2b5c8f", "#5b8ebf", "#d95f02"]

    bars = plt.bar(schemes, overheads, color=colors, width=0.5)
    plt.ylabel("Storage Overhead Factor (Raw Data Multiplier)", fontsize=11)
    plt.title("Storage Overhead: Erasure Coding vs 3-Way Replication", fontsize=13, fontweight="bold")
    plt.ylim(0, 3.5)
    plt.grid(axis="y", linestyle="--", alpha=0.5)

    for bar, val in zip(bars, overheads):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1, f"{val:.1f}x\n({val*100:.0f}%)", ha="center", fontsize=10, fontweight="bold")

    plt.tight_layout()
    overhead_plot = plots_dir / "storage_overhead_comparison.png"
    plt.savefig(overhead_plot, dpi=200)
    plt.close()
    print(f"Generated: {overhead_plot}")

    # 2. Repair Network Bandwidth Comparison (Bar Chart)
    plt.figure(figsize=(8, 5))
    repair_kb = list(df_1mb["Repair Transfer (KB)"])
    bars2 = plt.bar(schemes, repair_kb, color=["#1b9e77", "#7570b3", "#e7298a"], width=0.5)
    plt.ylabel("Network Data Transferred to Repair 1 Node (KB)", fontsize=11)
    plt.title("Repair Network Bandwidth for 1 MB File", fontsize=13, fontweight="bold")
    plt.grid(axis="y", linestyle="--", alpha=0.5)

    for bar, val in zip(bars2, repair_kb):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 15, f"{val:.0f} KB", ha="center", fontsize=10, fontweight="bold")

    plt.tight_layout()
    repair_plot = plots_dir / "repair_network_bandwidth.png"
    plt.savefig(repair_plot, dpi=200)
    plt.close()
    print(f"Generated: {repair_plot}")

    # 3. Recovery Latency Across File Sizes (Line Chart)
    plt.figure(figsize=(9, 5))
    for scheme, marker, col in [("RS (4+2)", "o-", "#2b5c8f"), ("XOR Parity (4+2)", "s-", "#5b8ebf"), ("3-Way Replication", "^-", "#d95f02")]:
        sub = df[df["Scheme"] == scheme]
        plt.plot(sub["File Size"], sub["Recovery Time (ms)"], marker, label=scheme, color=col, linewidth=2, markersize=7)

    plt.xlabel("File Size", fontsize=11)
    plt.ylabel("Recovery Latency (ms)", fontsize=11)
    plt.title("Recovery Latency Across File Sizes", fontsize=13, fontweight="bold")
    plt.legend(frameon=True)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    latency_plot = plots_dir / "recovery_latency_scaling.png"
    plt.savefig(latency_plot, dpi=200)
    plt.close()
    print(f"Generated: {latency_plot}")


if __name__ == "__main__":
    run_benchmarks()
