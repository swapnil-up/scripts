# Reflection Review — tending and spaced editing

## The problem

Notes get written and never revisited. The act of writing locks in a single pass of thinking, but the best ideas need repeated engagement to compound. This system keeps important thoughts moving with two loops: connect related notes, then revisit and revise the notes themselves.

## `tend.py` — the on-demand tending loop

The main entry point. It works on `unfinished/` and `Reflections/` and writes a generated dashboard to `Reflections/Tending.md`.

```bash
# Open the dashboard and tend the top 3 notes
python3 scripts/tend.py

# Read-only audit
python3 scripts/tend.py --stats

# Rebuild Reflections/Tending.md without opening a session
python3 scripts/tend.py --refresh

# Link suggestions for one note
python3 scripts/tend.py --suggest "Life is incremental"

# Semantic mode is on by default. Disable it for a fast lexical-only run:
python3 scripts/tend.py --no-semantic --suggest "Life is incremental"

# Rebuild the local embedding index
python3 scripts/tend.py --reindex

# Show index path, model, and note/chunk counts
python3 scripts/tend.py --index-info

# Only notes with no outgoing links
python3 scripts/tend.py --links

# Revisit notes that are due for revision
python3 scripts/tend.py --revisit

# Backlog cleanup: keep, merge, archive, delete
python3 scripts/tend.py --triage
```

The dashboard surfaces notes due for revisit, link debt, neglect, shortness, empty files, unlinked mentions, and duplicate candidates. `tend.py` can update `status` and review state in frontmatter and, after confirmation, insert links either in place or under a `## Related` heading.

### Revisiting

`tend --revisit` is the spaced-editing loop. It selects overdue or never-scheduled notes, shows the note's age, review state, and links, and offers:

```
[o]pen [a]ppend [r]elate [s]oon [l]ater [b]ury [x]archive [d]elete [n]ext [q]uit
```

- **open** launches the editor. After editing, you are asked to schedule the next revisit.
- **append** adds a dated `## Revisit YYYY-MM-DD` heading before opening, so each pass can leave a trace. Good prompts: *What still holds? What changed? What would you cut?*
- **relate** runs the normal link suggestions without leaving the revisit session.
- **soon / later** schedule from the current interval. **bury** moves the next revisit to tomorrow without increasing the review count.
- Notes in `unfinished/` that reach 350 words are promoted to `Reflections/` automatically.

Scheduling is stored in frontmatter, so it travels with the note through merges and renames:

| Field | Meaning |
|-------|---------|
| `reviewed` | Last date the note was actually revisited |
| `review_next` | Next due date |
| `review_interval` | Current gap in days |
| `review_ease` | Multiplier for longer intervals, starts at 2.5 |
| `review_count` | Number of completed revisits |

The schedule is deliberately simple:

| Completed revisits | Soon | Later |
|--------------------|------|-------|
| 0 | 1 day | 7 days |
| 1 | 3 days | 21 days |
| 2+ | interval × 1.5 | interval × ease |

`soon` lowers ease by 0.15 (minimum 1.3); `later` raises it by 0.10 (maximum 3.2). Notes without `review_next` are due, including all notes written before this loop existed. The legacy `.reflections_queue.json` tracker is no longer read; frontmatter is authoritative.

### Semantic mode

Semantic mode is on by default and adds candidate links from local `all-MiniLM-L6-v2` embeddings. It is a hybrid, not a replacement for the lexical checks:

- Mentions, title patterns, and shared terms stay first because they are precise and explainable.
- Embeddings add paraphrases and novel connections, shown last with a similarity score and a supporting snippet.
- Nothing is linked automatically; every suggestion still needs confirmation.
- Embeddings run locally through the already-installed Chroma/ONNX stack. No API key and no network calls.
- Notes are cleaned before embedding: headings, HTML comments, template boilerplate from `rough Notes/zTemplates/`, metadata lines, placeholder-only lines, and generated `## Related` sections are stripped. Old templates, new templates, and untemplated notes are handled the same way.
- Template-only notes with no prose are skipped by the index, so they cannot match each other.
- The cache lives in `~/.cache/tend/` and is keyed by vault path and cleaned note content. The first run embeds the vault (about a minute for ~300 notes); later runs only embed changed notes.
- The cache is derived and **not git-committed**. `--reindex` rebuilds it; deleting it is safe because it will be rebuilt automatically.
- Set `TEND_SEMANTIC=0` or pass `--no-semantic` to disable semantic mode. `--stats` stays fast unless you ask for `--index-info`.

Dismissals live in `.tend/feedback.json` in the vault and are meant to be committed. In a link session, choose `d <number>` to hide that pair in both directions. Use `--dismissed` to list them and `--undismiss "Note A" "Note B"` to restore one.

This is retrieval, not RAG generation: no LLM writes or explains the link. The snippet is the evidence. If you later want one-line explanations ("this contradicts…", "this is the same idea as…"), an LLM can rerank these candidates, but it should not be the source of truth.

The default editor is `code --wait`. Override it with `TEND_EDITOR` or `--editor`:

```bash
TEND_EDITOR="obsidian" python3 scripts/tend.py
TEND_EDITOR="nvim" python3 scripts/tend.py
```

