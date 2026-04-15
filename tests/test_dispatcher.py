"""Tests for logslice.dispatcher and logslice.cli_dispatcher."""
from __future__ import annotations

import argparse
from datetime import datetime
from typing import List

import pytest

from logslice.dispatcher import DispatchOptions, Dispatcher
from logslice.cli_dispatcher import add_dispatcher_args, dispatcher_opts_from_args
from logslice.parser import LogLine


def make_line(text: str = "hello") -> LogLine:
    return LogLine(
        raw=text,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level="INFO",
        message=text,
    )


# ---------------------------------------------------------------------------
# DispatchOptions
# ---------------------------------------------------------------------------

class TestDispatchOptions:
    def test_defaults(self):
        opts = DispatchOptions()
        assert opts.stop_on_first_match is False
        assert opts.default_channel == "default"

    def test_custom_values(self):
        opts = DispatchOptions(stop_on_first_match=True, default_channel="errors")
        assert opts.stop_on_first_match is True
        assert opts.default_channel == "errors"


# ---------------------------------------------------------------------------
# Dispatcher.register / channels
# ---------------------------------------------------------------------------

class TestDispatcherRegister:
    def test_register_adds_channel(self):
        d = Dispatcher()
        d.register("ch", lambda l: None)
        assert "ch" in d.channels()

    def test_unregister_removes_channel(self):
        d = Dispatcher()
        d.register("ch", lambda l: None)
        d.unregister("ch")
        assert "ch" not in d.channels()

    def test_unregister_unknown_is_safe(self):
        d = Dispatcher()
        d.unregister("nope")  # must not raise


# ---------------------------------------------------------------------------
# Dispatcher.dispatch
# ---------------------------------------------------------------------------

class TestDispatch:
    def test_calls_handler(self):
        received: List[LogLine] = []
        d = Dispatcher()
        d.register("default", received.append)
        line = make_line()
        d.dispatch(line)
        assert received == [line]

    def test_returns_handler_count(self):
        d = Dispatcher()
        d.register("default", lambda l: None)
        d.register("default", lambda l: None)
        assert d.dispatch(make_line()) == 2

    def test_no_handlers_returns_zero(self):
        d = Dispatcher()
        assert d.dispatch(make_line()) == 0

    def test_named_channel(self):
        received: List[LogLine] = []
        d = Dispatcher()
        d.register("errors", received.append)
        line = make_line()
        d.dispatch(line, channel="errors")
        assert received == [line]

    def test_stop_on_first_match(self):
        calls: List[int] = []
        opts = DispatchOptions(stop_on_first_match=True)
        d = Dispatcher(options=opts)
        d.register("default", lambda l: calls.append(1))
        d.register("default", lambda l: calls.append(2))
        count = d.dispatch(make_line())
        assert count == 1
        assert calls == [1]


# ---------------------------------------------------------------------------
# Dispatcher.dispatch_all
# ---------------------------------------------------------------------------

class TestDispatchAll:
    def test_yields_all_lines(self):
        d = Dispatcher()
        lines = [make_line(f"line{i}") for i in range(4)]
        result = list(d.dispatch_all(iter(lines)))
        assert result == lines

    def test_handler_called_for_each(self):
        received: List[LogLine] = []
        d = Dispatcher()
        d.register("default", received.append)
        lines = [make_line(f"l{i}") for i in range(3)]
        list(d.dispatch_all(iter(lines)))
        assert received == lines


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_dispatcher_args(p)
    return p


class TestCliDispatcher:
    def test_default_channel(self):
        args = _make_parser().parse_args([])
        assert args.dispatch_channel == "default"

    def test_custom_channel(self):
        args = _make_parser().parse_args(["--dispatch-channel", "alerts"])
        assert args.dispatch_channel == "alerts"

    def test_stop_first_default_false(self):
        args = _make_parser().parse_args([])
        assert args.dispatch_stop_first is False

    def test_stop_first_flag(self):
        args = _make_parser().parse_args(["--dispatch-stop-first"])
        assert args.dispatch_stop_first is True

    def test_opts_from_args_maps_correctly(self):
        args = _make_parser().parse_args(
            ["--dispatch-channel", "warn", "--dispatch-stop-first"]
        )
        opts = dispatcher_opts_from_args(args)
        assert opts.default_channel == "warn"
        assert opts.stop_on_first_match is True
