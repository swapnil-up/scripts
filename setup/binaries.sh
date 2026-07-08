#!/bin/bash
set -euo pipefail

echo ">>> BINARIES_START <<<"
echo "--- Installing Binaries and AppImages ---"

mkdir -p "$HOME/.local/bin"
mkdir -p "$HOME/opt"

# 1. Starship
if ! command -v starship &>/dev/null; then
	curl -sS https://starship.rs/install.sh | sh -s -- -y
fi

# 2. Kanata
KANATA_TARGET="$HOME/.local/bin/kanata"
if ! command -v kanata &>/dev/null; then
	TEMP_KANATA=$(mktemp -d)
	curl -L https://github.com/jtroo/kanata/releases/latest/download/linux-binaries-x64.zip -o "$TEMP_KANATA/kanata.zip"
	unzip -o "$TEMP_KANATA/kanata.zip" -d "$TEMP_KANATA"
	mv "$TEMP_KANATA/kanata_linux_x64" "$KANATA_TARGET"
	chmod +x "$KANATA_TARGET"
	rm -rf "$TEMP_KANATA"
elif [ "$(command -v kanata)" != "$KANATA_TARGET" ]; then
	ln -sf "$(command -v kanata)" "$KANATA_TARGET"
fi

# 3. Espanso (AppImage)
if ! command -v espanso &>/dev/null; then
	curl -L -o "$HOME/opt/Espanso.AppImage" 'https://github.com/espanso/espanso/releases/latest/download/Espanso-X11.AppImage'
	chmod u+x "$HOME/opt/Espanso.AppImage"
	yes | sudo "$HOME/opt/Espanso.AppImage" env-path register
	/usr/local/bin/espanso service register
	/usr/local/bin/espanso start
fi

# 4. Calibre
if ! command -v calibre &>/dev/null; then
	curl -sSL https://download.calibre-ebook.com/linux-installer.sh | sudo sh /dev/stdin install_dir=/opt isolated=false
fi

# 5. Anki (Launcher)
if ! command -v anki &>/dev/null; then
	TEMP_ANKI=$(mktemp -d)
	cd "$TEMP_ANKI"
	curl -L "https://github.com/ankitects/anki/releases/download/25.09/anki-launcher-25.09-linux.tar.zst" -o anki-launcher.tar.zst
	tar --use-compress-program=unzstd -xf anki-launcher.tar.zst
	cd anki-launcher*/
	sudo ./install.sh
	cd "$HOME"
	rm -rf "$TEMP_ANKI"
fi

# 6. Firefox Developer Edition
if [ ! -f "/opt/firefox-dev/firefox" ]; then
	echo "--- Installing Firefox Developer Edition ---"
	# 1. Cleanup broken remnants
	sudo rm -rf /opt/firefox-dev
	sudo rm -rf /opt/firefox
	
	# 2. Download and Extract
	TEMP_FF=$(mktemp -d)
	echo "Downloading Firefox Developer Edition..."
	curl -L "https://download.mozilla.org/?product=firefox-devedition-latest-ssl&os=linux64&lang=en-US" -o "$TEMP_FF/firefox.tar.archive"

	echo "Extracting..."
	# Mozilla tarball contains a 'firefox/' folder
	sudo tar -xf "$TEMP_FF/firefox.tar.archive" -C /opt/
	
	# Move the extracted 'firefox' folder to 'firefox-dev'
	sudo mv /opt/firefox /opt/firefox-dev

	# 3. Create Symlink to the actual binary (/opt/firefox-dev/firefox)
	sudo ln -sf /opt/firefox-dev/firefox /usr/local/bin/firefox-dev

	# 4. Create Desktop Entry
	echo "Creating desktop entry..."
	cat <<EOF | sudo tee /usr/share/applications/firefox-developer.desktop >/dev/null
[Desktop Entry]
Name=Firefox Developer Edition
GenericName=Web Browser
Exec=/usr/local/bin/firefox-dev %u
Terminal=false
Type=Application
Icon=/opt/firefox-dev/browser/chrome/icons/default/default128.png
Categories=Network;WebBrowser;Development;
MimeType=text/html;text/xml;application/xhtml+xml;application/xml;role=img/png;role=img/jpeg;role=img/gif;application/rss+xml;application/rdf+xml;image/gif;image/jpeg;image/png;x-scheme-handler/http;x-scheme-handler/https;
StartupNotify=true
EOF
	rm -rf "$TEMP_FF"
	echo "Firefox Developer Edition installed."
else
	echo "Firefox Developer Edition already exists, skipping."
fi

echo ">>> BINARIES_COMPLETE <<<"
