# Empirical Findings: Erasure Coding vs. Replication Benchmark

This document details the experimental findings gathered from the 90-run scale-out benchmark sweep across **100 KB, 500 KB, 1 MB, 5 MB, 10 MB, and 20 MB** payloads under varying failure modes.

---

## 1. Primary Empirical Findings

### 1.1 Storage Capacity Efficiency
- **3-Way Replication**: Requires a flat **$3.00\times$ storage overhead**. Storing a 20 MB payload consumes **60.0 MB** across the cluster.
- **Reed-Solomon (4+2)**: Delivers a **$1.50\times$ storage overhead**. Storing a 20 MB payload consumes **30.0 MB** — an exact **50% raw storage space savings** while matching the same 2-node failure tolerance.
- **Reed-Solomon (8+2)**: Reduces storage overhead to **$1.25\times$** (25% extra storage). Storing a 20 MB payload consumes only **25.0 MB** — a **58.3% storage reduction** relative to replication.

| Scheme | Raw Payload | Total Stored on Cluster | Overhead Multiplier | Capacity Savings vs. 3x Replication |
| :--- | :--- | :--- | :--- | :--- |
| **3-Way Replication** | 20.0 MB | 60.0 MB | $3.00\times$ | 0% (Baseline) |
| **Reed-Solomon (4+2)** | 20.0 MB | 30.0 MB | $1.50\times$ | **50.0%** |
| **Reed-Solomon (8+4)** | 20.0 MB | 30.0 MB | $1.50\times$ | **50.0%** (Tolerates 4 Failures) |
| **Reed-Solomon (8+2)** | 20.0 MB | 25.0 MB | $1.25\times$ | **58.3%** |
| **XOR Parity (4+2)** | 20.0 MB | 30.0 MB | $1.50\times$ | 50.0% (Only 1 Failure) |

---

## 2. Computational Latency and Scaling (Up to 20 MB)

Through vectorization over $\text{GF}(2^8)$, Cauchy Reed-Solomon scales smoothly across large file sizes:

- At **1 MB**: RS (4+2) encodes in **161 ms** and reconstructs from 2 dropped nodes in **53 ms**.
- At **10 MB**: RS (4+2) encodes in **731 ms** and reconstructs in **494 ms**.
- At **20 MB**: RS (4+2) encodes in **1.45 s** and reconstructs in **980 ms**.

### Observation on XOR Baseline:
While bitwise XOR parity has near-zero computational complexity for small payloads, pure Python XOR loops scale poorly on large byte strings, whereas NumPy-backed Galois Field matrix multiplication maintains linear scaling.

---

## 3. The Degraded Read Network Amplification Penalty

The benchmark confirms the fundamental trade-off identified in datacenter research:

When 1 node crashes in a 20 MB storage pool:
- **3-Way Replication**: Rebuilding the dead replica downloads **20 MB** across the network (1 full copy from a surviving peer).
- **Reed-Solomon (4+2)**: Rebuilding 1 missing shard requires fetching data from all $k=4$ surviving nodes ($4 \times 5\text{ MB} = 20\text{ MB}$ network transfer).
- **Reed-Solomon (8+2)**: Although RS (8+2) delivers the lowest storage overhead ($1.25\times$), repairing 1 failed node requires fetching data from all $k=8$ nodes ($8 \times 2.5\text{ MB} = 20\text{ MB}$ network transfer).
- **Network Fan-in Bottleneck**: For RS (8+2), the recovery orchestrator must open 8 parallel network sockets to distinct storage nodes. In congested production datacenters, this high fan-in creates tail latency spikes (stragglers).

---

## 4. Fault Tolerance Verification Matrix

Across all 90 runs:
1. **Reed-Solomon Codes**: Achieved **100% recovery success** under both 1-node and 2-node failures.
2. **3-Way Replication**: Achieved **100% recovery success** under 1-node and 2-node failures.
3. **XOR Parity (4+2)**:
   - 1 node failure: **100% recovery success**.
   - 2 concurrent node failures: **0% recovery success** (raises failure exception due to insufficient linear rank).

---

## 5. Engineering Recommendations for Storage Designers

1. **For Hot, Read-Intensive Workloads**:
   Use **3-Way Replication** to avoid CPU decoding overhead and minimize network fan-in latency.
2. **For General Cloud Storage & Scaled BLOB Tiers**:
   Use **Reed-Solomon (4+2) or (8+2)** to reclaim 50% to 58% of storage hardware expenditure.
3. **For Latency-Critical Erasure Coding**:
   Deploy **Local Reconstruction Codes (LRC)** to split $k$ into local parity clusters, avoiding full-$k$ network fan-in during single-node degraded reads.
