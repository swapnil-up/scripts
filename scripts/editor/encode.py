#!/usr/bin/env python3
"""
Re-encode a video using the best available hardware encoder (auto-detect),
falling back to CPU libx264. Default target: YouTube-friendly H.264/AAC.

Usage:
    encode.py input.mp4 -o out.mp4                 # auto-detect encoder
    encode.py input.mp4 -o out.mp4 --hw vaapi      # force VAAPI
    encode.py input.mp4 -o out.mp4 --hw cpu        # force software libx264
    encode.py input.mp4 -o out.mp4 --crf 21 --preset p4
    encode.py input.mp4 -o out.mp4 --scale 1080    # downscale to 1080p wide
"""

import sys
import os
from utils import validate_file, auto_output_path, run_ffmpeg
from encoder import resolve, ENCODER_NAMES


def encode(input_file, output_file, hw="auto", crf=23, preset=None, scale=None):
    validate_file(input_file)
    if hw not in ENCODER_NAMES:
        print(f"  Unknown encoder: {hw} (choose from {sorted(ENCODER_NAMES)})")
        sys.exit(1)

    enc = resolve(hw)

    vf = []
    if scale:
        vf.append(f"scale=-2:{scale}")
    fmt = enc.filter()
    if fmt:
        vf.append(fmt)

    cmd = ["ffmpeg", "-y"]
    cmd += enc.init_flags()
    cmd += ["-i", input_file]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += enc.flags(crf)
    if preset and enc.kind in ("nvenc", "cpu"):
        cmd += ["-preset", preset]
    cmd += ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", output_file]

    print(f"  Encoding with: {enc.describe()}")
    print(f"  CRF/CQ/QP : {crf}   Target: H.264 + AAC (YouTube-friendly)")
    if scale:
        print(f"  Scale     : height={scale}")
    run_ffmpeg(cmd)
    print(f"\n  ✓ Output: {output_file}")


if __name__ == "__main__":
    from parser import parse

    ns = parse(
        sys.argv[1:],
        options={"--hw": str, "--crf": int, "--preset": str, "--scale": int},
        doc=__doc__,
    )

    if not ns.positionals:
        print(__doc__)
        sys.exit(1)

    input_file = ns.positionals[0]
    output_file = ns.output
    if len(ns.positionals) > 1:
        output_file = ns.positionals[1]

    hw = ns.values.get("--hw", "auto")
    crf = ns.values.get("--crf", 23)
    preset = ns.values.get("--preset")
    scale = ns.values.get("--scale")

    if output_file is None:
        output_file = auto_output_path(input_file, "enc")

    encode(input_file, output_file, hw, crf, preset, scale)
