#!/usr/bin/env python3
"""
edit.py - Interactive orchestrator for the video editing pipeline.

Handles the full workflow: record screen → cut → text → gif
Tracks the "current working file" so you can re-cut as many times as needed.

Usage:
    python3 edit.py                      # record screen or convert GIF
    python3 edit.py video.mp4            # start editing an existing video
"""

import sys
import os
import json
import subprocess
from utils import (
    sidecar_path,
    auto_output_path,
    validate_file,
    get_video_info,
    format_time,
    log,
    log_init,
)


def run_script(script_name, args):
    """Run an editor script as a subprocess."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, script_name)
    cmd = [sys.executable, script_path] + args
    print(f"\n  → {' '.join(cmd)}\n")
    try:
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"\n  ⚠ {script_name} exited with code {result.returncode}")
            return False
        return True
    except KeyboardInterrupt:
        return False


def open_in_mpv(video_file):
    """Open a video in mpv for preview."""
    cmd = ["mpv", "--osd-level=3", video_file]
    print(f"\n  Opening {os.path.basename(video_file)} in mpv...")
    subprocess.run(cmd)


def print_header(text):
    width = 60
    print()
    print("=" * width)
    print(f"  {text}")
    print("=" * width)


def yesno(prompt, default=True):
    """Simple yes/no prompt."""
    hint = "Y/n" if default else "y/N"
    response = input(f"  {prompt} [{hint}] ").strip().lower()
    if not response:
        return default
    return response == "y"


def check_state(current_file):
    """Build pipeline state for the current working file."""
    if current_file is None:
        return {"file": None}

    markers_file = sidecar_path(current_file, "markers.json")
    markers_exist = os.path.exists(markers_file)
    cut_file = auto_output_path(current_file, "cut")
    texts_file = f"{current_file}.texts.json"
    texts_exist = os.path.exists(texts_file)
    text_output = auto_output_path(current_file, "text")
    text_output_exists = os.path.exists(text_output)

    return {
        "file": current_file,
        "markers_file": markers_file,
        "markers_exist": markers_exist,
        "cut_file": cut_file,
        "texts_file": texts_file,
        "texts_exist": texts_exist,
        "text_output": text_output,
        "text_output_exists": text_output_exists,
    }


def show_pipeline(state):
    """Display the current file and what's available downstream."""
    s = state
    print()

    if s["file"] is None:
        print(f"  {'─' * 40}")
        print(f"  No video loaded. Record a screen or convert a GIF.")
        print(f"  {'─' * 40}")
        return

    print(f"  {'─' * 50}")
    print(f"  Current: {os.path.basename(s['file'])}")
    print(f"  Marks define sections to REMOVE (not keep)")
    print(f"  {'─' * 50}")
    print(f"  {'Step':<22} {'Status':<28}")
    print(f"  {'─' * 50}")

    if s["markers_exist"]:
        with open(s["markers_file"]) as f:
            n = len(json.load(f))
        print(f"  {'Remove markers':<22} {f'{n} points saved':<28}")
    else:
        print(f"  {'Remove markers':<22} {'—':<28}")

    print(f"  {'Next trim output':<22} {os.path.basename(s['cut_file']):<28}")

    if s["texts_exist"]:
        print(f"  {'Text markers':<22} {'saved':<28}")
    else:
        print(f"  {'Text markers':<22} {'—':<28}")

    print(f"  {'Next text output':<22} {os.path.basename(s['text_output']):<28}")

    if s["text_output_exists"]:
        print(f"  {'Text burned in':<22} {'✓':<28}")

    print(f"  {'─' * 50}")


def menu(entries):
    """Show a numbered menu and return the selected index."""
    print()
    for i, (label, _) in enumerate(entries, 1):
        print(f"  [{i}] {label}")
    print("  [0] Back / Exit")
    print()

    while True:
        try:
            choice = input("  Select: ").strip()
            if choice == "0":
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(entries):
                return idx
            print(f"  Enter 0–{len(entries)}")
        except ValueError:
            print("  Enter a number")


def show_markers(state):
    """Display all cut markers with durations and what would be kept."""
    if not state["markers_exist"]:
        print("\n  No cut markers for this file.")
        input("  Press Enter...")
        return

    with open(state["markers_file"]) as f:
        markers = json.load(f)

    print(f"\n  Markers file: {state['markers_file']}")
    print(f"  {'─' * 50}")

    if len(markers) % 2 != 0:
        print(f"  ⚠ Odd number of markers ({len(markers)}) — missing a pair end!")
        for i, m in enumerate(markers, 1):
            print(f"    {i}. {format_time(m)}")
        input("  Press Enter...")
        return

    total_cut = 0
    print(f"  Sections to REMOVE:")
    for i in range(0, len(markers), 2):
        start = markers[i]
        end = markers[i + 1]
        dur = end - start
        total_cut += dur
        print(f"    Pair {i//2 + 1}: {format_time(start)} → {format_time(end)}  ({dur:.1f}s)")

    print(f"\n  Total to remove: {format_time(total_cut)} ({total_cut:.1f}s)")
    print(f"  (Everything else is KEPT in the output)")
    print(f"  {'─' * 50}")
    input("  Press Enter...")


