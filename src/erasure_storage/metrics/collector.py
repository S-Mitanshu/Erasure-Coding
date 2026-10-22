from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict

try:
    import psutil
except ImportError:
    psutil = None


@dataclass
class PhaseMetrics:
    phase_name: str
    duration_s: float = 0.0
    bytes_transferred: int = 0
    cpu_percent: float = 0.0
    memory_start_mb: float = 0.0
    memory_end_mb: float = 0.0
    memory_peak_mb: float = 0.0


class MetricsCollector:
    """Collects timing, I/O bandwidth, CPU utilization, and memory metrics for experiments."""

    def __init__(self):
        self.process = psutil.Process(os.getpid()) if psutil is not None else None
        self.phases: Dict[str, PhaseMetrics] = {}

    def _get_memory_mb(self) -> float:
        if self.process is None:
            return 0.0
        try:
            return self.process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0

    def measure(self, phase_name: str, bytes_transferred: int = 0):
        """Context manager to measure latency, CPU, and memory for an operation phase."""
        collector = self

        class _PhaseContext:
            def __enter__(self):
                self.start_mem = collector._get_memory_mb()
                if collector.process is not None:
                    # Prime CPU percent measurement
                    try:
                        collector.process.cpu_percent(interval=None)
                    except Exception:
                        pass
                self.start_time = time.perf_counter()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.perf_counter() - self.start_time
                end_mem = collector._get_memory_mb()
                cpu = 0.0
                if collector.process is not None:
                    try:
                        cpu = collector.process.cpu_percent(interval=None)
                    except Exception:
                        cpu = 0.0

                collector.phases[phase_name] = PhaseMetrics(
                    phase_name=phase_name,
                    duration_s=round(duration, 6),
                    bytes_transferred=bytes_transferred,
                    cpu_percent=round(cpu, 2),
                    memory_start_mb=round(self.start_mem, 2),
                    memory_end_mb=round(end_mem, 2),
                    memory_peak_mb=round(max(self.start_mem, end_mem), 2),
                )

        return _PhaseContext()

    def record_manual(
        self,
        phase_name: str,
        duration_s: float,
        bytes_transferred: int = 0,
        cpu_percent: float = 0.0,
        peak_memory_mb: float = 0.0,
    ) -> None:
        mem = self._get_memory_mb() if peak_memory_mb == 0.0 else peak_memory_mb
        self.phases[phase_name] = PhaseMetrics(
            phase_name=phase_name,
            duration_s=round(duration_s, 6),
            bytes_transferred=bytes_transferred,
            cpu_percent=round(cpu_percent, 2),
            memory_start_mb=round(mem, 2),
            memory_end_mb=round(mem, 2),
            memory_peak_mb=round(mem, 2),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            name: {
                "duration_s": m.duration_s,
                "bytes_transferred": m.bytes_transferred,
                "cpu_percent": m.cpu_percent,
                "memory_start_mb": m.memory_start_mb,
                "memory_end_mb": m.memory_end_mb,
                "memory_peak_mb": m.memory_peak_mb,
            }
            for name, m in self.phases.items()
        }
