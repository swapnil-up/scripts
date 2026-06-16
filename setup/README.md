# Setup

System bootstrap scripts. Runs on fresh Debian/Ubuntu.

## Scripts

| Script | Purpose |
|--------|---------|
| `bootstrap.sh` | Main orchestrator |
| `packages.sh` | APT apps, flatpaks, appimages, source builds |
| `languages.sh` | Python (pyenv), Node (nvm), Rust (rustup) |
| `services.sh` | Enable user services (kanata, etc.) |

## Flow

```
bootstrap.sh
  → adds PPAs (neovim, fastfetch, VS Code)
  → runs languages.sh (pyenv, nvm, rustup)
  → runs packages.sh (apt + extras)
  → stows config/
  → enables user services (kanata)
  → installs JetBrainsMono Nerd Font + Noto Color Emoji
```

## Run

```bash
cd setup && ./bootstrap.sh
```

Requires sudo for apt, udev rules, and some binaries.