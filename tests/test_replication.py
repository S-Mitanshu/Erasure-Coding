from erasure_storage.replication.replication_runner import run_replication_experiment


def test_replication_experiment_single_failure():
    payload = b"Testing 3-way replication with one failed node." * 10
    report = run_replication_experiment(payload, replication_factor=3, node_count=6, failed_nodes=[0])

    assert report["recovery_success"] is True
    assert report["storage_overhead_ratio"] == 3.0
    assert report["replicas_surviving"] == 2
    assert report["replicas_stored"] == 3
    assert report["original_hash"] == report["recovered_hash"]
    assert report["metrics"]["recovery"]["bytes_transferred"] == len(payload)


def test_replication_experiment_dual_failure():
    payload = b"Testing 3-way replication surviving dual node failure." * 5
    # Nodes 0 and 1 fail; node 2 survives
    report = run_replication_experiment(payload, replication_factor=3, node_count=6, failed_nodes=[0, 1])

    assert report["recovery_success"] is True
    assert report["replicas_surviving"] == 1


def test_replication_experiment_all_replicas_failed():
    payload = b"Testing catastrophic loss when all replica nodes fail."
    # Nodes 0, 1, 2 all fail
    report = run_replication_experiment(payload, replication_factor=3, node_count=6, failed_nodes=[0, 1, 2])

    assert report["recovery_success"] is False
    assert report["replicas_surviving"] == 0
