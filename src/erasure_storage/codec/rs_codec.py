from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List, Sequence, Union
import numpy as np

try:
    import galois
    _GF = galois.GF(2**8)
except ImportError:
    _GF = None


@dataclass
class Fragment:
    index: int
    file_id: str
    data: bytes
    fragment_type: str = "data"


class CodecType(str, Enum):
    REED_SOLOMON = "reed_solomon"
    XOR = "xor"


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


class BaseCodec(ABC):
    @abstractmethod
    def encode_data(self, payload: bytes) -> List[bytes]:
        pass

    @abstractmethod
    def recover_missing(
        self,
        available: Sequence[bytes],
        data_shards: int,
        parity_shards: int,
        missing_indexes: Sequence[int],
        expected_len: int | None = None,
    ) -> bytes:
        pass


class XORCodec(BaseCodec):
    """Baseline parity codec implementing bitwise XOR (RAID-5 style).

    Serves as an experimental baseline to compare against Reed-Solomon coding.
    Under XOR parity, single parity is generated from the data shards.
    It can recover from at most 1 data shard failure when parity is available.
    """

    def __init__(self, data_shards: int, parity_shards: int):
        self.data_shards = data_shards
        self.parity_shards = parity_shards

    def encode_data(self, payload: bytes) -> List[bytes]:
        if not payload:
            payload = b""

        shard_size = max(1, (len(payload) + self.data_shards - 1) // self.data_shards)
        padded = payload + b"\x00" * (shard_size * self.data_shards - len(payload))

        data_shards = [padded[i * shard_size : (i + 1) * shard_size] for i in range(self.data_shards)]
        parity = []
        parity_value = _xor_many(data_shards)
        for _ in range(self.parity_shards):
            parity.append(parity_value)

        return [*data_shards, *parity]

    def recover_missing(
        self,
        available: Sequence[bytes],
        data_shards: int,
        parity_shards: int,
        missing_indexes: Sequence[int],
        expected_len: int | None = None,
    ) -> bytes:
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

        missing_data = [idx for idx in missing_indexes if idx < data_shards]
        if len(missing_data) > 1:
            raise ValueError(f"XORCodec cannot recover from {len(missing_data)} data shard failures (max 1)")

        available_parity = [
            available_by_index[pos]
            for pos in range(data_shards, total_fragments)
            if pos not in missing_indexes
        ]

        for idx in missing_indexes:
            if idx < data_shards:
                if not available_parity:
                    raise ValueError("No parity fragment available to recover data shard")
                other_data = [available_by_index[pos] for pos in range(data_shards) if pos != idx]
                available_by_index[idx] = _xor_many([*other_data, available_parity[0]])
            else:
                available_by_index[idx] = _xor_many(
                    available_by_index[pos] for pos in range(data_shards) if pos not in missing_indexes
                )

        rebuilt = b"".join(available_by_index[idx] for idx in range(data_shards))
        if expected_len is not None:
            return rebuilt[:expected_len]
        return rebuilt.rstrip(b"\x00")


class ReedSolomonCodec(BaseCodec):
    """True Reed-Solomon Erasure Codec using Cauchy generator matrices over GF(2^8).

    Guarantees the Maximum Distance Separable (MDS) property: any k surviving
    shards from the total (k + m) shards are mathematically sufficient to
    reconstruct all missing data and parity shards.
    """

    def __init__(self, data_shards: int, parity_shards: int):
        self.data_shards = data_shards
        self.parity_shards = parity_shards
        if _GF is None:
            raise ImportError("galois library is required for ReedSolomonCodec. Run 'pip install galois'.")
        self._build_generator_matrix()

    def _build_generator_matrix(self) -> None:
        k, m = self.data_shards, self.parity_shards
        # Cauchy matrix: C_ij = 1 / (X_i + Y_j) in GF(2^8)
        # Distinct sets X and Y ensure every square submatrix is non-singular
        I = _GF.Identity(k)
        X = [_GF(i) for i in range(m)]
        Y = [_GF(m + j) for j in range(k)]
        P = _GF([[_GF(1) / (X[i] + Y[j]) for j in range(k)] for i in range(m)])
        self.G = np.vstack([I, P])

    def encode_data(self, payload: bytes) -> List[bytes]:
        k, m = self.data_shards, self.parity_shards
        if not payload:
            return [b""] * (k + m)

        shard_size = max(1, (len(payload) + k - 1) // k)
        padded = payload + b"\x00" * (shard_size * k - len(payload))

        data_matrix = np.frombuffer(padded, dtype=np.uint8).reshape((k, shard_size))
        encoded_gf = self.G @ _GF(data_matrix)
        return [bytes(encoded_gf[i]) for i in range(k + m)]

    def recover_missing(
        self,
        available: Sequence[bytes],
        data_shards: int,
        parity_shards: int,
        missing_indexes: Sequence[int],
        expected_len: int | None = None,
    ) -> bytes:
        total_fragments = data_shards + parity_shards
        missing_set = set(missing_indexes)
        surviving_indices = [i for i in range(total_fragments) if i not in missing_set]

        if len(surviving_indices) < data_shards:
            raise ValueError(
                f"Not enough fragments to recover: required {data_shards}, available {len(surviving_indices)}"
            )

        if len(available) != len(surviving_indices):
            raise ValueError("Shard count mismatch with available fragments")

        if not available or len(available[0]) == 0:
            return b""

        shard_size = len(available[0])

        # Pick the first k surviving shards to invert
        chosen_indices = surviving_indices[:data_shards]
        chosen_fragments = [available[surviving_indices.index(idx)] for idx in chosen_indices]

        # Extract the k x k submatrix corresponding to the chosen shards
        G_sub = self.G[chosen_indices, :]
        G_inv = np.linalg.inv(G_sub)

        collected_data = np.frombuffer(b"".join(chosen_fragments), dtype=np.uint8).reshape((data_shards, shard_size))
        reconstructed_gf = G_inv @ _GF(collected_data)
        rebuilt = bytes(reconstructed_gf.reshape(-1))

        if expected_len is not None:
            return rebuilt[:expected_len]
        return rebuilt.rstrip(b"\x00")


def get_codec(
    codec_type: Union[CodecType, str] = CodecType.REED_SOLOMON,
    data_shards: int = 4,
    parity_shards: int = 2,
) -> BaseCodec:
    """Factory to instantiate the requested codec."""
    if isinstance(codec_type, str):
        codec_type = CodecType(codec_type.lower())

    if codec_type == CodecType.REED_SOLOMON:
        return ReedSolomonCodec(data_shards, parity_shards)
    elif codec_type == CodecType.XOR:
        return XORCodec(data_shards, parity_shards)
    else:
        raise ValueError(f"Unsupported codec type: {codec_type}")
