# Timer

Countdown timers with i3bar indicator + rofi menu. See `scripts/rofi/rofi-timer-menu.sh`.

## Pieces

| Component | Location | Role |
|-----------|----------|------|
| daemon | `~/.local/bin/timer-daemon` | Unix socket server, rings + dunst on expiry |
| indicator | `~/.local/bin/timer-indicator` | One i3bar block; clicked → rofi menu |
| menu | `scripts/rofi/rofi-timer-menu.sh` | New timer / cancel via rofi |
| shutdown menu | `scripts/rofi/rofi-shutdown-menu.sh` | Delayed poweroff, cancel, and extend |
| presets | `~/.config/timers/presets` | Saved presets started with one click |
| service | `~/.config/systemd/user/timer-daemon.service` | Keeps daemon running |

## Presets

Save timers you run regularly in `~/.config/timers/presets` (one per line,
`Name | Duration` — duration uses the same format as the menu, e.g. `25m`,
`1h`, `90s`, `15`). They appear in the rofi menu under **Presets** and start
with a single click — no need to retype time and name. Comment lines with `#`.

## Delayed Shutdown Protocol

Run `,off` in the rofi smart launcher:

| Input | Action |
|-------|--------|
| `,off` | Menu: schedule 60s / 5m / 15m, or shut down now |
| `,off 5m` | Schedule a 5-minute poweroff |
| `,off cancel` | Cancel, after typing a reason |
| `,off add 5m` | Extend, after typing a reason |
| `,off now` | Confirm, then power off immediately |
| `,off status` | Print the remaining time |

Poweroff timers appear in i3bar as `Off 00:42`; clicking the block opens the
shutdown menu. Notifications are sent at 5 minutes, 1 minute, and 10 seconds
remaining, as applicable. The shutdown timer does **not** start at login — it
starts only when you run `,off`. The timer-daemon user service itself is
enabled at login, so it is ready to receive the timer.

Cancel and extend reasons are logged in `~/.local/state/timer-daemon.log`:

```bash
jq 'select(.event == "stop" or .event == "extend")' \
  ~/.local/state/timer-daemon.log
```

## Install

```bash
stow -R -t ~ -d config timer
systemctl --user daemon-reload
systemctl --user enable --now timer-daemon
```

The i3bar block is added by `i3status-wrapper` (already stowed). Restart i3bar
or reload i3 config to pick up the click handler.
