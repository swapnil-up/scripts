#!/usr/bin/env python3
"""
Convert a video to an optimized GIF using palette generation.

Usage:
    gif.py input.mp4 output.gif                # whole video
    gif.py input.mp4 output.gif --start 5 --duration 3   # segment
    gif.py --latest demo.gif --demo            # latest screen recording as GIF
"""

import sys
import os
import glob
import tempfile
from utils import run_ffmpeg, validate_file, get_video_info, parse_time, get_vedit_dir


def latest_screen_recording():
    """Find the most recent screen recording in ~/vedit/."""
    pattern = os.path.join(get_vedit_dir(), "screen_*.mp4")
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None


def create_gif(
    input_file,
    output_file,
    start=None,
    duration=None,
    fps=None,
    width=None,
    quality="medium",
):
    """
    Convert a video (or segment) to an optimized GIF using palette generation.

    Quality presets:
      demo   - README-ready: 600px, 10fps, 256 colors
      low    - smaller file, lower quality (good for long GIFs)
      medium - balanced (default)
      high   - better quality, larger file (good for short demos)
      max    - highest quality, no scaling

    When no --start or --duration is given, the whole video is converted.
    """
    validate_file(input_file)

    info = get_video_info(input_file)

    quality_map = {"d": "demo", "l": "low", "m": "medium", "h": "high", "x": "max"}
    quality = quality_map.get(quality, quality)

    quality_settings = {
        "demo": {"fps": 10, "scale": 600, "colors": 256},
        "low": {"fps": 10, "scale": 480, "colors": 128},
        "medium": {"fps": 15, "scale": 640, "colors": 256},
        "high": {"fps": 20, "scale": 800, "colors": 256},
        "max": {"fps": 30, "scale": -1, "colors": 256},
    }

    settings = quality_settings.get(quality, quality_settings["medium"])

    if fps:
        settings["fps"] = fps
    if width:
        settings["scale"] = width

    filters = []
    if settings["scale"] != -1 and info.get("width", 0) > settings["scale"]:
        filters.append(f"scale={settings['scale']}:-1:flags=lanczos")
    filters.append(f"fps={settings['fps']}")
    filter_str = ",".join(filters) if filters else None

    palette_file = tempfile.mktemp(suffix=".png")

    try:
        label = quality.upper() if quality != "demo" else "DEMO"
        print(f"Creating GIF — preset: {label}")
        print(f"  FPS    : {settings['fps']}")
        print(
            f"  Width  : {settings['scale'] if settings['scale'] != -1 else info.get('width', '?')}"
        )
        print(f"  Colors : {settings['colors']}")
        if start:
            print(f"  Start  : {start}")
        if duration:
            print(f"  Length : {duration}s")

        # Step 1: generate palette
        palette_cmd = ["ffmpeg", "-y"]
        if start:
            palette_cmd.extend(["-ss", str(parse_time(start))])
        if duration:
            palette_cmd.extend(["-t", str(parse_time(duration))])
        palette_cmd.extend(["-i", input_file])
        vf = f"{filter_str}," if filter_str else ""
        palette_cmd.extend(
            ["-vf", f"{vf}palettegen=max_colors={settings['colors']}:stats_mode=diff"]
        )
        palette_cmd.append(palette_file)

        print("Generating color palette...")
        run_ffmpeg(palette_cmd, show_progress=False)

        # Step 2: create GIF using palette
        gif_cmd = ["ffmpeg", "-y"]
        if start:
            gif_cmd.extend(["-ss", str(parse_time(start))])
        if duration:
            gif_cmd.extend(["-t", str(parse_time(duration))])
        gif_cmd.extend(["-i", input_file, "-i", palette_file])
        if filter_str:
            gif_cmd.extend(
                [
                    "-lavfi",
                    f"{filter_str} [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=5",
                ]
            )
        else:
            gif_cmd.extend(["-lavfi", "paletteuse=dither=bayer:bayer_scale=5"])
        gif_cmd.append(output_file)

        print("Creating GIF...")
        run_ffmpeg(gif_cmd, show_progress=False)

        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"\n  ✓ Created: {output_file} ({size_mb:.2f} MB)")

        if size_mb > 5:
            print("  Tip: use --quality low, shorter duration, or --width 480")

    finally:
        if os.path.exists(palette_file):
            os.unlink(palette_file)


if __name__ == "__main__":
    input_file = None
    output_file = None
    start = None
    duration = None
    fps = None
    width = None
    quality = "medium"
    use_latest = False

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--latest":
            use_latest = True
            i += 1
        elif arg == "--start" and i + 1 < len(sys.argv):
            start = sys.argv[i + 1]
            i += 2
        elif arg == "--duration" and i + 1 < len(sys.argv):
            duration = sys.argv[i + 1]
            i += 2
        elif arg == "--fps" and i + 1 < len(sys.argv):
            fps = int(sys.argv[i + 1])
            i += 2
        elif arg == "--width" and i + 1 < len(sys.argv):
            width = int(sys.argv[i + 1])
            i += 2
        elif arg == "--quality" and i + 1 < len(sys.argv):
            quality = sys.argv[i + 1]
            i += 2
        elif arg.startswith("--"):
            print(f"  Unknown option: {arg}")
            sys.exit(1)
        elif input_file is None:
            input_file = arg
            i += 1
        elif output_file is None:
            output_file = arg
            i += 1
        else:
            i += 1

    if use_latest:
        found = latest_screen_recording()
        if not found:
            print("  No screen recordings found in ~/vedit/.")
            sys.exit(1)
        input_file = found
        print(f"  Using latest recording: {input_file}")

    if not input_file or not output_file:
        print("Usage: gif.py INPUT OUTPUT [OPTIONS]")
        print("       gif.py --latest OUTPUT [OPTIONS]")
        print()
        print("Options:")
        print("  --start TIME        Start time (e.g. '10' or '00:00:10')")
        print("  --duration TIME     Duration in seconds (default: whole video)")
        print("  --fps FPS           Frame rate (default: depends on preset)")
        print("  --width WIDTH       Output width in pixels")
        print("  --quality PRESET    demo / low / medium / high / max")
        print("  --latest            Use latest screen recording from ~/vedit/")
        print()
        print("Examples:")
        print("  gif.py demo.mp4 demo.gif")
        print("  gif.py clip.mp4 clip.gif --start 10 --duration 5 --quality high")
        print("  gif.py --latest demo.gif --demo")
        sys.exit(1)

    create_gif(input_file, output_file, start, duration, fps, width, quality)
