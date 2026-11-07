---
name: demo-video
description: Record a polished screen-capture walkthrough of a running web app (any browser flow) with Playwright, then repair the video timeline and verify it before delivering a seekable MP4. Use when the user says "make a demo video", "record a walkthrough", "screen recording of the site", "video of the pages/design", "product tour video", or wants a shareable clip of a web flow. Also use when a Playwright/other screencast recording plays fine but seeks to the wrong place, or its duration is wrong.
---

# Demo video

Turn a live web flow into a short, shareable MP4: drive it with Playwright, add
optional caption chips, then **repair the timeline** (non-negotiable — see below)
and verify. Works in any repo.

## The one thing that will bite you

Playwright's `record_video_dir` writes a WebM whose frames are in the **correct
order** but carry **non-monotonic / scrambled timestamps** (recorder pads frames
`round(fps × Δt)`; the rounding accumulates — microsoft/playwright#35776).
Sequential playback looks perfect, so it hides — but **every naive ffmpeg
transcode reorders frames by those timestamps**. Symptom: `ffmpeg -ss 28 -i
out.mp4` shows footage from ~54s while `select='eq(n,700)'` shows something else
again — index and time disagree with each other and the wall clock.

Always run the repair step (`scripts/repair_and_verify.sh`) before delivering.

## Prerequisites

- Playwright + a browser binary. Python: `python3 -c "import playwright"`; if
  missing, `pip install playwright && playwright install chromium` (or use the
  Node package). Browsers often live in `~/.cache/ms-playwright/`.
- `ffmpeg` and `ffprobe` on `PATH`.
- The app running and reachable (dev server). Ask the user for the URL if unknown.

## Workflow

### 1. Recon (don't skip — selectors are where these scripts die)
- Confirm the app is up: `curl -s -o /dev/null -w '%{http_code}' <url>`.
- **Probe selectors with a throwaway script before recording**: load each route,
  dump candidate locators (`get_by_role`, `aria-label`, `input[name=...]`) and
  the counts. Guessing mid-recording wastes a whole take.
- Watch for full page reloads: a reload **drops SPA state** (e.g. a CMS's edit
  mode). Use in-page clicks / hash navigation where state must persist.
- Know the content reality: if a page has 1 item, don't write a 4-row hover demo.

### 2. Write the recording script
Start from `scripts/record_demo.py` (a working template). Key rules:
- **One context, one page for the whole session** → one continuous video. Don't
  open a new page per route; `page.goto(...)` on the same page.
- `record_video_size` = viewport size (default otherwise scales to fit 800×800).
- Keep the page open until the end; the video finalises on `context.close()`.
- Pace for humans: let entrance animations finish before scrolling; pause ~1s
  per section; scroll in small wheel steps rather than jumping.
- **Caption chips**: inject a `position:fixed` div into `document.body`
  (outside the app root, so React re-renders don't remove it). It survives SPA
  route changes; re-inject after full page loads.

### 3. Record
Run it. Read the log lines — the template asserts the key facts (e.g. a CMS save
hit disk, the changed value shows on the site). If a selector times out, fix and
re-run; a failed run leaves a partial/absent WebM, so clear the output dir first.

### 4. Repair + encode
```
bash scripts/repair_and_verify.sh raw.webm out.mp4        # see script for flags
```
Core of it:
```
ffmpeg -i raw.webm -vf "setpts=N/25/TB" -c:v libx264 -x264-params bframes=0 \
  -crf 20 -pix_fmt yuv420p -movflags +faststart -an out.mp4
```
`setpts=N/25/TB` makes storage order the timeline; `bframes=0` stops libx264 from
reordering. (Match the `/25` to the capture fps if not 25.)

### 5. Verify (mandatory)
- Index **and** seek must agree and match the wall clock (script does this).
- Fastest full eyeball: a contact sheet —
  `ffmpeg -i out.mp4 -vf "fps=1,scale=240:-1,tile=6x12" -frames:v 1 sheet.png`.
- Traps: `-ss` **before** `-i` is unreliable on these files; md5 across codecs is
  meaningless (VP8 vs H.264 pixels differ) — compare content visually.
- Validate any extraction method against a synthetic clip with burned-in
  timestamps (`testsrc2` + `drawtext=text='%{pts\:hms}'`) before trusting it.

### 6. Deliver
- Save to a **gitignored** folder (e.g. `video/`) unless told otherwise; the
  user usually doesn't want binaries committed. Prefer `.mp4`; keep the raw
  `.webm` as source only if asked.
- If the demo mutated app state/content, restore it and confirm `git status`
  matches the pre-recording state exactly.

## Pitfalls checklist
- Full reload drops SPA state (CMS edit mode) — avoid mid-flow reloads.
- Headless video has **no visible cursor**; hover *effects* still render.
- Nested list items: `ol li` may match child `<ul><li>` (tags). Use `ol > li`.
- Long static waits produce long duplicate runs — keep pauses tight.
- Re-run the repair step every time; the bug is in the source, not your command.

## Files
- `scripts/record_demo.py` — template recorder (captions, smooth scroll,
  single continuous page, self-checking asserts).
- `scripts/repair_and_verify.sh` — timeline repair + index/seek/contact-sheet checks.
