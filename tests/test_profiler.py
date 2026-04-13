"""Tests for logslice.profiler."""

import time
import pytest

from logslice.profiler import (
    ProfileOptions,
    StageTimer,
    PipelineProfile,
    format_profile,
)


class TestProfileOptions:
    def test_disabled_by_default(self):
        opts = ProfileOptions()
        assert opts.enabled is False

    def test_no_output_file_by_default(self):
        opts = ProfileOptions()
        assert opts.output_file is None

    def test_can_enable(self):
        opts = ProfileOptions(enabled=True)
        assert opts.enabled is True


class TestStageTimer:
    def test_elapsed_increases_over_time(self):
        t = StageTimer(name="read")
        time.sleep(0.01)
        assert t.elapsed >= 0.005

    def test_stop_freezes_elapsed(self):
        t = StageTimer(name="read")
        time.sleep(0.01)
        t.stop()
        frozen = t.elapsed
        time.sleep(0.02)
        assert t.elapsed == pytest.approx(frozen, abs=1e-9)

    def test_end_is_none_before_stop(self):
        t = StageTimer(name="filter")
        assert t.end is None


class TestPipelineProfile:
    def test_start_stage_registers_timer(self):
        p = PipelineProfile()
        p.start_stage("read")
        assert "read" in p.timers

    def test_stop_stage_sets_end(self):
        p = PipelineProfile()
        p.start_stage("read")
        time.sleep(0.005)
        p.stop_stage("read")
        assert p.timers["read"].end is not None

    def test_stop_nonexistent_stage_is_noop(self):
        p = PipelineProfile()
        p.stop_stage("ghost")  # should not raise

    def test_total_elapsed_zero_with_no_timers(self):
        p = PipelineProfile()
        assert p.total_elapsed() == 0.0

    def test_total_elapsed_covers_all_stages(self):
        p = PipelineProfile()
        p.start_stage("a")
        time.sleep(0.01)
        p.stop_stage("a")
        p.start_stage("b")
        time.sleep(0.01)
        p.stop_stage("b")
        assert p.total_elapsed() >= 0.015

    def test_as_dict_keys(self):
        p = PipelineProfile(line_count=100)
        p.start_stage("read")
        p.stop_stage("read")
        d = p.as_dict()
        assert set(d.keys()) == {"total_elapsed_s", "line_count", "lines_per_second", "stages"}

    def test_as_dict_line_count(self):
        p = PipelineProfile(line_count=42)
        p.start_stage("x")
        p.stop_stage("x")
        assert p.as_dict()["line_count"] == 42

    def test_lines_per_second_zero_when_no_elapsed(self):
        p = PipelineProfile(line_count=0)
        assert p.as_dict()["lines_per_second"] == 0


class TestFormatProfile:
    def test_contains_total_time(self):
        p = PipelineProfile(line_count=10)
        p.start_stage("read")
        p.stop_stage("read")
        out = format_profile(p)
        assert "Total time" in out

    def test_contains_stage_name(self):
        p = PipelineProfile()
        p.start_stage("filter")
        p.stop_stage("filter")
        out = format_profile(p)
        assert "filter" in out

    def test_contains_throughput(self):
        p = PipelineProfile(line_count=500)
        p.start_stage("s")
        p.stop_stage("s")
        out = format_profile(p)
        assert "Throughput" in out
