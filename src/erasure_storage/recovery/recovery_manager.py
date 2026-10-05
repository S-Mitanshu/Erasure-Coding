from __future__ import annotations

from erasure_storage.codec.rs_codec import ReedSolomonCodec
from erasure_storage.storage.node_store import NodeStore


class RecoveryManager:
    def __init__(self, node_store: NodeStore):
        self.node_store = node_store
        self.last_metrics = {}

    def recover_file(self, file_id: str, original_payload: bytes) -> bytes:
        available = []
        failed_nodes = sorted(self.node_store.failed_nodes)
        by_index = {}

        for node_id in sorted(self.node_store.nodes):
            if node_id in failed_nodes:
                continue
            for fragment in self.node_store.nodes[node_id].fragments:
                if fragment.file_id == file_id:
                    available.append(fragment.data)
                    by_index[fragment.index] = fragment.data

        if len(available) < 4:
            raise ValueError("Not enough fragments to recover file")

        codec = ReedSolomonCodec(4, 2)
        missing_indexes = sorted(set(range(6)) - set(by_index))
        recovered = codec.recover_missing(
            [by_index[idx] for idx in sorted(by_index)],
            data_shards=4,
            parity_shards=2,
            missing_indexes=missing_indexes,
        )

        self.last_metrics = {
            "file_id": file_id,
            "failed_nodes": failed_nodes,
            "recovery_success": recovered == original_payload,
            "bytes_recovered": len(recovered),
        }
        return recovered
