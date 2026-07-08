# Setup

System bootstrap scripts. Runs on fresh Debian/Ubuntu.

## Scripts

| Script | Purpose |
|--------|---------|
| `bootstrap.sh` | Main orchestrator |
| `repos.sh` | External repositories (LLVM, Neovim, VS Code) |
| `apt.sh` | APT packages (WM, CLI tools, build deps) |
| `system.sh` | udev rules, groups, system config |
| `languages.sh` | Python (pyenv), Node (nvm), Rust (rustup) |
| `kmp.sh` | JDK 21, Android SDK for Kotlin Multiplatform |
| `php.sh` | PHP CLI, extensions, Composer |
| `source.sh` | Builds from source (CMake, Clipmenu) |
| `binaries.sh` | Prebuilt binaries (Starship, Kanata, browsers) |
| `flatpak.sh` | Flatpak setup & Obsidian |
| `fonts.sh` | Nerd Fonts & emoji fonts |
| `stow.sh` | Dotfile symlinks |
| `piper.sh` | Piper TTS (downloads voice model) |
| `whisper.sh` | Whisper.cpp speech-to-text (builds from source) |
| `services.sh` | Enable user services (kanata, etc.) |

## Flow

```
bootstrap.sh
  → adds PPAs (Neovim, Fastfetch, VS Code, LLVM)
  → installs apt packages (WM, CLI, build deps)
  → system config (udev, groups)
  → languages: pyenv, nvm, rustup
  → toolchains: JDK/Android (KMP), PHP/Composer
  → builds source projects (CMake, Clipmenu)
  → installs prebuilt binaries & appimages
  → flatpak & Obsidian
  → Nerd Fonts + emojis
  → piper TTS + whisper.cpp
  → stows config/
  → enables user services (kanata)
```

## Run

```bash
cd setup && ./bootstrap.sh
```

Requires sudo for apt, udev rules, and some binaries.