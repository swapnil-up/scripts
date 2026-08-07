#!/usr/bin/env python3
"""
Auto-captioner: transcribe speech with whisper.cpp and burn subtitles into the
video using libass (stylized), or embed them as soft subtitles.

Usage:
    captions.py input.mp4 -o out.mp4                # burn styled subs (default)
    captions.py input.mp4 -o out.mp4 --soft         # embed soft subs (mov_text)
    captions.py input.mp4 -o out.mp4 --lang en --model ~/github/whisper.cpp/models/ggml-small.en.bin
    captions.py input.mp4 -o out.mp4 --style "FontName=DejaVu Sans,FontSize=18,Alignment=2"
    captions.py input.mp4 --srt-only                # just produce the .srt

The SRT is saved next to the output as <output>.srt and left in place.
"""

import sys
import os
import subprocess
from utils import (
    validate_file,
    auto_output_path,
    run_ffmpeg,
    temp_path,
    WHISPER_EXE,
    WHISPER_MODEL,
)
from encoder import resolve

DEFAULT_STYLE = (
    "FontName=DejaVu Sans,FontSize=20,PrimaryColour=&H00FFFFFF,"
    "OutlineColour=&H00101010,Outline=1.2,Shadow=1,BorderStyle=1,"
    "Alignment=2,MarginV=36"
)


def transcribe(input_file, lang="en", model=None, prefix=None):
    """Run whisper on the audio stream. Returns path to the .srt (or None)."""
    if not os.path.exists(WHISPER_EXE) or not os.path.exists(model or WHISPER_MODEL):
        print(
            f"whisper-cli or model missing.\n  exe:   {WHISPER_EXE}\n  model: {model or WHISPER_MODEL}\n"
            "Build it via setup/whisper.sh"
        )
        return None

    # Extract clean mono 16k audio for transcription.
    wav = temp_path(".wav")
    prefix = wav[:-4]  # whisper writes <prefix>.srt
    run_ffmpeg(
        ["ffmpeg", "-y", "-i", input_file, "-vn", "-ac", "1", "-ar", "16000", wav],
        show_progress=False,
    )

    try:
        cmd = [WHISPER_EXE, "-m", model or WHISPER_MODEL, "-f", wav]
        if lang:
            cmd += ["-l", lang]
        cmd += ["-osrt", "-of", prefix]
        print(f"  Transcribing with whisper...")
        subprocess.run(cmd, capture_output=True, text=True)

        srt = f"{prefix}.srt"
        if not os.path.exists(srt) or os.path.getsize(srt) == 0:
            if os.path.exists(srt):
                os.unlink(srt)
            print("  Transcription produced no subtitles (silent audio?).")
            return None
        return srt
    finally:
        if os.path.exists(wav):
            try:
                os.unlink(wav)
            except OSError:
                pass


def burn_subtitles(input_file, srt, output_file, style=None, hw="auto", crf=23):
    """Burn the SRT into the video with libass. Uses hw encoder if available."""
    style = style or DEFAULT_STYLE
    enc = resolve(hw)

    # Escape the srt path for the subtitles filter.
    esc = srt.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    vf_parts = [f"subtitles='{esc}':force_style='{style}'"]
    fmt = enc.filter()
    if fmt:
        vf_parts.append(fmt)

    cmd = ["ffmpeg", "-y"]
    cmd += enc.init_flags()
    cmd += ["-i", input_file, "-vf", ",".join(vf_parts)]
    cmd += enc.flags(crf)
    cmd += ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", output_file]

    print(f"  Burning subtitles (libass) with {enc.describe()}...")
    run_ffmpeg(cmd)


def embed_subtitles(input_file, srt, output_file):
    """Remux the SRT as soft subtitles (mov_text) — no video re-encode."""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-i", srt,
        "-map", "0:v", "-map", "0:a", "-map", "1:0",
        "-c", "copy",
        "-c:s", "mov_text",
        "-metadata:s:s:0", "language=eng",
        output_file,
    ]
    print(f"  Embedding soft subtitles (mov_text)...")
    run_ffmpeg(cmd)


def captions(input_file, output_file, soft=False, lang="en", model=None,
             style=None, srt_only=False, hw="auto", crf=23):
    validate_file(input_file)

    srt = transcribe(input_file, lang, model)
    if srt is None:
        sys.exit(1)

    if srt_only:
        dest = os.path.splitext(output_file)[0] + ".srt"
        os.replace(srt, dest)
        print(f"  ✓ SRT only: {dest}")
        return

    if soft:
        embed_subtitles(input_file, srt, output_file)
    else:
        burn_subtitles(input_file, srt, output_file, style, hw, crf)

    # Keep the srt alongside the output.
    dest = os.path.splitext(output_file)[0] + ".srt"
    if os.path.exists(dest):
        os.unlink(dest)
    os.replace(srt, dest)
    print(f"\n  ✓ Output: {output_file}\n  ✓ Subtitles: {dest}")


if __name__ == "__main__":
    from parser import parse

    ns = parse(
        sys.argv[1:],
        flags=("--soft", "--srt-only"),
        options={
            "--lang": str,
            "--model": str,
            "--style": str,
            "--hw": str,
            "--crf": int,
        },
        doc=__doc__,
    )

    if not ns.positionals:
        print(__doc__)
        sys.exit(1)

    input_file = ns.positionals[0]
    output_file = ns.output
    if len(ns.positionals) > 1:
        output_file = ns.positionals[1]

    soft = "--soft" in ns.values
    srt_only = "--srt-only" in ns.values
    lang = ns.values.get("--lang", "en")
    model = ns.values.get("--model")
    style = ns.values.get("--style")
    hw = ns.values.get("--hw", "auto")
    crf = ns.values.get("--crf", 23)

    if output_file is None:
        output_file = auto_output_path(input_file, "cap")

    captions(input_file, output_file, soft, lang, model, style, srt_only, hw, crf)
