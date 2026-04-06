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
APP_VERSION="3.4.0"
APP_ID="com.turbulencesolutions.agentlauncher"
PUBLISHER="Turbulence Solutions"
SPEC_FILE="launcher.spec"
DIST_DIR="dist"
BUILD_DIR="build"
ENTITLEMENTS="src/installer/macos/entitlements.plist"

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
# Step 2.1: Relocate _internal/ to Contents/Resources/ (codesign fix)
#
# macOS codesign treats all files in Contents/MacOS/ as code subcomponents.
# Moving _internal/ to Contents/Resources/ and symlinking ensures codesign
# only sees the launcher executable in Contents/MacOS/.  codesign does NOT
# traverse symlinks — they are recorded as-is in CodeResources.
# ---------------------------------------------------------------------------
echo "==> Relocating _internal/ to Contents/Resources/ (codesign fix)..."
mv "${APP_BUNDLE}/Contents/MacOS/_internal" "${APP_BUNDLE}/Contents/Resources/_internal"
ln -s "../Resources/_internal" "${APP_BUNDLE}/Contents/MacOS/_internal"
echo "  _internal/ -> Contents/Resources/_internal (symlinked)"

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
find "${APP_BUNDLE}/Contents/Resources/_internal" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true

# ---------------------------------------------------------------------------
# Step 3.5: Ad-hoc code signing with entitlements (bottom-up then bundle)
#
# NOTE: Bundle-level signing is intentionally skipped as a separate --deep step.
# PyInstaller embeds non-code resource files (data files, images, metadata) in
# _internal/ that macOS codesign cannot validate as code objects during a --deep
# recursive pass. Instead we use bottom-up component signing: sign each .dylib,
# .so, and Python.framework individually (leaf-first), then sign the launcher
# executable and the .app bundle without --deep to avoid the python3.11 dir error.
#
# Signing strategy:
#   1. Sign all .dylib and .so files individually (leaf components)
#   2. Sign Python.framework (nested bundle, uses --deep)
#   3. Sign the main launcher executable (with entitlements)
#   4. Sign the entire .app bundle (top-level, without --deep)
#
# --options runtime  enables the hardened runtime (required for notarization
#                    readiness and improves Gatekeeper trust scoring)
# --entitlements     grants permissions needed by the embedded Python runtime
# --force            overwrites any existing PyInstaller ad-hoc signature
# --sign -           ad-hoc identity (no Developer ID certificate)
# ---------------------------------------------------------------------------
echo "Step 3.5: Code signing (bottom-up with entitlements)..."

if [ ! -f "${ENTITLEMENTS}" ]; then
    echo "ERROR: Entitlements file not found at ${ENTITLEMENTS}" >&2
    exit 1
fi

# 1. Sign individual shared libraries (.dylib and .so) inside _internal/
echo "  Signing .dylib files..."
find "${APP_BUNDLE}/Contents/Resources/_internal" -name "*.dylib" -exec codesign --force --options runtime --sign - {} \;
echo "  Signing .so files..."
find "${APP_BUNDLE}/Contents/Resources/_internal" -name "*.so" -exec codesign --force --options runtime --sign - {} \;

# 2. Sign embedded Python.framework (valid nested bundle — uses --deep)
if [ -d "${APP_BUNDLE}/Contents/Resources/_internal/Python.framework" ]; then
    echo "  Signing Python.framework..."
    codesign --deep --force --options runtime --entitlements "${ENTITLEMENTS}" --sign - "${APP_BUNDLE}/Contents/Resources/_internal/Python.framework"
fi

# 3. Sign the main launcher executable inside the .app bundle.
#    NOTE: We verify the pre-bundle binary (dist/launcher/launcher) separately below.
#    Re-signing the CFBundleExecutable (Contents/MacOS/launcher) inside an already-signed
#    bundle triggers macOS bundle validation. We sign it here before the bundle seal.
echo "  Signing main executable..."
codesign --force --options runtime \
    --entitlements "${ENTITLEMENTS}" \
    --sign - "${APP_BUNDLE}/Contents/MacOS/launcher"

# 4. (top-level, without --deep).
#    Non-code files in _internal/ are included as resource rules via CodeResources
#    rather than as nested code objects, which avoids the python3.11 directory error.
echo "  Signing .app bundle..."
codesign --force --options runtime \
    --entitlements "${ENTITLEMENTS}" \
    --sign - "${APP_BUNDLE}"

# Verify code signatures
# NOTE: We verify the pre-bundle binary (dist/launcher/launcher) here, NOT the
# CFBundleExecutable inside the .app (Contents/MacOS/launcher). Verifying the
# CFBundleExecutable path directly after bundle sealing triggers macOS bundle
# validation which can fail on non-code resources in _internal/.
echo "Verifying code signatures..."
codesign --verify "${DIST_DIR}/launcher/launcher" && echo "  Pre-bundle binary: OK"
if [ -d "${APP_BUNDLE}/Contents/Resources/_internal/Python.framework" ]; then
    codesign --verify --deep "${APP_BUNDLE}/Contents/Resources/_internal/Python.framework" && echo "  Python.framework: OK"
fi
codesign --verify --verbose "${APP_BUNDLE}" && echo "  App bundle: OK"
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
