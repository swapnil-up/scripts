#!/bin/bash
set -euo pipefail

echo ">>> REPOS_START <<<"
echo "--- Configuring External Repositories ---"

# 1. LLVM 18 (Ubuntu — uses codename detection)
if [ ! -f "/etc/apt/sources.list.d/llvm-18.list" ]; then
	CODENAME=$(lsb_release -cs 2>/dev/null || echo "jammy")
	echo "Configuring LLVM 18 repository for $CODENAME..."
	curl -fsSL https://apt.llvm.org/llvm-snapshot.gpg.key | gpg --dearmor | sudo tee /usr/share/keyrings/llvm-18.gpg >/dev/null
	echo "deb [signed-by=/usr/share/keyrings/llvm-18.gpg] http://apt.llvm.org/$CODENAME/ llvm-toolchain-$CODENAME-18 main" | sudo tee /etc/apt/sources.list.d/llvm-18.list
fi

# 2. Neovim PPA
if ! grep -q "neovim-ppa/unstable" /etc/apt/sources.list.d/* 2>/dev/null; then
	sudo add-apt-repository ppa:neovim-ppa/unstable -y
fi

# 3. Fastfetch PPA
if ! grep -q "fastfetch" /etc/apt/sources.list.d/* 2>/dev/null; then
	sudo add-apt-repository ppa:zhangsongcui3371/fastfetch -y
fi

# 4. VS Code Repo
if [ ! -f "/etc/apt/sources.list.d/vscode.list" ]; then
	curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | sudo tee /usr/share/keyrings/microsoft.gpg >/dev/null
	echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/code stable main" | sudo tee /etc/apt/sources.list.d/vscode.list
fi

sudo apt update -y
echo ">>> REPOS_COMPLETE <<<"
