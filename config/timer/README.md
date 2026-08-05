# Timer

Countdown timers with i3bar indicator + rofi menu. See `scripts/rofi/rofi-timer-menu.sh`.

## Pieces

| Component | Location | Role |
|-----------|----------|------|
| daemon | `~/.local/bin/timer-daemon` | Unix socket server, rings + dunst on expiry |
| indicator | `~/.local/bin/timer-indicator` | One i3bar block; clicked → rofi menu |
| menu | `scripts/rofi/rofi-timer-menu.sh` | New timer / cancel via rofi |
| service | `~/.config/systemd/user/timer-daemon.service` | Keeps daemon running |

## Install

```bash
stow -R -t ~ -d config timer
systemctl --user daemon-reload
systemctl --user enable --now timer-daemon
```

The i3bar block is added by `i3status-wrapper` (already stowed). Restart i3bar
or reload i3 config to pick up the click handler.
