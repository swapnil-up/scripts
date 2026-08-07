# Timer

Countdown timers with i3bar indicator + rofi menu. See `scripts/rofi/rofi-timer-menu.sh`.

## Pieces

| Component | Location | Role |
|-----------|----------|------|
| daemon | `~/.local/bin/timer-daemon` | Unix socket server, rings + dunst on expiry |
| indicator | `~/.local/bin/timer-indicator` | One i3bar block; clicked → rofi menu |
| menu | `scripts/rofi/rofi-timer-menu.sh` | New timer / cancel via rofi |
| presets | `~/.config/timers/presets` | Saved presets started with one click |
| service | `~/.config/systemd/user/timer-daemon.service` | Keeps daemon running |

## Presets

Save timers you run regularly in `~/.config/timers/presets` (one per line,
`Name | Duration` — duration uses the same format as the menu, e.g. `25m`,
`1h`, `90s`, `15`). They appear in the rofi menu under **Presets** and start
with a single click — no need to retype time and name. Comment lines with `#`.

## Install

```bash
stow -R -t ~ -d config timer
systemctl --user daemon-reload
systemctl --user enable --now timer-daemon
```

The i3bar block is added by `i3status-wrapper` (already stowed). Restart i3bar
or reload i3 config to pick up the click handler.
