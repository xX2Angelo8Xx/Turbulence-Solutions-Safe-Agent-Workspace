# Bug Report: AgentEnvironmentLauncher.app Crash on Launch

## Problem Statement

**AgentEnvironmentLauncher.app v2.0.0** fails to launch on macOS 14.3. The application terminates immediately upon execution with "Launchd job spawn failed" error. The app binary exists and is structurally valid but crashes before any GUI or initialization can occur.

---

## System Information

| Property | Value |
|----------|-------|
| **Operating System** | macOS |
| **OS Version** | 14.3 |
| **Build Version** | 23D2057 |
| **Hardware** | MacBook Air M3 13-inch 2024 |
| **Memory** | 16 GB |
| **Processor Architecture** | arm64 |
| **User** | mathias |

---

## Application Details

| Property | Value |
|----------|-------|
| **App Name** | AgentEnvironmentLauncher |
| **Bundle ID** | com.turbulencesolutions.agentlauncher |
| **Version** | 2.0.0 |
| **Bundle Identifier** | CFBundleIdentifier: com.turbulencesolutions.agentlauncher |
| **Executable** | launcher (Mach-O 64-bit arm64) |
| **Min System Version** | 11.0 |
| **Publisher** | Turbulence Solutions (Copyright 2024) |

---

## Error Messages

### Error 1: Code Signature Validation
```
AgentEnvironmentLauncher.app: code has no resources but signature indicates they must be present
```

### Error 2: Bundle Format Recognition
```
AgentEnvironmentLauncher.app: bundle format unrecognized, invalid, or unsuitable
In subcomponent: /path/to/AgentEnvironmentLauncher.app/Contents/MacOS/_internal/python3.11
```

### Error 3: Launch Failure (via `open` command)
```
The application cannot be opened for an unexpected reason, error=Error Domain=RBSRequestErrorDomain Code=5 "Launch failed."
UserInfo={
  NSLocalizedFailureReason=Launch failed.,
  NSUnderlyingError=0x13180ba80 {
    Error Domain=NSPOSIXErrorDomain
    Code=153
    "Unknown error: 153"
    UserInfo={NSLocalizedDescription=Launchd job spawn failed}
  }
}
```

### Error 4: Process Termination (Direct Execution)
```
zsh: killed     ./AgentEnvironmentLauncher.app/Contents/MacOS/launcher
```

---

## Test Cases & Reproduction Steps

### Test Case 1: Launch via Finder/GUI
**Steps:**
1. Locate `AgentEnvironmentLauncher.app` in Finder
2. Double-click to launch
3. Observe the result

**Expected Result:** App window opens and initializes

**Actual Result:** 
- Error dialog: "The application cannot be opened for an unexpected reason"
- Error code 153 returned (Launchd job spawn failed)
- Process terminates immediately

---

### Test Case 2: Launch via `open` Command
**Steps:**
1. Run: `open /path/to/AgentEnvironmentLauncher.app`
2. Check stderr output

**Expected Result:** App launches successfully

**Actual Result:**
```
Error Domain=RBSRequestErrorDomain Code=5 "Launch failed."
Launchd job spawn failed (Code 153)
Exit code: 1
```

---

### Test Case 3: Direct Binary Execution
**Steps:**
1. Run: `/path/to/AgentEnvironmentLauncher.app/Contents/MacOS/launcher`
2. Observe process

**Expected Result:** Application runs

**Actual Result:**
```
zsh: killed     ./AgentEnvironmentLauncher.app/Contents/MacOS/launcher
```
Process is immediately killed by the system

---

### Test Case 4: Code Signature Verification
**Steps:**
1. Run: `codesign -v /path/to/AgentEnvironmentLauncher.app`
2. Check result

**Expected Result:** Valid signature or unsigned status

**Actual Result:**
```
AgentEnvironmentLauncher.app: code object is not signed at all
In architecture: arm64
```

---

### Test Case 5: Bundle Structure Validation
**Steps:**
1. Verify Contents structure
2. Check Info.plist
3. Verify executable binary

**Expected Result:** Valid macOS app bundle structure

**Actual Result:**
✅ Valid - Bundle structure is correct:
- `Contents/MacOS/launcher` (Mach-O 64-bit arm64, executable)
- `Contents/Info.plist` (valid XML plist)
- `Contents/Resources/` (exists)
- Embedded Python.framework (valid structure)

---

### Test Case 6: Binary Compatibility Check
**Steps:**
1. Run: `file ./launcher`
2. Run: `otool -L ./launcher`
3. Check dependencies

**Expected Result:** All dependencies available on system

