"""Performance profiling utilities for logslice pipeline runs."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ProfileOptions:
    enabled: bool = False
    output_file: Optional[str] = None


@dataclass
class StageTimer:
    name: str
    start: float = field(default_factory=time.perf_counter)
    end: Optional[float] = None

    def stop(self) -> None:
        self.end = time.perf_counter()

    @property
    def elapsed(self) -> float:
        if self.end is None:
            return time.perf_counter() - self.start
        return self.end - self.start


@dataclass
class PipelineProfile:
    timers: Dict[str, StageTimer] = field(default_factory=dict)
    line_count: int = 0

    def start_stage(self, name: str) -> StageTimer:
        timer = StageTimer(name=name)
        self.timers[name] = timer
        return timer

    def stop_stage(self, name: str) -> None:
        if name in self.timers:
            self.timers[name].stop()

    def total_elapsed(self) -> float:
        if not self.timers:
            return 0.0
        starts = [t.start for t in self.timers.values()]
        ends = [t.end for t in self.timers.values() if t.end is not None]
        if not ends:
            return 0.0
        return max(ends) - min(starts)

    def slowest_stage(self) -> Optional[str]:
        """Return the name of the stage with the highest elapsed time, or None if no stages exist."""
        if not self.timers:
            return None
        return max(self.timers, key=lambda name: self.timers[name].elapsed)

    def as_dict(self) -> dict:
        return {
            "total_elapsed_s": round(self.total_elapsed(), 6),
            "line_count": self.line_count,
            "lines_per_second": (
                round(self.line_count / self.total_elapsed(), 2)
                if self.total_elapsed() > 0
                else 0
            ),
            "stages": {
                name: round(t.elapsed, 6)
                for name, t in self.timers.items()
            },
        }


def format_profile(profile: PipelineProfile) -> str:
    d = profile.as_dict()
    slowest = profile.slowest_stage()
    lines = [
        f"Total time : {d['total_elapsed_s']:.4f}s",
        f"Lines      : {d['line_count']}",
        f"Throughput : {d['lines_per_second']} lines/s",
        f"Slowest    : {slowest if slowest else 'n/a'}",
        "Stages:",
    ]
    for stage, elapsed in d["stages"].items():
        lines.append(f"  {stage:<20} {elapsed:.6f}s")
    return "\n".join(lines)
