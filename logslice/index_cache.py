"""Utilities for caching log indexes alongside source files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from logslice.indexer import LogIndex, build_index, load_index, save_index

_INDEX_SUFFIX = ".logslice-idx"


def default_index_path(log_path: str) -> str:
    """Return the conventional cache path for *log_path*."""
    return log_path + _INDEX_SUFFIX


def get_or_build_index(
    log_path: str,
    index_path: Optional[str] = None,
    sample_every: int = 100,
    force_rebuild: bool = False,
) -> LogIndex:
    """Return a cached index if valid, otherwise build and cache a new one.

    Parameters
    ----------
    log_path:
        Path to the source log file.
    index_path:
        Where to store/load the index.  Defaults to ``<log_path>.logslice-idx``.
    sample_every:
        Sampling rate used when building a fresh index.
    force_rebuild:
        If True, always rebuild even if a valid cache exists.
    """
    if index_path is None:
        index_path = default_index_path(log_path)

    if not force_rebuild and os.path.exists(index_path):
        try:
            idx = load_index(index_path)
            if idx.is_valid_for(log_path):
                return idx
        except Exception:
            pass  # corrupt cache — fall through to rebuild

    idx = build_index(log_path, sample_every=sample_every)
    try:
        save_index(idx, index_path)
    except OSError:
        pass  # non-fatal: cache write failure
    return idx


def invalidate_cache(log_path: str, index_path: Optional[str] = None) -> bool:
    """Delete the cached index file if it exists.  Returns True if deleted."""
    if index_path is None:
        index_path = default_index_path(log_path)
    try:
        os.remove(index_path)
        return True
    except FileNotFoundError:
        return False
