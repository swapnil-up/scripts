#!/usr/bin/env python3
import sys
from utils import validate_file, print_video_info

if __name__ == "__main__":
    from parser import parse

    ns = parse(sys.argv[1:], doc=None)
    if not ns.positionals:
        print("Usage: info.py VIDEO_FILE")
        print("Example: info.py workout.mp4")
        sys.exit(1)

    validate_file(ns.positionals[0])
    print_video_info(ns.positionals[0])