def main():
    log_init("edit.py")

    current_file = None

    if len(sys.argv) >= 2:
        video_file = os.path.abspath(sys.argv[1])
        validate_file(video_file)
        current_file = video_file
        info = get_video_info(video_file)
        log(f"start with file: {video_file} ({info['duration']:.1f}s)")

        print_header("Video Editor Pipeline")
        print(f"  File     : {video_file}")
        print(f"  Duration : {format_time(info['duration'])} ({info['duration']:.1f}s)")
        print(f"          : {info.get('width', '?')}x{info.get('height', '?')}  {info.get('fps', '?')} fps  {info['size_mb']:.1f} MB")
    else:
        log("start: no file (record/convert mode)")
        print_header("Video Editor Pipeline")
        print(f"  No file loaded — start by recording a screen or converting to GIF.")
        print(f"  Once you record or load a video, the editing options appear.\n")

    while True:
        state = check_state(current_file)
        show_pipeline(state)

        if current_file is None:
            entries = [
                ("Record screen (select region)", "record_screen"),
                ("Convert latest recording to GIF", "gif_latest"),
            ]
        else:
            entries = [
                ("Record screen (select region)", "record_screen"),
                ("Convert latest recording to GIF", "gif_latest"),
                ("Show info", "info"),
                ("Preview in mpv", "preview"),
                ("Show which sections will be removed", "show_markers"),
                ("Mark sections to REMOVE (mpv, press 'm')", "mark_cuts"),
                ("Remove marked sections → trimmed video", "process_cuts"),
                ("Add text overlay markers", "mark_text"),
                ("Burn text into video", "process_text"),
                ("Create GIF from current video", "gif"),
                ("Run full pipeline (guided)", "full"),
            ]

        idx = menu(entries)
        if idx is None:
            print("\n  Bye!")
            break

        action = entries[idx][1]

        if action == "record_screen":
            log(f"action=record_screen")
            run_script("screen_record.py", ["--select"])
            from utils import get_vedit_dir
            import glob
            pattern = os.path.join(get_vedit_dir(), "screen_*.mp4")
            files = sorted(glob.glob(pattern))
            if files:
                latest = files[-1]
                log(f"recorded: {latest}")
                print(f"\n  ✓ Recording saved: {latest}")
                if yesno("Load this recording as the current video?", default=True):
                    current_file = latest
            input("  Press Enter...")

        elif action == "gif_latest":
            log(f"action=gif_latest")
            q_map = {"d": "demo", "l": "low", "m": "medium", "h": "high", "x": "max"}
            q = input("  Quality (d)emo / (l)ow / (m)edium / (h)igh / ma(x) [d]: ").strip().lower() or "d"
            quality = q_map.get(q, q)
            from utils import get_vedit_dir
            gif_dir = os.path.join(get_vedit_dir(), "gif")
            os.makedirs(gif_dir, exist_ok=True)
            out = input(f"  Output filename (default: {gif_dir}/demo.gif): ").strip()
            if not out:
                out = os.path.join(gif_dir, "demo.gif")
            elif not os.path.isabs(out) and "/" not in out:
                out = os.path.join(gif_dir, out)
            run_script("gif.py", ["--latest", out, "--quality", quality])
            input("  Press Enter...")

        elif action == "info":
            if current_file is None: continue
            log(f"action=info file={current_file}")
            from utils import print_video_info
            print_video_info(current_file)
            input("  Press Enter...")

        elif action == "preview":
            if current_file is None: continue
            log(f"action=preview file={current_file}")
            open_in_mpv(current_file)

        elif action == "show_markers":
            show_markers(state)

        elif action == "mark_cuts":
            if current_file is None: continue
            log(f"action=mark_cuts file={current_file}")
            run_script("cut_marker.py", [current_file])

        elif action == "process_cuts":
            if current_file is None: continue
            if not state["markers_exist"]:
                print("\n  No cut markers for current file. Mark cuts first.")
                input("  Press Enter...")
                continue
            log(f"action=process_cuts file={current_file}")
            if run_script("process_cuts.py", [current_file]):
                result = state["cut_file"]
                log(f"trimmed: {result}")
                print(f"\n  ✓ Trimmed: {result}")
                current_file = result
                if yesno("Trim this result too?", default=False):
                    print(f"  Now working on: {current_file}")
                    log(f"recut: current_file={current_file}")
            input("  Press Enter...")

        elif action == "mark_text":
            if current_file is None: continue
            if not os.path.exists(current_file):
                print(f"\n  {os.path.basename(current_file)} not found.")
                input("  Press Enter...")
                continue
            log(f"action=mark_text file={current_file}")
            run_script("text_marker.py", [current_file])

        elif action == "process_text":
            if current_file is None: continue
            if not state["texts_exist"]:
                print("\n  No text markers found for current file. Mark text first.")
                input("  Press Enter...")
                continue
            log(f"action=process_text file={current_file}")
            run_script("process_text.py", [current_file, state["text_output"]])
            input("  Press Enter...")

        elif action == "gif":
            if current_file is None: continue
            log(f"action=gif file={current_file}")
            handle_gif(current_file)
            input("  Press Enter...")

        elif action == "full":
            if current_file is None: continue
            log(f"action=full_pipeline start={current_file}")
            current_file = run_full_pipeline(current_file)
            log(f"full_pipeline_done: current_file={current_file}")


