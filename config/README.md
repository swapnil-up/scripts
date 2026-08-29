# Config

Dotfiles managed with git-stow. Each subdirectory is a stow package. Usually auto done by the bootstrap script.

## Packages

| Package | Description |
|---------|-------------|
| `agents/` | Agent configs |
| `bash/` | .bashrc, .profile |
| `conky/` | System info |
| `dunst/` | Notifications |
| `espanso/` | Text expansion |
| `gtk/` | GTK 3/4 settings |
| `i3/` | Window manager config |
| `i3status/` | Status bar |
| `kanata/` | Keyboard layout |
| `nvim/` | Neovim (Kickstart-based) |
| `picom/` | Compositor |
| `rofi/` | App launcher |
| `starship/` | Shell prompt |
| `timer/` | Timer daemon (systemd user unit) |
| `vscode/` | Editor settings |

## Stow Usage

```bash
# Link everything
cd config && stow -t ~ */

# Relink after edit
stow -R -t ~ package_name
```

## Integration Notes

- **kanata.kbd** mirrors i3 keybindings in symbol layer (`@i3q`, `@i3r`, etc.)
- **espanso** uses rofi for emoji/lenny/snippet pickers
- **i3** binds rofi-smart-launcher, anki, clipboard, screenshots