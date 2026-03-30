@echo off
setlocal EnableDelayedExpansion
set "CONFIG=%LOCALAPPDATA%\TurbulenceSolutions\python-path.txt"
set "DENY_MSG=Security gate cannot run -- Python runtime not found. All tool calls are blocked until the runtime is configured. Open the launcher Settings to fix."
if not exist "%CONFIG%" (
    echo ERROR: Python path configuration not found: !CONFIG! 1>&2
    echo {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "!DENY_MSG!"}}
    exit /b 0
)
set /p PYTHON_PATH=<"%CONFIG%"
if not defined PYTHON_PATH (
    echo ERROR: Python path configuration is empty: !CONFIG! 1>&2
    echo {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "!DENY_MSG!"}}
    exit /b 0
)
if not exist "!PYTHON_PATH!" (
    echo ERROR: Python executable not found: "!PYTHON_PATH!" 1>&2
    echo {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "!DENY_MSG!"}}
    exit /b 0
)
"!PYTHON_PATH!" %*
