@echo off
setlocal EnableDelayedExpansion
set "CONFIG=%LOCALAPPDATA%\TurbulenceSolutions\python-path.txt"
if not exist "%CONFIG%" (
    echo ERROR: Python path configuration not found: !CONFIG! 1>&2
    echo Please reinstall the Agent Environment Launcher or use Settings ^> Relocate Python Runtime. 1>&2
    exit /b 1
)
set /p PYTHON_PATH=<"%CONFIG%"
if not defined PYTHON_PATH (
    echo ERROR: Python path configuration is empty: !CONFIG! 1>&2
    echo Please reinstall the Agent Environment Launcher or use Settings ^> Relocate Python Runtime. 1>&2
    exit /b 1
)
if not exist "!PYTHON_PATH!" (
    echo ERROR: Python executable not found: "!PYTHON_PATH!" 1>&2
    echo Please reinstall the Agent Environment Launcher or use Settings ^> Relocate Python Runtime. 1>&2
    exit /b 1
)
"!PYTHON_PATH!" %*
