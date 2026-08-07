# Video Editing Toolkit (scripts/editor)

A suite of Unix-style Python scripts for screen recording, GoPro processing,
marker-based cutting, text overlays, captions, and YouTube upload. Each script
does one thing; orchestrators (`pipeline.py`, `edit.py`) compose them.

## Language

### Stage

**Stage**: A single transformation applied to a video (trim, normalize,
caption, encode, upload). One script per stage.
_Avoid_: script, tool, tooling

**Orchestrator**: A program that composes **Stages** into a flow, driving them
as subprocesses (`pipeline.py` for automation, `edit.py` for interactive use).
_Avoid_: wrapper, launcher, menu

### Video and files

**Source**: The input video being processed. Never modified in place.
_Avoid_: file, clip, asset

**Work file**: An intermediate video produced by a **Stage** between the
**Source** and the final output.
_Avoid_: intermediate, temp file, artifact

**Final**: The publishable video produced by the last encode **Stage**.
_Avoid_: output video, result

### Marking

**Cut marker**: A saved point in a video, recorded while watching in mpv.
Cut markers come in pairs — each pair defines a section to **remove**.
_Avoid_: marker, edit point, cut point

**Text marker**: A saved position (timestamp) at which a text overlay should
appear. Unlike **Cut markers**, text markers carry content and timing.
_Avoid_: marker, annotation

**Sidecar**: A JSON file holding **Cut markers** or **Text markers**, always
keyed by the Source's basename and stored in `~/vedit/` — regardless of where
the Source lives.
_Avoid_: marker file, metadata file, companion file

### Hardware encoding

**Hardware encoder**: The resolved encoding backend (vaapi/nvenc/qsv) plus its
device, or CPU fallback. Auto-detected; never hardcoded.
_Avoid_: gpu, accel, encoder type

**Encoder module**: `encoder.py` — the one place that turns a **Hardware
encoder** into ffmpeg arguments. Exposes `resolve(hw)` → `Encoder` with
`.flags(crf)`, `.filter()`, `.init_flags()`, `.describe()`. The publish tail
(audio codec + faststart) is **not** an encoder concern and stays in the
calling **Stage**.
_Avoid_: utils detection, inline flag building

**Sidecar module**: `sidecar.py` — owns **Sidecar** file I/O and the **Cut
marker** pairing invariant. `pair_cut_markers` is the single definition of
the even-count removal rule; `fmt_pairs` and `load_or_reset` serve all
marker producers/consumers.
_Avoid_: hand-rolled marker reading, scattered pair logic

**Stage CLI**: `parser.py` — the shared, thin parser every **Stage** uses.
Owns the flag-walk loop, the `-o`/`--output` spellings, and the "Unknown
option" exit convention; each **Stage** declares only its own flags.
_Avoid_: hand-rolled sys.argv loops, argparse (deliberately not used)

### Ingest and upload

**Ingest**: Copying footage from a GoPro SD card into `~/vedit/raw/`, renaming
with a capture timestamp. Idempotent.
_Avoid_: import, sync, copy-in

**Upload ledger**: `~/vedit/uploads.json` — the record of which **Finals** were
uploaded to YouTube and when. Written by the upload **Stage**, read by
`cleanup.py`.
_Avoid_: log, history, uploads file

## Relationships

- An **Orchestrator** drives one or more **Stages** as subprocesses.
- A **Source** flows through a sequence of **Stages**, producing **Work files**, ending at a **Final**.
- A **Source** has at most one **Sidecar** for **Cut markers** and one for **Text markers**, both keyed by basename.
- Two **Cut markers** form a pair defining a section to remove.
- An **Upload** **Stage** appends a record to the **Upload ledger**; `cleanup.py` reads it.
- **Ingest** produces **Sources** in `~/vedit/raw/`.
- Every **Stage** lives at a seam: it exposes both a callable and a CLI; orchestrators invoke the CLI.

## Example dialogue

> **Dev:** "When a **Source** is silenced-trimmed, does that overwrite the **Source**?"
> **Domain expert:** "No. Every **Stage** writes a new **Work file** — the **Source** is never touched. `silence_trim.py` writes its own marker **Sidecar**, then reuses the cut **Stage** to remove those sections."
>
> **Dev:** "Why does `upload.py` write to `uploads.json` instead of just logging?"
> **Domain expert:** "Because `cleanup.py` needs to know what's already on YouTube before it trashes the **Work files**. That's the **Upload ledger** — the record of truth for 'safe to delete'."

## Flagged ambiguities

- "marker" was used to mean both **Cut marker** and **Text marker** — resolved: distinct concepts (one is removal pairs, the other is content+timing), kept separate in code and language.
- `crf` default diverged across **Stages** (captions hard-coded 23, process_cuts 23, encode 23, silence_trim's caller divergence) — resolved: single default `23` in the **Encoder module**; captions now honors `--crf`.
- `-o/--output` was parsed differently across **Stages** (captions/lossless_trim accept both spellings, join only `-o`, audio treats output as positional) — resolved: every **Stage** now accepts both `-o` and `--output` (and keeps positional-output as a fallback) via the shared **Stage CLI** parser.
- "output" could mean any **Work file** or the **Final** — resolved: only the last encode **Stage**'s output is the **Final**.
- **Stages** were invoked in two styles (subprocess CLI vs in-process import in `silence_trim.py`→`process_cuts.py`) — resolved: `silence_trim.py` now drives `process_cuts.py` through its CLI seam (`--precise` when a re-encode is wanted), so every caller hits the same log/exit behavior and the same `fast` default.
- **Cut marker** pairing/validation was duplicated with inconsistent clamping (process_cuts, cut_marker, edit) — resolved: single `pair_cut_markers` in the **Sidecar module**; odd counts, reversed pairs, and out-of-range sections now fail uniformly.
