#!/usr/bin/env bash
# build_dmg.sh — macOS DMG build script for Agent Environment Launcher
# Supports Intel (x86_64) and Apple Silicon (arm64)
#
# Usage (run from repository root):
#   bash src/installer/macos/build_dmg.sh [x86_64|arm64]
#
# If no architecture argument is supplied the host architecture is used.
# If dist/launcher/ already exists PyInstaller is skipped.

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
APP_NAME="Agent Environment Launcher"
APP_BUNDLE_NAME="AgentEnvironmentLauncher"
APP_VERSION="2.0.0"
APP_ID="com.turbulencesolutions.agentlauncher"
PUBLISHER="Turbulence Solutions"
SPEC_FILE="launcher.spec"
DIST_DIR="dist"
BUILD_DIR="build"

# ---------------------------------------------------------------------------
# Architecture selection
# ---------------------------------------------------------------------------
if [ "${1:-}" = "x86_64" ] || [ "${1:-}" = "arm64" ]; then
    TARGET_ARCH="${1}"
else
    TARGET_ARCH="$(uname -m)"
fi

DMG_FILENAME="${APP_BUNDLE_NAME}-${APP_VERSION}-${TARGET_ARCH}.dmg"
APP_BUNDLE="${DIST_DIR}/${APP_BUNDLE_NAME}.app"

echo "==> Building ${APP_NAME} v${APP_VERSION} for ${TARGET_ARCH}"

# ---------------------------------------------------------------------------
# Step 1: Run PyInstaller (skip if dist/launcher already exists)
# ---------------------------------------------------------------------------
if [ ! -d "${DIST_DIR}/launcher" ]; then
    echo "==> Running PyInstaller..."
    python -m PyInstaller \
        --distpath "${DIST_DIR}" \
        --workpath "${BUILD_DIR}" \
        --noconfirm \
        "${SPEC_FILE}"
else
    echo "==> PyInstaller output found at ${DIST_DIR}/launcher — skipping build"
fi

# ---------------------------------------------------------------------------
# Step 2: Create .app bundle directory structure
# ---------------------------------------------------------------------------
echo "==> Creating .app bundle: ${APP_BUNDLE}"
rm -rf "${APP_BUNDLE}"
mkdir -p "${APP_BUNDLE}/Contents/MacOS"
mkdir -p "${APP_BUNDLE}/Contents/Resources"

# Copy all PyInstaller --onedir output into Contents/MacOS/
cp -R "${DIST_DIR}/launcher/"* "${APP_BUNDLE}/Contents/MacOS/"

# ---------------------------------------------------------------------------
# Step 3: Write Info.plist
# ---------------------------------------------------------------------------
cat > "${APP_BUNDLE}/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>${APP_ID}</string>
    <key>CFBundleVersion</key>
    <string>${APP_VERSION}</string>
    <key>CFBundleShortVersionString</key>
    <string>${APP_VERSION}</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright 2024 ${PUBLISHER}</string>
</dict>
</plist>
PLIST

# ---------------------------------------------------------------------------
# Step 4: Create DMG with hdiutil
# ---------------------------------------------------------------------------
echo "==> Creating DMG: ${DMG_FILENAME}"

# Stage .app in a temp directory so hdiutil has a clean source folder
STAGING_DIR="$(mktemp -d)"
cp -R "${APP_BUNDLE}" "${STAGING_DIR}/"

hdiutil create \
    -volname "${APP_NAME}" \
    -srcfolder "${STAGING_DIR}" \
    -ov \
    -format UDZO \
    -o "${DIST_DIR}/${DMG_FILENAME}"

rm -rf "${STAGING_DIR}"

echo "==> Done: ${DIST_DIR}/${DMG_FILENAME}"
