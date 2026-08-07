# Video Editor Pipeline

A coherent suite of lightweight Python scripts for **screen recording**, **GoPro
video processing**, marker-based cutting, text overlays, captions, GIF export,
and automated **YouTube uploads**. Uses mpv for marking and ffmpeg/whisper for
processing — designed for potato hardware where a full video editor won't run.

## Two ways to use it

1. **Interactive** — `edit.py` opens a menu; you pick what to do. Good for
   hand-crafted edits (cut a workout video, burn text, export a GIF).
2. **Automated** — `pipeline.py` runs the whole GoPro→upload flow unattended:
   silence-trim → normalize → captions → encode → upload.

## Directory layout (`~/vedit`)

| Stage   | Path        | Contents |
|---------|-------------|----------|
| Raw     | `~/vedit/raw/` | Ingested GoPro footage + screen recordings |
| Work    | `~/vedit/work/` | Intermediate stages (intermediates land here via `auto_output_path`) |
| Out     | `~/vedit/out/` | Final processed videos, ready to publish |
| GIF     | `~/vedit/gif/` | Exported GIFs |
| Sidecars | `~/vedit/*.json` | Cut/text markers (see below) |

Sidecars (markers) are keyed by the video's basename and stored in
`~/vedit/`, e.g. `~/vedit/video.markers.json` and `~/vedit/video.texts.json`,
**for every video regardless of where the file lives** (consistent).

## Requirements

- Python 3, FFmpeg + FFprobe in PATH
- `whisper-cli` + a model (build via `setup/whisper.sh`) — for captions
- `slop` (optional, interactive region selection)
- `youtubeuploader` binary + `client_secrets.json` (see upload.py) — for uploads

## Automated pipeline

### `pipeline.py` — one command, raw → published video

```bash
python3 pipeline.py raw/GP010001.mp4 --title "My first take" --upload
python3 pipeline.py raw/GP010001.mp4 --title "X" --tags a,b,c
python3 pipeline.py raw/GP010001.mp4 --trim 10:90       # cut to a section first
python3 pipeline.py --check                             # show encoder + upload config
```

Default stages: **[trim]** → **silence-trim** → **normalize** → **captions** → **encode**.
`--trim START:END` lossless-cuts a section first. `--no-trim`, `--no-captions`,
`--no-normalize` skip stages. `--hw vaapi|cpu|auto` selects the encoder.
`--upload` pushes the final to YouTube (unlisted by default). `--cleanup`
reminds you to trash originals afterward.

### Individual stage scripts

- `silence_trim.py` — **auto-trim**: detects silent pauses (`silencedetect`),
  removes them for a tight edit. No manual cutting.
  `silence_trim.py video.mp4 --noise -30dB --min-sil 0.5 --pad 0.25 --hw vaapi`
- `lossless_trim.py` — instant `-c copy` trim, 100% quality.
  `lossless_trim.py video.mp4 --start 10 --end 90 -o out.mp4`
- `audio.py --normalize` — **leveler + compressor**: loudnorm (-16 LUFS) + acompressor so
  shouting and quiet talking sound balanced. `audio.py in.mp4 out.mp4 --normalize`
- `captions.py` — **auto-captioner**: whisper transcribes speech → .srt burned
  via libass (stylized) or embedded as `mov_text` soft subs.
  `captions.py video.mp4 -o out.mp4` (burn) / `--soft` (embed) / `--srt-only`
- `encode.py` — **hardware encoder switch**: auto-detects vaapi/nvenc/qsv or
  falls back to CPU libx264. YouTube-friendly H.264/AAC.
  `encode.py video.mp4 -o out.mp4 --hw vaapi`
- `upload.py` — **youtubeuploader-wrapper** pushing to YouTube as **unlisted**.
  `upload.py out.mp4 --title "..." --desc "..." --privacy unlisted --tags a,b`
- `cleanup.py` — **trash collector**: after a confirmed upload, moves raw +
  intermediate files to the Trash to keep SSD clear. `cleanup.py --purge`

## GoPro auto-ingest

- `gopro-ingest.sh` — copies footage from an SD card into `~/vedit/raw/`,
  renaming with capture timestamps, idempotent.
  `./gopro-ingest.sh /media/swap/GOPro` (or a device node)
- `99-gopro.rules` — udev rule that runs the ingest automatically when the
  GoPro SD card is inserted. See install instructions at the top of the rule.

## Interactive suite — `edit.py`

```bash
python edit.py                    # record screen / convert GIF
python edit.py workout.mp4        # edit an existing video
```

Opens an interactive menu. Pipeline status is shown at the top. Marks define
sections to REMOVE. Tracks the current file across cuts so you can trim
iteratively, then add text or export a GIF.

