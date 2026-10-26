# Scripts

Personal dotfiles, system bootstrap, and automation utilities for an i3wm-based Ubuntu workstation.

## Structure

| Directory | Purpose |
|-----------|---------|
| [`config/`](config/) | Dotfiles managed via GNU stow (i3, rofi, nvim, kanata, espanso, etc.) |
| [`setup/`](setup/) | Idempotent bootstrap scripts for Ubuntu 22.04/24.04 |
| [`scripts/`](scripts/) | Automation utilities (rofi launchers, Anki, TTS/STT, video editing) |

## Quick Start

The repo must live at `~/github/scripts` (preflight enforces this).

```bash
cd ~/github/scripts/setup
./preflight.sh      # validate host, repo path, distro, base tools
./bootstrap.sh      # provision the machine (slow, needs sudo)
```

Preview the dotfile and script-link changes at any time:

```bash
./stow.sh --dry-run
./deploy-scripts.sh --dry-run
```

## Setup Flow

`bootstrap.sh` runs these steps in order and records per-script markers so an
interrupted run resumes where it stopped.

| Step | What it does |
|------|-------------|
| `repos.sh` | Adds PPAs (Neovim, fastfetch), LLVM, Sury PHP, VS Code |
| `apt.sh` | Installs packages from `manifest.sh`, skipping unavailable ones |
| `nepali.sh` | ibus-m17n engine and Nepali typing toggle |
| `system.sh` | Groups, udev rules (uinput, GoPro), linger, dark mode |
| `languages.sh` | pyenv, nvm + Node LTS, Rust |
| `python.sh` | Pinned Python + `requirements.txt` (`--optional` for heavy deps) |
| `kmp.sh` | Temurin JDK 21, Android SDK, Android udev rules |
| `php.sh` | PHP 8.3, extensions, Composer |
| `source.sh` | Builds CMake, Clipmenu, and fastfind from source |
| `binaries.sh` | Starship, Kanata, Espanso, Calibre, Anki, Firefox Dev, yt-dlp |
| `deploy-scripts.sh` | Links `scripts/` entries into `~/.local/bin` |
| `vault-scripts-link.sh` | Links vault scripts into `~/github/obsidian-vault` |
| `flatpak.sh` | Flatpak + Obsidian |
| `fonts.sh` | Nerd Fonts + Noto Color Emoji |
| `piper.sh` | Piper TTS + voice model |
| `whisper.sh` | Whisper.cpp speech-to-text |
| `youtube-upload.sh` | youtubeuploader binary + OAuth config |
| `stow.sh` | Links dotfiles, backs up conflicts, prunes stale links |
| `services.sh` | Enables kanata and timer-daemon user services |

Tool versions are pinned in [`setup/versions.env`](setup/versions.env).

## Verification

```bash
cd ~/github/scripts
make doctor           # or: ./setup/verify.sh
```

The verifier reports OS/repo mismatches, missing commands, mislinked config
files, broken i3 references, service state, group membership, git-crypt state,
and version drift. It exits nonzero on failures. To compare machines:

```bash
diff <(ssh device-b '~/github/scripts/setup/verify.sh' 2>&1) \
     <(./setup/verify.sh 2>&1)
```

## Key Integrations

| Feature | Stack |
|---------|-------|
| Keyboard layout | **kanata** — home-row mods, symbol layer, spacefn navigation mirroring i3 binds |
| Window manager | **i3** — custom modes (launch, system), scratchpad, quicknote |
| App launcher | **rofi** — smart launcher with app search, web search, todos, TTS/STT |
| Text expansion | **espanso** — emoji, lenny faces, snippets, calculator, case conversion |
| Shell prompt | **starship** |
| Editor | **neovim**, **VS Code** (generated from `settings.base.json`) |
| Notifications | **dunst** |
| System info | **conky** on desktop (projects, todos, stats, notes, quotes, year progress) |
| Video | **mpv** — timebox watch/break cycle, quality menu, bookmarks |
| Restlessness | `,off` delayed poweroff — cancel/extend requires a typed reason |
| Anki | Piper TTS card creation, reviewer workflow, game controller cards |
| TTS/STT | Piper TTS, Whisper.cpp |
| Clipboard | clipmenu + rofi |
| File search | fastfind (`swapnil-up/search`) + rofi |

## Maintenance

```bash
# Re-link everything safely (backs up conflicts, prunes stale links)
cd ~/github/scripts/setup && ./stow.sh

# Preview first
./stow.sh --dry-run

# Format and lint
make format   # shfmt + black
make lint     # shell syntax checks

# Kanata status
systemctl --user status kanata
alias k='systemctl --user restart kanata'
```

If stow replaces a real file, the original is moved to
`~/.local/state/setup-backup/<timestamp>/`.

## Adding a New Config Package

```bash
mkdir -p config/<package>/.config/<app>/
# place files inside
cd ~/github/scripts/setup && ./stow.sh          # or: stow -R -t ~ -d config <package>
```

Files in `config/<package>/` are stowed relative to `$HOME` — for example,
`config/i3/.config/i3/config` becomes `~/.config/i3/config`.

## Requirements

| OS | Status |
|----|--------|
| Ubuntu 22.04 (jammy) | Supported; current development host |
| Ubuntu 24.04 (noble) | Supported; clean-machine validation still pending |

- The repo must be at `~/github/scripts`.
- Run as a normal user; sudo is used internally.
- x86_64 is the tested architecture.
- Internet access is required for packages, fonts, binaries, and toolchains.
- Some group changes require a logout/login (or reboot).

## Manual Steps After Bootstrap

- Unlock secrets with `git-crypt unlock` (required for GitHub/Conky widgets).
- Add the GitHub token in `config/bash/.env.secret` and
  `config/conky/.config/conky/secrets.env`.
- Create `~/.config/youtubeuploader/client_secrets.json` from Google OAuth for
  video uploads.
- Clone the Obsidian vault at `~/github/obsidian-vault`.
- Put machine-specific VS Code values in
  `~/.config/Code/User/settings.local.json` (merged at stow time).
- First run of youtubeuploader/Anki/Espanso may prompt for OAuth or service
  registration.

See [`setup/README.md`](setup/README.md) for script-level details and
[`setup/PARITY-PLAN.md`](setup/PARITY-PLAN.md) for the remediation plan.
