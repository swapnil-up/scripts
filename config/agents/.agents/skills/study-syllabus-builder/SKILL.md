---
name: study-syllabus-builder
description: Builds and updates learning syllabuses in the study knowledge base (~/github/study/). Use whenever the user wants to plan a learning path, add a new topic or exam, discover what to study next, register a finished topic, or update a syllabus.md file. Trigger on phrases like "what should I study next", "syllabus for X", "plan a path through Y", "I've finished Z, what's next", "add a topic/exam", "how does X relate to Y", "I'm ready to branch into Z" — even if the user doesn't say the word "syllabus" explicitly. Does NOT write flashcard content — that's anki-smith's job; this skill only manages navigation files and CSV stubs.
---

# Study Syllabus Builder

You maintain the `syllabus.md` navigation files in the user's study knowledge base at `~/github/study/`. You do **not** write flashcard content — see "Hard boundaries" below.

## Repo structure

```
syllabus.md                       ← top-level nav, lists all topics/exams
exams/
  nec-ait/
    syllabus.md                   ← exam-specific (finite, deadline-driven)
    <section>.csv
topics/
  psychology/
    syllabus.md                   ← permanent, curiosity-driven
    biases.csv
    memory.csv
```

- **Topics** are open-ended and permanent. A topic can have multiple concept CSVs — one per major concept, not one giant CSV per topic. Small, focused files are the point: an agent should never have to load a whole domain to touch one concept.
- **Exams** are finite and goal-oriented. Their syllabus.md should map directly onto the official exam syllabus/curriculum where one exists, and may track sources (past papers, official docs) that topics don't need.

## Before you touch anything

Always do this first, before creating or editing a single file:

1. **Scan before creating.** `ls`/`find`/`grep` the relevant part of the repo (and the top-level `syllabus.md`) for existing or near-duplicate topics before adding a new one. Synonyms count — "cognitive biases" and "biases" are the same topic.
2. **Read the surrounding context.** Read the parent `syllabus.md` and any topic/exam it names as related, before writing anything. Don't regenerate a whole file from scratch when updating — preserve what's already there and edit around it.
3. **If genuinely ambiguous** whether something is a new topic vs. a section of an existing one, ask — don't guess and create a fragmenting duplicate.

## Naming conventions

- Directory and file names: lowercase, hyphen-separated (`cognitive-biases/`, not `CognitiveBiases/` or `cognitive_biases/`).
- Tags mirror the path: `topic::subtopic::concept` (e.g. `psychology::biases::anchoring`).
- Related-topic references use the actual relative path or slug, not just a free-text name, so concept-linker can resolve them programmatically (e.g. `topics/programming/caching` not "caching stuff").

## Syllabus.md format

```markdown
# Topic Name

## Prerequisites
- Concept A
- Concept B

## Sections
1. [ ] Section One — beginner
2. [ ] Section Two — intermediate
3. [ ] Section Three — advanced

## Related topics
- topics/other-domain — one-line reason this connects

## Status
Last touched: YYYY-MM-DD
```

- **Checkboxes are the progress state.** `[ ]` = not started, `[~]` = in progress, `[x]` = done. This is the only durable record of what's been studied — examiner and concept-linker both read it, so keep it current rather than inferring progress fresh each time.
- **Difficulty lives inline on the section line**, not as a separate field.
- Keep syllabus.md concise — it's navigation, not content. If a section needs real explanation, that belongs in the concept CSV (via anki-smith) or a notes file, not here.

CSV files are pipe-delimited: `question|answer|extra|tags`. This skill only ever writes the header row as a stub — never actual card content.

## Hard boundaries — never do these

- **Never write real flashcard content** into a CSV. If a CSV needs cards, tell the user to run anki-smith on it — don't attempt it yourself even for "just one example card."
- **Never mark a section `[x]` done without the user confirming it.** Don't infer completion from context.
- **Never delete or restructure existing sections/topics without explicit confirmation.** Additive edits are safe by default; destructive ones aren't.

## Operations

### New topic or exam
1. Scan for duplicates/synonyms (see "Before you touch anything").
2. Decide placement: `topics/` (open-ended) vs `exams/` (finite, goal-bound).
3. Create the directory using the slug convention.
4. Write `syllabus.md` using the format above — prerequisites, sections with checkboxes and difficulty, related topics with real paths.
5. Create one empty CSV stub (header only) per major concept named in Sections — not one CSV for the whole topic unless it's genuinely a single concept.
6. Register the new topic/exam in the **parent** syllabus.md (add it to the relevant list there).
7. Run the "Connect" step below before finishing.
8. Tell the user what was created and that card content needs anki-smith next — don't silently stop short of saying that.

### Update (user has studied something, or wants a section added)
1. Read the current syllabus.md in full.
2. Apply the minimal edit — flip a checkbox, add a section, add/adjust a prerequisite. Don't rewrite unrelated parts.
3. If a new section maps to a new concept, create its CSV stub and mention it needs anki-smith.
4. Update the `Last touched` date.

### Suggest (what to study next)
1. Read the syllabus.md for the topic/area of interest, plus its listed prerequisites and related topics.
2. Use the checkboxes to see what's actually done vs. not — don't assume.
3. Propose a short, ordered path: next unfinished section in the current topic first, then 1-3 newly-unlocked branches (topics whose prerequisites are now satisfied).
4. Keep the answer to a tight list, not an essay — this is navigation, not a lecture.

### Connect (cross-references)
1. When a topic is created or meaningfully updated, check sibling and previously-seen topics for overlapping concepts (shared keywords, analogous structures).
2. Add a "Related topics" entry with a one-line reason.
3. **Make it reciprocal** — if you add A → B, check B's syllabus.md and add B → A if it's missing.
4. For deep cross-domain scanning across the whole repo, defer to the concept-linker skill rather than trying to read everything yourself.