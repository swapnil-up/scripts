#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=versions.env
source "$SCRIPT_DIR/versions.env"

echo ">>> LANGUAGES_START <<<"
echo "--- Running Language/Runtime Installer ---"

if [ ! -d "$HOME/.pyenv" ]; then
	echo "Installing Pyenv..."
	curl https://pyenv.run | bash
else
	echo "Pyenv already installed, skipping..."
fi
echo ">>> LANGUAGES_PYENV_DONE <<<"

# Install NVM, then Node LTS through NVM (the installer does not install Node).
if [ ! -d "$HOME/.nvm" ]; then
	echo "Installing NVM..."
	curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/${NVM_VERSION}/install.sh | bash
fi

export NVM_DIR="$HOME/.nvm"
if [ ! -s "$NVM_DIR/nvm.sh" ]; then
	echo "ERROR: nvm.sh not found after install" >&2
	exit 1
fi

set +u
# shellcheck disable=SC1091
. "$NVM_DIR/nvm.sh"
echo "Ensuring Node LTS..."
nvm install --lts
nvm alias default 'lts/*'
set -u
echo ">>> LANGUAGES_NVM_DONE <<<"

if ! command -v cargo &>/dev/null; then
	echo "Installing Rust..."
	curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
fi
if [ -f "$HOME/.cargo/env" ]; then
	# shellcheck disable=SC1091
	. "$HOME/.cargo/env"
fi
echo ">>> LANGUAGES_RUST_DONE <<<"

if ! command -v tree-sitter &>/dev/null; then
	echo "Installing Tree-sitter CLI via Cargo (building from source, this may take a few minutes)..."
	cargo install tree-sitter-cli 2>&1 | tee -a "${LOG_FILE:-/dev/null}"
	echo "Tree-sitter CLI installed."
fi
echo ">>> LANGUAGES_COMPLETE <<<"
