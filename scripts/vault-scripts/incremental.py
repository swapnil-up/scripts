#!/usr/bin/env python3
import json
import random
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box
from rich.text import Text

__script = Path(__file__)
if not __script.is_absolute():
    __script = Path.cwd() / __script
VAULT_ROOT = __script.parent.parent
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

console = Console()
session_count = 0


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
        return now + timedelta(days=1)

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

    next_date = now + timedelta(days=interval)
    note.update({
        "interval": interval,
        "ease_factor": round(ease, 2),
        "repetitions": reps,
        "last_reviewed": now.strftime("%Y-%m-%d"),
        "next_review": next_date.strftime("%Y-%m-%d"),
    })
    return next_date


def promote_note(tracker, path):
    source = VAULT_ROOT / path
    rel = path.replace("unfinished/", "Reflections/")
    target = VAULT_ROOT / rel

    if target.exists():
        console.print(f"  [yellow]! Target already exists, skipping promotion.[/yellow]")
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
    console.print(f"  [green]Promoted to Reflections ({wc} words)[/green]")
    return rel


# --- UI helpers ---

def get_greeting():
    hour = datetime.now().hour
    if hour < 5:
        return "Late night"
    if hour < 12:
        return "Morning"
    if hour < 17:
        return "Afternoon"
    if hour < 22:
        return "Evening"
    return "Night"


def get_streak(tracker):
    streak = 0
    current = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    while True:
        has_review = any(
            note.get("last_reviewed") == current
            for note in tracker["notes"].values()
        )
        if not has_review:
            break
        streak += 1
        current = (datetime.strptime(current, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    return streak


def count_due(tracker):
    today = datetime.now().strftime("%Y-%m-%d")
    return sum(
        1 for note in tracker["notes"].values()
        if note.get("next_review") and note["next_review"] <= today
    )


def get_echo():
    md_files = list(REFLECTIONS_DIR.glob("*.md"))
    if not md_files:
        return None
    random.shuffle(md_files)
    for f in md_files[:5]:
        text = f.read_text(encoding="utf-8")
        in_frontmatter = False
        lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped == "---":
                in_frontmatter = not in_frontmatter
                continue
            if in_frontmatter:
                continue
            if stripped and not stripped.startswith("#") and len(stripped) > 30:
                lines.append(stripped)
        if lines:
            return random.choice(lines), f.name
    return None


def show_welcome(tracker):
    streak = get_streak(tracker)
    due = count_due(tracker)
    total = len(tracker["notes"])
    greeting = get_greeting()

    content = Text()
    content.append(f"  {greeting}\n\n", style="bold")
    content.append(f"  Review streak: {streak} day{'s' if streak != 1 else ''}\n", style="cyan")
    if due > 0:
        content.append(f"  Notes due: {due}\n", style="yellow")
    else:
        content.append(f"  Notes due: {due}\n", style="green")
    content.append(f"  Total notes: {total}\n", style="dim")

    echo = get_echo()
    if echo:
        line, source = echo
        content.append("\n")
        content.append(f"  \"{line}\"\n", style="italic")
        content.append(f"  \u2014 from {source}\n", style="dim")

    console.print(Panel(content, box=box.ROUNDED, border_style="blue"))


def show_goodbye():
    global session_count
    if session_count == 0:
        return
    content = Text()
    content.append(f"\n  Reviewed {session_count} note{'s' if session_count != 1 else ''} this session", style="bold")
    console.print(Panel(content, box=box.ROUNDED, border_style="green"))


def show_note_card(tracker, note_path):
    title = Path(note_path).name
    data = tracker["notes"][note_path]
    is_unfinished = data.get("is_unfinished", False)
    next_str = data.get("next_review")

    content = Text()
    content.append(f"  {title}", style="bold")
    if is_unfinished:
        content.append("  (fragment)", style="yellow")
    if next_str:
        next_dt = datetime.strptime(next_str, "%Y-%m-%d")
        overdue = (datetime.now() - next_dt).days
        if overdue > 0:
            content.append(f"\n  Overdue by {overdue} day{'s' if overdue > 1 else ''}", style="red")

    console.print(Panel(content, box=box.SIMPLE, border_style="cyan"))



# --- Main loop ---

def main_loop():
    global session_count
    tracker = sync_vault(load_tracker())
    save_tracker(tracker)

    show_welcome(tracker)

    while True:
        note_path = get_next_note(tracker)
        if not note_path:
            console.print("\n[yellow]No notes to review. Write something first![/yellow]")
            break

        title = Path(note_path).name
        is_unfinished = tracker["notes"][note_path].get("is_unfinished", False)

        show_note_card(tracker, note_path)

        cmd = Prompt.ask(
            "  [bold]o[/bold]pen  [bold]b[/bold]ury  [bold]s[/bold]kip  [bold]q[/bold]uit",
            choices=["o", "b", "s", "q"],
            default="o",
            show_choices=False,
        )

        if cmd == "q":
            break
        if cmd == "s":
            continue
        if cmd == "b":
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            tracker["notes"][note_path]["next_review"] = tomorrow
            tracker["notes"][note_path]["bury_count"] += 1
            save_tracker(tracker)
            console.print("  [dim]Buried until tomorrow[/dim]")
            continue

        if cmd == "o":
            full_path = VAULT_ROOT / note_path
            subprocess.run([EDITOR, str(full_path)])

            if is_unfinished:
                new_path = promote_note(tracker, note_path)
                note_path = new_path

            data = tracker["notes"][note_path]
            reps = data.get("repetitions", 0)
            interval = data.get("interval", 0)

            if data.get("first_reviewed") is None:
                rating = Prompt.ask(
                    "  [bold]s[/bold]oon  [bold]l[/bold]ater",
                    choices=["s", "l"],
                    default="s",
                    show_choices=False,
                )
                if rating in ("s", "l"):
                    update_note(tracker, note_path, rating)
                    save_tracker(tracker)
                    console.print("  [green]\u2192 First review: tomorrow[/green]")
                    session_count += 1
                else:
                    console.print("  [dim]Skipping rating, status unchanged.[/dim]")
                continue
            elif reps == 0:
                preview_soon = 1
                preview_later = 7
            elif reps == 1:
                preview_soon = 3
                preview_later = 21
            else:
                preview_soon = max(1, int(interval * 1.5))
                preview_later = max(1, int(interval * 3.0))

            rating = Prompt.ask(
                f"  [bold]s[/bold]oon ({preview_soon}d)  [bold]l[/bold]ater ({preview_later}d)",
                choices=["s", "l"],
                default="s",
                show_choices=False,
            )
            if rating in ("s", "l"):
                next_date = update_note(tracker, note_path, rating)
                save_tracker(tracker)
                label = "Soon" if rating == "s" else "Later"
                days_until = (next_date - datetime.now()).days
                console.print(
                    f"  [green]\u2192 {label}: next review in {days_until} day{'s' if days_until != 1 else ''} ({next_date.strftime('%a %b %d')})[/green]"
                )
                session_count += 1
            else:
                console.print("  [dim]Skipping rating, status unchanged.[/dim]")

    show_goodbye()


if __name__ == "__main__":
    main_loop()
