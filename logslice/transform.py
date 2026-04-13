"""High-level stream transformation combining sampling and deduplication."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator

from logslice.dedup import DedupOptions, dedup_lines
from logslice.parser import LogLine
from logslice.sampler import SampleOptions, apply_sampling


@dataclass
class TransformConfig:
    """Aggregated configuration for all stream-transform steps."""

    sample: SampleOptions = field(default_factory=SampleOptions)
    dedup: DedupOptions = field(default_factory=DedupOptions)


def apply_transforms(
    lines: Iterable[LogLine],
    config: TransformConfig,
) -> Iterator[LogLine]:
    """Apply deduplication then sampling to *lines*.

    Order: dedup first so that sampling ratios are computed on the
    already-deduplicated stream.
    """
    stream = dedup_lines(lines, config.dedup)
    stream = apply_sampling(stream, config.sample)
    yield from stream


def build_transform_config(
    every_nth: int = 1,
    max_lines: int | None = None,
    head: int | None = None,
    tail: int | None = None,
    dedup: bool = False,
) -> TransformConfig:
    """Convenience factory used by the CLI layer."""
    return TransformConfig(
        sample=SampleOptions(
            every_nth=every_nth,
            max_lines=max_lines,
            head=head,
            tail=tail,
        ),
        dedup=DedupOptions(enabled=dedup),
    )
