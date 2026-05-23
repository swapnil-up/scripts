#!/usr/bin/env python3
"""
Control audio on a video: mute, adjust volume, replace, or mix in a track.

Usage:
    audio.py input.mp4 output.mp4 --mute                  # remove audio
    audio.py input.mp4 output.mp4 --volume 0.5             # lower to 50%
    audio.py input.mp4 output.mp4 --add music.mp3          # replace audio
    audio.py input.mp4 output.mp4 --add music.mp3 --mix    # mix with existing
    audio.py input.mp4 output.mp4 --add music.mp3 --mix --volume 0.3  # existing at 30%
"""

import sys
import os
from utils import run_ffmpeg, validate_file


def process_audio(video_file, output_file, mute=False, volume=None, add_audio=None, mix=False):
    validate_file(video_file)
    if add_audio:
        validate_file(add_audio)

    cmd = ["ffmpeg", "-y", "-i", video_file]

    if mute:
        cmd.extend(["-c:v", "copy", "-an", output_file])
        print("  Removing all audio tracks.")
        run_ffmpeg(cmd)
        print(f"\n  ✓ Output: {output_file}")
        return

    if add_audio:
        cmd.extend(["-i", add_audio])
        has_audio = True

    if add_audio and not mix:
        # Replace: use video from input, audio from add_audio
        cmd.extend(["-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", output_file])
        print(f"  Replacing audio with: {add_audio}")
        run_ffmpeg(cmd)
        print(f"\n  ✓ Output: {output_file}")
        return

    if add_audio and mix:
        # Mix: layer add_audio over existing
        vol_original = f"volume={volume}" if volume is not None else "volume=1.0"
        vol_new = "volume=1.0"
        filter_complex = (
            f"[0:a]{vol_original}[a0];"
            f"[1:a]{vol_new}[a1];"
            f"[a0][a1]amix=inputs=2:duration=first[a]"
        )
        cmd.extend(["-c:v", "copy", "-filter_complex", filter_complex, "-map", "0:v:0", "-map", "[a]", "-c:a", "aac", output_file])
        print(f"  Mixing in: {add_audio}")
        if volume is not None:
            print(f"  Original audio at {volume}x")
        run_ffmpeg(cmd)
        print(f"\n  ✓ Output: {output_file}")
        return

    # Volume-only adjustment
    if volume is not None:
        cmd.extend(["-c:v", "copy", "-af", f"volume={volume}", output_file])
        print(f"  Adjusting volume to {volume}x")
        run_ffmpeg(cmd)
        print(f"\n  ✓ Output: {output_file}")
        return

    # No-op (shouldn't happen given CLI validation)
    print("  No changes specified. Copying as-is.")
    run_ffmpeg([*cmd, "-c", "copy", output_file])


if __name__ == "__main__":
    input_file = None
    output_file = None
    mute = False
    volume = None
    add_audio = None
    mix = False

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--mute":
            mute = True
            i += 1
        elif arg == "--volume" and i + 1 < len(sys.argv):
            volume = float(sys.argv[i + 1])
            i += 2
        elif arg == "--add" and i + 1 < len(sys.argv):
            add_audio = sys.argv[i + 1]
            i += 2
        elif arg == "--mix":
            mix = True
            i += 1
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

    if not input_file or not output_file:
        print(__doc__.strip())
        sys.exit(1)

    process_audio(input_file, output_file, mute, volume, add_audio, mix)
