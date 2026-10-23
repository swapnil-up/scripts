# Setup Parity Plan

Status: implemented on jammy; second-device verification pending.

Goal: make `setup/` a reliable, repeatable definition of a machine, and make
drift between devices visible and fixable.

Targets: Debian/Ubuntu. Current device is Ubuntu 22.04 jammy; repo docs claim
24.04 noble. Both jammy and noble must be supported, with noble as the
long-term target.

Decisions (locked):

1. Support both jammy and noble; prefer noble-compatible choices.
2. Host-only scripts and tools are brought into the repo and provisioned.
3. The repo always lives at `~/github/scripts`; preflight enforces it.
4. Work proceeds phase by phase.
5. Secrets stay encrypted at rest. Rotate only if a plaintext leak is found.

## Confirmed findings

- `setup/apt.sh:23` installs `postgresql-16-pgvector`, which does not exist on
  jammy. With `set -euo pipefail`, this aborts the bootstrap.
- `setup/kmp.sh`, `php.sh`, `piper.sh`, and `flatpak.sh` append to
  `~/.bashrc`/`~/.profile`, which are stow targets. On a fresh machine those
  writes happen before `stow.sh`, which then deletes the real files. On an
  existing machine the writes modify the repo.
- `config/picom/picom.conf` stows to `~/picom.conf`, but i3 runs
  `picom --config ~/.config/picom/picom.conf`. That file is untracked on this
  device and absent on a fresh device.
- `setup/stow.sh` stale-link cleanup searches the source tree instead of
  `$HOME`; directory cleanup is mostly inert; real-file cleanup uses `rm -f`
  with no backup.
- Missing runtime dependencies include `picom`, `dex`, `xss-lock`, `xinput`,
  `xdotool`, `slop`, `playerctl`, `jq`, `sqlite3`, `gh`, `ffmpeg`,
  `imagemagick`, `tesseract-ocr`, `libnotify-bin`, `unzip`,
  `x11-xserver-utils`, `network-manager-gnome`, and a terminal emulator.
- No Python dependency installation or lockfile exists.
- Tracked config references unmanaged files: `quicknote.sh`,
  `connect_and_launch.sh`, `startup.sh`, `keyboard.sh`, fastfind, and the
  conky vault path `$HOME/obsidian-vault` instead of
  `$HOME/github/obsidian-vault`.
- Hardcoded `/home/swap` paths exist in shell config, i3, VS Code settings,
  and the GoPro udev rule.
- Toolchain versions drift because `latest` downloads and hardcoded pins are
  mixed with no manifest: starship, kanata, espanso, calibre, yt-dlp, Firefox
  Dev, Anki 25.09, fonts 3.4.0, NVM 0.39.7, JDK 21.0.11, Android 36.
- `languages.sh` expects nvm's installer to install Node LTS; it does not.
- Secrets are encrypted at HEAD but unlocked in the working tree. Conky
  sources `secrets.env` without checking whether git-crypt is locked.
- Bootstrap assumes `lsb_release`, `curl`, `gpg`, `git`, and `unzip` exist
  before `apt.sh` installs them.
- `bootstrap.sh` deletes LLVM repo files on every run, immediately before
  `repos.sh` re-adds them.
- `services.sh` may fail starting kanata before the user is active in the
  `uinput` group.
- README files are stale: raylib mention, OS version, missing scripts in the
  setup table, and a raw stow quick-start that bypasses `stow.sh`.

## Phase 0 — Safety and inventory

Status: implemented.

- [x] Audit secret history. Every committed blob of
  `config/bash/.env.secret` and `config/conky/.config/conky/secrets.env`
  begins with the `GITCRYPT` header, and `git grep` finds no plaintext token
  in the commits that touched them. The remote is public, but the secrets are
  encrypted at rest. No rotation is required from this audit. Rotate only if
  the unlocked working tree is ever copied off-device or shared.
