@echo off
REM ============================================================
REM  PyPackage Manager Pro - Windows build script (build.bat)
REM  Builds a standalone PyPackageManagerPro.exe using PyInstaller
REM ============================================================

setlocal

echo.
echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on PATH. Install Python 3.10+ first.
    exit /b 1
)

echo [2/4] Installing/upgrading dependencies...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    exit /b 1
)

echo [3/4] Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [4/4] Building executable with PyInstaller...
pyinstaller build.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    exit /b 1
)

echo.
echo ============================================================
echo  Build complete! Your executable is at:
echo  dist\PyPackageManagerPro\PyPackageManagerPro.exe
echo ============================================================

endlocal
