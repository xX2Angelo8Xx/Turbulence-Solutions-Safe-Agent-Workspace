@echo off
setlocal EnableDelayedExpansion
set "CONFIG=%LOCALAPPDATA%\TurbulenceSolutions\python-path.txt"
set "DENY_MSG=Security gate cannot run -- Python runtime not found. All tool calls are blocked until the runtime is configured. Open the launcher Settings to fix."

rem --- Primary path: read python-path.txt ---
set "PYTHON_PATH="
if exist "%CONFIG%" (
    set /p PYTHON_PATH=<"%CONFIG%"
)
if defined PYTHON_PATH (
    if exist "!PYTHON_PATH!" goto :run_python
)

rem --- Fallback 1: standard per-machine install location ---
set "CANDIDATE1=%ProgramFiles%\TurbulenceSolutions\python-embed\python.exe"
if exist "!CANDIDATE1!" (
    set "PYTHON_PATH=!CANDIDATE1!"
    rem Auto-heal: write the found path back so future invocations are fast.
    echo !PYTHON_PATH!>"%CONFIG%"
    goto :run_python
)

rem --- Fallback 2: per-user install location ---
set "CANDIDATE2=%LOCALAPPDATA%\Programs\TurbulenceSolutions\python-embed\python.exe"
if exist "!CANDIDATE2!" (
    set "PYTHON_PATH=!CANDIDATE2!"
    rem Auto-heal: write the found path back so future invocations are fast.
    echo !PYTHON_PATH!>"%CONFIG%"
    goto :run_python
)

rem --- All paths exhausted: deny ---
echo ERROR: Python executable not found via python-path.txt or fallback locations. 1>&2
echo {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "!DENY_MSG!"}}
exit /b 0

:run_python
"!PYTHON_PATH!" %*
