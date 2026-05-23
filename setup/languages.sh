#!/bin/bash
set -euo pipefail

echo ">>> LANGUAGES_START <<<"
echo "--- Running Language/Runtime Installer ---"

if [ ! -d "$HOME/.pyenv" ]; then
	echo "Installing Pyenv..."
	curl https://pyenv.run | bash
else
	echo "Pyenv already installed, skipping..."
fi
echo ">>> LANGUAGES_PYENV_DONE <<<"

# Install NVM (Node Version Manager) if missing
if [ ! -d "$HOME/.nvm" ]; then
	echo "Installing NVM..."
	curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

	export NVM_DIR="$HOME/.nvm"
	[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

	nvm install --lts
	nvm use --lts
fi
echo ">>> LANGUAGES_NVM_DONE <<<"

# Install Rust via Rustup if missing
if ! command -v cargo &>/dev/null; then
	echo "Installing Rust..."
	curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
fi
echo ">>> LANGUAGES_RUST_DONE <<<"

# Install Tree-sitter CLI via Cargo (The GLIBC-safe way)
if ! command -v tree-sitter &>/dev/null; then
	echo "Installing Tree-sitter CLI via Cargo (building from source, check setup.log)..."
	# This ensures it's compiled specifically for your system's GLIBC
	cargo install tree-sitter-cli >> "${LOG_FILE:-/dev/null}" 2>&1
fi
echo ">>> LANGUAGES_COMPLETE <<<"
