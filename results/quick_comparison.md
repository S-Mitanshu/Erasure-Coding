# Storage Scheme Comparison: Erasure Coding vs Replication

| Scheme | File Size | Raw Size (KB) | Total Stored (KB) | Overhead Ratio | Repair Transfer (KB) | Encode Time (ms) | Recovery Time (ms) | Max Fault Tolerance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RS (4+2) | 100 KB | 100.0 | 150.0 | 1.50x | 100.0 | 13.67 | 15.72 | 2 Nodes (MDS) |
| XOR Parity (4+2) | 100 KB | 100.0 | 150.0 | 1.50x | 100.0 | 47.1 | 38.29 | 1 Node (Single Parity) |
| 3-Way Replication | 100 KB | 100.0 | 300.0 | 3.00x | 100.0 | 0.03 | 0.02 | 2 Nodes (Replica Copy) |
| RS (4+2) | 500 KB | 500.0 | 750.0 | 1.50x | 500.0 | 35.63 | 23.54 | 2 Nodes (MDS) |
| XOR Parity (4+2) | 500 KB | 500.0 | 750.0 | 1.50x | 500.0 | 130.18 | 148.93 | 1 Node (Single Parity) |
| 3-Way Replication | 500 KB | 500.0 | 1500.0 | 3.00x | 500.0 | 0.06 | 0.03 | 2 Nodes (Replica Copy) |
| RS (4+2) | 1 MB | 1024.0 | 1536.0 | 1.50x | 1024.0 | 161.0 | 53.68 | 2 Nodes (MDS) |
| XOR Parity (4+2) | 1 MB | 1024.0 | 1536.0 | 1.50x | 1024.0 | 232.24 | 529.85 | 1 Node (Single Parity) |
| 3-Way Replication | 1 MB | 1024.0 | 3072.0 | 3.00x | 1024.0 | 0.06 | 0.03 | 2 Nodes (Replica Copy) |
| RS (4+2) | 2 MB | 2048.0 | 3072.0 | 1.50x | 2048.0 | 198.6 | 85.88 | 2 Nodes (MDS) |
| XOR Parity (4+2) | 2 MB | 2048.0 | 3072.0 | 1.50x | 2048.0 | 740.25 | 386.07 | 1 Node (Single Parity) |
| 3-Way Replication | 2 MB | 2048.0 | 6144.0 | 3.00x | 2048.0 | 0.01 | 0.01 | 2 Nodes (Replica Copy) |