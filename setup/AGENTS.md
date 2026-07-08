# AGENTS

## Modifying Packages

- apt.sh: Check existence before installing (`dpkg -s` or `command -v`)
- Keep idempotent: rerunning should be safe
- Add comments for why each package is needed

## Adding New Packages

1. **APT**: Add to APPS array in apt.sh
2. **PPA**: Add check block like neovim-ppa/fastfetch
3. **Flatpak**: Use flathub, add XDG_DATA_DIRS export
4. **AppImage**: Download to ~/opt, register path
5. **Source**: Use temp dir, cleanup after install
6. **Cargo**: Check `command -v` before install

## Run

```bash
# Full bootstrap (slow)
./bootstrap.sh

# Just packages (faster)
./apt.sh
```

## Gotchas

- Some packages need reboot (udev rules, user groups)
- clipmenu builds from source each run if missing
- Espanso AppImage needs `env-path register`
- Anki launcher needs libxcb dependencies