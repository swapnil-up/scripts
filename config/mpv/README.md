# mpv

Stowed to `~/.config/mpv/`.

## Contents

| Path | Purpose |
|------|---------|
| `mpv.conf` | Playback defaults (`save-position-on-quit`, ytdl format cap) |
| `input.conf` | Keybindings, including bookmarker |
| `scripts/timebox.lua` | Watch/break cycle (7 min watch, 3 min break, SPACE to resume) |
| `scripts/quality-menu.lua` | Quality/profile menu |
| `scripts/bookmarker-menu.lua` | Bookmark menu |
| `script-opts/timebox.conf` | Timebox durations and flags |
| `script-opts/quality-menu.conf` | Quality-menu settings |

## Local state (not tracked)

These live in `~/.config/mpv/` but are intentionally not stowed or committed:

- `timebox.state` — current watch/break progress for this machine
- `watch_later/` — per-file resume positions
- `bookmarker.json` — local bookmark list

Delete `timebox.state` to reset the watch budget.

## Timebox

Defaults to 7 minutes of viewing, then a 3-minute black-screen break. The video
stays paused after the break until SPACE is pressed. Progress persists across
episodes and mpv restarts.

Tune in `script-opts/timebox.conf`:

```ini
watch_minutes=7
break_minutes=3
count_paused_time=no
persist_state=yes
```
