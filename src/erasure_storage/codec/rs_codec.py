from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass
class Fragment:
    index: int
    file_id: str
    data: bytes
    fragment_type: str = "data"


def _xor_bytes(left: bytes, right: bytes) -> bytes:
    length = max(len(left), len(right))
    left_padded = left + b"\x00" * (length - len(left))
    right_padded = right + b"\x00" * (length - len(right))
    return bytes(a ^ b for a, b in zip(left_padded, right_padded))


def _xor_many(items: Iterable[bytes]) -> bytes:
    result = b""
    for item in items:
        result = _xor_bytes(result, item)
    return result


class ReedSolomonCodec:
    def __init__(self, data_shards: int, parity_shards: int):
        self.data_shards = data_shards
        self.parity_shards = parity_shards

    def encode_data(self, payload: bytes) -> List[bytes]:
        if not payload:
            payload = b""

        shard_size = max(1, (len(payload) + self.data_shards - 1) // self.data_shards)
        padded = payload + b"\x00" * (shard_size * self.data_shards - len(payload))

        data_shards = [padded[i * shard_size:(i + 1) * shard_size] for i in range(self.data_shards)]
        parity = []
        parity_value = _xor_many(data_shards)
        for _ in range(self.parity_shards):
            parity.append(parity_value)

        return [*data_shards, *parity]

    def recover_missing(self, available: Sequence[bytes], data_shards: int, parity_shards: int, missing_indexes: Sequence[int]) -> bytes:
        if not available:
            raise ValueError("No available fragments for recovery")

        total_fragments = data_shards + parity_shards
        if len(available) + len(missing_indexes) != total_fragments:
            raise ValueError("Shard count mismatch")

        available_by_index = {}
        cursor = 0
        for idx in range(total_fragments):
            if idx in missing_indexes:
                continue
            available_by_index[idx] = available[cursor]
            cursor += 1

        for idx in missing_indexes:
            if idx < data_shards:
                known = [available_by_index[pos] for pos in range(total_fragments) if pos not in missing_indexes and pos != idx]
                if not known:
                    raise ValueError("Not enough fragments to recover this data shard")
                available_by_index[idx] = _xor_many(known)
            else:
                available_by_index[idx] = _xor_many(
                    available_by_index[pos] for pos in range(data_shards) if pos not in missing_indexes
                )

        rebuilt = b"".join(available_by_index[idx] for idx in range(data_shards))
        return rebuilt.rstrip(b"\x00")
