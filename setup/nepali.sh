#!/bin/bash
set -euo pipefail

echo ">>> NEPALI_START <<<"
echo "--- Setting up Nepali (Devanagari) typing via ibus-m17n ---"

# Phonetic transliteration: type "namaste" -> नमस्ते
#   Engine:   m17n:ne:rom-translit
#   Toggle:   Super+Shift+Space (global, any app)
#   Cheat:    $mod+Shift+s opens rofi cheatsheet (needs deploy-scripts.sh)

# 1. Packages (check before install)
for pkg in ibus ibus-m17n; do
	if ! dpkg -s "$pkg" >/dev/null 2>&1; then
		echo "Installing $pkg..."
		sudo apt install -y "$pkg"
	fi
done

# 2. Make ibus the system IM (sets ~/.xinputrc -> env vars + daemon autostart)
if command -v im-config &>/dev/null; then
	echo "Setting ibus as the input method..."
	im-config -n ibus
fi

# 3. Register the Nepali engine + global switch (idempotent)
gsettings set org.freedesktop.ibus.general use-global-engine true
gsettings set org.freedesktop.ibus.general.hotkey triggers "['<Super><Shift>space']"
gsettings set org.freedesktop.ibus.general preload-engines "['xkb:us::eng', 'm17n:ne:rom-translit']"

# 4. Restart daemon if running so the change applies immediately
if pgrep -x ibus-daemon >/dev/null 2>&1; then
	ibus restart || true
fi

echo "Nepali typing ready. Super+Shift+Space toggles, \$mod+Shift+s shows the cheatsheet."
echo ">>> NEPALI_COMPLETE <<<"
