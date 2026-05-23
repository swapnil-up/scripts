#!/usr/bin/env python3
import json
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
VAULT_ROOT = SCRIPT_PATH.parent.parent

REFLECTIONS = VAULT_ROOT / "Reflections"
UNFINISHED = VAULT_ROOT / "unfinished"
TRACKER_FILE = VAULT_ROOT / ".reflections_queue.json"

UNFINISHED.mkdir(exist_ok=True)

WORD_THRESHOLD = 350


def word_count(note: Path) -> int:
    return len(note.read_text(encoding="utf-8").split())


def move_preserve_metadata(src: Path, dst: Path):
    src.rename(dst)


def load_tracker():
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE) as f:
            return json.load(f)
    return {"notes": {}}


def save_tracker(tracker):
    with open(TRACKER_FILE, "w") as f:
        json.dump(tracker, f, indent=2)


def rekey(tracker, old_key, new_key, is_unfinished):
    if old_key in tracker["notes"]:
        entry = tracker["notes"].pop(old_key)
        entry["is_unfinished"] = is_unfinished
        tracker["notes"][new_key] = entry


if __name__ == "__main__":
    print("Vault root:", VAULT_ROOT)
    print("Reflections:", REFLECTIONS)
    print("Unfinished:", UNFINISHED)
    print("-----")

    tracker = load_tracker()
    changed = False

    # 1. Reflections → unfinished
    for note in REFLECTIONS.rglob("*.md"):
        wc = word_count(note)

        if wc < WORD_THRESHOLD:
            target = UNFINISHED / note.name
            if not target.exists():
                old_key = str(note.relative_to(VAULT_ROOT))
                new_key = str(target.relative_to(VAULT_ROOT))
                move_preserve_metadata(note, target)
                rekey(tracker, old_key, new_key, is_unfinished=True)
                changed = True
                print(f"→ unfinished ({wc} words): {new_key}")

    # 2. unfinished → Reflections
    for note in UNFINISHED.glob("*.md"):
        wc = word_count(note)

        if wc >= WORD_THRESHOLD:
            target = REFLECTIONS / note.name
            if not target.exists():
                old_key = str(note.relative_to(VAULT_ROOT))
                new_key = str(target.relative_to(VAULT_ROOT))
                move_preserve_metadata(note, target)
                rekey(tracker, old_key, new_key, is_unfinished=False)
                changed = True
                print(f"→ reflections ({wc} words): {new_key}")

    if changed:
        save_tracker(tracker)
        print("Tracker updated.")

    print("Done.")
