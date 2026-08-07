#!/usr/bin/env python3
"""
Hardware encoder module: resolve the best available encoder and translate a
resolved encoder into the ffmpeg arguments a Stage needs.

Every fact that varies with the encoder kind (codec flags, pixel-format filter,
VAAPI device setup) lives here. The publish tail (audio codec + faststart) is
NOT an encoder concern and stays with the calling Stage.

Usage:
    from encoder import resolve
    enc = resolve("vaapi")            # probe/force -> Encoder("vaapi", device)
    enc = resolve("auto")             # detect best (vaapi > nvenc > qsv > cpu)
    enc.flags(crf=23)                 # -> ["-c:v", "h264_vaapi", "-qp", "23", ...]
    enc.filter()                      # -> "format=nv12,hwupload" | "format=yuv420p" | None
    enc.init_flags()                  # -> ["-vaapi_device", device] | []
"""

import glob
import os
import shutil
import subprocess

ENCODER_NAMES = {"auto", "vaapi", "nvenc", "qsv", "cpu"}


class Encoder:
    """A resolved hardware encoder: kind, optional device, and its ffmpeg flags."""

    def __init__(self, kind, device=None):
        self.kind = kind
        self.device = device

    def describe(self):
        if self.kind == "cpu":
            return "CPU (libx264)"
        label = self.kind.upper()
        return f"{label} ({self.device})" if self.device else label

    def flags(self, crf=23):
        """Codec + quality flags for this encoder's -c:v. Default CRF is 23 everywhere."""
        if self.kind == "vaapi":
            if not self.device:
                raise ValueError("VAAPI encoder requires a device (pass via resolve).")
            return ["-c:v", "h264_vaapi", "-qp", str(crf), "-bf", "0"]
        if self.kind == "nvenc":
            return ["-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", str(crf)]
        if self.kind == "qsv":
            return ["-c:v", "h264_qsv", "-global_quality", str(crf)]
        return ["-c:v", "libx264", "-preset", "fast", "-crf", str(crf)]

    def filter(self):
        """Pixel-format filter needed before the encoder's -c:v, or None."""
        if self.kind == "vaapi":
            return "format=nv12,hwupload"
        return "format=yuv420p"

    def init_flags(self):
        """Flags to set up the encoder's device (must appear before the input)."""
        if self.kind == "vaapi" and self.device:
            return ["-vaapi_device", self.device]
        return []


def _vaapi_devices():
    """Return renderD* devices that can actually encode h264 via VAAPI."""
    working = []
    for dev in sorted(glob.glob("/dev/dri/renderD*")):
        test_out = "/tmp/vedit_vaapi_test.mp4"
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-init_hw_device", f"vaapi=va:{dev}",
            "-f", "lavfi", "-i", "testsrc=duration=0.1:size=160x120:rate=10",
            "-vf", "format=nv12,hwupload",
            "-c:v", "h264_vaapi",
            test_out,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            if os.path.exists(test_out):
                os.unlink(test_out)
        except OSError:
            pass
        if result.returncode == 0:
            working.append(dev)
    return working


def _qsv_available():
    """Check whether the local ffmpeg can encode with h264_qsv."""
    test_out = "/tmp/vedit_qsv_test.mp4"
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i", "testsrc=duration=0.1:size=160x120:rate=10",
        "-c:v", "h264_qsv",
        test_out,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        if os.path.exists(test_out):
            os.unlink(test_out)
    except OSError:
        pass
    return result.returncode == 0


def resolve(hw="auto"):
    """
    Pick the best available hardware encoder.

    Order: vaapi (probed on real devices) > nvenc > qsv > cpu (libx264).
    When forced, the kind is fixed but the real device is still resolved.
    """
    force = hw
    if force and force != "auto":
        if force == "vaapi":
            vaapi = _vaapi_devices()
            if not vaapi:
                raise ValueError("No usable VAAPI device found on this system.")
            return Encoder("vaapi", vaapi[0])
        if force == "nvenc":
            return Encoder("nvenc")
        if force == "qsv":
            return Encoder("qsv")
        if force == "cpu":
            return Encoder("cpu")
        raise ValueError(f"Unknown encoder: {force}")

    vaapi = _vaapi_devices()
    if vaapi:
        return Encoder("vaapi", vaapi[0])

    if shutil.which("nvidia-smi"):
        return Encoder("nvenc")

    if glob.glob("/dev/dri/renderD*") and _qsv_available():
        return Encoder("qsv")

    return Encoder("cpu")
