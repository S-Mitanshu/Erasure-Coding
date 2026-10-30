with open('docs/MASTER_REFERENCE_DOSSIER.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.startswith('# 8. COMPREHENSIVE VISUAL PLOT CATALOG'):
        new_lines.append('# 8. COMPREHENSIVE VISUAL PLOT CATALOG & QUALITY FIXES\n\n')
        new_lines.append('All plots are generated at 300 DPI publication resolution and stored in `results/plots/`. Every single figure has been directly embedded into the formal BTP report:\n\n')
        new_lines.append('1. **`system_architecture_flow.png` (Figure 3.1)**:\n')
        new_lines.append('   End-to-End System Pipeline and Ingestion Architecture Flowchart. Matches `docs/flow.svg` with publication-grade formatting, showing Ingestion -> Codec Selection (RS / XOR / Replication) -> Virtual NodeStore -> Failure Injection -> Quorum Validation -> Submatrix Inversion -> SHA-256 Verification and Telemetry.\n')
        new_lines.append('2. **`storage_overhead_by_scheme.png` (Figure 4.1)**:\n')
        new_lines.append('   Bar chart proving the 50.0% to 58.3% capacity savings of RS (4+2) (1.50x) and RS (8+2) (1.25x) over 3-Way Replication (3.00x).\n')
        new_lines.append('3. **`recovery_latency_scaling_20mb.png` (Figure 4.2)**:\n')
        new_lines.append('   Line chart demonstrating strictly linear sub-second recovery latency up to 20 MB payloads (980 ms).\n')
        new_lines.append('4. **`degraded_read_amplification.png` (Figure 4.3)**:\n')
        new_lines.append('   Bar chart illustrating the network repair traffic penalty and connection fan-in concentration (1 node in replication vs. 4 in RS 4+2 vs. 8 in RS 8+2).\n')
        new_lines.append('5. **`fault_tolerance_matrix.png` (Figure 4.4)**:\n')
        new_lines.append('   Green/Red verification heatmap displaying 100% recovery for RS codes under multi-failure modes, contrasting with XOR failure at 2 dropped nodes.\n')
        new_lines.append('6. **`generalized_storage_overhead_surface.png` (Figure 4.5)**:\n')
        new_lines.append('   Continuous parameter curves mapping storage overhead across k in [2, 16] for m in {1, 2, 3, 4, 6}.\n')
        new_lines.append('7. **`generalized_pareto_frontier.png` (Figure 4.6 - Resolved Collision)**:\n')
        new_lines.append('   Pareto trade-off scatter plot. Fixed text overlap between RS (4+2), Colossus (6+3), and RS (8+4) by implementing staggered radial callout vectors, custom pointer arcs, and translucent pill badges.\n')
        new_lines.append('8. **`generalized_repair_bandwidth_scaling.png` (Figure 4.7)**:\n')
        new_lines.append('   Projected repair traffic scaling for large files up to 100 MB, highlighting the 50% bandwidth reduction of Azure LRC.\n')
        new_lines.append('9. **`generalized_large_file_latency_projection.png` (Figure 4.8)**:\n')
        new_lines.append('   Reconstruction duration curves extrapolated up to 100 MB payloads.\n\n')
        skip = True
    elif skip and line.startswith('# 9.'):
        skip = False
        new_lines.append(line)
    elif not skip:
        new_lines.append(line)

with open('docs/MASTER_REFERENCE_DOSSIER.md', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Updated MASTER_REFERENCE_DOSSIER.md Section 8 successfully.')
