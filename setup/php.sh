#!/bin/bash
set -euo pipefail

echo ">>> PHP_START <<<"
echo "--- Setting up PHP + Composer ---"

# ── PHP (CLI + common extensions) ─────────────────────────────────
PHP_VERSION="8.3"
PHP_PACKAGES=(
	"php${PHP_VERSION}-cli"
	"php${PHP_VERSION}-mbstring"
	"php${PHP_VERSION}-xml"
	"php${PHP_VERSION}-curl"
	"php${PHP_VERSION}-sqlite3"
	"php${PHP_VERSION}-mysql"
	"php${PHP_VERSION}-bcmath"
	"php${PHP_VERSION}-zip"
	"php${PHP_VERSION}-gd"
	"php${PHP_VERSION}-intl"
	"php${PHP_VERSION}-xsl"
	"php${PHP_VERSION}-xmlrpc"
)

INSTALL_PHP=false
for pkg in "${PHP_PACKAGES[@]}"; do
	if ! dpkg -s "$pkg" >/dev/null 2>&1; then
		INSTALL_PHP=true
		break
	fi
done

if [ "$INSTALL_PHP" = true ]; then
	echo "Installing PHP ${PHP_VERSION} and extensions..."
	sudo apt install -y "${PHP_PACKAGES[@]}"
else
	echo "PHP ${PHP_VERSION} already installed, skipping..."
fi

# ── Composer ───────────────────────────────────────────────────────
if ! command -v composer &>/dev/null; then
	echo "Installing Composer..."
	curl -sS https://getcomposer.org/installer | sudo php -- --install-dir=/usr/local/bin --filename=composer
else
	echo "Composer already installed, skipping..."
fi

# ── PATH for Composer global binaries ──────────────────────────────
COMPOSER_BIN='export PATH="$PATH:$HOME/.config/composer/vendor/bin"'
if ! grep -q "\.config/composer/vendor/bin" "$HOME/.bashrc" 2>/dev/null; then
	echo "$COMPOSER_BIN" >> "$HOME/.bashrc"
	echo "Added Composer vendor/bin to .bashrc"
fi

echo ">>> PHP_COMPLETE <<<"
