# Scripts

Utilities and automation.

## Categories

| Category | Description |
|----------|-------------|
| `anki/` | Piper integration, reviewer workflow, game cards |
| `editor/` | Video: records, trims, captions, auto-pipeline, YouTube upload (see editor/README.md) |
| `espanso/` | Calculator, case picker, shell helpers |
| `obsidian/` | Incremental笔记, move unfinished |
| `rofi/` | Smart launcher, todo menu, timer menu, shutdown menu |
| `snippets/` | FastAPI, React, JS templates |
| `utils/` | piper (TTS), whisper (STT), countdown |
| `template/` | TIL, why, obsidian templates |

## timer-daemon

Logs start/expire/stop/extend events to `~/.local/state/timer-daemon.log` (JSON lines).

```bash
cat ~/.local/state/timer-daemon.log | jq .
```

Timers carry an `action`: `notify` (default) or `poweroff`. The latter is used by
`,off` and runs `systemctl poweroff` on expiry. Poweroff timers are shown
separately in i3bar and are excluded from the normal timer menu.

## Usage

Most scripts are called directly or via keybinding (i3/espanso).

## Integration

- `anki-piper.sh`: triggered by i3 `$mod+o`, captures highlighted text
- `rofi-smart-launcher.sh`: triggered by i3 `$mod+d`; apps, comma commands, and aliases
  - Search uses fuzzy matching sorted by match strength; the idle list is ordered by most recent use (`~/.cache/rofi-launcher/usage.json`)
  - `,tend` opens the tending menu; other aliases include `,bootstrap`, `,crawler`, `,k`, `,newip`, `,docker-clean`, `,clickpaste`
  - `,w gh cats` searches GitHub; `,w yt cats` YouTube; `,w wiki nepal` Wikipedia
  - `,off` opens the delayed-shutdown menu; `,off cancel` and `,off add 5m` require a typed reason
- `rofi-tend-menu.sh`: opened from `$mod+d` via `,tend`; Obsidian tending, revisits, audits, and dashboard
- `piper.sh`/`whisper.sh`: use ~/github/piper_tts for TTS
- `warp-new-ip.sh`: rotates the Cloudflare WARP registration (disconnect, delete, register, connect); run via `,newip`
