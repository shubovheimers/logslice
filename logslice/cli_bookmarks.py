"""CLI subcommands for managing log file bookmarks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from logslice.bookmarks import (
    Bookmark,
    DEFAULT_BOOKMARK_DIR,
    save_bookmark,
    load_bookmark,
    delete_bookmark,
    list_bookmarks,
)


def add_bookmark_subparser(subparsers: argparse._SubParsersAction) -> None:
    bm = subparsers.add_parser("bookmark", help="Manage named positions in log files")
    bm_sub = bm.add_subparsers(dest="bookmark_cmd", required=True)

    # bookmark save
    save_p = bm_sub.add_parser("save", help="Save a bookmark")
    save_p.add_argument("name", help="Bookmark name")
    save_p.add_argument("filepath", help="Path to the log file")
    save_p.add_argument("offset", type=int, help="Byte offset in the file")
    save_p.add_argument("line_number", type=int, help="Line number at the offset")
    save_p.add_argument("--timestamp", default=None, help="ISO timestamp at this position")

    # bookmark load
    load_p = bm_sub.add_parser("load", help="Show a saved bookmark")
    load_p.add_argument("name", help="Bookmark name")

    # bookmark delete
    del_p = bm_sub.add_parser("delete", help="Delete a bookmark")
    del_p.add_argument("name", help="Bookmark name")

    # bookmark list
    bm_sub.add_parser("list", help="List all bookmarks")


def run_bookmark(args: argparse.Namespace, bookmark_dir: Path = DEFAULT_BOOKMARK_DIR) -> int:
    """Dispatch bookmark subcommands. Returns exit code."""
    cmd = args.bookmark_cmd

    if cmd == "save":
        bm = Bookmark(
            name=args.name,
            filepath=args.filepath,
            offset=args.offset,
            line_number=args.line_number,
            timestamp=args.timestamp,
        )
        path = save_bookmark(bm, bookmark_dir)
        print(f"Bookmark '{args.name}' saved to {path}")
        return 0

    if cmd == "load":
        bm = load_bookmark(args.name, bookmark_dir)
        if bm is None:
            print(f"Bookmark '{args.name}' not found.", file=sys.stderr)
            return 1
        print(f"name:        {bm.name}")
        print(f"file:        {bm.filepath}")
        print(f"offset:      {bm.offset}")
        print(f"line_number: {bm.line_number}")
        if bm.timestamp:
            print(f"timestamp:   {bm.timestamp}")
        return 0

    if cmd == "delete":
        removed = delete_bookmark(args.name, bookmark_dir)
        if removed:
            print(f"Bookmark '{args.name}' deleted.")
            return 0
        print(f"Bookmark '{args.name}' not found.", file=sys.stderr)
        return 1

    if cmd == "list":
        bookmarks = list_bookmarks(bookmark_dir)
        if not bookmarks:
            print("No bookmarks saved.")
            return 0
        for bm in bookmarks:
            ts = f"  [{bm.timestamp}]" if bm.timestamp else ""
            print(f"{bm.name:20s}  {bm.filepath}  @{bm.offset} line {bm.line_number}{ts}")
        return 0

    print(f"Unknown bookmark command: {cmd}", file=sys.stderr)
    return 1