- [x] Document `git-crypt unlock` in `setup/README.md`.
- [x] Add `setup/preflight.sh`: root refusal, `~/github/scripts` enforcement,
  jammy/noble allowlist, architecture warning, and installation of
  `ca-certificates curl git gnupg lsb-release unzip` before `repos.sh`.
- [x] Add `setup/manifest.sh` as the single package/command manifest. `apt.sh`
  and `binaries.sh` will be wired to it in Phase 1.
- [x] Wire preflight into `bootstrap.sh` before repository setup.

Acceptance: met — bootstrap aborts early with a clear message on an
unsupported machine, secrets state is documented, and there is one dependency
list.

## Phase 1 — Make bootstrap correct on supported machines

Status: implemented.

- [x] `apt.sh` now reads `manifest.sh`, batches installs, skips packages
  unavailable on the current release, and supports `--dry-run`.
- [x] Postgres and `postgresql-contrib` stay in `APT_DATABASE` for project
  work. `postgresql-16-pgvector` moved to `APT_OPTIONAL` and is skipped on
  jammy.
- [x] Added the missing packages to the manifest: picom, dex, xss-lock,
  xinput, xdotool, slop, playerctl, jq, sqlite3, gh, ffmpeg, imagemagick,
  tesseract-ocr, libnotify-bin, x11-xserver-utils, network-manager-gnome,
  kitty, nautilus, dmenu, bc, file, xdg-utils, x11-utils, and libfuse2t64.
- [x] Removed the unconditional LLVM repository deletion from `bootstrap.sh`.
  `repos.sh` now replaces LLVM and Sury entries when the codename changes.
  PPA additions are nonfatal and skip their automatic apt update.
- [x] Removed all `.bashrc`/`.profile` writes from `kmp.sh`, `php.sh`,
  `piper.sh`, `flatpak.sh`, and `languages.sh`. `config/bash` is canonical.
- [x] `languages.sh` installs Node LTS through nvm and sets `lts/*` as the
  default alias.
- [x] `kmp.sh` installs `java 21-tem`, sets and uses it, and verifies the
  active version.
- [x] `system.sh` reloads udev rules; `services.sh` enables kanata but defers
  start with a warning when the uinput/input groups are not active.
- [x] `nepali.sh` guards gsettings/im-config so a headless run warns instead
  of failing.
- [x] `software-properties-common` added to preflight so `add-apt-repository`
  exists before `repos.sh`.

Acceptance: script-level checks pass on jammy. Full clean-machine runs on
jammy and noble still need to be performed on real machines. `~/.bashrc` and
`~/.profile` are written only by `config/bash`; no setup script appends to
them.

## Phase 2 — Fix stow and config ownership

Status: implemented.

- [x] Picom config moved to `config/picom/.config/picom/picom.conf`. The old
  real `~/.config/picom/picom.conf` is preserved in the stow backup and the
  stale `~/picom.conf` link was pruned by restowing.
- [x] `stow.sh` rewritten:
  - `--dry-run` mode.
  - Backs up conflicts to `~/.local/state/setup-backup/<timestamp>/` instead
    of deleting them.
  - Runs `stow -n` before each real stow and aborts on unresolved conflicts.
  - Uses `--no-folding` for every package so shared directories are not
    replaced by package symlinks.
  - Prunes dangling links that point into `config/`.
  - Reports stowed packages, backups, and pruned links.
- [x] `deploy-scripts.sh` now has `--dry-run`, relinks stale repo links, and
  prunes links whose source was removed. It skips dangling foreign links.
- [x] Removed hardcoded `/home/swap` from `.bashrc`, `.profile`, and the i3
  status command. The GoPro udev rule is handled in Phase 3.
- [x] VS Code settings are generated from `settings.base.json` plus
  `~/.config/Code/User/settings.local.json`. The LeetCode workspace path now
  lives in the local file, not in git.
- [x] Strategy chosen: provision shared state from this repo, with local
  overlays only for machine-specific values (currently VS Code settings).

