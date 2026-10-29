"""Generates final publication-quality figures from results/summary.csv.

Outputs:
1. results/plots/storage_overhead_by_scheme.png
2. results/plots/recovery_latency_scaling_20mb.png
3. results/plots/degraded_read_amplification.png
4. results/plots/fault_tolerance_matrix.png
"""

from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def generate_all_plots(csv_path: str = "results/summary.csv"):
    df = pd.read_csv(csv_path)
    plots_dir = Path("results/plots")
    plots_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.size"] = 10

    # -------------------------------------------------------------
    # Plot 1: Storage Overhead Comparison
    # -------------------------------------------------------------
    plt.figure(figsize=(9, 5))
    schemes = ["RS (8+2)", "RS (4+2)", "RS (8+4)", "XOR (4+2)", "3-Way Replication"]
    overheads = [1.25, 1.50, 1.50, 1.50, 3.00]
    colors = ["#1b9e77", "#2b5c8f", "#7570b3", "#386cb0", "#d95f02"]

    bars = plt.bar(schemes, overheads, color=colors, width=0.55, edgecolor="black", linewidth=0.8)
    plt.ylabel("Storage Overhead Multiplier (Total / Raw)", fontsize=11, fontweight="bold")
    plt.title("Storage Capacity Overhead: Erasure Coding vs Replication", fontsize=13, fontweight="bold", pad=12)
    plt.ylim(0, 3.6)
    plt.grid(axis="y", linestyle="--", alpha=0.5)

    for bar, val in zip(bars, overheads):
        savings = f"{(1 - (val/3.0))*100:.0f}% savings" if val < 3.0 else "Baseline"
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.1,
            f"{val:.2f}x\n({savings})",
            ha="center",
            fontsize=9.5,
            fontweight="bold",
        )

    plt.tight_layout()
    p1 = plots_dir / "storage_overhead_by_scheme.png"
    plt.savefig(p1, dpi=300)
    plt.close()
    print(f"Generated: {p1}")

    # -------------------------------------------------------------
    # Plot 2: Recovery Latency Scaling up to 20 MB (1 Failure)
    # -------------------------------------------------------------
    plt.figure(figsize=(10, 5.5))
    df_f1 = df[df["Failures Tested"] == 1]
    palette = {
        "RS (4+2)": ("#2b5c8f", "o-"),
        "RS (8+2)": ("#1b9e77", "s-"),
        "RS (8+4)": ("#7570b3", "^-"),
        "XOR (4+2)": ("#e6ab02", "d-"),
        "3-Way Replication": ("#d95f02", "x--"),
    }

    for scheme, (color, style) in palette.items():
        sub = df_f1[df_f1["Scheme"] == scheme].sort_values("Size (MB)")
        plt.plot(
            sub["Size (MB)"],
            sub["Recovery Time (ms)"],
            style,
            label=scheme,
            color=color,
            linewidth=2,
            markersize=6,
        )

    plt.xlabel("Payload Size (MB)", fontsize=11, fontweight="bold")
    plt.ylabel("Recovery Latency (ms)", fontsize=11, fontweight="bold")
    plt.title("Degraded Read & Recovery Latency Scaling (Up to 20 MB)", fontsize=13, fontweight="bold", pad=12)
    plt.legend(frameon=True, fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    p2 = plots_dir / "recovery_latency_scaling_20mb.png"
    plt.savefig(p2, dpi=300)
    plt.close()
    print(f"Generated: {p2}")

    # -------------------------------------------------------------
    # Plot 3: Network Repair Bandwidth Amplification (20 MB File)
    # -------------------------------------------------------------
    plt.figure(figsize=(9, 5))
    df_20m = df[(df["File Size"] == "20 MB") & (df["Failures Tested"] == 1)]
    schemes_20m = ["3-Way Replication", "RS (4+2)", "RS (8+2)", "RS (8+4)"]
    bw_vals = []
    for s in schemes_20m:
        match = df_20m[df_20m["Scheme"] == s]
        bw_vals.append(match["Repair Bandwidth (MB)"].values[0] if len(match) > 0 else 0)

    bars3 = plt.bar(
        schemes_20m,
        bw_vals,
        color=["#d95f02", "#2b5c8f", "#1b9e77", "#7570b3"],
        width=0.55,
        edgecolor="black",
        linewidth=0.8,
    )
    plt.ylabel("Data Downloaded Across Network to Repair 1 Node (MB)", fontsize=11, fontweight="bold")
    plt.title("Degraded Read Network Amplification (20 MB Payload)", fontsize=13, fontweight="bold", pad=12)
    plt.grid(axis="y", linestyle="--", alpha=0.5)

    for bar, val in zip(bars3, bw_vals):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.4,
            f"{val:.1f} MB",
            ha="center",
            fontsize=10,
            fontweight="bold",
        )

    plt.tight_layout()
    p3 = plots_dir / "degraded_read_amplification.png"
    plt.savefig(p3, dpi=300)
    plt.close()
    print(f"Generated: {p3}")

    # -------------------------------------------------------------
    # Plot 4: Fault Tolerance Matrix (Success Rate Heatmap)
    # -------------------------------------------------------------
    plt.figure(figsize=(8, 4.5))
    schemes_ft = ["3-Way Replication", "RS (4+2)", "RS (8+2)", "RS (8+4)", "XOR (4+2)"]
    failures = [0, 1, 2]

    # Matrix: rows = schemes, cols = failures (0, 1, 2)
    matrix = np.zeros((len(schemes_ft), len(failures)))
    for r, s in enumerate(schemes_ft):
        for c, f in enumerate(failures):
            sub = df[(df["Scheme"] == s) & (df["Failures Tested"] == f)]
            success_rate = (sub["Recovery Success"].sum() / len(sub)) * 100 if len(sub) > 0 else 0
            matrix[r, c] = success_rate

    im = plt.imshow(matrix, cmap="RdYlGn", vmin=0, vmax=100, aspect="auto")
    plt.xticks(ticks=range(len(failures)), labels=["0 Failures", "1 Failure", "2 Failures"], fontsize=10, fontweight="bold")
    plt.yticks(ticks=range(len(schemes_ft)), labels=schemes_ft, fontsize=10, fontweight="bold")
    plt.title("Fault Tolerance Verification Matrix (% Recovery Success)", fontsize=13, fontweight="bold", pad=12)

    for r in range(len(schemes_ft)):
        for c in range(len(failures)):
            val = matrix[r, c]
            status = "PASS (100%)" if val == 100 else f"FAIL ({val:.0f}%)"
            color = "black" if val > 50 else "white"
            plt.text(c, r, status, ha="center", va="center", fontsize=10, fontweight="bold", color=color)

    cbar = plt.colorbar(im)
    cbar.set_label("Recovery Success Rate (%)", fontsize=10, fontweight="bold")

    plt.tight_layout()
    p4 = plots_dir / "fault_tolerance_matrix.png"
    plt.savefig(p4, dpi=300)
    plt.close()
    print(f"Generated: {p4}")


if __name__ == "__main__":
    generate_all_plots()
