#!/usr/bin/env python3
"""
Record the X11 screen to a video file.

Usage:
    screen_record.py                         # full screen, auto-named
    screen_record.py demo.mp4                # full screen, named
    screen_record.py --select                 # select region, auto-named
    screen_record.py demo.mp4 --select        # select region, named
    screen_record.py --region 0 0 800 600     # explicit region, auto-named
"""

import sys
import os
import subprocess
import signal
import datetime
from utils import get_vedit_dir


def auto_name():
    """Generate a timestamped filename in ~/vedit/."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(get_vedit_dir(), f"screen_{ts}.mp4")


def select_region():
    """Use slop to interactively select a region. Returns (x, y, w, h) or None."""
    try:
        result = subprocess.run(
            ["slop", "-f", "%x %y %w %h"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return None
        parts = result.stdout.strip().split()
        if len(parts) == 4:
            return (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))
    except (FileNotFoundError, ValueError, IndexError, subprocess.TimeoutExpired):
        pass
    return None


def record_screen(output_file, region=None, fps=30, show_mouse=True):
    cmd = ["ffmpeg", "-y"]

    if region:
        x, y, w, h = region
        cmd.extend(["-video_size", f"{w}x{h}", "-f", "x11grab", "-i", f":0.0+{x},{y}"])
    else:
        cmd.extend(["-f", "x11grab", "-i", ":0.0"])

    cmd.extend(["-draw_mouse", "1" if show_mouse else "0"])
    cmd.extend(["-framerate", str(fps)])
    cmd.extend(["-c:v", "libx264", "-preset", "ultrafast", "-crf", "23"])
    cmd.extend(["-movflags", "+frag_keyframe+empty_moov"])
    cmd.append(output_file)

    print(f"  Output : {output_file}")
    if region:
        print(f"  Region : {region[0]},{region[1]} ({region[2]}x{region[3]})")
    else:
        print(f"  Region : full screen")
    print(f"  FPS    : {fps}")
    print(f"  Mouse  : {'shown' if show_mouse else 'hidden'}")
    print("\n  Recording... Press Ctrl+C to stop.\n")

    process = subprocess.Popen(cmd)

    def signal_handler(sig, frame):
        print("\n  Stopping recording, finishing write...")
        # ffmpeg already received SIGINT from the terminal
        # and is shutting down gracefully — just wait for it

    signal.signal(signal.SIGINT, signal_handler)
    process.wait()

    if os.path.exists(output_file):
        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"  ✓ Saved: {output_file} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    output_file = None
    region = None
    fps = 30
    show_mouse = True
    select_mode = False

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--select":
            select_mode = True
            i += 1
        elif arg == "--region" and i + 4 < len(sys.argv):
            region = (
                int(sys.argv[i + 1]),
                int(sys.argv[i + 2]),
                int(sys.argv[i + 3]),
                int(sys.argv[i + 4]),
            )
            i += 5
        elif arg == "--fps" and i + 1 < len(sys.argv):
            fps = int(sys.argv[i + 1])
            i += 2
        elif arg == "--no-mouse":
            show_mouse = False
            i += 1
        elif arg.startswith("--"):
            print(f"  Unknown option: {arg}")
            sys.exit(1)
        else:
            output_file = arg
            i += 1

    if select_mode:
        print("  Select a region on screen...")
        sel = select_region()
        if sel:
            region = sel
            print(f"  Selected: {sel[0]},{sel[1]} ({sel[2]}x{sel[3]})")
        else:
            print("  Region selection failed or cancelled.")
            print("  Use --region X Y W H to specify coordinates manually.")
            sys.exit(1)

    if output_file is None:
        output_file = auto_name()

    record_screen(output_file, region, fps, show_mouse)