```
  Current: workout.mp4
  Marks define sections to REMOVE (not keep)

  Step                   Status
  ──────────────────────────────────────────
  Remove markers         4 points saved
  Next trim output       workout_cut.mp4
  Text markers           saved
  Next text output       workout_text.mp4
  ──────────────────────────────────────────

  [1]  Record screen (select region)
  [2]  Convert latest recording to GIF
  [3]  Join multiple clips into one
  [6]  Audio: mute, volume, replace, mix
  [8]  Mark sections to REMOVE (mpv, press 'm')
  [9]  Remove marked sections → trimmed video
  [10] Add text overlay markers
  [11] Burn text into video
  [13] Run full pipeline (guided)
```

## Script reference (standalone)

### `screen_record.py` — Capture screen to MP4 (`~/vedit/raw/`)
```
python3 screen_record.py                    # full screen, auto-named
python3 screen_record.py demo.mp4           # full screen, named
python3 screen_record.py --select           # select region, auto-named
```
Uses `slop` for interactive region selection. Press Ctrl+C to stop — file stays
valid even if interrupted.

### `gif.py` — Video to GIF
```
python3 gif.py input.mp4 output.gif                     # whole video
python3 gif.py input.mp4 output.gif --start 5 --duration 3
python3 gif.py --latest demo.gif --demo                 # latest recording
```
Quality presets: `demo`, `low`, `medium`, `high`, `max`. Shorthand: `d,l,m,h,x`.

### `audio.py` — mute / volume / normalize / replace / mix
```
python3 audio.py in.mp4 out.mp4 --mute                  # remove audio
python3 audio.py in.mp4 out.mp4 --volume 0.5            # lower to 50%
python3 audio.py in.mp4 out.mp4 --normalize             # loudness + compressor
python3 audio.py in.mp4 out.mp4 --add music.wav         # replace audio
python3 audio.py in.mp4 out.mp4 --add music.wav --mix   # mix over existing
```
Video always runs full length — no `-shortest` truncation.

### `join.py` — Concatenate multiple clips
```
python3 join.py clip1.mp4 clip2.mp4 clip3.mp4      # join clips
python3 join.py --latest out.mp4                   # join 3 latest recordings
```
Stream-copy when codecs match; falls back to re-encode.

### `cut_marker.py` + `process_cuts.py` — remove marked sections
```
python3 cut_marker.py workout.mp4        # press 'm' to mark pairs, 'q' to save
python3 process_cuts.py workout.mp4     # → workout_cut.mp4 (markers from ~/vedit)
```
| Key | Action |
|-----|--------|
| `m` | Mark cut point (pairs = section to remove) |
| `[`/`]` | Speed down/up |
| `←`/`→` / `↑`/`↓` | Seek 5s / 60s |
| `SPACE` / `q` | Pause / quit & save |
`--precise` re-encodes (frame-accurate); default is fast stream-copy. `--hw`
and `--crf` control hardware encoding.

### `text_marker.py` + `process_text.py` — text overlays
```
python3 text_marker.py video.mp4       # press 't' to mark a position
python3 process_text.py video.mp4 out  # burn text in
```
Markers saved to `~/vedit/<stem>.texts.json`.

### `info.py` — metadata
```
python3 info.py video.mp4
```
Shows duration, resolution, FPS, codec, size, bitrate, audio details.

## Output locations

| Output | Default path |
|--------|-------------|
| Screen recordings | `~/vedit/raw/screen_<ts>.mp4` |
| Ingested GoPro clips | `~/vedit/raw/<ts>_<name>.MP4` |
| Cut markers | `~/vedit/<stem>.markers.json` |
| Text markers | `~/vedit/<stem>.texts.json` |
| Silence-trimmed | `auto_output_path(...)` → `<stem>_tight.mp4` |
| Trimmed (lossless) | `<stem>_trimmed.mp4` |
| Trimmed (markers) | Next to input: `<stem>_cut.mp4` |
| Text video | Next to input: `<stem>_text.mp4` |
| Replaced/mixed audio | given `-o`, else next to input `<stem>_audio.mp4` |
| Muted / volume / normalized | via `audio.py -o OUT` |
| Final publish encode | `~/vedit/out/<stem>_final.mp4` |
| GIFs | `~/vedit/gif/<stem>.gif` |
| Upload log | `~/vedit/uploads.json` |
| Session log | `~/vedit/edit.log` / `~/vedit/ingest.log` |

## Design notes

- **Potato-friendly**: mpv + ffmpeg run on anything.
- **Non-destructive**: originals never modified; outputs go to new files.
- **Repeatable**: mark once, re-process with different settings.
- **Unix-y**: each script does one thing; the orchestrators compose them.
- **Consistent sidecars**: markers/texts always keyed by basename in `~/vedit/`.