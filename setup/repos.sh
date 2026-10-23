#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=versions.env
source "$SCRIPT_DIR/versions.env"

echo ">>> REPOS_START <<<"
echo "--- Configuring External Repositories ---"

# Detect OS codename (used by LLVM and PHP repos)
if command -v lsb_release &>/dev/null; then
	CODENAME=$(lsb_release -cs)
else
	echo "ERROR: lsb_release not found — cannot detect OS codename. Install lsb-release." >&2
	exit 1
fi

# 1. LLVM 18
LLVM_LIST="/etc/apt/sources.list.d/llvm-${LLVM_VERSION}.list"
if [ -f "$LLVM_LIST" ] && ! grep -q "$CODENAME" "$LLVM_LIST"; then
	echo "Removing stale LLVM 18 repository entry..."
	sudo rm -f "$LLVM_LIST"
fi
if [ ! -f "$LLVM_LIST" ]; then
	echo "Configuring LLVM 18 repository for $CODENAME..."
	curl -fsSL https://apt.llvm.org/llvm-snapshot.gpg.key | gpg --dearmor | sudo tee /usr/share/keyrings/llvm-${LLVM_VERSION}.gpg >/dev/null
	echo "deb [signed-by=/usr/share/keyrings/llvm-${LLVM_VERSION}.gpg] http://apt.llvm.org/$CODENAME/ llvm-toolchain-$CODENAME-$LLVM_VERSION main" | sudo tee "$LLVM_LIST"
fi

# 2. Neovim PPA
if ! grep -q "neovim-ppa/unstable" /etc/apt/sources.list.d/* 2>/dev/null; then
	sudo add-apt-repository -n -y ppa:neovim-ppa/unstable ||
		echo "  [WARN] could not add the Neovim PPA; apt will use the archive version"
fi

# 3. Fastfetch PPA
if ! grep -q "fastfetch" /etc/apt/sources.list.d/* 2>/dev/null; then
	sudo add-apt-repository -n -y ppa:zhangsongcui3371/fastfetch ||
		echo "  [WARN] could not add the Fastfetch PPA"
fi

# 4. VS Code Repo
if [ ! -f "/etc/apt/sources.list.d/vscode.list" ]; then
	curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | sudo tee /usr/share/keyrings/microsoft.gpg >/dev/null
	echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/code stable main" | sudo tee /etc/apt/sources.list.d/vscode.list
fi

# 5. Ondřej Surý PHP (migrated from deprecated PPA to packages.sury.org)
if [ -f "/etc/apt/sources.list.d/ondrej-ubuntu-php-jammy.list" ]; then
	echo "Removing deprecated ondrej/php PPA (moved to packages.sury.org)..."
	sudo rm -f /etc/apt/sources.list.d/ondrej-ubuntu-php-jammy.list
fi
SURY_LIST="/etc/apt/sources.list.d/sury-php.list"
if [ -f "$SURY_LIST" ] && ! grep -q "$CODENAME" "$SURY_LIST"; then
	echo "Removing stale Sury PHP repository entry..."
	sudo rm -f "$SURY_LIST"
fi
if [ ! -f "$SURY_LIST" ]; then
	curl -fsSL https://packages.sury.org/php/apt.gpg | sudo tee /usr/share/keyrings/sury-php.gpg >/dev/null
	echo "deb [signed-by=/usr/share/keyrings/sury-php.gpg] https://packages.sury.org/php/ $CODENAME main" | sudo tee "$SURY_LIST"
fi

sudo apt-get update -y
echo ">>> REPOS_COMPLETE <<<"
