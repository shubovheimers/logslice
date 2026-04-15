"""Integration tests: trace_lines wired through cli_tracer helpers."""
from __future__ import annotations

import argparse
from datetime import datetime
from typing import Optional

from logslice.parser import LogLine
from logslice.cli_tracer import add_trace_args, trace_opts_from_args
from logslice.tracer import trace_lines


def _line(raw: str, extra: Optional[dict] = None) -> LogLine:
    return LogLine(
        raw=raw,
        timestamp=datetime(2024, 6, 1, 0, 0, 0),
        level="DEBUG",
        message=raw,
        extra=extra or {},
    )


def _parse(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    add_trace_args(p)
    return p.parse_args(argv)


class TestTracerIntegration:
    def test_field_filter_end_to_end(self):
        ns = _parse(["--trace-field", "tid", "--trace-id", "req-1"])
        opts = trace_opts_from_args(ns)
        lines = [
            _line("start", extra={"tid": "req-1"}),
            _line("noise", extra={"tid": "req-2"}),
            _line("end", extra={"tid": "req-1"}),
        ]
        result = list(trace_lines(lines, opts))
        assert len(result) == 2
        assert result[0].raw == "start"
        assert result[1].raw == "end"

    def test_pattern_filter_end_to_end(self):
        ns = _parse(["--trace-pattern", r"trace=(?P<trace_id>[a-z0-9-]+)", "--trace-id", "abc"])
        opts = trace_opts_from_args(ns)
        lines = [
            _line("trace=abc processing"),
            _line("trace=def other"),
            _line("trace=abc done"),
            _line("no trace here"),
        ]
        result = list(trace_lines(lines, opts))
        assert len(result) == 2
        assert "abc" in result[0].raw
        assert "abc" in result[1].raw

    def test_collect_all_trace_ids_no_filter(self):
        ns = _parse(["--trace-field", "tid"])
        opts = trace_opts_from_args(ns)
        lines = [
            _line("a", extra={"tid": "t1"}),
            _line("b", extra={"tid": "t2"}),
            _line("c"),  # no tid
        ]
        result = list(trace_lines(lines, opts))
        assert len(result) == 2

    def test_inactive_opts_passthrough_all_lines(self):
        ns = _parse([])
        opts = trace_opts_from_args(ns)
        lines = [_line("x"), _line("y"), _line("z")]
        assert list(trace_lines(lines, opts)) == lines
