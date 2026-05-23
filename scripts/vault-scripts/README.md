# Reflection Review — a spaced-repetition writing system

## The problem

Notes get written and never revisited. The act of writing locks in a single pass of thinking, but the best ideas need repeated engagement to compound. This system applies Anki-style spaced repetition to a folder of markdown notes, so important thoughts resurface frequently and forgettable ones drift out naturally.

## The two scripts

### `incremental.py` — the review loop

The daily driver. Opens an interactive terminal session that:

1. Picks a note biased by how overdue it is, whether it's unfinished (<350 words, gets 2.5x priority), and whether it's never been reviewed (+3 recency boost)
2. Shows you the title, lets you open in nvim, bury it to tomorrow, skip, or quit
3. After editing, you rate the note **soon** (important, want to engage more) or **later** (not as important)
4. Scheduling follows an SM-2 inspired curve:

| Reps | Soon | Later |
|------|------|-------|
| 0 (first real rating) | 1 day | 7 days |
| 1 | 3 days | 21 days |
| 2+ | interval × 1.5 | interval × 3.0 |

- Ease factor drifts up (+0.1) on Soon, down (−0.15) on Later
- If a note from `unfinished/` reaches 350+ words after editing, it's auto-promoted to `Reflections/` with a fresh schedule
- **Bury** ([b]) defers to tomorrow without touching the schedule — like Anki's bury
- First review is always a 1-day fast nudge regardless of rating, to get acquainted

### `move_unfinished.py` — the batch utility

Scans both directories and moves notes across the 350-word threshold:

- `Reflections/` → `unfinished/` if under 350 words
- `unfinished/` → `Reflections/` if 350+ words

Also rekeys the tracker so scheduling history isn't lost. Run this occasionally (or after importing a batch of notes) to keep the folders aligned.

## How the folders work

| Folder | Purpose | Word count |
|--------|---------|------------|
| `Reflections/` | Finished, substantial writing | 350+ words |
| `unfinished/` | Seeds, fragments, half-thoughts | <350 words |

The unfinished notes get a 2.5x priority multiplier in selection, so they surface more often. The goal is to expand each one to 350 words through repeated engagement, then auto-promote it to Reflections.

- `last_reviewed` — when you last rated the note
- `next_review` — when it's due again
- `interval` — current gap in days (grows unbounded)
- `ease_factor` — Anki-style multiplier, starts at 2.5
- `repetitions` — successful review count
- `first_reviewed` — set on first rating (triggers the fast nudge)
- `is_unfinished` — whether the file lives in `unfinished/`
- `bury_count` — how many times you've deferred it (no schedule impact)

## Workflow

```
# Daily review session
python3 scripts/incremental.py

# After importing a batch of new notes, realign folders
python3 scripts/move_unfinished.py
```

## Git subtree — tracking scripts elsewhere

These two scripts are tracked in this vault AND in `~/github/scripts` via `git subtree`. The vault's primary branch is `sync`.

### Update flow (after changing vault scripts)

```bash
# 1. Commit on sync as usual, then regenerate the split branch
cd ~/github/obsidian-vault
git checkout sync
git subtree split --prefix=scripts -b vault-scripts

# 2. Pull into the scripts repo
cd ~/github/scripts
git subtree pull --prefix=scripts/vault-scripts obsidian-vault vault-scripts
```

The `vault-scripts` branch is a synthetic split — it gets force-replaced each time. Never merge it into `sync`.

## Design notes

The semantics invert Anki's normal mapping:
- **Anki**: "Hard" → short interval (you struggled), "Easy" → long interval (you knew it)
- **Here**: "Soon" → short interval (you want to engage more), "Later" → long interval (can wait)

Both converge to the same math. The labeling fits the writing context: important thoughts should resurface soon, not be buried by a long interval.