**Actual Result:**
- ✅ Binary type correct: `Mach-O 64-bit executable arm64`
- ✅ All system frameworks linked exist:
  - Carbon.framework
  - ApplicationServices.framework
  - CoreFoundation.framework
  - CoreServices.framework
  - libSystem.B.dylib
  - libz.1.dylib
- ⚠️ **Issue:** Crash occurs before dependent libraries can be validated at runtime

---

## Diagnostic Information Gathered

### Bundle Structure
```
AgentEnvironmentLauncher.app/
├── Contents/
│   ├── Info.plist (valid)
│   ├── MacOS/
│   │   ├── launcher (Mach-O 64-bit arm64, 2.7MB)
│   │   └── _internal/
│   │       ├── Python → Python.framework/Versions/3.11/Python
│   │       ├── Python.framework/ (valid structure)
│   │       ├── python3.11/ (directory containing lib-dynload)
│   │       ├── base_library.zip
│   │       ├── Tcl/Tk data libraries
│   │       ├── PIL (image processing)
│   │       ├── customtkinter (GUI library)
│   │       └── Multiple .dylib dependencies
│   └── Resources/ (exists)
```

### Python Runtime Environment
- ✅ Python framework present: 3.11
- ✅ Python binary valid: `Mach-O 64-bit dynamically linked shared library arm64` (6.7MB)
- ✅ python3.11 directory exists with lib-dynload modules
- ✅ All Python packages bundled:
  - PIL (Pillow) with .dylibs
  - customtkinter (GUI)
  - Base library archive

---

## Attempted Troubleshooting Steps

| Action | Result |
|--------|--------|
| Remove invalid code signature | ❌ Still cannot re-sign (PyInstaller bundle limitation) |
| Remove Gatekeeper quarantine attributes | ❌ Crash persists |
| Strip all extended attributes (xattr) | ❌ Crash persists |
| Remove .DS_Store files | ❌ Crash persists |
| Install to /Applications | ❌ Crash persists |
| Direct binary execution | ❌ Immediate kill by system |
| Enable debug output (PYINSTALLER_DEBUG) | ❌ Process killed too fast to capture output |

---

## Analysis & Potential Root Causes

### Confirmed Valid
- ✅ Bundle structure is correct macOS app bundle
- ✅ Binary architecture matches system (arm64)
- ✅ All linked system frameworks exist
- ✅ Python runtime is properly bundled
- ✅ No quarantine or security attributes blocking execution

### Potential Issues
1. **PyInstaller Signature Issue** - PyInstaller-built apps have known code signing limitations on macOS with certain configurations
2. **Python Runtime Incompatibility** - The bundled Python 3.11 may be incompatible with:
   - This specific macOS version (14.3)
   - This specific hardware (M3 chip)
   - This specific configuration
3. **Entitlements or Hardening** - Missing or incorrect code signing entitlements required for execution
4. **RPATH Configuration** - Incorrect runtime library search paths in the binary
5. **Dylib Dependency Missing** - A required dylib is missing or incompatible despite appearing present in otool output

---

## Steps Taken to Test

1. ✅ Verified macOS version and build
2. ✅ Examined bundle structure
3. ✅ Validated Info.plist configuration  
4. ✅ Checked binary architecture (arm64)
5. ✅ Verified system framework availability
6. ✅ Tested code signature status
7. ✅ Attempted signature removal and re-signing
8. ✅ Removed Gatekeeper quarantine attributes
9. ✅ Cleaned extended attributes
10. ✅ Tested via multiple launch methods (Finder, open, direct)
11. ✅ Inspected dylib dependencies with otool
12. ✅ Attempted system call tracing with dtruss

---

## Recommendation for Developer

This appears to be a **PyInstaller build configuration issue**. Please investigate:

1. **Rebuild the application** with:
   - Latest PyInstaller version
   - Proper ad-hoc code signing (`--codesign-identity=-`)
   - Correct entitlements for arm64 macOS 14+
   
2. **Verify** bundled Python 3.11 is compiled for:
   - arm64 architecture
   - macOS 11+ compatibility
   - Correct deployment target

3. **Test** on target hardware before release:
   - MacBook Air M3 specifically
   - macOS 14.3 specifically

4. **Consider** creating a universal binary (arm64 + x86_64) if targeting Intel Macs as well

---

## Environment

- **Hardware:** MacBook Air M3 13-inch 2024
- **RAM:** 16 GB
- **macOS:** 14.3 (23D2057)
- **Date of Report:** March 17, 2026
- **App Version Tested:** 2.0.0
- **Build Method:** PyInstaller (inferred from binary structure)
