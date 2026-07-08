#!/bin/bash
set -euo pipefail

echo ">>> APT_START <<<"
echo "--- Installing APT Packages ---"

APPS=(
	"tmux" "fzf" "ripgrep" "htop" "bash-completion" "bash"
	"conky-all" "dbus" "dunst" "flameshot" "git-crypt"
	"i3-wm" "i3status" "mpv" "rofi" "stow" "tree" "i3lock"
	"blueman" "pulseaudio-utils" "libpulse0" "maim"
	"npm" "trash-cli" "gedit" "zoxide" "ncal" "pipx"
	"firefox" "brightnessctl" "feh" "neovim" "fastfetch" "code"
	"build-essential" "git" "curl" "libssl-dev" "zlib1g-dev" 
	"libbz2-dev" "libreadline-dev" "libsqlite3-dev" "libncursesw5-dev" 
	"xz-utils" "tk-dev" "libxml2-dev" "libxmlsec1-dev" "libffi-dev" 
	"liblzma-dev" "pkg-config" "libc6-dev-i386" "clang-18" 
	"libclang-common-18-dev" "python3-pip" "python3-venv" "python3-full"
	"libasound2-dev" "libx11-dev" "libxrandr-dev" "libxi-dev" 
	"libxcursor-dev" "libxinerama-dev" "libxkbcommon-dev"
	"libxcb-xinerama0" "libxcb-cursor0" "libnss3" "zstd" "libfuse2"
	"xsel" "xclip" "libextutils-pkgconfig-perl"
)

for app in "${APPS[@]}"; do
	if ! dpkg -l "$app" 2>/dev/null | grep -q '^ii'; then
		echo "Installing $app..."
		sudo apt install -y "$app"
	fi
done

echo ">>> APT_COMPLETE <<<"
