# Kanata

Keyboard remapping with [kanata](https://github.com/jtroo/kanata).

## Configs

- **kanata.kbd** (main) — full config with number row, home-row mods, symbol layer, mouse movement, i3 key aliases, and spacefn layer for navigation.
- **kanata-safe.kbd** (safe) — minimal fallback with no number row, `f24` prefix on tap-hold to prevent key repeat issues, no mouse or symbol layer. Use when the full config causes issues (e.g., in VMs or certain games).

## Integration

- `alias k='systemctl --user restart kanata'` in .bashrc
- i3 keybindings mirrored in the symbol and spacefn layers
