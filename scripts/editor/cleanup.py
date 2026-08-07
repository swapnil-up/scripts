#!/usr/bin/env python3
"""
Trash collector: delete heavy raw files (and intermediate work files) once a
video has been successfully uploaded to YouTube. Keeps your SSD clear.

Reads ~/vedit/uploads.json (written by upload.py) for confirmation. Files are
moved to ~/.local/share/Trash first (recoverable), not rm'd.

Usage:
    cleanup.py                      # dry-run: show what would be removed
    cleanup.py --purge              # actually move to trash
    cleanup.py --purge --raw        # also trash out/ finals
    cleanup.py --purge --force      # don't ask for confirmation
"""

import sys
import os
import json
import glob

VEDIT = os.path.expanduser("~/vedit")
UPLOADS = os.path.join(VEDIT, "uploads.json")
TRASH = os.path.expanduser("~/.local/share/Trash/files")


def _uploads():
    if not os.path.exists(UPLOADS):
        return []
    try:
        with open(UPLOADS) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _stem(path):
    return os.path.splitext(os.path.basename(path))[0]


def _related(path, stage, include_final=False):
    """Files in a vedit stage dir related to the uploaded file's stem."""
    if stage == "out" and not include_final:
        return []
    pattern = os.path.join(VEDIT, stage, f"{_stem(path)}*")
    return sorted(glob.glob(pattern))


def cleanup(purge=False, include_final=False, force=False):
    confirmed = [r for r in _uploads() if r.get("url")]
    if not confirmed:
        print("  No confirmed uploads found in ~/vedit/uploads.json.")
        return

    candidates = []
    for r in confirmed:
        for stage in ("raw", "work"):
            candidates.extend(_related(r["file"], stage))
        if include_final:
            candidates.extend(_related(r["file"], "out", include_final=True))

    # Dedupe, keep existing files only.
    seen = set()
    files = []
    total_mb = 0.0
    for p in candidates:
        p = os.path.normpath(p)
        if p in seen or not os.path.exists(p):
            continue
        seen.add(p)
        files.append(p)
        total_mb += os.path.getsize(p) / (1024 * 1024)

    if not files:
        print("  No related raw/intermediate files found.")
        return

    print(f"  {len(files)} file(s), {total_mb:.1f} MB:")
    for p in files:
        print(f"    {p}")

    if not purge:
        print("\n  [dry-run] nothing removed. Run with --purge to move these to trash.")
        return

    if not force and not _confirm():
        print("  Aborted.")
        return

    os.makedirs(TRASH, exist_ok=True)
    for p in files:
        dest = os.path.join(TRASH, os.path.basename(p))
        try:
            if os.path.exists(dest):
                os.unlink(dest)
            os.replace(p, dest)
            print(f"  trashed: {os.path.basename(p)}")
        except OSError as e:
            print(f"  failed: {p} ({e})")


def _confirm(prompt="  Move these to trash? [y/N]: "):
    return input(prompt).strip().lower() in ("y", "yes")


if __name__ == "__main__":
    from parser import parse

    ns = parse(
        sys.argv[1:],
        flags=("--purge", "--raw", "--force"),
    )

    cleanup(
        "--purge" in ns.values,
        "--raw" in ns.values,
        "--force" in ns.values,
    )
