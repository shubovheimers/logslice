"""Tests for logslice.replayer and logslice.cli_replayer."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.replayer import ReplayOptions, replay_lines, _delta_seconds
from logslice.cli_replayer import add_replay_args, replay_opts_from_args


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dt(hour: int, minute: int, second: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, second, tzinfo=timezone.utc)


def make_line(text: str, ts: datetime | None = None) -> LogLine:
    return LogLine(raw=text, timestamp=ts, level=None, message=text)


def _collect(lines, opts, delays: List[float]) -> List[LogLine]:
    """Collect replayed lines, recording sleep calls into *delays*."""
    def fake_sleep(secs: float) -> None:
        delays.append(secs)

    return list(replay_lines(lines, opts, _sleep=fake_sleep))


# ---------------------------------------------------------------------------
# ReplayOptions validation
# ---------------------------------------------------------------------------

class TestReplayOptions:
    def test_defaults_not_enabled(self):
        opts = ReplayOptions()
        assert opts.enabled is False

    def test_zero_speed_raises(self):
        with pytest.raises(ValueError, match="speed"):
            ReplayOptions(enabled=True, speed=0.0)

    def test_negative_speed_raises(self):
        with pytest.raises(ValueError, match="speed"):
            ReplayOptions(enabled=True, speed=-1.0)

    def test_negative_max_delay_raises(self):
        with pytest.raises(ValueError, match="max_delay"):
            ReplayOptions(enabled=True, max_delay=-0.1)


# ---------------------------------------------------------------------------
# _delta_seconds
# ---------------------------------------------------------------------------

def test_delta_seconds_positive():
    assert _delta_seconds(_dt(0, 0, 0), _dt(0, 0, 5)) == pytest.approx(5.0)


def test_delta_seconds_zero_for_equal():
    assert _delta_seconds(_dt(0, 0, 0), _dt(0, 0, 0)) == pytest.approx(0.0)


def test_delta_seconds_clamps_negative_to_zero():
    assert _delta_seconds(_dt(0, 1, 0), _dt(0, 0, 0)) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# replay_lines
# ---------------------------------------------------------------------------

def test_disabled_yields_all_immediately():
    lines = [make_line("a"), make_line("b")]
    delays: List[float] = []
    result = _collect(lines, ReplayOptions(enabled=False), delays)
    assert [l.raw for l in result] == ["a", "b"]
    assert delays == []


def test_none_opts_yields_all_immediately():
    lines = [make_line("a")]
    delays: List[float] = []
    result = _collect(lines, None, delays)
    assert len(result) == 1
    assert delays == []


def test_sleep_called_for_gap():
    lines = [
        make_line("first", _dt(0, 0, 0)),
        make_line("second", _dt(0, 0, 4)),
    ]
    delays: List[float] = []
    opts = ReplayOptions(enabled=True, speed=1.0, max_delay=10.0)
    _collect(lines, opts, delays)
    assert delays == [pytest.approx(4.0)]


def test_speed_divides_delay():
    lines = [
        make_line("a", _dt(0, 0, 0)),
        make_line("b", _dt(0, 0, 10)),
    ]
    delays: List[float] = []
    opts = ReplayOptions(enabled=True, speed=2.0, max_delay=60.0)
    _collect(lines, opts, delays)
    assert delays == [pytest.approx(5.0)]


def test_max_delay_caps_sleep():
    lines = [
        make_line("a", _dt(0, 0, 0)),
        make_line("b", _dt(0, 1, 0)),   # 60 s gap
    ]
    delays: List[float] = []
    opts = ReplayOptions(enabled=True, speed=1.0, max_delay=3.0)
    _collect(lines, opts, delays)
    assert delays == [pytest.approx(3.0)]


def test_no_sleep_for_lines_without_timestamp():
    lines = [make_line("a"), make_line("b"), make_line("c")]
    delays: List[float] = []
    opts = ReplayOptions(enabled=True)
    _collect(lines, opts, delays)
    assert delays == []


def test_real_time_ignores_speed():
    lines = [
        make_line("a", _dt(0, 0, 0)),
        make_line("b", _dt(0, 0, 6)),
    ]
    delays: List[float] = []
    opts = ReplayOptions(enabled=True, speed=100.0, max_delay=60.0, real_time=True)
    _collect(lines, opts, delays)
    assert delays == [pytest.approx(6.0)]


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_replay_args(p)
    return p


class TestAddReplayArgs:
    def test_replay_flag_defaults_false(self):
        args = _make_parser().parse_args([])
        assert args.replay is False

    def test_replay_flag_true_when_set(self):
        args = _make_parser().parse_args(["--replay"])
        assert args.replay is True

    def test_speed_default(self):
        args = _make_parser().parse_args([])
        assert args.replay_speed == pytest.approx(1.0)

    def test_custom_speed(self):
        args = _make_parser().parse_args(["--replay-speed", "4.0"])
        assert args.replay_speed == pytest.approx(4.0)

    def test_max_delay_default(self):
        args = _make_parser().parse_args([])
        assert args.replay_max_delay == pytest.approx(5.0)

    def test_real_time_default_false(self):
        args = _make_parser().parse_args([])
        assert args.replay_real_time is False


class TestReplayOptsFromArgs:
    def test_returns_none_when_not_requested(self):
        args = _make_parser().parse_args([])
        assert replay_opts_from_args(args) is None

    def test_returns_options_when_enabled(self):
        args = _make_parser().parse_args(["--replay", "--replay-speed", "2.0"])
        opts = replay_opts_from_args(args)
        assert opts is not None
        assert opts.enabled is True
        assert opts.speed == pytest.approx(2.0)

    def test_real_time_propagated(self):
        args = _make_parser().parse_args(["--replay", "--replay-real-time"])
        opts = replay_opts_from_args(args)
        assert opts is not None
        assert opts.real_time is True