For convenience:

```bash
alias tend='python3 ~/github/obsidian-vault/scripts/tend.py'
# fast lexical-only alternative:
alias tend-lex='python3 ~/github/obsidian-vault/scripts/tend.py --no-semantic'
```

On i3, press `$mod+d` and choose `,tend` to open the Tend menu: revisit due notes, link notes, audit, triage, refresh the dashboard, or open it in Obsidian.

`tend.py` does not require the Obsidian plugins. Use Obsidian's core Backlinks → Unlinked mentions pane alongside it.

## Workflow

The workflow is intentionally low-friction:

1. **Connect a few notes.** Run `tend` (or `tend --links` to focus on notes with no outgoing links). Review a suggestion, link it, or dismiss it.
2. **Revise a few notes.** Run `tend --revisit` for notes that are due. Open, append, link, schedule, or archive. The goal is a small number of real edits, not clearing a queue.
3. **Use the dashboard as a menu, not a debt collector.** `Reflections/Tending.md` surfaces due revisions, unlinked mentions, semantic neighbors, duplicates, empty/template-only notes, and neglected notes. It refreshes on run and on quit.
4. **Audit occasionally.** `tend --stats` is read-only. `tend --triage` is for backlog cleanup.
5. **Use Obsidian core for browsing.** Backlinks → Unlinked mentions, graph view with the orphan filter, and random note are enough. No plugins required.

## What we're building

The direction is deliberately incremental:

1. **Direct essay-to-essay links first.** MOCs and concept notes are optional and should emerge only when a cluster of notes has earned one.
2. **Hybrid suggestions.** Exact mentions, title patterns, and shared terms provide precision and evidence. Local embeddings provide recall for paraphrases and non-obvious connections. Nothing is linked without confirmation.
3. **Noise control before automation.** Template-aware cleaning removes boilerplate; template-only notes are skipped by the index; dismissed pairs are remembered. The goal is fewer, better suggestions, not maximum coverage.
4. **Spaced editing, not just spaced recall.** Revisit scheduling lives in frontmatter; each pass should change, sharpen, or retire the note.
5. **Local-first.** Embeddings run locally, the index is disposable, and feedback is a small committed JSON file. No API key is required.
6. **RAG later, as a layer.** The next useful addition is an optional local-LLM reranker/explainer over retrieved candidates ("these agree", "these contradict", "this is the same idea"). Retrieval and the snippet remain the source of truth.
7. **MOCs after the graph is denser.** Once there are enough direct links, cluster the graph and propose MOCs rather than inventing them up front.
8. **Further out:** link-health checks, better duplicate merging, and an evaluation loop for accepted vs dismissed suggestions.

The index cache is derived state. Do not commit it. The feedback file is the only link-quality state worth preserving across machines.

## Legacy scripts

These remain in the repo because they are still useful, but they are no longer the primary review loop.

### `incremental.py` — old SM-2 review session

An older standalone review script with its own `.reflections_queue.json` tracker. `tend --review` now runs the unified revisit loop instead. Use this only if you specifically want the old SM-2 behavior; its schedule is not connected to the frontmatter state used by `tend`.

### `move_unfinished.py` — batch folder utility

Scans both directories and moves notes across the 350-word threshold:

- `Reflections/` → `unfinished/` if under 350 words
- `unfinished/` → `Reflections/` if 350+ words

Also rekeys the old tracker. Run this occasionally (or after importing a batch of notes) to keep the folders aligned. `tend --revisit` also promotes notes it edits past 350 words.

## How the folders work

| Folder | Purpose | Word count |
|--------|---------|------------|
| `Reflections/` | Finished, substantial writing | 350+ words |
| `unfinished/` | Seeds, fragments, half-thoughts | <350 words |

The goal is to expand each unfinished note to 350 words through repeated engagement, then let `tend --revisit` promote it to `Reflections/`. Shorter notes get a priority boost during revisit selection.

## Workflow

```
# Connect notes
python3 scripts/tend.py

# Revisit and revise what is due
python3 scripts/tend.py --revisit

# After importing a batch of new notes, realign folders
python3 scripts/move_unfinished.py
```

## Symlink setup

These scripts live in `~/github/scripts/scripts/vault-scripts/` and are symlinked into the vault's `scripts/` directory. The canonical source is this repo — edit here, commit here, push from here.

The symlinks are created automatically by `setup/vault-scripts-link.sh` during bootstrap. On a new device, run `setup/bootstrap.sh` or just `setup/vault-scripts-link.sh` directly after both repos are cloned.

To set up manually on a new device:
```bash
mkdir -p ~/github/obsidian-vault/scripts
for f in tend.py incremental.py move_unfinished.py README.md; do
  ln -s ~/github/scripts/scripts/vault-scripts/"$f" ~/github/obsidian-vault/scripts/"$f"
done
```

## Design notes

The semantics invert Anki's normal mapping:
- **Anki**: "Hard" → short interval (you struggled), "Easy" → long interval (you knew it)
- **Here**: "Soon" → short interval (you want to engage more), "Later" → long interval (can wait)

Both converge to the same math. The labeling fits the writing context: important thoughts should resurface soon, not be buried by a long interval.