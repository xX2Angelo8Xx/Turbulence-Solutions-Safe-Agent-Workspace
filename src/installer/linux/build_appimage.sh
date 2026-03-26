#!/usr/bin/env bash
# build_appimage.sh — Linux AppImage build script for Agent Environment Launcher
# Supports x86_64 and aarch64 architectures
#
# Usage (run from repository root):
#   bash src/installer/linux/build_appimage.sh [x86_64|aarch64]
#
# If no architecture argument is supplied the host architecture is used.
# If dist/launcher/ already exists PyInstaller is skipped.

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
APP_NAME="Agent Environment Launcher"
APP_BUNDLE_NAME="TurbulenceSolutionsLauncher"
APP_VERSION="3.2.3"
APP_ID="com.turbulencesolutions.agentlauncher"
PUBLISHER="Turbulence Solutions"
SPEC_FILE="launcher.spec"
DIST_DIR="dist"
BUILD_DIR="build"
APPDIR="${DIST_DIR}/AppDir"

APPIMAGETOOL_URL_x86_64="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
APPIMAGETOOL_URL_aarch64="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-aarch64.AppImage"

# ---------------------------------------------------------------------------
# Architecture selection
# ---------------------------------------------------------------------------
if [ "${1:-}" = "x86_64" ] || [ "${1:-}" = "aarch64" ]; then
    TARGET_ARCH="${1}"
else
    TARGET_ARCH="$(uname -m)"
fi

APPIMAGE_FILENAME="${APP_BUNDLE_NAME}-${TARGET_ARCH}.AppImage"

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

# Validate PyInstaller output exists before proceeding
if [ ! -d "${DIST_DIR}/launcher" ]; then
    echo "ERROR: PyInstaller output not found at ${DIST_DIR}/launcher" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Step 2: Create AppDir structure
# ---------------------------------------------------------------------------
echo "==> Creating AppDir structure: ${APPDIR}"
rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

# Copy all PyInstaller --onedir output into AppDir/usr/bin/
cp -R "${DIST_DIR}/launcher/"* "${APPDIR}/usr/bin/"

# INS-018: Copy the Python embeddable distribution into the AppImage if it has
# been populated at build time.  On Linux the bundled PyInstaller Python is the
# primary runtime; python-embed/ acts as a portable fallback for the security
# gate shim (INS-019/INS-020).
PYTHON_EMBED_SRC="src/installer/python-embed"
if [ -f "${PYTHON_EMBED_SRC}/python3" ] || [ -f "${PYTHON_EMBED_SRC}/python" ]; then
    echo "==> Copying python-embed into AppDir..."
    mkdir -p "${APPDIR}/usr/bin/python-embed"
    cp -R "${PYTHON_EMBED_SRC}/"* "${APPDIR}/usr/bin/python-embed/"
else
    echo "==> python-embed not populated — skipping (Linux uses system/PyInstaller Python)"
fi

# FIX-057: Bundle the ts-python shim inside the AppImage for first-launch deployment
echo "==> Bundling ts-python shim..."
mkdir -p "${APPDIR}/usr/share/shims"
cp "src/installer/shims/ts-python" "${APPDIR}/usr/share/shims/ts-python"
chmod +x "${APPDIR}/usr/share/shims/ts-python"

# ---------------------------------------------------------------------------
# Step 3: Write .desktop file
# ---------------------------------------------------------------------------
DESKTOP_FILE_NAME="${APP_ID}.desktop"

cat > "${APPDIR}/usr/share/applications/${DESKTOP_FILE_NAME}" << DESKTOP
[Desktop Entry]
Name=${APP_NAME}
Exec=launcher
Icon=${APP_ID}
Type=Application
Categories=Development;Utility;
Comment=${PUBLISHER} Agent Environment Launcher
DESKTOP

# AppImage spec requires .desktop at AppDir root
cp "${APPDIR}/usr/share/applications/${DESKTOP_FILE_NAME}" "${APPDIR}/${APP_ID}.desktop"

# ---------------------------------------------------------------------------
# Step 4: Create placeholder icon (AppImage spec requires icon at AppDir root)
# ---------------------------------------------------------------------------
# Minimal valid SVG using company brand colours: #0A1D4E background, #5BC5F2 text
cat > "${APPDIR}/${APP_ID}.svg" << 'SVG'
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <rect width="256" height="256" fill="#0A1D4E"/>
  <text x="128" y="160" font-size="120" text-anchor="middle" fill="#5BC5F2">TS</text>
</svg>
SVG

cp "${APPDIR}/${APP_ID}.svg" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/${APP_ID}.svg"

# ---------------------------------------------------------------------------
# Step 5: Write AppRun entry point
# ---------------------------------------------------------------------------
cat > "${APPDIR}/AppRun" << 'APPRUN'
#!/bin/bash
set -e
SELF_DIR="$(dirname "$(readlink -f "$0")")"
exec "${SELF_DIR}/usr/bin/launcher" "$@"
APPRUN

chmod +x "${APPDIR}/AppRun"

# ---------------------------------------------------------------------------
# Step 6: Download appimagetool if not present
# ---------------------------------------------------------------------------
APPIMAGETOOL="./appimagetool-${TARGET_ARCH}.AppImage"

if [ ! -f "${APPIMAGETOOL}" ]; then
    echo "==> Downloading appimagetool for ${TARGET_ARCH}..."
    if [ "${TARGET_ARCH}" = "x86_64" ]; then
        APPIMAGETOOL_URL="${APPIMAGETOOL_URL_x86_64}"
    elif [ "${TARGET_ARCH}" = "aarch64" ]; then
        APPIMAGETOOL_URL="${APPIMAGETOOL_URL_aarch64}"
    else
        echo "ERROR: Unsupported architecture for appimagetool download: ${TARGET_ARCH}" >&2
        exit 1
    fi
    curl -fsSL --proto '=https' --tlsv1.2 -o "${APPIMAGETOOL}" "${APPIMAGETOOL_URL}"
    chmod +x "${APPIMAGETOOL}"
else
    echo "==> appimagetool found at ${APPIMAGETOOL} — skipping download"
fi

# ---------------------------------------------------------------------------
# Step 7: Run appimagetool to produce the final .AppImage
# ---------------------------------------------------------------------------
echo "==> Running appimagetool: ${APPIMAGE_FILENAME}"
ARCH="${TARGET_ARCH}" "${APPIMAGETOOL}" "${APPDIR}" "${DIST_DIR}/${APPIMAGE_FILENAME}"

# Make the resulting AppImage executable
chmod +x "${DIST_DIR}/${APPIMAGE_FILENAME}"

echo "==> Done: ${DIST_DIR}/${APPIMAGE_FILENAME}"
