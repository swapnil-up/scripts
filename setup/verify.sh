#!/bin/bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$REPO_ROOT/config"

# shellcheck source=manifest.sh
source "$SCRIPT_DIR/manifest.sh"
# shellcheck source=versions.env
source "$SCRIPT_DIR/versions.env"

FAILURES=0
WARNINGS=0
OKS=0

ok() {
	OKS=$((OKS + 1))
	printf '  [OK]   %s\n' "$1"
}

warn() {
	WARNINGS=$((WARNINGS + 1))
	printf '  [WARN] %s\n' "$1"
}

fail() {
	FAILURES=$((FAILURES + 1))
	printf '  [FAIL] %s\n' "$1"
}

section() {
	printf '\n== %s ==\n' "$1"
}

# Make tools installed outside /usr/bin visible in a non-login shell.
export PATH="$HOME/.local/bin:$HOME/.pyenv/shims:$HOME/.cargo/bin:$PATH"
for dir in \
	"$HOME/Android/Sdk/cmdline-tools/latest/bin" \
	"$HOME/Android/Sdk/platform-tools" \
	/var/lib/flatpak/exports/bin \
	"$HOME/.local/share/flatpak/exports/bin"; do
	[ -d "$dir" ] && PATH="$dir:$PATH"
done
[ -s "$HOME/.nvm/nvm.sh" ] && {
	set +u
	# shellcheck disable=SC1091
	. "$HOME/.nvm/nvm.sh" >/dev/null 2>&1
	set -u
}
[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ] && {
	set +u
	# shellcheck disable=SC1091
	. "$HOME/.sdkman/bin/sdkman-init.sh" >/dev/null 2>&1
	set -u
}

printf '\n=== Setup parity report: %s ===\n' "$(hostname)"
printf 'Generated: %s\n' "$(date -Iseconds)"

section "Host and repository"
if [ -r /etc/os-release ]; then
	# shellcheck disable=SC1091
	. /etc/os-release
	codename="${UBUNTU_CODENAME:-${VERSION_CODENAME:-unknown}}"
	ok "OS: ${PRETTY_NAME:-unknown} ($codename)"
	case " ${SUPPORTED_CODENAMES[*]} " in
	*" $codename "*) ok "codename $codename is supported" ;;
	*) fail "codename $codename is not supported (want: ${SUPPORTED_CODENAMES[*]})" ;;
	esac
else
	fail "cannot read /etc/os-release"
fi

arch="$(uname -m)"
case "$arch" in
x86_64) ok "architecture: $arch" ;;
*) warn "architecture $arch is not x86_64; some vendor binaries may not work" ;;
esac

if [ "$REPO_ROOT" = "$HOME/github/scripts" ]; then
	ok "repo is at $REPO_ROOT"
else
	fail "repo must live at $HOME/github/scripts (found $REPO_ROOT)"
fi

section "Required commands"
for command in "${REQUIRED_COMMANDS[@]}"; do
	if command -v "$command" >/dev/null 2>&1; then
		ok "$command"
	else
		fail "missing command: $command"
	fi
done
if [ -f "$HOME/.local/share/blesh/ble.sh" ]; then
	ok "ble.sh installed"
else
	fail "ble.sh is not installed"
fi

