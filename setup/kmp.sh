#!/bin/bash
set -euo pipefail

echo ">>> KMP_START <<<"
echo "--- Setting up Kotlin Multiplatform (Android + JDK) ---"

# ── SDKMAN (for JDK) ──────────────────────────────────────────────
if [ ! -d "$HOME/.sdkman" ]; then
	echo "Installing SDKMAN..."
	curl -s "https://get.sdkman.io" | bash
else
	echo "SDKMAN already installed, skipping..."
fi

set +u
source "$HOME/.sdkman/bin/sdkman-init.sh"
set -u

# ── JDK 21 (Temurin) ──────────────────────────────────────────────
if ! java -version 2>&1 | grep -q "21"; then
	echo "Installing JDK 21 (Temurin)..."
	sdk install java 21.0.11-tem
else
	echo "JDK 21 already installed, skipping..."
fi

# ── JAVA_HOME (persist via shell config) ──────────────────────────
JAVA_HOME_LINE='export JAVA_HOME=$HOME/.sdkman/candidates/java/current'
if ! grep -q "JAVA_HOME" "$HOME/.bashrc" 2>/dev/null; then
	echo "$JAVA_HOME_LINE" >> "$HOME/.bashrc"
	echo "Added JAVA_HOME to .bashrc"
fi

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

# ── ANDROID_HOME (persist via shell config) ───────────────────────
ANDROID_HOME_LINE='export ANDROID_HOME=$HOME/Android/Sdk'
ANDROID_PATH_LINE='export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools'
if ! grep -q "ANDROID_HOME" "$HOME/.bashrc" 2>/dev/null; then
	{
		echo "$ANDROID_HOME_LINE"
		echo "$ANDROID_PATH_LINE"
	} >> "$HOME/.bashrc"
	echo "Added ANDROID_HOME to .bashrc"
fi

# ── SDK components (platform-tools, platform, build-tools) ────────
echo "Installing SDK components (platform-tools, platform android-36, build-tools 36.0.0)..."
yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --sdk_root="$ANDROID_HOME" \
	"platform-tools" \
	"platforms;android-36" \
	"build-tools;36.0.0" \
	2>&1 | grep -E "Installing|Downloading|done" || echo "  [WARN] sdkmanager may have failed — check output above"

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
