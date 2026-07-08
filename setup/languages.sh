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
# install.sh handles everything: downloads nvm, installs node LTS, sets default
if [ ! -d "$HOME/.nvm" ]; then
	echo "Installing NVM..."
	curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
fi
echo ">>> LANGUAGES_NVM_DONE <<<"

# Install Rust via Rustup if missing
if ! command -v cargo &>/dev/null; then
	echo "Installing Rust..."
	curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
	. "$HOME/.cargo/env"
fi
echo ">>> LANGUAGES_RUST_DONE <<<"

# Install Tree-sitter CLI via Cargo (The GLIBC-safe way)
if ! command -v tree-sitter &>/dev/null; then
	echo "Installing Tree-sitter CLI via Cargo (building from source, this may take a few minutes)..."
	cargo install tree-sitter-cli 2>&1 | tee -a "${LOG_FILE:-/dev/null}"
	echo "Tree-sitter CLI installed."
fi
echo ">>> LANGUAGES_COMPLETE <<<"
