#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EXPECTED_ROOT="$HOME/github/scripts"

# shellcheck source=manifest.sh
source "$SCRIPT_DIR/manifest.sh"

die() {
	echo "PREFLIGHT: $*" >&2
	exit 1
}

warn() {
	echo "PREFLIGHT: WARN: $*" >&2
}

echo ">>> PREFLIGHT_START <<<"
echo "--- Checking bootstrap preconditions ---"

if [ "$(id -u)" -eq 0 ]; then
	die "run as your user, not root (sudo is used internally)"
fi

if ! command -v apt-get >/dev/null 2>&1; then
	die "apt-get not found; this setup supports Debian/Ubuntu only"
fi

for cmd in sudo dpkg-query; do
	if ! command -v "$cmd" >/dev/null 2>&1; then
		die "$cmd is required before bootstrap can run"
	fi
done

actual_root="$(readlink -f "$REPO_ROOT")"
expected_root="$(readlink -f "$EXPECTED_ROOT")"
if [ "$actual_root" != "$expected_root" ]; then
	die "repo must live at $EXPECTED_ROOT (found $actual_root)"
fi

CODENAME=""
if [ -r /etc/os-release ]; then
	# shellcheck disable=SC1091
	. /etc/os-release
	CODENAME="${UBUNTU_CODENAME:-${VERSION_CODENAME:-}}"
fi
if [ -z "$CODENAME" ] && command -v lsb_release >/dev/null 2>&1; then
	CODENAME="$(lsb_release -cs)"
fi
if [ -z "$CODENAME" ]; then
	die "could not detect the OS codename"
fi

supported=false
for name in "${SUPPORTED_CODENAMES[@]}"; do
	if [ "$CODENAME" = "$name" ]; then
		supported=true
		break
	fi
done
if [ "$supported" != true ]; then
	die "unsupported release '$CODENAME' (supported: ${SUPPORTED_CODENAMES[*]})"
fi

if [ "$(uname -m)" != "x86_64" ]; then
	warn "architecture is $(uname -m); several vendor binaries are x86_64-only"
fi

missing=()
for pkg in "${PREFLIGHT_PACKAGES[@]}"; do
	if ! dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed"; then
		missing+=("$pkg")
	fi
done

if [ "${#missing[@]}" -gt 0 ]; then
	echo "Installing preflight packages: ${missing[*]}"
	export DEBIAN_FRONTEND=noninteractive
	sudo apt-get update -y
	sudo apt-get install -y "${missing[@]}"
fi

missing_commands=()
for cmd in "${PREFLIGHT_COMMANDS[@]}"; do
	if ! command -v "$cmd" >/dev/null 2>&1; then
		missing_commands+=("$cmd")
	fi
done
if [ "${#missing_commands[@]}" -gt 0 ]; then
	die "preflight commands still missing: ${missing_commands[*]}"
fi

echo "Preflight OK: $CODENAME on $(uname -m) at $EXPECTED_ROOT"
echo ">>> PREFLIGHT_COMPLETE <<<"
