"""Archive filtered log output to compressed files."""
from __future__ import annotations

import gzip
import bz2
import lzma
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

from logslice.parser import LogLine

_COMPRESSORS = {
    ".gz": gzip.open,
    ".bz2": bz2.open,
    ".xz": lzma.open,
}


@dataclass
class ArchiveOptions:
    output_path: str = ""
    compression: str = "gz"  # gz | bz2 | xz | none
    overwrite: bool = False
    encoding: str = "utf-8"

    def __post_init__(self) -> None:
        valid = {"gz", "bz2", "xz", "none"}
        if self.compression not in valid:
            raise ValueError(f"compression must be one of {valid}, got {self.compression!r}")

    def enabled(self) -> bool:
        return bool(self.output_path)

    def resolved_path(self) -> Path:
        p = Path(self.output_path)
        if self.compression != "none" and not p.suffix == f".{self.compression}":
            p = p.with_suffix(p.suffix + f".{self.compression}")
        return p


def _open_archive(path: Path, compression: str, overwrite: bool):
    if path.exists() and not overwrite:
        raise FileExistsError(f"Archive already exists: {path}. Use overwrite=True to replace.")
    path.parent.mkdir(parents=True, exist_ok=True)
    ext = f".{compression}"
    opener = _COMPRESSORS.get(ext)
    if opener is None:
        return open(path, "wt", encoding="utf-8")
    return opener(path, "wt", encoding="utf-8")


def archive_lines(
    lines: Iterable[LogLine],
    opts: ArchiveOptions,
) -> int:
    """Write *lines* to the archive described by *opts*.

    Returns the number of lines written.
    """
    if not opts.enabled():
        raise ValueError("ArchiveOptions.output_path must be set before archiving.")

    dest = opts.resolved_path()
    count = 0
    with _open_archive(dest, opts.compression, opts.overwrite) as fh:
        for line in lines:
            fh.write(line.raw if line.raw.endswith("\n") else line.raw + "\n")
            count += 1
    return count


def iter_archive(
    lines: Iterable[LogLine],
    opts: ArchiveOptions,
) -> Iterator[LogLine]:
    """Pass *lines* through while simultaneously writing them to an archive."""
    if not opts.enabled():
        yield from lines
        return

    dest = opts.resolved_path()
    with _open_archive(dest, opts.compression, opts.overwrite) as fh:
        for line in lines:
            fh.write(line.raw if line.raw.endswith("\n") else line.raw + "\n")
            yield line
