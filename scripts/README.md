# Scripts

Utilities and automation.

## Categories

| Category | Description |
|----------|-------------|
| `anki/` | Piper integration, reviewer workflow, game cards |
| `editor/` | Video: records, trims, captions, auto-pipeline, YouTube upload (see editor/README.md) |
| `espanso/` | Calculator, case picker, shell helpers |
| `obsidian/` | Incremental笔记, move unfinished |
| `rofi/` | Smart launcher, todo menu, timer menu |
| `snippets/` | FastAPI, React, JS templates |
| `utils/` | piper (TTS), whisper (STT), countdown |
| `template/` | TIL, why, obsidian templates |

## Usage

Most scripts are called directly or via keybinding (i3/espanso).

## Integration

- `anki-piper.sh`: triggered by i3 `$mod+o`, captures highlighted text
- `rofi-smart-launcher.sh`: triggered by i3 `$mod+d`
- `piper.sh`/`whisper.sh`: use ~/github/piper_tts for TTS