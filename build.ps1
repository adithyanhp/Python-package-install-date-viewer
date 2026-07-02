# ============================================================
#  PyPackage Manager Pro - Windows build script (build.ps1)
#  Builds a standalone PyPackageManagerPro.exe using PyInstaller
# ============================================================

$ErrorActionPreference = "Stop"

function Write-Step($msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Magenta
}

try {
    Write-Step "Checking Python..."
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python was not found on PATH. Install Python 3.10+ first."
    }
    Write-Host "Found $pythonVersion"

    Write-Step "Installing/upgrading dependencies..."
    python -m pip install --upgrade pip | Out-Null
    python -m pip install -r requirements.txt

    Write-Step "Cleaning previous build artifacts..."
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue dist

    Write-Step "Building executable with PyInstaller..."
    pyinstaller build.spec

    Write-Step "Build complete!"
    Write-Host "Executable: dist\PyPackageManagerPro\PyPackageManagerPro.exe" -ForegroundColor Green
}
catch {
    Write-Host "BUILD FAILED: $_" -ForegroundColor Red
    exit 1
}
