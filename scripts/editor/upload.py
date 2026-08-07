#!/usr/bin/env python3
"""
Auto-upload a processed video to YouTube as an unlisted video, via the
youtubeuploader CLI binary (bypasses the browser).

First run needs a one-time for OAuth (browser). Subsequent runs use a cached
token. Requires client_secrets.json — create it via the youtubeuploader README.

Usage:
    upload.py video.mp4 --title "My video" --desc "notes..."
    upload.py video.mp4 --title "X" --privacy unlisted --tags a,b,c
    upload.py --check           # verify uploader + secrets are configured
"""

import sys
import os
import json
import subprocess
import datetime
from utils import validate_file, YT_UPLOADER, YT_SECRETS, YT_TOKEN

PRIVACY = {"public", "unlisted", "private"}


def check_config():
    missing = []
    if not os.path.exists(YT_UPLOADER):
        missing.append(f"youtubeuploader binary: {YT_UPLOADER}")
    if not os.path.exists(YT_SECRETS):
        missing.append(f"client_secrets.json: {YT_SECRETS}")
    if not os.path.exists(YT_TOKEN):
        missing.append(f"OAuth token (first run will create it): {YT_TOKEN}")
    if missing:
        print("Missing configuration:")
        for m in missing:
            print(f"  - {m}")
        print("\nDownload youtubeuploader and set up client_secrets.json per:")
        print("  https://github.com/porjo/youtubeuploader")
        return False
    return True


def upload(input_file, title, desc="", tags=None, privacy="unlisted",
           category_id=None, thumbnail=None, quiet=True):
    validate_file(input_file)
    if privacy not in PRIVACY:
        print(f"  Invalid privacy: {privacy} (choose from {sorted(PRIVACY)})")
        sys.exit(1)
    if not check_config():
        sys.exit(1)

    cmd = [YT_UPLOADER, "-filename", os.path.abspath(input_file),
           "-secrets", YT_SECRETS, "-cache", YT_TOKEN,
           "-title", title, "-privacy", privacy]
    if desc:
        cmd += ["-description", desc]
    if tags:
        cmd += ["-tags", ",".join(tags)]
    if category_id:
        cmd += ["-categoryId", str(category_id)]
    if thumbnail:
        validate_file(thumbnail)
        cmd += ["-thumbnail", os.path.abspath(thumbnail)]
    if quiet:
        cmd += ["-quiet"]

    print(f"  Uploading (as {privacy}):")
    print(f"    file : {input_file}")
    print(f"    title: {title}")
    if quiet:
        print("  (quiet mode — send SIGUSR1 for progress)")

    result = subprocess.run(cmd, capture_output=not quiet, text=not quiet)
    if result.returncode != 0:
        print(f"  Upload failed (exit {result.returncode}).", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(1)

    # Try to extract the YouTube URL from output.
    url = None
    text = (result.stdout or "") + (result.stderr or "")
    for token in ("youtu.be/", "youtube.com/watch", "youtube.com/embed"):
        if token in text:
            import re
            m = re.search(r"(https?://\S*" + token + r"\S*)", text)
            if m:
                url = m.group(1).rstrip('.,)')
                break

    ts = datetime.datetime.now().isoformat(timespec="seconds")
    record = {"file": os.path.abspath(input_file), "title": title, "url": url,
              "privacy": privacy, "tags": tags, "uploaded_at": ts}
    _log_upload(record)

    if url:
        print(f"\n  ✓ Uploaded: {url}")
    else:
        print(f"\n  ✓ Upload complete (URL not captured — check your channel).")
    return record


def _log_upload(record):
    """Append a record to ~/vedit/uploads.json for the trash collector."""
    path = os.path.join(os.path.expanduser("~/vedit"), "uploads.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    entries = []
    if os.path.exists(path):
        try:
            with open(path) as f:
                entries = json.load(f)
        except (json.JSONDecodeError, OSError):
            entries = []
    entries.append(record)
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)


if __name__ == "__main__":
    from parser import parse

    ns = parse(
        sys.argv[1:],
        flags=("--quiet", "--check"),
        options={
            "--title": str,
            "--desc": str,
            "--description": str,
            "--tags": lambda s: [t.strip() for t in s.split(",") if t.strip()],
            "--privacy": str,
            "--category": str,
            "--thumbnail": str,
        },
        doc=__doc__,
    )

    if "--check" in ns.values:
        if check_config():
            print("Configuration OK.")
            sys.exit(0)
        sys.exit(1)

    pos = ns.positionals
    input_path = pos[0] if pos else None
    title = ns.values.get("--title") or (pos[1] if len(pos) > 1 else None)
    desc = ns.values.get("--desc") or ns.values.get("--description")
    tags = ns.values.get("--tags")
    privacy = ns.values.get("--privacy", "unlisted")
    category_id = ns.values.get("--category")
    thumbnail = ns.values.get("--thumbnail")
    quiet = "--quiet" in ns.values

    if input_path is None or title is None:
        print(__doc__)
        sys.exit(1)

    upload(input_path, title, desc, tags, privacy, category_id, thumbnail, quiet)