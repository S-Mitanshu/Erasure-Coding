from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Sequence, Union

from erasure_storage.common.checksum import sha256_hex
from erasure_storage.coordinator.coordinator import Coordinator
from erasure_storage.recovery.recovery_manager import RecoveryManager
from erasure_storage.storage.node_store import NodeStore


def _normalize_failed_nodes(failed_nodes: Sequence[int] | Iterable[int] | None) -> List[int]:
    if failed_nodes is None:
        return []
    return sorted({int(node_id) for node_id in failed_nodes})


def run_experiment(
    payload: bytes,
    data_shards: int = 4,
    parity_shards: int = 2,
    node_count: int = 6,
    failed_nodes: Sequence[int] | Iterable[int] | None = None,
    output_dir: Union[str, Path, None] = None,
) -> dict:
    file_id = None
    failed = _normalize_failed_nodes(failed_nodes)
    coordinator = Coordinator(data_shards=data_shards, parity_shards=parity_shards, node_count=node_count)
    file_id = coordinator.ingest_file(payload)
    placement = coordinator.assign_fragments(file_id)

    node_store = NodeStore(node_count=node_count)
    node_store.store_fragments(placement)
    node_store.fail_nodes(failed)

    manager = RecoveryManager(node_store)
    recovered = manager.recover_file(file_id, payload)
    report = {
        "file_id": file_id,
        "input_size_bytes": len(payload),
        "original_hash": coordinator.file_checksums[file_id],
        "recovered_hash": sha256_hex(recovered),
        "data_shards": data_shards,
        "parity_shards": parity_shards,
        "storage_nodes": node_count,
        "failed_nodes": failed,
        "recovery_success": recovered == payload,
        "fragment_count": len(placement),
        "fragments_per_node": {
            str(node_id): len(node_store.nodes[node_id].fragments)
            for node_id in range(node_count)
        },
        "recovery_metrics": manager.last_metrics,
    }

    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        json_path = output_path / "experiment_report.json"
        md_path = output_path / "experiment_report.md"

        json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        md_path.write_text(
            "# Experiment Report\n\n"
            + f"- File ID: {report['file_id']}\n"
            + f"- Input size: {report['input_size_bytes']} bytes\n"
            + f"- Data shards: {report['data_shards']}\n"
            + f"- Parity shards: {report['parity_shards']}\n"
            + f"- Storage nodes: {report['storage_nodes']}\n"
            + f"- Failed nodes: {report['failed_nodes']}\n"
            + f"- Recovery success: {report['recovery_success']}\n"
            + f"- Original hash: {report['original_hash']}\n"
            + f"- Recovered hash: {report['recovered_hash']}\n",
            encoding="utf-8",
        )

    return report
