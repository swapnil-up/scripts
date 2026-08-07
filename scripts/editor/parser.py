#!/usr/bin/env python3
"""
Thin shared CLI parser for the editor Stages.

Owns the only things the hand-rolled parsers were duplicating:
  - the flag-vs-positional walk loop,
  - the `-o` / `--output` spelling difference (both accepted the same way),
  - the "Unknown option" error + exit(1) convention,
  - value-type coercion for options that take a number.

Each Stage still declares its own flags and decides what to do with the
collected positionals; this module does not invent domain logic for them.

Usage:
    from parser import parse
    ns = parse(argv, flags=("--mute", "--mix"),
               options={"--volume": float, "--add": str})
    ns.positionals   -> ["in.mp4", "out.mp4"]
    ns.output         -> the -o / --output value, or None
    ns.values["--volume"] -> 0.5  (coerced to float)
"""

import sys


def _error_usage(doc):
    sys.exit(doc.strip() if doc else 1)


class Namespace:
    """Result of a parse: positionals, resolved output, coerced option values."""

    def __init__(self, positionals, output, values):
        self.positionals = positionals
        self.output = output
        self.values = values


def parse(argv, flags=(), options=None, output_names=("-o", "--output"), doc=None):
    """
    Parse a Stage's argv.

    argv           list of raw arguments (sys.argv[1:]).
    flags          tuple of boolean flags (presence -> True).
    options        dict {name: converter} for options that consume a value.
                   converters: floats for numbers, str (default) for strings.
    output_names   spellings accepted for the shared output flag.
    doc            usage text printed on a hard failure (unset when arg expected).

    Returns Namespace with:
      positionals   -> all non-flag args, in order (input first, output last).
      output        -> the -o / --output value if given, else None.
      values        -> {flag: True} for flags, {name: coerced} for options.
    """
    if options is None:
        options = {}
    values = {}
    positionals = []
    output = None
    i = 0
    while i < len(argv):
        arg = argv[i]

        if arg in output_names:
            if i + 1 >= len(argv):
                print(f"  {arg} requires a value")
                _error_usage(doc)
            output = argv[i + 1]
            i += 2
            continue

        if arg in flags:
            values[arg] = True
            i += 1
            continue

        if arg in options:
            if i + 1 >= len(argv):
                print(f"  {arg} requires a value")
                _error_usage(doc)
            raw = argv[i + 1]
            conv = options[arg]
            try:
                values[arg] = conv(raw)
            except (ValueError, TypeError):
                print(f"  Invalid value for {arg}: {raw}")
                _error_usage(doc)
            i += 2
            continue

        if arg.startswith("-") and arg != "-":
            print(f"  Unknown option: {arg}")
            _error_usage(doc)

        positionals.append(arg)
        i += 1

    return Namespace(positionals, output, values)