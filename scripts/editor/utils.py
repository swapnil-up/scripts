#!/usr/bin/env python3
import subprocess
import sys
import os
import json
import datetime

VEDIT_DIR = os.path.expanduser("~/vedit")
LOG_FILE = os.path.join(VEDIT_DIR, "edit.log")


def get_vedit_dir():
    """Return the vedit data directory, creating it if needed."""
    os.makedirs(VEDIT_DIR, exist_ok=True)
    return VEDIT_DIR


def log_init(tool_name):
    """Start a fresh log for this session (overwrites previous log)."""
    os.makedirs(VEDIT_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "w") as f:
        f.write(f"[{ts}] === {tool_name} ===\n")


def log(message):
    """Append a timestamped message to the edit log."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {message}\n")


def sidecar_path(input_file, extension):
    """
    Return the path for a sidecar file in ~/vedit/.
    e.g. sidecar_path('/some/path/myvideo.mp4', 'markers.json')
         -> '~/vedit/myvideo.markers.json'
    """
    stem = os.path.splitext(os.path.basename(input_file))[0]
    return os.path.join(get_vedit_dir(), f"{stem}.{extension}")


def auto_output_path(input_file, suffix, ext=None):
    """
    Build an auto-generated output path next to the input file.
    e.g. auto_output_path('/some/path/myvideo.mp4', 'cut')
         -> '/some/path/myvideo_cut.mp4'
    """
    directory = os.path.dirname(os.path.abspath(input_file))
    stem = os.path.splitext(os.path.basename(input_file))[0]
    if ext is None:
        ext = os.path.splitext(input_file)[1].lstrip(".")
    return os.path.join(directory, f"{stem}_{suffix}.{ext}")


def run_ffmpeg(cmd, show_progress=True):
    """Execute ffmpeg command and handle errors"""
    if show_progress:
        # Show ffmpeg output for progress
        result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}", file=sys.stderr)
            sys.exit(1)
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}", file=sys.stderr)
            sys.exit(1)
    return result


def get_duration(video_file):
    """Get video duration in seconds"""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_file,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error getting duration: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return float(result.stdout.strip())


def get_video_info(video_file):
    """Get comprehensive video information"""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        video_file,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error getting video info: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(result.stdout)

    # Extract useful info
    video_stream = next(
        (s for s in data["streams"] if s["codec_type"] == "video"), None
    )
    audio_stream = next(
        (s for s in data["streams"] if s["codec_type"] == "audio"), None
    )

    info = {
        "duration": float(data["format"].get("duration", 0)),
        "size_mb": float(data["format"].get("size", 0)) / (1024 * 1024),
        "bitrate": int(data["format"].get("bit_rate", 0)),
    }

    if video_stream:
        info.update(
            {
                "width": video_stream.get("width"),
                "height": video_stream.get("height"),
                "fps": eval(
                    video_stream.get("r_frame_rate", "0/1")
                ),  # e.g. "30/1" -> 30
                "codec": video_stream.get("codec_name"),
            }
        )

    if audio_stream:
        info["has_audio"] = True
        info["audio_codec"] = audio_stream.get("codec_name")
    else:
        info["has_audio"] = False

    return info


def validate_file(filepath):
    """Check if file exists"""
    if not os.path.isfile(filepath):
        print(f"Error: {filepath} not found")
        sys.exit(1)


def format_time(seconds):
    """Convert seconds to HH:MM:SS.ms format"""
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{int(hours):02d}:{int(mins):02d}:{secs:06.3f}"


def parse_time(time_str):
    """
    Parse time string to seconds
    Accepts: "10", "1:30", "01:30:45", "00:01:30.5"
    """
    time_str = time_str.strip()

    # Already in seconds
    try:
        return float(time_str)
    except ValueError:
        pass

    # Parse HH:MM:SS or MM:SS format
    parts = time_str.split(":")
    if len(parts) == 3:  # HH:MM:SS
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:  # MM:SS
        m, s = parts
        return int(m) * 60 + float(s)
    else:
        print(f"Error: Invalid time format '{time_str}'")
        print("Use: seconds (10), MM:SS (1:30), or HH:MM:SS (01:30:45)")
        sys.exit(1)


def print_video_info(video_file):
    """Print formatted video information"""
    info = get_video_info(video_file)

    print(f"\nVideo: {video_file}")
    print(f"  Duration: {format_time(info['duration'])} ({info['duration']:.1f}s)")
    print(f"  Resolution: {info.get('width', '?')}x{info.get('height', '?')}")
    print(f"  FPS: {info.get('fps', '?')}")
    print(f"  Codec: {info.get('codec', '?')}")
    print(f"  Size: {info['size_mb']:.1f} MB")
    print(f"  Bitrate: {info['bitrate'] / 1000:.0f} kbps")
    print(f"  Audio: {'Yes' if info['has_audio'] else 'No'}")
    if info["has_audio"]:
        print(f"  Audio Codec: {info.get('audio_codec', '?')}")
    print()
