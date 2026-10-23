#!/usr/bin/env python3
"""Merge a local override into a JSONC base file and emit plain JSON.

Usage: jsonc-merge.py BASE [LOCAL] > OUT
"""

import json
import os
import sys


def strip_jsonc(text: str) -> str:
    out = []
    i = 0
    in_string = False
    escaped = False

    while i < len(text):
        char = text[i]
        if in_string:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            i += 1
            continue

        if char == '"':
            in_string = True
            out.append(char)
            i += 1
            continue

        if char == "/" and i + 1 < len(text) and text[i + 1] == "/":
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue

        if char == "/" and i + 1 < len(text) and text[i + 1] == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue

        out.append(char)
        i += 1

    cleaned = []
    in_string = False
    escaped = False
    i = 0
    text = "".join(out)

    while i < len(text):
        char = text[i]
        if in_string:
            cleaned.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
            cleaned.append(char)
        elif char == ",":
            j = i + 1
            while j < len(text) and text[j] in " \t\r\n":
                j += 1
            if j < len(text) and text[j] in "}]":
                i += 1
                continue
            cleaned.append(char)
        else:
            cleaned.append(char)
        i += 1

    return "".join(cleaned)


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.loads(strip_jsonc(handle.read()))


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2

    merged = load(sys.argv[1])
    if len(sys.argv) > 2 and os.path.isfile(sys.argv[2]):
        merged.update(load(sys.argv[2]))

    json.dump(merged, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
