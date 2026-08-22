---
name: study-csv-builder
description: Builds the master Anki import CSV from all topic/exam CSVs in the study knowledge base (~/github/study/). Use when the user wants to import new cards into Anki, rebuild after adding/modifying CSV files, or understand the import workflow. Triggered by "rebuild the deck", "build the master CSV", "import new cards", "update Anki", "build.sh".
---

# Study CSV Builder

You manage the Anki import pipeline for `~/github/study/`.

## The build script

`build.sh` at the repo root walks `topics/` and `exams/`, finds all `*.csv` files, skips stubs (header-only = 1 line), concatenates card rows into `master-anki.csv`.

```bash
bash build.sh
```

## What it does

- Scans `topics/**/*.csv` and `exams/**/*.csv`
- Skips files with only a header line (these are stubs created by syllabus-builder, not yet populated)
- Concatenates all card rows into `master-anki.csv`
- Result: one pipe-delimited CSV with `question|answer|extra|tags`

## Import into Anki

1. Open Anki → File → Import
2. Select `master-anki.csv`
3. Set **Type** to Basic (or your preferred note type)
4. Set **Fields separated by** to `|`
5. Map fields: 1→Front, 2→Back, 3→Extra, 4→Tags
6. Import

Re-importing is safe — Anki matches on Front field and skips duplicates. Existing cards are untouched; only genuinely new cards are added.

## When to rebuild

- After anki-smith generates new cards (new rows in an existing CSV or a new CSV)
- After adding a new topic/exam (syllabus-builder creates the stub, anki-smith fills it)
- Before a study session where you want your latest cards in Anki

## Tag convention

Tags mirror the file path: `exam::nec-ait::section1` or `topic::psychology::biases`. This lets you create filtered decks in Anki for any subset.
