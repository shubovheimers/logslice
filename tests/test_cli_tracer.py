"""Tests for logslice.cli_tracer."""
from __future__ import annotations

import argparse

import pytest

from logslice.cli_tracer import add_trace_args, trace_opts_from_args
from logslice.tracer import TraceOptions


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_trace_args(p)
    return p


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"trace_field": None, "trace_pattern": None, "trace_id": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddTraceArgs:
    def test_trace_field_default_none(self):
        p = _make_parser()
        ns = p.parse_args([])
        assert ns.trace_field is None

    def test_trace_pattern_default_none(self):
        p = _make_parser()
        ns = p.parse_args([])
        assert ns.trace_pattern is None

    def test_trace_id_default_none(self):
        p = _make_parser()
        ns = p.parse_args([])
        assert ns.trace_id is None

    def test_trace_field_parsed(self):
        p = _make_parser()
        ns = p.parse_args(["--trace-field", "request_id"])
        assert ns.trace_field == "request_id"

    def test_trace_pattern_parsed(self):
        p = _make_parser()
        ns = p.parse_args(["--trace-pattern", r"req=(?P<trace_id>\w+)"])
        assert ns.trace_pattern == r"req=(?P<trace_id>\w+)"

    def test_trace_id_parsed(self):
        p = _make_parser()
        ns = p.parse_args(["--trace-id", "abc123"])
        assert ns.trace_id == "abc123"


class TestTraceOptsFromArgs:
    def test_defaults_produce_inactive_opts(self):
        opts = trace_opts_from_args(_make_args())
        assert not opts.enabled
        assert not opts.is_active()

    def test_field_enables(self):
        opts = trace_opts_from_args(_make_args(trace_field="tid"))
        assert opts.enabled
        assert opts.field == "tid"

    def test_pattern_enables(self):
        opts = trace_opts_from_args(_make_args(trace_pattern=r"req=(?P<trace_id>\w+)"))
        assert opts.enabled
        assert opts.pattern == r"req=(?P<trace_id>\w+)"

    def test_trace_id_forwarded(self):
        opts = trace_opts_from_args(_make_args(trace_field="tid", trace_id="xyz"))
        assert opts.trace_id == "xyz"

    def test_no_field_or_pattern_not_enabled(self):
        opts = trace_opts_from_args(_make_args(trace_id="only-id"))
        assert not opts.enabled
