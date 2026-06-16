# Scripts

Personal dotfiles, system bootstrap, and automation utilities for an i3wm-based Linux workstation.

## Structure

| Directory | Purpose |
|-----------|---------|
| [`config/`](config/) | Dotfiles managed via GNU stow (kanata, i3, nvim, rofi, espanso, etc.) |
| [`setup/`](setup/) | Bootstrap scripts to provision a fresh Debian/Ubuntu system |
| [`scripts/`](scripts/) | Automation utilities (rofi launchers, anki, TTS/STT, video editing) |

## Quick Start

```bash
# Bootstrap a full system
cd setup && ./bootstrap.sh

# Or just link dotfiles
cd config && stow -t ~ */
```

## Setup Flow

`bootstrap.sh` runs these steps in order:

| Step | What it does |
|------|-------------|
| `repos.sh` | Adds PPAs (neovim, fastfetch, LLVM, VS Code) |
| `apt.sh` | Installs apt packages |
| `system.sh` | Creates `uinput` group, sets up udev rules for kanata |
| `languages.sh` | Installs pyenv, nvm + Node LTS, Rust |
| `source.sh` | Builds CMake, raylib, clipmenu from source |
| `binaries.sh` | Installs kanata, espanso, calibre, anki, Firefox Developer Edition |
| `flatpak.sh` | Installs flatpak + Obsidian |
| `fonts.sh` | Installs JetBrainsMono Nerd Font + Noto Color Emoji |
| `stow.sh` | Symlinks all dotfiles via stow |
| `services.sh` | Enables kanata systemd user service |

## Key Integrations

| Feature | Stack |
|---------|-------|
| Keyboard layout | **kanata** — home-row mods, symbol layer, spacefn navigation mirroring i3 binds |
| Window manager | **i3** — custom modes (launch, system), scratchpad, quicknote |
| App launcher | **rofi** — smart launcher with app search, web search, todos, TTS/STT |
| Text expansion | **espanso** — emoji, lenny faces, snippets, calculator, case conversion |
| Shell prompt | **starship** with custom config |
| Editor | **neovim** (kickstart-based), **VS Code** (settings synced via stow) |
| Notifications | **dunst** |
| System info | **conky** on desktop (projects, todos, stats, notes, quotes, year progress) |
| Anki | Custom scripts for piper TTS card creation, reviewer workflow, game controller cards |
| TTS/STT | Piper TTS, Whisper.cpp |
| Clipboard | clipmenu + rofi |

## Maintenance

```bash
# Re-link a single stow package after editing
stow -R -t ~ package_name     # e.g., stow -R -t ~ i3

# Format and lint
make format   # shfmt + black
make lint     # shell syntax checks

# Check kanata status
systemctl --user status kanata
alias k='systemctl --user restart kanata'
```

## Adding a New Config Package

```bash
mkdir -p config/<package>/.config/<app>/
# place files inside
stow -R -t ~ -d config <package>
```

Files in `config/<package>/` are stowed relative to `$HOME` — for example, `config/i3/.config/i3/config` becomes `~/.config/i3/config`.

## Requirements

- **OS**: Debian/Ubuntu (tested on Noble Numbat 24.04)
- **Shell**: bash or zsh
- **Sudo**: needed for package installs, udev rules
- **Internet**: downloads binaries, fonts, language toolchains
