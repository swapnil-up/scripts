# Video Editor Pipeline

A suite of lightweight Python scripts for **screen recording**, **marker-based cutting**, **text overlays**, and **GIF export**. Uses mpv for marking and ffmpeg for processing — designed for potato hardware where a full video editor won't run.

## Requirements

- Python 3, FFmpeg + FFprobe in PATH
- `slop` (optional, for interactive region selection)

## Quick Start

### Record a screen demo → GIF

```bash
python3 edit.py                    # no file needed
[1] Record screen                  # select a region, Ctrl+C to stop
→ "Load this recording?" → yes
[2] Convert latest recording to GIF
→ press Enter for defaults → saved to ~/vedit/gif/
```

### Edit an existing video

```bash
python3 edit.py workout.mp4
```

Opens an interactive menu. Pipeline status is shown at the top:

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
  [3]  Show info
  [4]  Preview in mpv
  [5]  Show which sections will be removed
  [6]  Mark sections to REMOVE (mpv, press 'm')
  [7]  Remove marked sections → trimmed video
  [8]  Add text overlay markers
  [9]  Burn text into video
  [10] Create GIF from current video
  [11] Run full pipeline (guided)
```

The orchestrator tracks your current file across cuts so you can trim iteratively — cut, review, cut again, then add text or export a GIF.

## Scripts

### `screen_record.py` — Capture screen to MP4

```bash
python3 screen_record.py                    # full screen, auto-named
python3 screen_record.py demo.mp4           # full screen, named
python3 screen_record.py --select           # select region, auto-named
```

Auto-saves to `~/vedit/screen_<timestamp>.mp4`. Uses `slop` for interactive
region selection. Press Ctrl+C to stop — file is valid even if interrupted.

### `gif.py` — Video to GIF

```bash
python3 gif.py input.mp4 output.gif                     # whole video
python3 gif.py input.mp4 output.gif --start 5 --duration 3
python3 gif.py --latest demo.gif --demo                  # latest recording
```

Quality presets: `demo` (600px, 10fps), `low`, `medium`, `high`, `max`.
Shorthand: `d`, `l`, `m`, `h`, `x`.

### `cut_marker.py` — Mark sections to remove

```bash
python3 cut_marker.py workout.mp4
```

Opens video in mpv. Each `m` press adds a timestamp. Marks come in pairs —
each pair defines a section to **remove**. Saves to `~/vedit/<stem>.markers.json`.

| Key | Action |
|-----|--------|
| `m` | Mark cut point |
| `[` / `]` | Speed down / up |
| `LEFT` / `RIGHT` | Seek 5s |
| `UP` / `DOWN` | Seek 60s |
| `SPACE` | Pause |
| `q` | Quit & save |

### `process_cuts.py` — Remove marked sections

```bash
python3 process_cuts.py workout.mp4           # → workout_cut.mp4
python3 process_cuts.py workout.mp4 out.mp4   # explicit output
```

Reads markers, extracts segments between cut pairs, concatenates them.

### `text_marker.py` + `process_text.py` — Add text overlays

```bash
python3 text_marker.py workout_cut.mp4        # press 't' to mark
python3 process_text.py workout_cut.mp4 out.mp4  # burn text in
```

Text markers saved as `<video>.texts.json`. Prompts for text, duration,
position, font size, and color after closing mpv.

### `info.py` — Video metadata

```bash
python3 info.py video.mp4
```

Shows duration, resolution, FPS, codec, size, bitrate, audio details.

## Output Locations

| Output | Default path |
|--------|-------------|
| Screen recordings | `~/vedit/screen_<ts>.mp4` |
| Cut markers | `~/vedit/<stem>.markers.json` |
| Trimmed video | Next to input as `<stem>_cut.mp4` |
| Text markers | `<input>.texts.json` |
| Text video | Next to input as `<stem>_text.mp4` |
| GIFs | `~/vedit/gif/<stem>.gif` |
| Session log | `~/vedit/edit.log` (overwritten each run) |

## Design Notes

- **Potato-friendly**: mpv + ffmpeg, runs on anything.
- **Non-destructive**: Original file is never modified.
- **Repeatable**: Mark once, re-process with different settings.
- **Unix-y**: Each script does one thing; the orchestrator composes them.
