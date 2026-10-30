"""Generalized Parameter Sweep and Theoretical/Empirical Modeling for Erasure Coding.

Plots:
1. results/plots/generalized_storage_overhead_surface.png:
   Overhead (k+m)/k across continuous values of k (2 to 16) and m (1 to 6).
2. results/plots/generalized_repair_bandwidth_scaling.png:
   Network amplification factor and data downloaded for large files (1 MB, 10 MB, 50 MB, 100 MB).
3. results/plots/generalized_large_file_latency_projection.png:
   Reconstruction latency projected across large file sizes (1 MB to 100 MB) for different codes.
4. results/plots/generalized_pareto_frontier.png:
   Fault tolerance (m) vs Storage Overhead factor for standard industrial codes with clean, collision-free annotations.
"""

from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


def generate_generalized_plots():
    plots_dir = Path("results/plots")
    plots_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.size"] = 10

    # -------------------------------------------------------------
    # 1. Storage Overhead Surface across (k, m)
    # -------------------------------------------------------------
    k_vals = np.arange(2, 17)
    m_vals = [1, 2, 3, 4, 6]

    plt.figure(figsize=(9, 5.5))
    colors = ["#2ca02c", "#1f77b4", "#ff7f0e", "#9467bd", "#d62728"]

    for m, c in zip(m_vals, colors):
        overheads = [(k + m) / k for k in k_vals]
        plt.plot(k_vals, overheads, "o-", label=f"Parity m = {m}", color=c, linewidth=2, markersize=5)

    plt.axhline(3.0, color="#d95f02", linestyle="--", linewidth=2, label="3-Way Replication (3.0x)")
    plt.axhline(2.0, color="#7570b3", linestyle=":", linewidth=1.5, label="2-Way Replication (2.0x)")

    plt.title("Storage Overhead Factor as a Function of Data Shards (k) and Parity Shards (m)", fontsize=12, fontweight="bold", pad=12)
    plt.xlabel("Number of Data Shards (k)", fontsize=11, fontweight="bold")
    plt.ylabel("Storage Overhead Multiplier [(k + m) / k]", fontsize=11, fontweight="bold")
    plt.xticks(k_vals)
    plt.ylim(1.0, 3.5)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(frameon=True, fontsize=9.5, loc="upper right")
    plt.tight_layout()

    p1 = plots_dir / "generalized_storage_overhead_surface.png"
    plt.savefig(p1, dpi=300)
    plt.close()
    print(f"Generated: {p1}")

    # -------------------------------------------------------------
    # 2. Repair Network Bandwidth for Large Files (1MB to 100MB)
    # -------------------------------------------------------------
    file_sizes_mb = np.array([1, 5, 10, 20, 50, 100])
    plt.figure(figsize=(10, 5.5))

    schemes = [
        {"name": "3-Way Replication (Read 1 node)", "factor": 1.0, "style": "s--", "color": "#d95f02"},
        {"name": "RS (4+2) [4 fan-in connections]", "factor": 1.0, "style": "o-", "color": "#1f77b4"},
        {"name": "RS (8+2) [8 fan-in connections]", "factor": 1.0, "style": "^-", "color": "#2ca02c"},
        {"name": "RS (12+4) [12 fan-in connections]", "factor": 1.0, "style": "d-", "color": "#9467bd"},
        {"name": "Azure LRC (12, 2, 2) [Local Repair: 6 nodes]", "factor": 0.5, "style": "v-.", "color": "#e377c2"},
    ]

    for s in schemes:
        transferred = file_sizes_mb * s["factor"]
        plt.plot(file_sizes_mb, transferred, s["style"], label=s["name"], color=s["color"], linewidth=2, markersize=6)

    plt.title("Network Repair Traffic for a Single Node Failure Across Large Files", fontsize=12, fontweight="bold", pad=12)
    plt.xlabel("File Size (MB)", fontsize=11, fontweight="bold")
    plt.ylabel("Data Downloaded to Repair 1 Node (MB)", fontsize=11, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(frameon=True, fontsize=9.5)
    plt.tight_layout()

    p2 = plots_dir / "generalized_repair_bandwidth_scaling.png"
    plt.savefig(p2, dpi=300)
    plt.close()
    print(f"Generated: {p2}")

    # -------------------------------------------------------------
    # 3. Large-File Latency Scaling (Empirical + JIT Model up to 100MB)
    # -------------------------------------------------------------
    large_sizes = np.array([1, 5, 10, 20, 50, 75, 100])
    plt.figure(figsize=(10, 5.5))

    plt.plot(large_sizes, large_sizes * 49.0, "o-", label="RS (4+2) - [~49 ms/MB]", color="#1f77b4", linewidth=2)
    plt.plot(large_sizes, large_sizes * 47.0, "s-", label="RS (8+2) - [~47 ms/MB]", color="#2ca02c", linewidth=2)
    plt.plot(large_sizes, large_sizes * 51.0, "^-", label="RS (8+4) - [~51 ms/MB]", color="#9467bd", linewidth=2)
    plt.plot(large_sizes, large_sizes * 0.05, "x--", label="3-Way Replication - [Direct Copy]", color="#d95f02", linewidth=2)

    plt.title("Reconstruction Latency Scaling for Large Workloads (Up to 100 MB)", fontsize=12, fontweight="bold", pad=12)
    plt.xlabel("Payload Size (MB)", fontsize=11, fontweight="bold")
    plt.ylabel("Reconstruction Latency (ms)", fontsize=11, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(frameon=True, fontsize=10)
    plt.tight_layout()

    p3 = plots_dir / "generalized_large_file_latency_projection.png"
    plt.savefig(p3, dpi=300)
    plt.close()
    print(f"Generated: {p3}")

    # -------------------------------------------------------------
    # 4. Pareto Frontier: Fault Tolerance (m) vs. Storage Overhead (Collision-Free)
    # -------------------------------------------------------------
    plt.figure(figsize=(10, 6.2))

    # Explicit text offsets and arrow styles to eliminate collisions between identical/nearby points:
    # Notice: Backblaze (1.25, 4) vs RS(8+2) (1.25, 2)
    # RS(4+2) (1.50, 2) vs Colossus (1.50, 3) vs RS(8+4) (1.50, 4)
    industrial_codes = [
        {
            "name": "Backblaze: RS (16+4)",
            "overhead": 1.25, "m": 4, "color": "#e377c2",
            "xytext": (-150, 25), "va": "bottom", "ha": "right"
        },
        {
            "name": "RS (8+2) [High Density]",
            "overhead": 1.25, "m": 2, "color": "#2ca02c",
            "xytext": (-140, -25), "va": "top", "ha": "right"
        },
        {
            "name": "Meta f4: RS (10+4)",
            "overhead": 1.40, "m": 4, "color": "#17becf",
            "xytext": (-10, 35), "va": "bottom", "ha": "center"
        },
        {
            "name": "RS (8+4) [High Resilience]",
            "overhead": 1.50, "m": 4, "color": "#9467bd",
            "xytext": (55, 30), "va": "bottom", "ha": "left"
        },
        {
            "name": "Google Colossus: RS (6+3)",
            "overhead": 1.50, "m": 3, "color": "#bcbd22",
            "xytext": (65, 0), "va": "center", "ha": "left"
        },
        {
            "name": "RS (4+2) [Our Prototype]",
            "overhead": 1.50, "m": 2, "color": "#1f77b4",
            "xytext": (55, -28), "va": "top", "ha": "left"
        },
        {
            "name": "Meta f4: RS (14+10)",
            "overhead": 1.71, "m": 10, "color": "#8c564b",
            "xytext": (25, -15), "va": "center", "ha": "left"
        },
        {
            "name": "3-Way Replication",
            "overhead": 3.00, "m": 2, "color": "#d95f02",
            "xytext": (-140, 20), "va": "bottom", "ha": "right"
        },
    ]

    for item in industrial_codes:
        plt.scatter(item["overhead"], item["m"], s=150, color=item["color"], zorder=6, edgecolor="black", linewidth=1.2)
        plt.annotate(
            item["name"],
            xy=(item["overhead"], item["m"]),
            xytext=item["xytext"],
            textcoords="offset points",
            fontsize=9.5,
            fontweight="bold",
            va=item["va"],
            ha=item["ha"],
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=item["color"], lw=1.2, alpha=0.95),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.15", color=item["color"], lw=1.3),
        )

    plt.title("Pareto Trade-off: Fault Tolerance (m) vs. Storage Overhead Factor", fontsize=13, fontweight="bold", pad=14)
    plt.xlabel("Storage Overhead Multiplier [(k + m) / k]", fontsize=11, fontweight="bold")
    plt.ylabel("Fault Tolerance: Simultaneous Node Crashes Tolerated (m)", fontsize=11, fontweight="bold")
    plt.xlim(1.0, 3.3)
    plt.ylim(0.5, 12.0)
    plt.grid(True, linestyle="--", alpha=0.5)

    # Highlight optimal region
    plt.axvspan(1.15, 1.75, color="#2ca02c", alpha=0.08, label="Optimal Industrial Sweet Spot (1.25x - 1.71x)")
    plt.legend(frameon=True, loc="upper right", fontsize=10)
    plt.tight_layout()

    p4 = plots_dir / "generalized_pareto_frontier.png"
    plt.savefig(p4, dpi=300)
    plt.close()
    print(f"Generated clean Pareto plot: {p4}")


if __name__ == "__main__":
    generate_generalized_plots()
