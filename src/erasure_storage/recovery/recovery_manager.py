from __future__ import annotations

from typing import Union
from erasure_storage.codec.rs_codec import CodecType, get_codec, BaseCodec
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

        if len(by_index) < self.data_shards:
            raise ValueError(
                f"Not enough fragments to recover file: need {self.data_shards}, got {len(by_index)}"
            )

        total_shards = self.data_shards + self.parity_shards
        missing_indexes = sorted(set(range(total_shards)) - set(by_index))
        available_sorted = [by_index[idx] for idx in sorted(by_index)]

        recovered = self.codec.recover_missing(
            available=available_sorted,
            data_shards=self.data_shards,
            parity_shards=self.parity_shards,
            missing_indexes=missing_indexes,
            expected_len=len(original_payload) if original_payload is not None else None,
        )

        self.last_metrics = {
            "file_id": file_id,
            "failed_nodes": failed_nodes,
            "recovery_success": recovered == original_payload,
            "bytes_recovered": len(recovered),
            "data_shards": self.data_shards,
            "parity_shards": self.parity_shards,
            "codec": self.codec_type.value,
        }
        return recovered