def handle_gif(current_file):
    """Interactive prompt for creating a GIF."""
    from utils import get_duration, get_vedit_dir
    source = current_file
    dur = get_duration(source)
    stem = os.path.splitext(os.path.basename(source))[0]

    print(f"\n  Source: {source}  ({dur:.1f}s total)")
    print(f"  {'─' * 40}")

    start = input("  Start time (empty for beginning): ").strip()

    max_dur = dur - (float(start) if start else 0)
    print(f"  (video left: {max_dur:.1f}s)")
    duration = input("  Duration in seconds (default 5): ").strip() or "5"

    quality_map = {"d": "demo", "l": "low", "m": "medium", "h": "high", "x": "max"}
    q = input("  Quality (d)emo / (l)ow / (m)edium / (h)igh / ma(x) [m]: ").strip().lower() or "m"
    quality = quality_map.get(q, q)

    gif_dir = os.path.join(get_vedit_dir(), "gif")
    os.makedirs(gif_dir, exist_ok=True)
    default_out = os.path.join(gif_dir, f"{stem}.gif")
    out = input(f"  Output filename (default: {default_out}): ").strip()
    if not out:
        out = default_out
    elif not os.path.isabs(out) and "/" not in out:
        out = os.path.join(gif_dir, out)

    args = [source, out, "--duration", duration, "--quality", quality]
    if start:
        args.extend(["--start", start])
    run_script("gif.py", args)


def run_full_pipeline(start_file):
    """Guided walk through the full pipeline with iterative cutting.
    Returns the final file after all stages."""
    print_header("Full Pipeline")
    current_file = start_file

    # Cutting loop
    while True:
        print(f"\n  Current file: {current_file}")
        state = check_state(current_file)

        if not state["markers_exist"]:
            print("\n  Step: Mark sections to cut out.")
            print("  Press 'm' in mpv at each point, then 'q' to save.\n")
            input("  Press Enter to open mpv...")
            if not run_script("cut_marker.py", [current_file]):
                input("  Press Enter...")
                return start_file
            state = check_state(current_file)

        if not state["markers_exist"]:
            print("  No markers were saved. Moving to text stage.")
            break

        print(f"\n  Removing marked sections...")
        if not run_script("process_cuts.py", [current_file]):
            input("  Press Enter...")
            return start_file

        current_file = state["cut_file"]
        print(f"\n  ✓ Trimmed: {current_file}")

        if not yesno("Trim this result too?", default=False):
            break

    # Text stage
    if not os.path.exists(current_file):
        print(f"\n  {current_file} not found. Skipping text stage.")
        input("  Press Enter...")
        return current_file

    state = check_state(current_file)

    if not state["texts_exist"]:
        print(f"\n  Step: Add text overlays to {os.path.basename(current_file)}.")
        print("  Press 't' at each position, then enter text after closing mpv.\n")
        input("  Press Enter to open mpv...")
        if not run_script("text_marker.py", [current_file]):
            input("  Press Enter...")
            return current_file
        state = check_state(current_file)

    if state["texts_exist"] and not state["text_output_exists"]:
        print(f"\n  Burning text into video...")
        run_script("process_text.py", [current_file, state["text_output"]])
        state = check_state(current_file)

    final = state["text_output"] if state["text_output_exists"] else current_file
    print(f"\n  ✓ Pipeline done! Final output: {final}")
    input("  Press Enter...")
    return final


if __name__ == "__main__":
    main()
