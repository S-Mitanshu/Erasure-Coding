from __future__ import annotations

import time
from typing import Optional, Union

from erasure_storage.codec.rs_codec import BaseCodec, CodecType, get_codec
from erasure_storage.metrics.collector import MetricsCollector
from erasure_storage.storage.node_store import NodeStore


class RecoveryManager:
    def __init__(
        self,
        node_store: NodeStore,
        data_shards: int = 4,
        parity_shards: int = 2,
        codec_type: Union[CodecType, str] = CodecType.REED_SOLOMON,
    ):
        self.node_store = node_store
        self.data_shards = data_shards
        self.parity_shards = parity_shards
        self.codec_type = codec_type if isinstance(codec_type, CodecType) else CodecType(str(codec_type).lower())
        self.codec: BaseCodec = get_codec(self.codec_type, data_shards, parity_shards)
        self.last_metrics = {}

    def recover_file(
        self,
        file_id: str,
        original_payload: bytes,
        collector: Optional[MetricsCollector] = None,
    ) -> bytes:
        start_time = time.perf_counter()
        failed_nodes = sorted(self.node_store.failed_nodes)
        by_index = {}
        total_bytes_available = 0

        for node_id in sorted(self.node_store.nodes):
            if node_id in failed_nodes:
                continue
            for fragment in self.node_store.nodes[node_id].fragments:
                if fragment.file_id == file_id:
                    by_index[fragment.index] = fragment.data
                    total_bytes_available += len(fragment.data)

        if len(by_index) < self.data_shards:
            raise ValueError(
                f"Not enough fragments to recover file: need {self.data_shards}, got {len(by_index)}"
            )

        total_shards = self.data_shards + self.parity_shards
        missing_indexes = sorted(set(range(total_shards)) - set(by_index))
        available_sorted = [by_index[idx] for idx in sorted(by_index)]

        # The repair process downloads at least k shards to reconstruct
        shard_size = len(available_sorted[0]) if available_sorted else 0
        recovery_read_bytes = self.data_shards * shard_size

        recovered = self.codec.recover_missing(
            available=available_sorted,
            data_shards=self.data_shards,
            parity_shards=self.parity_shards,
            missing_indexes=missing_indexes,
            expected_len=len(original_payload) if original_payload is not None else None,
        )

        recovery_duration = time.perf_counter() - start_time

        self.last_metrics = {
            "file_id": file_id,
            "failed_nodes": failed_nodes,
            "recovery_success": recovered == original_payload,
            "bytes_recovered": len(recovered),
            "recovery_read_bytes": recovery_read_bytes,
            "recovery_time_s": round(recovery_duration, 6),
            "data_shards": self.data_shards,
            "parity_shards": self.parity_shards,
            "codec": self.codec_type.value,
        }

        if collector is not None:
            collector.record_manual(
                phase_name="recovery",
                duration_s=recovery_duration,
                bytes_transferred=recovery_read_bytes,
            )

        return recovered
