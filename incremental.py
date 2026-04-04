import os
import json
import random
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
VAULT_ROOT = Path.home() / "obsidian-vault"
REFLECTIONS_DIR = VAULT_ROOT / "Reflections"
TRACKER_FILE = VAULT_ROOT / ".reflections_queue.json"
EDITOR = "nvim"

def load_tracker():
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE, 'r') as f:
            return json.load(f)
    return {"notes": {}}

def sync_vault(tracker):
    """Adds new notes and removes deleted ones from the tracker."""
    current_files = {str(p.relative_to(VAULT_ROOT)) for p in REFLECTIONS_DIR.glob("*.md")}
    tracked_files = set(tracker["notes"].keys())

    # Add new
    for f in current_files - tracked_files:
        tracker["notes"][f] = {
            "last_reviewed": None,
            "next_review": datetime.now().strftime("%Y-%m-%d"),
        }
    
    # Remove deleted
    for f in tracked_files - current_files:
        del tracker["notes"][f]
    
    return tracker

def get_next_note(tracker):
    """Logic: Grab the top 5 most 'overdue' notes and pick 1 randomly."""
    if not tracker["notes"]:
        return None
        
    # Sort all notes by next_review date
    sorted_notes = sorted(tracker["notes"].items(), key=lambda x: x[1]["next_review"])
    
    # Pick from the top 5 (or fewer if vault is small)
    pool_size = min(5, len(sorted_notes))
    candidate_pool = sorted_notes[:pool_size]
    
    selected_note = random.choice(candidate_pool)
    return selected_note[0]

def update_note(tracker, path, choice):
    """Scheduling with RNG 'Fuzz'."""
    now = datetime.now()
    
    if choice == 's':  # Soon
        # Base: 2 days. Fuzz: +/- 1 day
        days = 2 + random.choice([-1, 0, 1])
    else:  # Later
        # Base: 20 days. Fuzz: +/- 4 days
        days = 20 + random.randint(-4, 4)
    
    # Ensure we never schedule for the past (minimum 1 day)
    days = max(1, days)
    
    tracker["notes"][path].update({
        "last_reviewed": now.strftime("%Y-%m-%d"),
        "next_review": (now + timedelta(days=days)).strftime("%Y-%m-%d")
    })

def main_loop():
    tracker = sync_vault(load_tracker())
    
    while True:
        note_path = get_next_note(tracker)
        if not note_path:
            print("No notes found in Reflections!")
            break
            
        print(f"\n--- [ Next Note: {Path(note_path).name} ] ---")
        cmd = input("[o]pen, [s]kip, [q]uit? ").lower()
        
        if cmd == 'q': 
            break
        if cmd == 's': 
            continue 
        
        if cmd == 'o':
            full_path = VAULT_ROOT / note_path
            # Open Neovim and wait
            subprocess.run([EDITOR, str(full_path)])
            
            # Rate it
            rating = input("Rate: [s]oon or [l]ater? ").lower()
            if rating in ['s', 'l']:
                update_note(tracker, note_path, rating)
                # Save after every successful edit
                with open(TRACKER_FILE, 'w') as f:
                    json.dump(tracker, f, indent=2)
            else:
                print("Skipping rating, status unchanged.")

if __name__ == "__main__":
    main_loop()