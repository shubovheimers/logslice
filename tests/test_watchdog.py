"""Tests for logslice.watchdog."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from logslice.watchdog import WatchOptions, tail_file
from logslice.parser import LogLine


# ---------------------------------------------------------------------------
# WatchOptions
# ---------------------------------------------------------------------------

class TestWatchOptions:
    def test_defaults(self):
        opts = WatchOptions()
        assert opts.enabled is False
        assert opts.poll_interval == 0.5
        assert opts.max_idle is None
        assert opts.follow_rotated is False

    def test_invalid_poll_interval_raises(self):
        with pytest.raises(ValueError, match="poll_interval"):
            WatchOptions(poll_interval=0)

    def test_negative_poll_interval_raises(self):
        with pytest.raises(ValueError):
            WatchOptions(poll_interval=-1.0)

    def test_custom_values(self):
        opts = WatchOptions(enabled=True, poll_interval=1.0, max_idle=30.0)
        assert opts.enabled is True
        assert opts.poll_interval == 1.0
        assert opts.max_idle == 30.0


# ---------------------------------------------------------------------------
# tail_file
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text("")  # create empty file
    return p


def _append(path: Path, text: str) -> None:
    with open(path, "a") as fh:
        fh.write(text + "\n")


class TestTailFile:
    def test_yields_new_lines(self, log_file: Path):
        opts = WatchOptions(poll_interval=0.05, max_idle=0.3)
        # Write lines *after* tail_file has sought to EOF
        import threading

        def writer():
            time.sleep(0.05)
            _append(log_file, "2024-01-01T00:00:01 INFO hello")
            _append(log_file, "2024-01-01T00:00:02 ERROR boom")

        t = threading.Thread(target=writer, daemon=True)
        t.start()
        results = list(tail_file(log_file, opts))
        t.join()
        assert len(results) == 2
        assert all(isinstance(r, LogLine) for r in results)

    def test_returns_log_line_objects(self, log_file: Path):
        opts = WatchOptions(poll_interval=0.05, max_idle=0.2)
        import threading

        def writer():
            time.sleep(0.05)
            _append(log_file, "2024-01-01T10:00:00 WARN disk full")

        t = threading.Thread(target=writer, daemon=True)
        t.start()
        results = list(tail_file(log_file, opts))
        t.join()
        assert results[0].raw == "2024-01-01T10:00:00 WARN disk full"

    def test_exits_after_max_idle(self, log_file: Path):
        opts = WatchOptions(poll_interval=0.05, max_idle=0.15)
        start = time.monotonic()
        results = list(tail_file(log_file, opts))
        elapsed = time.monotonic() - start
        assert results == []
        assert elapsed < 1.0  # should finish quickly

    def test_pre_existing_content_skipped(self, log_file: Path):
        """Lines already in the file before watching are not emitted."""
        _append(log_file, "2024-01-01T00:00:00 INFO pre-existing")
        opts = WatchOptions(poll_interval=0.05, max_idle=0.15)
        results = list(tail_file(log_file, opts))
        assert results == []
