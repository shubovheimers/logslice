"""CLI helpers for the --profile flag in logslice."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from logslice.profiler import PipelineProfile, ProfileOptions, format_profile


def add_profile_args(parser: argparse.ArgumentParser) -> None:
    """Attach profiling arguments to an existing argument parser."""
    group = parser.add_argument_group("profiling")
    group.add_argument(
        "--profile",
        action="store_true",
        default=False,
        help="Print pipeline performance stats after processing.",
    )
    group.add_argument(
        "--profile-out",
        metavar="FILE",
        default=None,
        help="Write profile output to FILE instead of stderr.",
    )


def profile_opts_from_args(args: argparse.Namespace) -> ProfileOptions:
    """Build a ProfileOptions from parsed CLI arguments."""
    return ProfileOptions(
        enabled=getattr(args, "profile", False),
        output_file=getattr(args, "profile_out", None),
    )


def emit_profile(
    profile: PipelineProfile,
    opts: ProfileOptions,
) -> None:
    """Write formatted profile output to the configured destination."""
    if not opts.enabled:
        return
    text = format_profile(profile) + "\n"
    if opts.output_file:
        try:
            with open(opts.output_file, "w", encoding="utf-8") as fh:
                fh.write(text)
        except OSError as exc:
            print(f"logslice: could not write profile: {exc}", file=sys.stderr)
    else:
        sys.stderr.write(text)
