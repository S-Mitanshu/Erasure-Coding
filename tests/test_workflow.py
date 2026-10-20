import itertools
from pathlib import Path

from erasure_storage.codec.rs_codec import CodecType, ReedSolomonCodec, XORCodec, get_codec
from erasure_storage.coordinator.coordinator import Coordinator
from erasure_storage.experiment_runner import run_experiment
from erasure_storage.recovery.recovery_manager import RecoveryManager
from erasure_storage.storage.node_store import NodeStore


def test_encode_decode_round_trip():
    codec = ReedSolomonCodec(data_shards=4, parity_shards=2)
    payload = b"Learn from failure, rebuild with parity."

    fragments = codec.encode_data(payload)
    missing = [5, 3]
    available = [fragment for idx, fragment in enumerate(fragments) if idx not in missing]
    recovered = codec.recover_missing(available, data_shards=4, parity_shards=2, missing_indexes=missing)

    assert recovered == payload


def test_xor_codec_round_trip():
    codec = XORCodec(data_shards=4, parity_shards=2)
    payload = b"Baseline XOR parity recovery test."

    fragments = codec.encode_data(payload)
    missing = [4]
    available = [fragment for idx, fragment in enumerate(fragments) if idx not in missing]
    recovered = codec.recover_missing(available, data_shards=4, parity_shards=2, missing_indexes=missing)

    assert recovered == payload


def test_reed_solomon_all_two_failure_combinations():
    codec = ReedSolomonCodec(data_shards=4, parity_shards=2)
    payload = b"Testing true MDS property: any 4 of 6 shards reconstruct the payload!"

    fragments = codec.encode_data(payload)
    assert len(fragments) == 6

    # Test every possible pair of missing shards (15 combinations)
    for missing_pair in itertools.combinations(range(6), 2):
        missing = list(missing_pair)
        available = [fragment for idx, fragment in enumerate(fragments) if idx not in missing]
        recovered = codec.recover_missing(
            available,
            data_shards=4,
            parity_shards=2,
            missing_indexes=missing,
            expected_len=len(payload),
        )
        assert recovered == payload, f"Failed on missing pair: {missing}"


def test_coordinator_and_recovery_process():
    payload = b"A file to distribute across nodes safely."
    coordinator = Coordinator(data_shards=4, parity_shards=2, node_count=6)

    file_id = coordinator.ingest_file(payload)
    placement = coordinator.assign_fragments(file_id)

    assert len(placement) == 6
    assert all(fragment.file_id == file_id for fragment in placement)

    node_store = NodeStore(node_count=6)
    node_store.store_fragments(placement)

    failed_nodes = [2, 5]
    node_store.fail_nodes(failed_nodes)
    manager = RecoveryManager(node_store, data_shards=4, parity_shards=2)

    recovered = manager.recover_file(file_id, payload)
    assert recovered == payload
    assert manager.last_metrics["recovery_success"] is True
    assert manager.last_metrics["failed_nodes"] == failed_nodes


def test_experiment_runner_with_codecs():
    payload = b"Testing experiment runner with both codec options."
    
    # Run with Reed-Solomon
    rs_report = run_experiment(payload, data_shards=4, parity_shards=2, failed_nodes=[1, 4], codec_type=CodecType.REED_SOLOMON)
    assert rs_report["recovery_success"] is True
    assert rs_report["codec"] == "reed_solomon"

    # Run with XOR
    xor_report = run_experiment(payload, data_shards=4, parity_shards=2, failed_nodes=[1], codec_type=CodecType.XOR)
    assert xor_report["recovery_success"] is True
    assert xor_report["codec"] == "xor"


def test_checksum_verification_logic():
    payload = b"checksum verification"
    coordinator = Coordinator(data_shards=3, parity_shards=2, node_count=5)
    file_id = coordinator.ingest_file(payload)

    checksum = coordinator.file_checksums[file_id]
    assert checksum.startswith("sha256:")
    assert coordinator.verify_file(file_id, payload) is True
    assert coordinator.verify_file(file_id, b"wrong") is False


def test_experiment_config_file_exists():
    assert Path("configs").exists()
    assert Path("configs/experiment.yaml").exists()
