# Shared setup manifest. Source this file; do not execute it.
# This is the single source of truth for package and command expectations.
# shellcheck shell=bash

SUPPORTED_CODENAMES=(jammy noble)

# Installed before any repository setup so the bootstrap can run on a minimal
# Debian/Ubuntu image.
PREFLIGHT_PACKAGES=(
	"ca-certificates"
	"curl"
	"git"
	"gnupg"
	"lsb-release"
	"software-properties-common"
	"unzip"
)
PREFLIGHT_COMMANDS=("sudo" "apt-get" "dpkg-query" "lsb_release")

# CLI, shell, and small utilities.
APT_CLI=(
	"bash"
	"bash-completion"
	"bc"
	"cloudflare-warp"
	"fastfetch"
	"file"
	"fzf"
	"git"
	"git-crypt"
	"gh"
	"htop"
	"jq"
	"libnotify-bin"
	"ncal"
	"pipx"
	"psmisc"
	"ripgrep"
	"sqlite3"
	"stow"
	"tmux"
	"trash-cli"
	"tree"
	"xdg-utils"
	"zoxide"
)

# Window manager, desktop integration, and notifications.
APT_DESKTOP=(
	"blueman"
	"brightnessctl"
	"conky-all"
	"dbus"
	"dex"
	"dunst"
	"feh"
	"flameshot"
	"i3-wm"
	"i3lock"
	"i3status"
	"maim"
	"network-manager-gnome"
	"picom"
	"playerctl"
	"rofi"
	"slop"
	"x11-utils"
	"x11-xserver-utils"
	"xclip"
	"xdotool"
	"xinput"
	"xsel"
	"xss-lock"
)

# Terminal, file manager, editors, and media.
APT_APPS=(
	"code"
	"ffmpeg"
	"firefox"
	"gedit"
	"imagemagick"
	"kitty"
	"mpv"
	"nautilus"
	"neovim"
	"tesseract-ocr"
)

# Language and build toolchains.
APT_BUILD=(
	"build-essential"
	"clang-18"
	"libasound2-dev"
	"libbz2-dev"
	"libc6-dev-i386"
	"libclang-common-18-dev"
	"libextutils-pkgconfig-perl"
	"libffi-dev"
	"libfontconfig1-dev"
	"libfreetype6-dev"
	"libfuse2"
	"liblzma-dev"
	"libncurses-dev"
	"libncursesw5-dev"
	"libnss3"
	"libpulse0"
	"libreadline-dev"
	"libsqlite3-dev"
	"libssl-dev"
	"libx11-dev"
	"libxcb-cursor0"
	"libxcb-render0-dev"
	"libxcb-shape0-dev"
	"libxcb-xfixes0-dev"
	"libxcb-xinerama0"
	"libxcursor-dev"
	"libxi-dev"
	"libxinerama-dev"
	"libxkbcommon-dev"
	"libxml2-dev"
	"libxmlsec1-dev"
	"libxrandr-dev"
	"pkg-config"
	"pulseaudio-utils"
	"python3-full"
	"python3-pip"
	"python3-venv"
	"tk-dev"
	"xz-utils"
	"zlib1g-dev"
	"zstd"
)

# Database packages used by project work.
APT_DATABASE=(
	"postgresql"
	"postgresql-contrib"
)

# Applications installed outside apt (flatpak, AppImage, source, binaries).
FLATPAK_APPS=("md.obsidian.Obsidian")

# Optional packages installed only if available for the current release.
# pgvector is release-specific and is not in jammy's archive.
APT_OPTIONAL=(
	"libfuse2t64"
	"postgresql-16-pgvector"
)

# Packages that are intentionally not managed by apt because setup installs
# them from vendor releases.
VENDOR_PACKAGES=(
	"anki"
	"calibre"
	"espanso"
	"kanata"
	"starship"
	"yt-dlp"
)

# Python dependencies live in requirements.txt and requirements-optional.txt;
# setup/python.sh installs them into the pinned pyenv interpreter.

# Commands the verifier expects to exist after a complete bootstrap.
REQUIRED_COMMANDS=(
	"adb"
	"alacritty"
	"anki"
	"blueman-applet"
	"brightnessctl"
	"cargo"
	"clipmenud"
	"code"
	"composer"
	"conky"
	"convert"
	"dex"
	"dunst"
	"feh"
	"ffmpeg"
	"firefox"
	"firefox-dev"
	"fzf"
	"gh"
	"git"
	"i3"
	"java"
	"jq"
	"kanata"
	"killall"
	"kitty"
	"make"
	"maim"
	"mpv"
	"nautilus"
	"nm-applet"
	"node"
	"notify-send"
	"obsidian"
	"php"
	"picom"
	"playerctl"
	"python3"
	"rg"
	"rofi"
	"sdkmanager"
	"slop"
	"sqlite3"
	"starship"
	"stow"
	"tesseract"
	"tmux"
	"unzip"
	"warp-cli"
	"xdotool"
	"xinput"
	"xrandr"
	"xss-lock"
	"yt-dlp"
	"zoxide"
)
