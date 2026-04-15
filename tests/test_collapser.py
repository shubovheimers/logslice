"""Tests for logslice.collapser."""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.collapser import CollapseOptions, collapse_lines


def make_line(text: str, level: str = "INFO") -> LogLine:
    return LogLine(
        raw=text,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=text,
    )


def collect(lines) -> List[LogLine]:
    return list(lines)


# ---------------------------------------------------------------------------
# CollapseOptions validation
# ---------------------------------------------------------------------------

class TestCollapseOptions:
    def test_defaults_disabled(self):
        opts = CollapseOptions()
        assert opts.enabled is False

    def test_min_repeats_default(self):
        opts = CollapseOptions()
        assert opts.min_repeats == 2

    def test_min_repeats_below_2_raises(self):
        with pytest.raises(ValueError):
            CollapseOptions(enabled=True, min_repeats=1)

    def test_custom_label(self):
        opts = CollapseOptions(enabled=True, label="(x{n})")
        assert opts.label == "(x{n})"


# ---------------------------------------------------------------------------
# Passthrough when disabled
# ---------------------------------------------------------------------------

class TestCollapseDisabled:
    def test_none_opts_passthrough(self):
        lines = [make_line("hello"), make_line("hello"), make_line("hello")]
        result = collect(collapse_lines(lines, opts=None))
        assert len(result) == 3

    def test_disabled_opts_passthrough(self):
        opts = CollapseOptions(enabled=False)
        lines = [make_line("a"), make_line("a")]
        result = collect(collapse_lines(lines, opts))
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Collapsing behaviour
# ---------------------------------------------------------------------------

class TestCollapseEnabled:
    def _opts(self, **kw) -> CollapseOptions:
        return CollapseOptions(enabled=True, **kw)

    def test_no_repeats_unchanged(self):
        opts = self._opts()
        lines = [make_line("a"), make_line("b"), make_line("c")]
        result = collect(collapse_lines(lines, opts))
        assert len(result) == 3
        assert result[0].raw == "a"

    def test_single_repeat_below_min_unchanged(self):
        # run of 2 with min_repeats=3 → no annotation
        opts = self._opts(min_repeats=3)
        lines = [make_line("x"), make_line("x")]
        result = collect(collapse_lines(lines, opts))
        assert len(result) == 1
        assert "repeated" not in result[0].raw

    def test_run_of_two_collapsed(self):
        opts = self._opts()
        lines = [make_line("msg"), make_line("msg")]
        result = collect(collapse_lines(lines, opts))
        assert len(result) == 1
        assert "2x" in result[0].raw

    def test_run_of_five_collapsed(self):
        opts = self._opts()
        lines = [make_line("boom")] * 5
        result = collect(collapse_lines(lines, opts))
        assert len(result) == 1
        assert "5x" in result[0].raw

    def test_interleaved_runs(self):
        opts = self._opts()
        lines = (
            [make_line("a")] * 3
            + [make_line("b")] * 2
            + [make_line("c")]
        )
        result = collect(collapse_lines(lines, opts))
        assert len(result) == 3
        assert "3x" in result[0].raw
        assert "2x" in result[1].raw
        assert "repeated" not in result[2].raw

    def test_custom_label_used(self):
        opts = self._opts(label="(seen {n} times)")
        lines = [make_line("z"), make_line("z"), make_line("z")]
        result = collect(collapse_lines(lines, opts))
        assert "(seen 3 times)" in result[0].raw

    def test_empty_input_yields_nothing(self):
        opts = self._opts()
        assert collect(collapse_lines([], opts)) == []

    def test_timestamp_preserved(self):
        opts = self._opts()
        ts = datetime(2024, 6, 15, 8, 30, 0)
        lines = [LogLine(raw="err", timestamp=ts, level="ERROR", message="err")] * 2
        result = collect(collapse_lines(lines, opts))
        assert result[0].timestamp == ts
