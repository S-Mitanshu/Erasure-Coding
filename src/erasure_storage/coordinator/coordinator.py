from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Dict, List

from erasure_storage.common.checksum import sha256_hex
from erasure_storage.codec.rs_codec import ReedSolomonCodec


@dataclass
class FragmentRecord:
    index: int
    file_id: str
    node_id: int
    fragment_type: str
    checksum: str
    data: bytes


class Coordinator:
    def __init__(self, data_shards: int, parity_shards: int, node_count: int):
        self.data_shards = data_shards
        self.parity_shards = parity_shards
        self.node_count = node_count
        self.codec = ReedSolomonCodec(data_shards, parity_shards)
        self.file_checksums: Dict[str, str] = {}
        self.file_payloads: Dict[str, bytes] = {}
        self.file_fragments: Dict[str, List[FragmentRecord]] = {}

    def ingest_file(self, payload: bytes) -> str:
        file_id = str(uuid.uuid4())
        self.file_payloads[file_id] = payload
        self.file_checksums[file_id] = sha256_hex(payload)
        return file_id

    def assign_fragments(self, file_id: str) -> List[FragmentRecord]:
        if file_id not in self.file_payloads:
            raise KeyError(f"Unknown file ID: {file_id}")

        payload = self.file_payloads[file_id]
        fragments = self.codec.encode_data(payload)
        records: List[FragmentRecord] = []

        for index, chunk in enumerate(fragments):
            node_id = index % self.node_count
            fragment_type = "data" if index < self.data_shards else "parity"
            records.append(
                FragmentRecord(
                    index=index,
                    file_id=file_id,
                    node_id=node_id,
                    fragment_type=fragment_type,
                    checksum=sha256_hex(chunk),
                    data=chunk,
                )
            )

        self.file_fragments[file_id] = records
        return records

    def verify_file(self, file_id: str, content: bytes) -> bool:
        return self.file_checksums.get(file_id) == sha256_hex(content)
