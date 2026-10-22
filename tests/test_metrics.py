import time
from erasure_storage.metrics.collector import MetricsCollector
from erasure_storage.experiment_runner import run_experiment


def test_metrics_collector_measure_phase():
    collector = MetricsCollector()
    with collector.measure("test_phase", bytes_transferred=1024):
        time.sleep(0.01)

    result = collector.to_dict()
    assert "test_phase" in result
    phase = result["test_phase"]
    assert phase["duration_s"] >= 0.008
    assert phase["bytes_transferred"] == 1024
    assert "cpu_percent" in phase
    assert "memory_peak_mb" in phase


def test_experiment_report_contains_full_metrics():
    payload = b"Payload for testing metrics integration in reports." * 20
    report = run_experiment(payload, data_shards=4, parity_shards=2, failed_nodes=[1])

    assert "metrics" in report
    assert "encoding" in report["metrics"]
    assert "recovery" in report["metrics"]
    assert report["storage_overhead_ratio"] > 1.0
    assert report["metrics"]["encoding"]["bytes_transferred"] > len(payload)
    assert report["metrics"]["recovery"]["bytes_transferred"] > 0
    assert report["metrics"]["recovery"]["duration_s"] >= 0
