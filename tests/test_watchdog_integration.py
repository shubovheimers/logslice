"""Integration tests for the watchdog tail pipeline."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from logslice.watchdog import WatchOptions, tail_file
from logslice.filter import filter_by_level


def _append(path: Path, text: str) -> None:
    with open(path, "a") as fh:
        fh.write(text + "\n")


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "live.log"
    p.write_text("")
    return p


class TestWatchIntegration:
    def test_multiple_levels_all_received(self, log_file: Path):
        opts = WatchOptions(poll_interval=0.05, max_idle=0.4)
        lines_to_write = [
            "2024-06-01T12:00:01 INFO  service started",
            "2024-06-01T12:00:02 WARN  memory high",
            "2024-06-01T12:00:03 ERROR disk failure",
        ]

        def writer():
            time.sleep(0.05)
            for ln in lines_to_write:
                _append(log_file, ln)
                time.sleep(0.02)

        t = threading.Thread(target=writer, daemon=True)
        t.start()
        results = list(tail_file(log_file, opts))
        t.join()
        assert len(results) == 3
        levels = [r.level for r in results]
        assert "INFO" in levels
        assert "WARN" in levels
        assert "ERROR" in levels

    def test_filter_by_level_on_tailed_lines(self, log_file: Path):
        opts = WatchOptions(poll_interval=0.05, max_idle=0.4)

        def writer():
            time.sleep(0.05)
            _append(log_file, "2024-06-01T12:00:01 INFO  heartbeat")
            _append(log_file, "2024-06-01T12:00:02 ERROR crash detected")
            time.sleep(0.02)

        t = threading.Thread(target=writer, daemon=True)
        t.start()
        all_lines = list(tail_file(log_file, opts))
        t.join()
        errors = list(filter_by_level(iter(all_lines), levels={"ERROR"}))
        assert len(errors) == 1
        assert errors[0].level == "ERROR"

    def test_raw_text_preserved(self, log_file: Path):
        opts = WatchOptions(poll_interval=0.05, max_idle=0.3)
        raw = "2024-06-01T09:00:00 DEBUG raw text preserved"

        def writer():
            time.sleep(0.05)
            _append(log_file, raw)

        t = threading.Thread(target=writer, daemon=True)
        t.start()
        results = list(tail_file(log_file, opts))
        t.join()
        assert results[0].raw == raw
