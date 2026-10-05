import json
from pathlib import Path

from erasure_storage.experiment_runner import run_experiment


def test_run_experiment_creates_report_and_recovery_summary(tmp_path):
    payload = b"A controlled demo for fault-tolerant storage."
    report = run_experiment(payload, data_shards=4, parity_shards=2, node_count=6, failed_nodes=[2, 5], output_dir=tmp_path)

    assert report["recovery_success"] is True
    assert report["failed_nodes"] == [2, 5]
    assert report["storage_nodes"] == 6
    assert report["input_size_bytes"] == len(payload)
    assert report["recovered_hash"]
    assert (tmp_path / "experiment_report.json").exists()
    assert (tmp_path / "experiment_report.md").exists()

    json_data = json.loads((tmp_path / "experiment_report.json").read_text())
    assert json_data["recovery_success"] is True