Acceptance: stow is non-destructive, idempotent, and reports its actions;
picom uses the tracked path. Verified on the current jammy host, including a
sandboxed conflict test. Full two-device verification remains in Phase 4.

## Phase 3 — Provision or remove missing integrations

Status: implemented.

- [x] Promoted `quicknote.sh`, `startup.sh`, and `keyboard.sh` into `scripts/`.
  `deploy-scripts.sh` links them into `~/.local/bin`; i3 now uses the deployed
  startup path. The original copies were moved to the setup backup directory.
- [x] Removed the broken `Mod1+Shift+b` binding to the nonexistent
  `connect_and_launch.sh`.
- [x] `source.sh` clones and builds `swapnil-up/search` as `fastfind-release`,
  so the `$mod+g` fastfind binding works on a fresh machine.
- [x] Conky vault path defaults to `$HOME/github/obsidian-vault`.
- [x] Conky GitHub widgets skip secret sourcing when the file is missing or
  still encrypted, printing `0` instead.
- [x] `system.sh` installs the GoPro udev rule from the tracked template,
  substituting the real home directory and username.
- [x] Added `setup/python.sh`, `requirements.txt`, and
  `requirements-optional.txt`. Base dependencies install by default; heavy
  optional dependencies (chromadb, numpy, Playwright) require `--optional`.
- [x] Added `setup/versions.env` and wired it into languages, KMP, PHP,
  binaries, repositories, and source builds.
- [x] Added `psmisc` for i3 `killall`. Alacritty is not packaged for jammy, so
  `binaries.sh` now builds it with Cargo after Rust is installed.
- [x] Fixed the `ble.sh` source path and added pinned ble.sh installation to
  `binaries.sh`; the verifier checks that it is present.

Acceptance: active i3 bindings resolve to existing executables; conky widgets
degrade cleanly on a locked/missing secret; Python scripts run after bootstrap.
Verified on the current jammy host. The udev install itself and a fresh
fastfind build need a sudo-enabled bootstrap run, so only their rendered
outputs were checked here. Two-device verification remains in Phase 4.

## Phase 4 — Verification and documentation

Status: implemented, except the second-device run.

- [x] Added `setup/verify.sh` and `make doctor`. Reports:
  - OS, architecture, codename support, repo location
  - missing commands from `manifest.sh`
  - config files not linked to the repo
  - i3 config syntax and missing referenced paths
  - user services enabled/running
  - `uinput`/`input`/`video`/`plugdev` membership
  - git-crypt locked/unlocked state
  - Python/Java/PHP/Node/CMake versions and Obsidian flatpak
- [x] Verifier has a deterministic text format and exits nonzero on failures.
- [x] Rewrote `README.md`: current setup flow, verification, OS matrix,
  manual steps, maintenance, and removed raylib/stale stow instructions.
- [x] Updated `setup/README.md`: script table, OS support, verification, and
  manual steps.
- [ ] Run the verifier on the second device and diff the output. This needs
  access to that machine.

A full `bootstrap.sh` rerun completed on the jammy host on 2026-10-23 and the
verifier reports `75 ok, 0 warning(s), 0 failure(s)`. The rerun caught two
packaging issues that are now fixed: Alacritty has no jammy package (built via
Cargo instead) and `apt.sh` treated packages with no install candidate as
available.

Acceptance: a single command produces a parity report that explains any
remaining difference between devices.

## Decisions

Resolved:

1. Support both jammy and noble; noble is the long-term target.
2. Bring host-only scripts and tools into the repo and provision them.
3. The repo always lives at `~/github/scripts`; preflight enforces it.
4. Work proceeds phase by phase.
5. Secrets stay encrypted at rest; rotate only if a plaintext leak is found.
6. Shared config is provisioned from this repo. Machine-specific values use
   local overlays; VS Code uses `settings.local.json`, merged at stow time.
