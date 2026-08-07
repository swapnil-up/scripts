#!/usr/bin/env python3
"""
Sidecar module: owns the marker **Sidecar** files and the one invariant both
marker kinds share — that **Cut markers** come in pairs, each pair removing a
section.

Takeaway for callers:
  - Load/save and the (l)oad/(d)elete/(c)ancel prompt live here, once.
  - `pair_cut_markers` is the single definition of the even-count removal
    invariant. Every consumer (process_cuts, cut_marker, edit) goes through it
    so odd counts, reversed pairs, and out-of-range bounds are decided in one
    place and are unit-testable without a running Stage.
"""

import json
import os
from utils import sidecar_path


def markers_path(input_file):
    """Sidecar for **Cut markers**: ~/vedit/<stem>.markers.json"""
    return sidecar_path(input_file, "markers.json")


def texts_path(input_file):
    """Sidecar for **Text markers**: ~/vedit/<stem>.texts.json"""
    return sidecar_path(input_file, "texts.json")


def load_json(path, default=None):
    """Read a JSON sidecar, or `default` (None) if absent/unreadable."""
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def save_json(path, data, indent=2):
    """Write a JSON sidecar atomically."""
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=indent)
    os.replace(tmp, path)


def load_or_reset(path, kind):
    """
    Interactive prompt when an existing sidecar is found: (l)oad it,
    (d)elete and start fresh, or (c)ancel.

    Returns (data, cancelled):
      cancelled is True when the user chose (c)ancel — the caller should abort.
      Otherwise data holds the existing content (load) or the empty list (delete).
    """
    if not os.path.exists(path):
        return [], False

    response = input(
        f"Found existing {kind}. (l)oad them, (d)elete and start fresh, or (c)ancel? "
    )
    if response.lower() == "l":
        data = load_json(path, [])
        print(f"Loaded {len(data)} existing {kind}")
        return data, False
    if response.lower() == "d":
        os.remove(path)
        print(f"Deleted old {kind}, starting fresh")
        return [], False
    print("Cancelled")
    return [], True


def pair_cut_markers(markers, duration=None, pad=0.0):
    """
    The core **Cut marker** invariant: markers is a flat, sorted list of
    timestamps; reading them strictly as start/end pairs, each pair is a
    section to REMOVE.

    Returns a list of (kept_start, kept_end) keep-segments built from the
    missing space between pairs, clamped to [0, duration] and padded.

    Raises ValueError on an odd marker count (a pair missing its end), or when
    markers are out of range / reversed relative to the clip.
    """
    if not markers:
        raise ValueError("No markers to cut.")
    if len(markers) % 2 != 0:
        raise ValueError(f"Odd number of markers ({len(markers)}) — each cut needs a start AND end.")

    pairs = [(markers[i], markers[i + 1]) for i in range(0, len(markers), 2)]

    segments = []
    last_kept_end = 0.0
    for start, end in pairs:
        if end < start:
            raise ValueError(f"Reversed cut pair: {start} > {end}")
        if start < last_kept_end - 1e-9:
            raise ValueError("Overlapping/out-of-order cut sections.")
        if start > last_kept_end:
            kept_start = max(0.0, last_kept_end + pad)
            kept_end = min(duration, start - pad)
            if kept_end - kept_start > 1e-9:
                segments.append((kept_start, kept_end))
        last_kept_end = max(last_kept_end, end)

    if last_kept_end < duration:
        kept_start = max(0.0, last_kept_end + pad)
        if kept_start < duration:
            segments.append((kept_start, duration))

    if not segments:
        raise ValueError("All video would be cut out — nothing to keep.")

    return segments


def fmt_pairs(markers):
    """Return [(start, end), ...] for display, or None on an odd count."""
    if not markers or len(markers) % 2 != 0:
        return None
    return [(markers[i], markers[i + 1]) for i in range(0, len(markers), 2)]