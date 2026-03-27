#!/usr/bin/env python3
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
VAULT_ROOT = SCRIPT_PATH.parent.parent

REFLECTIONS = VAULT_ROOT / "Reflections"
UNFINISHED = VAULT_ROOT / "unfinished"

UNFINISHED.mkdir(exist_ok=True)

WORD_THRESHOLD = 100


def word_count(note: Path) -> int:
    return len(note.read_text(encoding="utf-8").split())


def move_preserve_metadata(src: Path, dst: Path):
    """
    Uses atomic rename to preserve timestamps.
    Assumes same filesystem.
    """
    src.rename(dst)


print("Vault root:", VAULT_ROOT)
print("Reflections:", REFLECTIONS)
print("Unfinished:", UNFINISHED)
print("-----")


# 1. Reflections → unfinished
for note in REFLECTIONS.rglob("*.md"):
    wc = word_count(note)

    if wc < WORD_THRESHOLD:
        target = UNFINISHED / note.name
        if not target.exists():
            move_preserve_metadata(note, target)
            print(f"→ unfinished ({wc} words): {note.relative_to(VAULT_ROOT)}")


# 2. unfinished → Reflections
for note in UNFINISHED.glob("*.md"):
    wc = word_count(note)

    if wc >= WORD_THRESHOLD:
        target = REFLECTIONS / note.name
        if not target.exists():
            move_preserve_metadata(note, target)
            print(f"→ reflections ({wc} words): {note.relative_to(VAULT_ROOT)}")


print("Done.")
