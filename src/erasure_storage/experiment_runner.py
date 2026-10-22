from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Sequence, Union

from erasure_storage.codec.rs_codec import CodecType
from erasure_storage.common.checksum import sha256_hex
from erasure_storage.coordinator.coordinator import Coordinator
from erasure_storage.metrics.collector import MetricsCollector
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
    codec_type: Union[CodecType, str] = CodecType.REED_SOLOMON,
) -> dict:
    failed = _normalize_failed_nodes(failed_nodes)
    actual_codec = codec_type if isinstance(codec_type, CodecType) else CodecType(str(codec_type).lower())
    collector = MetricsCollector()

    coordinator = Coordinator(
        data_shards=data_shards,
        parity_shards=parity_shards,
        node_count=node_count,
        codec_type=actual_codec,
    )
    file_id = coordinator.ingest_file(payload)

    with collector.measure("encoding"):
        placement = coordinator.assign_fragments(file_id)

    total_stored_bytes = sum(len(f.data) for f in placement)
    collector.phases["encoding"].bytes_transferred = total_stored_bytes

    node_store = NodeStore(node_count=node_count)
    node_store.store_fragments(placement)
    node_store.fail_nodes(failed)

    manager = RecoveryManager(
        node_store=node_store,
        data_shards=data_shards,
        parity_shards=parity_shards,
        codec_type=actual_codec,
    )

    with collector.measure("recovery"):
        recovered = manager.recover_file(file_id, payload)

    recovery_read_bytes = data_shards * (len(placement[0].data) if placement else 0)
    collector.phases["recovery"].bytes_transferred = recovery_read_bytes

    input_size = len(payload)
    storage_overhead = round(total_stored_bytes / input_size, 4) if input_size > 0 else 0.0

    report = {
        "file_id": file_id,
        "codec": actual_codec.value,
        "input_size_bytes": input_size,
        "total_stored_bytes": total_stored_bytes,
        "storage_overhead_ratio": storage_overhead,
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
        "metrics": collector.to_dict(),
        "recovery_metrics": manager.last_metrics,
    }

    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        json_path = output_path / "experiment_report.json"
        md_path = output_path / "experiment_report.md"

        json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        enc_m = report["metrics"].get("encoding", {})
        rec_m = report["metrics"].get("recovery", {})
        md_path.write_text(
            "# Experiment Report\n\n"
            + f"- File ID: {report['file_id']}\n"
            + f"- Codec: {report['codec']}\n"
            + f"- Input size: {report['input_size_bytes']} bytes\n"
            + f"- Total stored bytes: {report['total_stored_bytes']} bytes ({report['storage_overhead_ratio']}x overhead)\n"
            + f"- Data shards: {report['data_shards']}\n"
            + f"- Parity shards: {report['parity_shards']}\n"
            + f"- Storage nodes: {report['storage_nodes']}\n"
            + f"- Failed nodes: {report['failed_nodes']}\n"
            + f"- Recovery success: {report['recovery_success']}\n"
            + f"- Encoding time: {enc_m.get('duration_s', 0):.4f}s\n"
            + f"- Recovery time: {rec_m.get('duration_s', 0):.4f}s\n"
            + f"- Recovery network transfer: {rec_m.get('bytes_transferred', 0)} bytes\n"
            + f"- Peak memory: {rec_m.get('memory_peak_mb', 0):.2f} MB\n"
            + f"- Original hash: {report['original_hash']}\n"
            + f"- Recovered hash: {report['recovered_hash']}\n",
            encoding="utf-8",
        )

    return report
