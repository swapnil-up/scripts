# Setup

System bootstrap scripts. Runs on fresh Ubuntu 22.04/24.04.

## Scripts

| Script | Purpose |
|--------|---------|
| `bootstrap.sh` | Main orchestrator |
| `preflight.sh` | Validates host, repo location, distro, and base tools |
| `manifest.sh` | Shared package/command manifest (sourced, not executed) |
| `versions.env` | Pinned tool versions shared by setup scripts |
| `repos.sh` | External repositories (LLVM, Neovim, VS Code) |
| `apt.sh` | APT packages (WM, CLI tools, build deps) |
| `system.sh` | udev rules, groups, system config |
| `languages.sh` | Python (pyenv), Node (nvm), Rust (rustup) |
| `python.sh` | Pinned Python version + `requirements*.txt` (`--optional` for heavy deps) |
| `kmp.sh` | JDK 21, Android SDK for Kotlin Multiplatform |
| `php.sh` | PHP CLI, extensions, Composer |
| `source.sh` | Builds from source (CMake, Clipmenu, fastfind) |
| `binaries.sh` | Prebuilt binaries (Starship, Kanata, browsers), Cargo-built Alacritty, ble.sh |
| `flatpak.sh` | Flatpak setup & Obsidian |
| `fonts.sh` | Nerd Fonts & emoji fonts |
| `stow.sh` | Dotfile symlinks, conflict backup, stale-link pruning |
| `deploy-scripts.sh` | Links `scripts/` entries into `~/.local/bin` |
| `piper.sh` | Piper TTS (downloads voice model) |
| `whisper.sh` | Whisper.cpp speech-to-text (builds from source) |
| `youtube-upload.sh` | youtubeuploader binary + YouTube OAuth for vedit uploads |
| `services.sh` | Enable user services (kanata, etc.) |
| `verify.sh` | Parity report: commands, links, i3 refs, services, groups, secrets, versions |

## Flow

```
bootstrap.sh
  → preflight (repo path, distro, base tools)
  → adds PPAs (Neovim, Fastfetch, VS Code, LLVM)
  → installs apt packages from manifest.sh (WM, CLI, build deps)
  → system config (udev, groups)
  → languages: pyenv, nvm + Node LTS, rustup
  → Python dependencies (base; `--optional` for chromadb/playwright)
  → toolchains: JDK/Android (KMP), PHP/Composer
  → builds source projects (CMake, Clipmenu, fastfind)
  → installs prebuilt binaries, appimages, ble.sh, and builds Alacritty
  → flatpak & Obsidian
  → Nerd Fonts + emojis
  → piper TTS + whisper.cpp
  → stows config/ and links scripts/ into ~/.local/bin
  → enables user services (kanata)
```

## OS Support

| Release | Status |
|---------|--------|
| Ubuntu 22.04 (jammy) | Supported; current development host |
| Ubuntu 24.04 (noble) | Supported; clean-machine validation pending |

## Requirements

- Ubuntu **22.04 (jammy)** or **24.04 (noble)**.
- The repo must live at `~/github/scripts`.
- Run as your normal user, not root. Sudo is used internally.
- `preflight.sh` installs `ca-certificates`, `curl`, `git`, `gnupg`,
  `lsb-release`, `software-properties-common`, and `unzip` before the rest of the bootstrap runs.

## Verification

```bash
./verify.sh          # from setup/
make doctor          # from repo root
```

It exits nonzero if anything required is missing. Run it on both machines and
diff the output to see remaining parity gaps.

See [`PARITY-PLAN.md`](PARITY-PLAN.md) for the remediation plan and known
manual steps.

## Run

```bash
cd ~/github/scripts/setup && ./bootstrap.sh
```

To check a host without provisioning anything:

```bash
cd ~/github/scripts/setup && ./preflight.sh
```

Requires sudo for apt, udev rules, and some binaries.

Stow never deletes real files: conflicts are moved to
`~/.local/state/setup-backup/<timestamp>/`. Preview changes first with:

```bash
./stow.sh --dry-run
./deploy-scripts.sh --dry-run
```

VS Code settings are generated from
`config/vscode/.config/Code/User/settings.base.json` plus an optional
machine-local `~/.config/Code/User/settings.local.json`. Put host-specific
paths in the local file; it is not tracked.

## Manual Steps

- Run `git-crypt unlock` before relying on secrets.
- Put the GitHub token in `config/bash/.env.secret` and
  `config/conky/.config/conky/secrets.env`.
- Add `~/.config/youtubeuploader/client_secrets.json` for video uploads.
- Clone the Obsidian vault at `~/github/obsidian-vault`.
- Log out and back in after the first run so new groups (uinput/input/video)
  apply.
- Put machine-specific VS Code values in
  `~/.config/Code/User/settings.local.json`.

## Secrets

`config/bash/.env.secret` and `config/conky/.config/conky/secrets.env` are
encrypted in git with git-crypt. After cloning on a new machine, unlock them
with your key before relying on anything that reads those values:

```bash
git-crypt unlock
```

A locked repo leaves those files as binary data. `.bashrc` skips a locked
secret file; conky scripts currently expect it unlocked.