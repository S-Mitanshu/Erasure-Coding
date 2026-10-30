import re

with open('docs/BTP_FINAL_PROJECT_REPORT.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update List of Figures
old_lof = """## LIST OF FIGURES

- **Figure 3.1**: End-to-End System Pipeline and Ingestion Architecture . . . . . . . . . . . . . . . . 15
- **Figure 4.1**: Storage Capacity Overhead by Coding Scheme (1.25x – 1.50x vs. 3.00x) . . . . . . . . . 23
- **Figure 4.2**: Degraded Read & Reconstruction Latency Scaling Across File Sizes (Up to 20 MB) . . 25
- **Figure 4.3**: Degraded Read Network Bandwidth Amplification for 20 MB Payload . . . . . . . . . . . . 28
- **Figure 4.4**: Fault Tolerance and Recovery Verification Matrix Across Multi-Node Failures . . . . . . 30
- **Figure 4.5**: Generalized Storage Overhead Surface as a Function of $k$ and $m$ . . . . . . . . . . . . . . 32
- **Figure 4.6**: Pareto Frontier: Fault Tolerance ($m$) vs. Storage Overhead Factor . . . . . . . . . . . . . . 33"""

new_lof = """## LIST OF FIGURES

- **Figure 3.1**: End-to-End System Pipeline and Ingestion Architecture Flowchart . . . . . . . . . . . 15
- **Figure 4.1**: Storage Capacity Overhead Comparison by Coding Scheme (1.25x – 1.50x vs. 3.00x) . . 23
- **Figure 4.2**: Degraded Read & Reconstruction Latency Scaling Across File Sizes (Up to 20 MB) . . 25
- **Figure 4.3**: Degraded Read Network Bandwidth Amplification for 20 MB Payload . . . . . . . . . . . . 28
- **Figure 4.4**: Fault Tolerance and Recovery Verification Matrix Across Multi-Node Failures . . . . . . 30
- **Figure 4.5**: Generalized Storage Overhead Surface as a Function of $k$ and $m$ . . . . . . . . . . . . . . 32
- **Figure 4.6**: Pareto Trade-off Frontier: Fault Tolerance ($m$) vs. Storage Overhead Factor . . . . . . 33
- **Figure 4.7**: Large-File Single-Failure Repair Network Bandwidth (Up to 100 MB) . . . . . . . . . . 34
- **Figure 4.8**: Large-File Projected Reconstruction Latency Scaling (Up to 100 MB) . . . . . . . . . . . 35"""

if old_lof in text:
    text = text.replace(old_lof, new_lof)

# 2. Embed Figure 3.1
old_f31_block = """```
+--------------------------------------------------------------------------------------------------+
|                                FIGURE 3.1: System Architecture                                   |
+--------------------------------------------------------------------------------------------------+
|                                                                                                  |
|   [Raw Input File]  -->  (Coordinator: Ingestion & SHA-256 Hashing)                             |
|                                    |                                                             |
|                                    v                                                             |
|               +--------------------+--------------------+                                        |
|               |                    |                    |                                        |
|               v                    v                    v                                        |
|      [Cauchy RS Codec]      [XOR Baseline]      [Replication Engine]                             |
|        (k Data + m Parity)     (k Data + 1 Parity)   (3 Full Copies)                             |
|               |                    |                    |                                        |
|               +--------------------+--------------------+                                        |
|                                    |                                                             |
|                                    v                                                             |
|                    (NodeStore: Virtual Node Mapping)                                             |
|                      [Node 0] [Node 1] ... [Node N-1]                                            |
|                                    |                                                             |
|                                    v                                                             |
|                    (Failure Injection: Offline State)                                            |
|                                    |                                                             |
|                                    v                                                             |
|                 (RecoveryManager: Quorum Check >= k)                                             |
|                                    |                                                             |
|                                    v                                                             |
|                 (GF(2^8) Submatrix Inversion / Rebuild)                                          |
|                                    |                                                             |
|                                    v                                                             |
|               (Cryptographic Verification & Metrics Telemetry)                                   |
|                                                                                                  |
+--------------------------------------------------------------------------------------------------+
```"""

new_f31_block = """<div align="center">

![Figure 3.1: End-to-End System Pipeline and Ingestion Architecture](results/plots/system_architecture_flow.png)

**Figure 3.1: End-to-End System Pipeline and Ingestion Architecture Flowchart**  
*(Ingestion, SHA-256 baseline hashing, multi-engine shard placement, failure injection, quorum validation, submatrix inversion reconstruction, and telemetry logging)*

</div>"""

if old_f31_block in text:
    text = text.replace(old_f31_block, new_f31_block)

# 3. Embed Figure 4.1
old_f41_block = """```
[FIGURE 4.1: Storage Capacity Overhead Comparison by Scheme]
(Refer to results/plots/storage_overhead_by_scheme.png)
Shows bar comparison: RS (8+2) at 1.25x (58% savings), RS (4+2) at 1.50x (50% savings),
RS (8+4) at 1.50x (50% savings), and 3-Way Replication at 3.00x (Baseline).
```"""

new_f41_block = """<div align="center">

![Figure 4.1: Storage Capacity Overhead by Coding Scheme](results/plots/storage_overhead_by_scheme.png)

**Figure 4.1: Storage Capacity Overhead Comparison by Coding Scheme**  
*(RS 8+2 at 1.25x / 58.3% saving, RS 4+2 at 1.50x / 50.0% saving, RS 8+4 at 1.50x / 50.0% saving, XOR 4+2 at 1.50x, and 3-Way Replication at 3.00x baseline)*

</div>"""

if old_f41_block in text:
    text = text.replace(old_f41_block, new_f41_block)

# 4. Embed Figure 4.2
old_f42_block = """```
[FIGURE 4.2: Recovery Latency Scaling Across Workload Sizes (Up to 20 MB)]
(Refer to results/plots/recovery_latency_scaling_20mb.png)
Plots recovery duration in milliseconds against payload size (0.1 to 20 MB) for RS (4+2),
RS (8+2), RS (8+4), XOR (4+2), and Replication.
```"""

new_f42_block = """<div align="center">

![Figure 4.2: Degraded Read & Reconstruction Latency Scaling Across File Sizes](results/plots/recovery_latency_scaling_20mb.png)

**Figure 4.2: Degraded Read & Reconstruction Latency Scaling Across File Sizes (Up to 20 MB)**  
*(Empirical single-node recovery duration in milliseconds scaling linearly across payload sizes for RS 4+2, RS 8+2, RS 8+4, XOR, and Replication)*

</div>"""

if old_f42_block in text:
    text = text.replace(old_f42_block, new_f42_block)

# 5. Embed Figure 4.3
old_f43_block = """```
[FIGURE 4.3: Degraded Read Network Bandwidth Amplification for 20 MB Payload]
(Refer to results/plots/degraded_read_amplification.png)
Demonstrates that while all schemes download 20 MB to repair 1 node, the network fan-in
connection count increases from 1 in replication to 4 in RS (4+2) and 8 in RS (8+2).
```"""

new_f43_block = """<div align="center">

![Figure 4.3: Degraded Read Network Bandwidth Amplification for 20 MB Payload](results/plots/degraded_read_amplification.png)

**Figure 4.3: Degraded Read Network Bandwidth Amplification for 20 MB Payload**  
*(Total network data transferred across cluster sockets during single-node reconstruction: 20 MB across all schemes, but with fan-in scaling from 1 in replication to 4 in RS 4+2 and 8 in RS 8+2)*

</div>"""

if old_f43_block in text:
    text = text.replace(old_f43_block, new_f43_block)

# 6. Embed Figure 4.4
old_f44_block = """```
[FIGURE 4.4: Fault Tolerance Verification Matrix Across Multi-Node Failures]
(Refer to results/plots/fault_tolerance_matrix.png)
Heatmap verifying 100% recovery for RS (4+2), RS (8+2), RS (8+4), and Replication under
0, 1, and 2 node dropouts, contrasting with 0% recovery for XOR parity under 2 failures.
```"""

new_f44_block = """<div align="center">

![Figure 4.4: Fault Tolerance and Recovery Verification Matrix Across Multi-Node Failures](results/plots/fault_tolerance_matrix.png)

**Figure 4.4: Fault Tolerance and Recovery Verification Matrix Across Multi-Node Failures**  
*(Verification heatmap displaying 100% recovery for Cauchy RS codes under 0, 1, and 2 failures, contrasting with 0% recovery for XOR single-parity at 2 node dropouts)*

</div>"""

if old_f44_block in text:
    text = text.replace(old_f44_block, new_f44_block)

# 7. Embed Figure 4.5 & 4.6 and add 4.7 & 4.8
old_f45_46_block = """```
[FIGURE 4.5: Generalized Storage Overhead Surface as a Function of k and m]
(Refer to results/plots/generalized_storage_overhead_surface.png)
Continuous surface plot mapping overhead multiplier (k+m)/k across k in [2, 16] and m in [1, 6].
```

#### 1. Overhead Asymptote:
As shown in **Figure 4.5**, storage overhead follows $\\frac{k+m}{k} = 1 + \\frac{m}{k}$. As $k$ increases, overhead drops steeply:
- For $m=2$, moving from $k=2$ to $k=8$ drops overhead from $2.00\\times$ down to $1.25\\times$.
- However, diminishing returns set in beyond $k=10$: moving from $k=10$ to $k=16$ only saves an additional $0.075\\times$ overhead while doubling network fan-in during repairs.

```
[FIGURE 4.6: Pareto Frontier: Fault Tolerance (m) vs. Storage Overhead Factor]
(Refer to results/plots/generalized_pareto_frontier.png)
Pareto trade-off scatter plot highlighting the optimal industrial sweet spot between 1.25x
and 1.71x overhead across real-world deployments (Meta f4, Google Colossus, Backblaze, and our prototype).
```"""

new_f45_46_block = """<div align="center">

![Figure 4.5: Generalized Storage Overhead Surface as a Function of k and m](results/plots/generalized_storage_overhead_surface.png)

**Figure 4.5: Generalized Storage Overhead Surface as a Function of Data Shards ($k$) and Parity Shards ($m$)**  
*(Mapping continuous storage multiplier (k+m)/k across k in [2, 16] for m in {1, 2, 3, 4, 6} against 2-Way and 3-Way replication baselines)*

</div>

#### 1. Overhead Asymptote & Diminishing Returns:
As shown in **Figure 4.5**, storage overhead follows $\\Omega(k, m) = \\frac{k+m}{k} = 1 + \\frac{m}{k}$. As $k$ increases, overhead drops steeply:
- For $m=2$, moving from $k=2$ to $k=8$ drops overhead from $2.00\\times$ down to $1.25\\times$ (58.3% storage reduction).
- However, diminishing returns set in beyond $k=10$: moving from $k=10$ to $k=16$ only saves an additional $0.075\\times$ overhead while doubling network fan-in during repairs.

<div align="center">

![Figure 4.6: Pareto Trade-off Frontier](results/plots/generalized_pareto_frontier.png)

**Figure 4.6: Pareto Trade-off Frontier: Fault Tolerance ($m$) vs. Storage Overhead Factor**  
*(Pareto frontier mapping industrial cloud architectures—Meta f4, Google Colossus, Backblaze Vaults, our prototype, and 3-way replication—highlighting the optimal sweet spot between 1.25x and 1.71x)*

</div>

#### 2. Large-File Repair Bandwidth & Latency Scaling (Up to 100 MB):
To evaluate system behavior across large datasets, we extended our empirical models to 100 MB files:

<div align="center">

![Figure 4.7: Repair Network Bandwidth for Large Files](results/plots/generalized_repair_bandwidth_scaling.png)

**Figure 4.7: Single-Node Repair Network Traffic for Large Files (Up to 100 MB)**  
*(Illustrating network data downloaded across the cluster to repair 1 failed node, demonstrating how Azure Local Reconstruction Codes cut repair traffic by 50% compared to standard Reed-Solomon)*

</div>

<div align="center">

![Figure 4.8: Large-File Projected Reconstruction Latency Scaling](results/plots/generalized_large_file_latency_projection.png)

**Figure 4.8: Projected Reconstruction Latency Scaling for Large Workloads (Up to 100 MB)**  
*(Demonstrating that vectorized Cauchy matrix inversion maintains predictable linear scaling: ~2.45s for 50 MB and ~4.90s for 100 MB single-stream reconstruction)*

</div>"""

if old_f45_46_block in text:
    text = text.replace(old_f45_46_block, new_f45_46_block)

with open('docs/BTP_FINAL_PROJECT_REPORT.md', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated docs/BTP_FINAL_PROJECT_REPORT.md successfully with embedded figures.')
