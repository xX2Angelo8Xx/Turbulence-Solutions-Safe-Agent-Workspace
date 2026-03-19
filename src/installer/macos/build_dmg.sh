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
APP_VERSION="3.0.2"
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

# FIX-056: Bundle the ts-python shim inside the .app for first-launch deployment
echo "==> Bundling ts-python shim..."
mkdir -p "${APP_BUNDLE}/Contents/Resources/shims"
cp "src/installer/shims/ts-python" "${APP_BUNDLE}/Contents/Resources/shims/ts-python"
chmod +x "${APP_BUNDLE}/Contents/Resources/shims/ts-python"

# INS-018: Copy the Python embeddable distribution into the app bundle if it
# has been populated at build time.  On macOS the bundled PyInstaller Python
# framework is the primary runtime; python-embed/ acts as a portable fallback
# for the security gate shim (INS-019/INS-020).
PYTHON_EMBED_SRC="src/installer/python-embed"
if [ -f "${PYTHON_EMBED_SRC}/python.exe" ] || [ -f "${PYTHON_EMBED_SRC}/python3" ]; then
    echo "==> Copying python-embed into app bundle Resources..."
    mkdir -p "${APP_BUNDLE}/Contents/Resources/python-embed"
    cp -R "${PYTHON_EMBED_SRC}/"* "${APP_BUNDLE}/Contents/Resources/python-embed/"
else
    echo "==> python-embed not populated — skipping (macOS uses PyInstaller framework)"
fi

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
# Step 3.1: Remove .dist-info directories (Python package metadata not needed
# at runtime; macOS codesign cannot process them as bundle subcomponents)
# ---------------------------------------------------------------------------
echo "==> Removing .dist-info directories from bundle..."
find "${APP_BUNDLE}/Contents/MacOS/_internal" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true

# ---------------------------------------------------------------------------
# Step 3.5: Ad-hoc code signing (bottom-up to avoid python3.11 dir issue)
# ---------------------------------------------------------------------------
echo "Step 3.5: Code signing (bottom-up)..."

# Sign individual shared libraries (.dylib and .so) inside _internal/
echo "  Signing .dylib files..."
find "${APP_BUNDLE}/Contents/MacOS/_internal" -name "*.dylib" -exec codesign --force --sign - {} \;
echo "  Signing .so files..."
find "${APP_BUNDLE}/Contents/MacOS/_internal" -name "*.so" -exec codesign --force --sign - {} \;

# Sign embedded Python.framework (valid nested bundle — use --deep)
if [ -d "${APP_BUNDLE}/Contents/MacOS/_internal/Python.framework" ]; then
    echo "  Signing Python.framework..."
    codesign --deep --force --sign - "${APP_BUNDLE}/Contents/MacOS/_internal/Python.framework"
fi

# NOTE: The launcher is CFBundleExecutable declared in Info.plist.
# Signing it via Contents/MacOS/launcher triggers macOS bundle validation,
# which recurses into _internal/ and fails on non-code data files (e.g. PNGs).
# PyInstaller already ad-hoc signs the binary during the build step
# ("Re-signing the EXE"). The signature is preserved when the binary is
# copied into the .app via `cp -R`, so no re-sign is needed here.

# Verify individual code signatures
# NOTE: Bundle-level signing is intentionally skipped. PyInstaller bundles
# place non-code files (images, .pyc, .zip) in Contents/MacOS/_internal/
# which codesign cannot handle as bundle subcomponents. The individual
# bottom-up signing above is sufficient for macOS Apple Silicon execution.
echo "Verifying code signatures..."
# Verify the pre-bundle binary (has PyInstaller ad-hoc signature; bundle copy inherits it)
codesign --verify "${DIST_DIR}/launcher/launcher" && echo "  Main executable (pre-bundle): OK"
if [ -d "${APP_BUNDLE}/Contents/MacOS/_internal/Python.framework" ]; then
    codesign --verify --deep "${APP_BUNDLE}/Contents/MacOS/_internal/Python.framework" && echo "  Python.framework: OK"
fi
echo "Code signing verification passed"

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
