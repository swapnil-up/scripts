#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=versions.env
source "$SCRIPT_DIR/versions.env"

echo ">>> KMP_START <<<"
echo "--- Setting up Kotlin Multiplatform (Android + JDK) ---"
JAVA_MAJOR="${JAVA_VERSION%%-*}"

# ── SDKMAN (for JDK) ──────────────────────────────────────────────
if [ ! -d "$HOME/.sdkman" ]; then
	echo "Installing SDKMAN..."
	curl -s "https://get.sdkman.io" | bash
else
	echo "SDKMAN already installed, skipping..."
fi

set +u
export sdkman_auto_answer=true
export sdkman_auto_selfupdate=false
# shellcheck disable=SC1091
source "$HOME/.sdkman/bin/sdkman-init.sh"

# ── JDK (Temurin) ─────────────────────────────────────────────────
if ! java -version 2>&1 | grep -q "version \"$JAVA_MAJOR"; then
	echo "Installing JDK $JAVA_VERSION (Temurin)..."
	sdk install java "$JAVA_VERSION"
else
	echo "JDK $JAVA_VERSION already installed, skipping..."
fi
sdk default java "$JAVA_VERSION"
sdk use java "$JAVA_VERSION"
set -u

if ! java -version 2>&1 | grep -q "version \"$JAVA_MAJOR"; then
	echo "ERROR: JDK $JAVA_VERSION is not the active Java version" >&2
	exit 1
fi
export JAVA_HOME="$HOME/.sdkman/candidates/java/current"

# ── Android SDK ───────────────────────────────────────────────────
ANDROID_SDK="$HOME/Android/Sdk"
if [ ! -f "$ANDROID_SDK/cmdline-tools/latest/bin/sdkmanager" ]; then
	echo "Installing Android SDK command-line tools..."
	mkdir -p "$ANDROID_SDK/cmdline-tools"
	curl -sL "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip" -o /tmp/cmdline-tools.zip
	unzip -q /tmp/cmdline-tools.zip -d "$ANDROID_SDK/cmdline-tools"
	mv "$ANDROID_SDK/cmdline-tools/cmdline-tools" "$ANDROID_SDK/cmdline-tools/latest"
	rm /tmp/cmdline-tools.zip
else
	echo "Android cmdline-tools already installed, skipping..."
fi

export ANDROID_HOME="$ANDROID_SDK"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"

# ── SDK components (platform-tools, platform, build-tools) ────────
SDKMANAGER="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"
echo "Accepting Android SDK licenses..."
set +e
yes | "$SDKMANAGER" --sdk_root="$ANDROID_HOME" --licenses >/dev/null 2>&1
set -e

echo "Installing SDK components (platform-tools, platform $ANDROID_PLATFORM, build-tools $ANDROID_BUILD_TOOLS)..."
set +e
yes | "$SDKMANAGER" --sdk_root="$ANDROID_HOME" \
	"platform-tools" \
	"platforms;$ANDROID_PLATFORM" \
	"build-tools;$ANDROID_BUILD_TOOLS" \
	2>&1 | grep -E "Installing|Downloading|done"
set -e

# ── udev rule for Android devices ─────────────────────────────────
UDEV_FILE="/etc/udev/rules.d/51-android.rules"
if [ ! -f "$UDEV_FILE" ]; then
	echo "Setting up Android udev rules..."
	sudo tee "$UDEV_FILE" >/dev/null <<'EOF'
# Google (Pixel, Nexus, and many phones in debug mode)
SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", MODE="0666", GROUP="plugdev"
# Samsung
SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", MODE="0666", GROUP="plugdev"
# Xiaomi / Redmi
SUBSYSTEM=="usb", ATTR{idVendor}=="2717", MODE="0666", GROUP="plugdev"
# OnePlus
SUBSYSTEM=="usb", ATTR{idVendor}=="22d9", MODE="0666", GROUP="plugdev"
EOF
	sudo udevadm control --reload-rules
	sudo udevadm trigger
else
	echo "Android udev rules already exist, skipping..."
fi

# Add user to plugdev group
if ! groups "$USER" | grep -q "plugdev"; then
	sudo usermod -aG plugdev "$USER"
	echo "Added $USER to plugdev group (may need re-login)"
fi

echo ">>> KMP_COMPLETE <<<"
