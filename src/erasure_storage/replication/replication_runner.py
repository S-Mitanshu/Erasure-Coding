from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Union

from erasure_storage.common.checksum import sha256_hex
from erasure_storage.metrics.collector import MetricsCollector


@dataclass
class ReplicaRecord:
    node_id: int
    file_id: str
    data: bytes
    checksum: str


class ReplicationNodeStore:
    """Simulates distributed storage nodes holding full replicas."""

    def __init__(self, node_count: int):
        self.node_count = node_count
        self.nodes: Dict[int, List[ReplicaRecord]] = {i: [] for i in range(node_count)}
        self.failed_nodes: set[int] = set()

    def store_replica(self, node_id: int, record: ReplicaRecord) -> None:
        if node_id not in self.nodes:
            raise KeyError(f"Invalid node_id: {node_id}")
        self.nodes[node_id].append(record)

    def fail_nodes(self, failed: Sequence[int]) -> None:
        self.failed_nodes.update(failed)

    def get_surviving_replicas(self, file_id: str) -> List[ReplicaRecord]:
        surviving = []
        for node_id, records in self.nodes.items():
            if node_id in self.failed_nodes:
                continue
            for r in records:
                if r.file_id == file_id:
                    surviving.append(r)
        return surviving


def run_replication_experiment(
    payload: bytes,
    replication_factor: int = 3,
    node_count: int = 6,
    failed_nodes: Sequence[int] | Iterable[int] | None = None,
    output_dir: Union[str, Path, None] = None,
) -> dict:
    """Executes an N-way replication storage and recovery experiment.

    Mirrors the reporting schema of run_experiment() to allow direct side-by-side
    comparison against erasure coding across overhead, recovery latency, and network cost.
    """
    if replication_factor > node_count:
        raise ValueError(
            f"Replication factor {replication_factor} cannot exceed node count {node_count}"
        )

    failed = sorted({int(n) for n in failed_nodes}) if failed_nodes is not None else []
    file_id = str(uuid.uuid4())
    original_hash = sha256_hex(payload)
    input_size = len(payload)
    collector = MetricsCollector()

    # 1. Ingestion / Replication phase
    # Replicas are distributed round-robin across the first R nodes
    store = ReplicationNodeStore(node_count=node_count)
    replica_nodes = [i % node_count for i in range(replication_factor)]
    records: List[ReplicaRecord] = []

    with collector.measure("encoding"):
        for nid in replica_nodes:
            rec = ReplicaRecord(
                node_id=nid,
                file_id=file_id,
                data=payload,
                checksum=original_hash,
            )
            store.store_replica(nid, rec)
            records.append(rec)

    total_stored_bytes = sum(len(r.data) for r in records)
    collector.phases["encoding"].bytes_transferred = total_stored_bytes

    # 2. Simulate Node Failures
    store.fail_nodes(failed)

    # 3. Recovery phase
    with collector.measure("recovery"):
        surviving = store.get_surviving_replicas(file_id)
        if not surviving:
            recovered_payload = b""
            recovery_success = False
            recovery_read_bytes = 0
        else:
            # Reconstruct by copying from the first surviving replica
            source_replica = surviving[0]
            recovered_payload = source_replica.data
            recovery_success = (recovered_payload == payload)
            # Repairing one failed replica copies 1 full file across the network
            recovery_read_bytes = len(recovered_payload)

    collector.phases["recovery"].bytes_transferred = recovery_read_bytes

    storage_overhead = (
        round(total_stored_bytes / input_size, 4) if input_size > 0 else 0.0
    )

    report = {
        "file_id": file_id,
        "storage_mode": "replication",
        "codec": f"replication_{replication_factor}x",
        "replication_factor": replication_factor,
        "input_size_bytes": input_size,
        "total_stored_bytes": total_stored_bytes,
        "storage_overhead_ratio": storage_overhead,
        "original_hash": original_hash,
        "recovered_hash": sha256_hex(recovered_payload) if recovered_payload else "",
        "storage_nodes": node_count,
        "replica_nodes": replica_nodes,
        "failed_nodes": failed,
        "recovery_success": recovery_success,
        "replicas_stored": len(records),
        "replicas_surviving": len(surviving),
        "metrics": collector.to_dict(),
        "recovery_metrics": {
            "file_id": file_id,
            "failed_nodes": failed,
            "recovery_success": recovery_success,
            "bytes_recovered": len(recovered_payload),
            "recovery_read_bytes": recovery_read_bytes,
            "replicas_surviving": len(surviving),
        },
    }

    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        json_path = output_path / "replication_experiment_report.json"
        md_path = output_path / "replication_experiment_report.md"

        json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        rec_m = report["metrics"].get("recovery", {})
        md_path.write_text(
            "# Replication Experiment Report\n\n"
            + f"- File ID: {report['file_id']}\n"
            + f"- Mode: {report['storage_mode']} ({report['replication_factor']}x)\n"
            + f"- Input size: {report['input_size_bytes']} bytes\n"
            + f"- Total stored bytes: {report['total_stored_bytes']} bytes ({report['storage_overhead_ratio']}x overhead)\n"
            + f"- Storage nodes: {report['storage_nodes']}\n"
            + f"- Replica nodes: {report['replica_nodes']}\n"
            + f"- Failed nodes: {report['failed_nodes']}\n"
            + f"- Recovery success: {report['recovery_success']}\n"
            + f"- Replicas surviving: {report['replicas_surviving']}/{report['replicas_stored']}\n"
            + f"- Recovery network transfer: {rec_m.get('bytes_transferred', 0)} bytes\n"
            + f"- Original hash: {report['original_hash']}\n"
            + f"- Recovered hash: {report['recovered_hash']}\n",
            encoding="utf-8",
        )

    return report
