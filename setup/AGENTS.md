# AGENTS

## Modifying Packages

- apt.sh reads from `manifest.sh`; add packages there, not in apt.sh
- Keep scripts idempotent: rerunning should be safe
- The manifest is also the source of truth for the future verifier
- Add comments for why each package is needed
- Packages unavailable on the current release are skipped with a warning
- Bump tool versions in `versions.env`, not inline in scripts

## Adding New Packages

1. **APT**: Add to the right array in `manifest.sh`
2. **Optional APT**: Add to `APT_OPTIONAL` if it is release-specific
3. **PPA**: Add check block like neovim-ppa/fastfetch in repos.sh
4. **Flatpak**: Add to `FLATPAK_APPS` in manifest.sh
5. **Python**: Add to `requirements.txt` (base) or `requirements-optional.txt` (heavy)
6. **AppImage**: Download to ~/opt, register path
7. **Source**: Use temp dir, cleanup after install
8. **Cargo**: Check `command -v` before install
9. **Required command**: Add it to `REQUIRED_COMMANDS`

## Run

```bash
# Full bootstrap (slow)
./bootstrap.sh

# Just packages (faster)
./apt.sh

# Show what apt.sh would install
./apt.sh --dry-run

# Validate host and repo location without installing
./preflight.sh

# Full parity report (or: make doctor from the repo root)
./verify.sh

# Preview stow and script-link changes
./stow.sh --dry-run
./deploy-scripts.sh --dry-run
```

## Gotchas

- `stow.sh` backs up conflicting files to `~/.local/state/setup-backup/<timestamp>/`
  and never deletes real files. It links files individually (`--no-folding`).
- VS Code `settings.json` is generated from `settings.base.json` plus
  `~/.config/Code/User/settings.local.json`; put machine-specific values in
  the local file, not in the repo.
- Some packages need reboot (udev rules, user groups)
- clipmenu builds from source each run if missing
- Espanso AppImage needs `env-path register`
- Anki launcher needs libxcb dependencies