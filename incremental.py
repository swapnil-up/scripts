import json
import random
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
VAULT_ROOT = SCRIPT_PATH.parent.parent
REFLECTIONS_DIR = VAULT_ROOT / "Reflections"
UNFINISHED_DIR = VAULT_ROOT / "unfinished"
TRACKER_FILE = VAULT_ROOT / ".reflections_queue.json"
EDITOR = "nvim"
PROMOTION_THRESHOLD = 350

DEFAULT_NOTE = {
    "last_reviewed": None,
    "next_review": None,
    "interval": 0,
    "ease_factor": 2.5,
    "repetitions": 0,
    "first_reviewed": None,
    "is_unfinished": False,
    "bury_count": 0,
}


def load_tracker():
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE, "r") as f:
            return json.load(f)
    return {"notes": {}}


def save_tracker(tracker):
    with open(TRACKER_FILE, "w") as f:
        json.dump(tracker, f, indent=2)


def word_count(path):
    return len(Path(path).read_text(encoding="utf-8").split())


def sync_vault(tracker):
    current_files = set()

    for p in REFLECTIONS_DIR.glob("*.md"):
        key = str(p.relative_to(VAULT_ROOT))
        current_files.add(key)
        if key not in tracker["notes"]:
            entry = dict(DEFAULT_NOTE)
            entry["next_review"] = datetime.now().strftime("%Y-%m-%d")
            tracker["notes"][key] = entry

    for p in UNFINISHED_DIR.glob("*.md"):
        key = str(p.relative_to(VAULT_ROOT))
        current_files.add(key)
        if key not in tracker["notes"]:
            entry = dict(DEFAULT_NOTE)
            entry["next_review"] = datetime.now().strftime("%Y-%m-%d")
            entry["is_unfinished"] = True
            tracker["notes"][key] = entry

    for key in list(tracker["notes"].keys()):
        if key not in current_files:
            del tracker["notes"][key]

    for note in tracker["notes"].values():
        for field, default in DEFAULT_NOTE.items():
            if field not in note:
                note[field] = default
        note.pop("again_count", None)

    return tracker


def compute_score(note_entry, now):
    next_review_str = note_entry.get("next_review")
    if next_review_str:
        next_review = datetime.strptime(next_review_str, "%Y-%m-%d")
        overdue = (now - next_review).days
    else:
        overdue = 0

    score = overdue + 1
    if note_entry.get("is_unfinished"):
        score *= 2.5
    if note_entry.get("first_reviewed") is None:
        score += 3
    score += random.uniform(0, 2)
    return score


def get_next_note(tracker):
    if not tracker["notes"]:
        return None

    now = datetime.now()
    scored = [
        (compute_score(data, now), path)
        for path, data in tracker["notes"].items()
    ]
    scored.sort(key=lambda x: -x[0])
    pool_size = min(5, len(scored))
    return random.choice(scored[:pool_size])[1]


def update_note(tracker, path, rating):
    note = tracker["notes"][path]
    now = datetime.now()

    if note["first_reviewed"] is None:
        note["next_review"] = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        note["first_reviewed"] = now.strftime("%Y-%m-%d")
        note["last_reviewed"] = now.strftime("%Y-%m-%d")
        return

    interval = note.get("interval", 0)
    reps = note.get("repetitions", 0)
    ease = note.get("ease_factor", 2.5)

    if reps == 0:
        interval = 1 if rating == "s" else 7
        reps = 1
    elif reps == 1:
        interval = 3 if rating == "s" else 21
        reps += 1
    else:
        multiplier = 1.5 if rating == "s" else 3.0
        interval = max(1, int(interval * multiplier))
        reps += 1

    if rating == "s":
        ease = min(3.0, ease + 0.1)
    else:
        ease = max(1.3, ease - 0.15)

    note.update({
        "interval": interval,
        "ease_factor": round(ease, 2),
        "repetitions": reps,
        "last_reviewed": now.strftime("%Y-%m-%d"),
        "next_review": (now + timedelta(days=interval)).strftime("%Y-%m-%d"),
    })


def promote_note(tracker, path):
    source = VAULT_ROOT / path
    rel = path.replace("unfinished/", "Reflections/")
    target = VAULT_ROOT / rel

    if target.exists():
        print(f"  ! Target already exists at {rel}, skipping promotion.")
        return path

    wc = word_count(source)
    if wc < PROMOTION_THRESHOLD:
        return path

    source.rename(target)

    entry = tracker["notes"].pop(path)
    entry["is_unfinished"] = False
    entry["interval"] = 0
    entry["repetitions"] = 0
    entry["first_reviewed"] = datetime.now().strftime("%Y-%m-%d")
    entry["next_review"] = None
    tracker["notes"][rel] = entry

    save_tracker(tracker)
    print(f"  Promoted to Reflections ({wc} words)")
    return rel


def main_loop():
    tracker = sync_vault(load_tracker())
    save_tracker(tracker)

    while True:
        note_path = get_next_note(tracker)
        if not note_path:
            print("No notes found!")
            break

        title = Path(note_path).name
        is_unfinished = tracker["notes"][note_path].get("is_unfinished", False)
        flag = " [f]" if is_unfinished else ""
        print(f"\n--- [ {title}{flag} ] ---")

        cmd = input("[o]pen, [b]ury, [s]kip, [q]uit? ").strip().lower()

        if cmd == "q":
            break
        if cmd == "s":
            continue
        if cmd == "b":
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            tracker["notes"][note_path]["next_review"] = tomorrow
            tracker["notes"][note_path]["bury_count"] += 1
            save_tracker(tracker)
            continue

        if cmd == "o":
            full_path = VAULT_ROOT / note_path
            subprocess.run([EDITOR, str(full_path)])

            if is_unfinished:
                note_path = promote_note(tracker, note_path)

            rating = input("Rate: [s]oon or [l]ater? ").strip().lower()
            if rating in ("s", "l"):
                update_note(tracker, note_path, rating)
                save_tracker(tracker)
            else:
                print("Skipping rating, status unchanged.")


if __name__ == "__main__":
    main_loop()
