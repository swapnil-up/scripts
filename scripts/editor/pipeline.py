#!/usr/bin/env python3
"""
One-command automated pipeline: raw GoPro footage → published unlisted video.

Chains the stage scripts; each stage writes to ~/vedit and passes the result
to the next stage automatically.

Default pipeline: [trim] → silence-trim → normalize → captions → encode.
Add --upload to push to YouTube (unlisted). --cleanup trashes originals after.

Usage:
    pipeline.py raw/GP010001.mp4 --title "My first take" --upload
    pipeline.py raw/GP010001.mp4 --title "X" --tags a,b,c
    pipeline.py raw/GP010001.mp4 --trim 10:90            # cut to a section first
    pipeline.py raw/GP010001.mp4 --no-trim --no-captions
    pipeline.py --check
"""

import sys
import os
import subprocess
from utils import (
    auto_output_path,
    out_dir,
    sidecar_path,
)
from encoder import resolve

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run(script, args):
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, script)] + args
    print(f"  >>> {' '.join(cmd)}")
    return subprocess.call(cmd) == 0


def main():
    from parser import parse

    args = sys.argv[1:]

    if "--check" in args:
        print(f"  Encoder: {resolve('auto').describe()}")
        import upload
        upload.check_config()
        return

    ns = parse(
        args,
        flags=("--upload", "--no-upload", "--cleanup",
               "--no-trim", "--no-captions", "--no-subtitles", "--no-normalize"),
        options={
            "--title": str,
            "--desc": str,
            "--tags": str,
            "--privacy": str,
            "--trim": str,
            "--hw": str,
        },
        doc=__doc__,
    )

    opts = {
        "title": ns.values.get("--title"),
        "desc": ns.values.get("--desc", ""),
        "tags": ns.values.get("--tags"),
        "privacy": ns.values.get("--privacy", "unlisted"),
        "hw": ns.values.get("--hw", "auto"),
        "trim": ns.values.get("--trim"),
        "upload": "--upload" in ns.values,
        "cleanup": "--cleanup" in ns.values,
        "skip": set(),
    }
    if "--no-upload" in ns.values:
        opts["upload"] = False
    for flag in ("--no-trim", "--no-captions", "--no-subtitles", "--no-normalize"):
        if flag in ns.values:
            opts["skip"].add("trim" if flag == "--no-trim" else
                             "captions" if flag in ("--no-captions", "--no-subtitles") else
                             "normalize")

    if not ns.positionals:
        print(__doc__)
        sys.exit(1)

    video = os.path.abspath(ns.positionals[0])
    if not os.path.exists(video):
        print(f"  Error: {video} not found.")
        sys.exit(1)

    current = video
    print(f"\n  Pipeline input : {os.path.basename(video)}")
    print(f"  Encoder        : {resolve(opts['hw']).kind.upper()}")
    if opts["skip"]:
        print(f"  Skipping       : {', '.join(sorted(opts['skip']))}")

    # 1. optional lossless trim
    if opts["trim"] and "trim" not in opts["skip"]:
        start, _, end = opts["trim"].partition(":")
        out = auto_output_path(current, "trimmed")
        if run("lossless_trim.py", [current, "--start", start, "--end", end, "-o", out]):
            current = out

    # 2. auto silence trim
    if "trim" not in opts["skip"]:
        tight = auto_output_path(current, "tight")
        if run("silence_trim.py", [current, "-o", tight, "--hw", opts["hw"]]):
            current = tight

    # 3. normalize audio
    if "normalize" not in opts["skip"]:
        norm = auto_output_path(current, "norm")
        if run("audio.py", [current, norm, "--normalize"]):
            current = norm

    # 4. captions
    if "captions" not in opts["skip"]:
        cap = auto_output_path(current, "cap")
        if run("captions.py", [current, "-o", cap, "--hw", opts["hw"]]):
            current = cap

    # 5. encode final (YouTube-friendly)
    final_name = os.path.splitext(os.path.basename(video))[0] + "_final.mp4"
    final = os.path.join(out_dir(), final_name)
    run("encode.py", [current, "-o", final, "--hw", opts["hw"]])

    print(f"\n  Final: {final}")

    # 6. upload
    if opts["upload"]:
        up = ["upload.py", final, "--title", opts["title"] or os.path.basename(video),
              "--privacy", opts["privacy"]]
        if opts["desc"]:
            up += ["--desc", opts["desc"]]
        if opts["tags"]:
            up += ["--tags", opts["tags"]]
        run("upload.py", up[1:])

    print("\n  Pipeline complete ✓")
    if opts["cleanup"]:
        print("  Now run: cleanup.py --purge  (trashes originals once upload confirmed)")


if __name__ == "__main__":
    main()