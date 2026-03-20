# macOS Installation Guide — Agent Environment Launcher

## Why This Is Needed

macOS Gatekeeper blocks applications that are not signed with an Apple Developer ID certificate and notarized by Apple. Since Agent Environment Launcher uses ad-hoc code signing (no Developer ID), macOS will display a warning when you first open the app after downloading it.

You may see one of these messages:
- **"AgentEnvironmentLauncher" is damaged and can't be opened.**
- **"AgentEnvironmentLauncher" can't be opened because Apple cannot check it for malicious software.**
- **"AgentEnvironmentLauncher" can't be opened because it is from an unidentified developer.**

This is expected behavior for internally distributed applications without Apple notarization. The app is safe to use.

---

## Installation Steps

### Step 1: Download the DMG

Download the latest `AgentEnvironmentLauncher-x.x.x-arm64.dmg` from the GitHub Releases page.

### Step 2: Mount the DMG

Double-click the `.dmg` file to mount it. Drag `AgentEnvironmentLauncher.app` to your **Applications** folder (or any folder of your choice).

### Step 3: Remove the Quarantine Flag

macOS marks all files downloaded from the internet with a quarantine attribute. This must be removed before the app can launch.

**Open Terminal** (Applications → Utilities → Terminal) and run:

```bash
xattr -cr /Applications/AgentEnvironmentLauncher.app
```

> If you placed the app in a different folder, adjust the path accordingly.

### Step 4: Launch the App

Double-click `AgentEnvironmentLauncher.app` to launch it. It should now open without any Gatekeeper warnings.

---

## Alternative Methods

If you prefer not to use Terminal, there are two other approaches:

### Method A: Right-Click → Open

1. Right-click (or Control-click) `AgentEnvironmentLauncher.app`
2. Select **Open** from the context menu
3. A dialog appears: "macOS cannot verify the developer..." — click **Open**
4. The app launches. Subsequent launches via double-click will work normally.

### Method B: System Settings

1. Try to open the app normally (it will be blocked)
2. Open **System Settings** → **Privacy & Security**
3. Scroll down to the **Security** section
4. You will see: "AgentEnvironmentLauncher was blocked..." with an **Open Anyway** button
5. Click **Open Anyway** and confirm

---

## Troubleshooting

### "App is damaged and can't be opened"

This specifically means the quarantine attribute is still present. Use the Terminal method:

```bash
xattr -cr /Applications/AgentEnvironmentLauncher.app
```

### App closes immediately after opening

If the app launches but immediately closes, check the system log for details:

```bash
# View recent crash logs
log show --predicate 'subsystem == "com.apple.launchd"' --last 1m
```

Report the output to the development team.

### Verifying the app signature

To confirm the app is properly signed:

```bash
codesign --verify --verbose /Applications/AgentEnvironmentLauncher.app
```

Expected output: `valid on disk` — this confirms structural integrity.

---

## For Developers

The app is ad-hoc signed with entitlements that allow:
- Unsigned executable memory (required by embedded Python.framework)
- Disabled library validation (required for PyInstaller-bundled .dylib/.so files)
- DYLD environment variables (required by PyInstaller's bootloader)

To enable "zero-friction" installation without the `xattr` workaround, the project would need:
1. Apple Developer ID certificate ($99/year)
2. Code signing with the Developer ID in CI
3. Notarization via `xcrun notarytool submit`
4. Stapling the notarization ticket to the DMG
