# Config

Dotfiles managed with git-stow. Each subdirectory is a stow package. Usually auto done by the bootstrap script.

## Packages

| Package | Description |
|---------|-------------|
| `bash/` | .bashrc, .profile |
| `zsh/` | .zshrc |
| `nvim/` | Neovim (Kickstart-based) |
| `i3/` | Window manager config |
| `rofi/` | App launcher |
| `kanata/` | Keyboard layout |
| `espanso/` | Text expansion |
| `vscode/` | Editor settings |
| `starship/` | Shell prompt |
| `dunst/` | Notifications |
| `conky/` | System info |
| `picom/` | Compositor |
| `i3status/` | Status bar |
| `timer/` | Timer daemon (systemd user unit) |

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