section "Config links"
link_total=0
link_bad=0
for package_dir in "$CONFIG_DIR"/*/; do
	package="$(basename "$package_dir")"
	while IFS= read -r -d '' entry; do
		[ "$(basename "$entry")" = "README.md" ] && continue
		rel="${entry#"$package_dir"}"
		target="$HOME/$rel"
		expected="$(realpath -m "$entry")"
		link_total=$((link_total + 1))
		if [ -L "$target" ] && [ "$(realpath -m "$target")" = "$expected" ]; then
			continue
		fi
		link_bad=$((link_bad + 1))
		if [ -e "$target" ]; then
			fail "$package: $target is not linked to the repo"
		else
			fail "$package: missing link $target"
		fi
	done < <(find "$package_dir" -mindepth 1 \( -type f -o -type l \) -print0)
done

if [ "$link_bad" -eq 0 ]; then
	ok "all $link_total package files are linked correctly"
else
	fail "$link_bad of $link_total package files are missing or mislinked"
fi

if [ -f "$HOME/.config/Code/User/settings.json" ]; then
	if python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$HOME/.config/Code/User/settings.json" 2>/dev/null; then
		ok "VS Code settings.json is valid JSON"
	else
		fail "VS Code settings.json is not valid JSON"
	fi
else
	fail "VS Code settings.json was not generated"
fi

section "i3 config"
if command -v i3 >/dev/null 2>&1; then
	if i3 -C -c "$HOME/.config/i3/config" >/tmp/verify-i3.$$ 2>&1; then
		ok "i3 config syntax"
	else
		fail "i3 config syntax errors:"
		sed 's/^/         /' /tmp/verify-i3.$$
	fi
	rm -f /tmp/verify-i3.$$
else
	warn "i3 is not installed; cannot validate config"
fi

declare -A seen_paths=()
while IFS= read -r line; do
	case "$line" in
	\#* | "") continue ;;
	esac
	for raw in $(grep -oE '(~|\$HOME)/[^ "]+' <<<"$line" 2>/dev/null || true); do
		path="${raw%%[,;)]*}"
		[ -n "${seen_paths[$path]:-}" ] && continue
		seen_paths[$path]=1
		expanded="${path/#\~/$HOME}"
		expanded="${expanded/#\$HOME/$HOME}"
		if [ -e "$expanded" ]; then
			continue
		fi
		case "$expanded" in
		"$HOME/.config"/* | "$HOME/.local"/* | "$HOME/github/scripts"/*)
			fail "i3 references missing path: $path"
			;;
		*)
			warn "i3 references missing data path: $path"
			;;
		esac
	done
done <"$HOME/.config/i3/config"

section "User services"
for unit in kanata timer-daemon; do
	if ! systemctl --user list-unit-files "$unit.service" >/dev/null 2>&1 ||
		! systemctl --user cat "$unit.service" >/dev/null 2>&1; then
		warn "$unit.service is not installed"
		continue
	fi
	if systemctl --user is-enabled --quiet "$unit.service"; then
		ok "$unit.service is enabled"
	else
		fail "$unit.service is not enabled"
	fi
	if systemctl --user is-active --quiet "$unit.service"; then
		ok "$unit.service is running"
	else
		warn "$unit.service is not running"
	fi
done

section "Groups"
current_groups=" $(id -nG) "
for group in uinput input video plugdev; do
	if [ "$(id -u)" = "0" ]; then
		warn "running as root; group checks skipped"
		break
	fi
	if ! getent group "$group" >/dev/null 2>&1; then
		warn "group $group does not exist"
	elif [[ "$current_groups" == *" $group "* ]]; then
		ok "member of $group"
	else
		fail "not a member of $group (log out/in after setup)"
	fi
done

section "Secrets"
for secret in config/bash/.env.secret config/conky/.config/conky/secrets.env; do
	path="$REPO_ROOT/$secret"
	if [ ! -f "$path" ]; then
		warn "$secret missing"
	elif head -c 10 "$path" 2>/dev/null | grep -q GITCRYPT; then
		warn "$secret is git-crypt locked (run: git-crypt unlock)"
	else
		ok "$secret is unlocked"
	fi
done

section "Versions"
if command -v python3 >/dev/null 2>&1; then
	python_version="$(python3 --version 2>&1)"
	if [[ "$python_version" == *"$PYTHON_VERSION"* ]]; then
		ok "Python $PYTHON_VERSION"
	else
		warn "Python is $python_version (pinned: $PYTHON_VERSION)"
	fi
else
	fail "python3 is not installed"
fi
for tool in node php cmake; do
	if command -v "$tool" >/dev/null 2>&1; then
		ok "$tool: $("$tool" --version 2>&1 | head -n1)"
	else
		warn "$tool is not installed"
	fi
done
if command -v java >/dev/null 2>&1; then
	java_version="$(java -version 2>&1 | head -n1)"
	if [[ "$java_version" == *"version \"${JAVA_VERSION%%-*}"* ]]; then
		ok "java: $java_version"
	else
		fail "java is $java_version (pinned: $JAVA_VERSION)"
	fi
else
	fail "java is not installed"
fi

if command -v flatpak >/dev/null 2>&1; then
	if flatpak list --app --columns=application 2>/dev/null | grep -qx "md.obsidian.Obsidian"; then
		ok "Obsidian flatpak is installed"
	else
		warn "Obsidian flatpak is not installed"
	fi
fi

printf '\nSummary: %d ok, %d warning(s), %d failure(s)\n' "$OKS" "$WARNINGS" "$FAILURES"
if [ "$FAILURES" -gt 0 ]; then
	exit 1
fi
