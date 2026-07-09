# BVH Viewer packaging script
# Runs dependency checks, copies MocapApi.dll, and builds the Windows executable.

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BVH Viewer Build Tool" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
Write-Host "[1/7] Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python was not found. Install Python 3.8+ and add it to PATH." -ForegroundColor Red
    exit 1
}
Write-Host "OK: Python environment: $pythonVersion" -ForegroundColor Green
Write-Host ""

# 2. Install dependencies
Write-Host "[2/7] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --upgrade
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Dependency installation reported an issue. Continuing build..." -ForegroundColor Yellow
}
Write-Host "OK: Dependency step completed" -ForegroundColor Green
Write-Host ""

# 3. Check MocapApi.dll
Write-Host "[3/7] Checking MocapApi.dll..." -ForegroundColor Yellow
$localDll = "lib\MocapApi.dll"
if (-not (Test-Path $localDll)) {
    $sdkCandidates = @()
    if ($env:NOITOM_MOCAP_SDK) {
        $sdkCandidates += (Join-Path $env:NOITOM_MOCAP_SDK "lib\windows\x64\MocapApi.dll")
    }
    $sdkCandidates += @(
        "..\NoitomMocapSDK\lib\windows\x64\MocapApi.dll",
        "..\..\NoitomMocapSDK\lib\windows\x64\MocapApi.dll",
        "C:\Noitom\NoitomMocapSDK\lib\windows\x64\MocapApi.dll"
    )

    $sourceDll = $null
    foreach ($candidate in $sdkCandidates) {
        if (Test-Path $candidate) {
            $sourceDll = $candidate
            break
        }
    }

    if ($sourceDll) {
        if (-not (Test-Path "lib")) {
            New-Item -ItemType Directory -Path "lib" | Out-Null
        }
        Copy-Item $sourceDll $localDll -Force
        Write-Host "OK: Copied MocapApi.dll from: $sourceDll" -ForegroundColor Green
    } else {
        Write-Host "ERROR: MocapApi.dll was not found." -ForegroundColor Red
        Write-Host "Set the SDK path first, then reopen PowerShell:" -ForegroundColor Yellow
        Write-Host '  setx NOITOM_MOCAP_SDK "C:\path\to\NoitomMocapSDK"' -ForegroundColor White
        exit 1
    }
} else {
    Write-Host "OK: MocapApi.dll exists: $localDll" -ForegroundColor Green
}
Write-Host ""

# 4. Clean previous build
Write-Host "[4/7] Cleaning old build files..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "OK: Removed build directory" -ForegroundColor Green
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "OK: Removed dist directory" -ForegroundColor Green
}
Write-Host ""

# 5. Check required files
Write-Host "[5/7] Checking required files..." -ForegroundColor Yellow
$requiredFiles = @(
    "bvh_visualizer_improved.py",
    "build_bvh_viewer.spec",
    "app_icon.ico",
    "ui\__init__.py",
    "ui\components.py",
    "ui\renderer.py",
    "ui\colors.py",
    "ui\metrics.py"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
        Write-Host "MISSING: $file" -ForegroundColor Red
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "ERROR: Required files are missing. Build cannot continue." -ForegroundColor Red
    exit 1
}
Write-Host "OK: All required files exist" -ForegroundColor Green
Write-Host ""

# 6. Build executable
Write-Host "[6/7] Building executable..." -ForegroundColor Yellow
Write-Host "This may take 3-5 minutes." -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date
pyinstaller build_bvh_viewer.spec --clean --noconfirm
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyInstaller build failed." -ForegroundColor Red
    Write-Host "Try running manually: pyinstaller build_bvh_viewer.spec" -ForegroundColor Yellow
    exit 1
}
Write-Host ""
Write-Host "OK: Build finished in $([math]::Round($duration, 1)) seconds" -ForegroundColor Green
Write-Host ""

# 7. Verify output
Write-Host "[7/7] Verifying output..." -ForegroundColor Yellow
if (Test-Path "dist\BVH_Viewer.exe") {
    $fileSize = (Get-Item "dist\BVH_Viewer.exe").Length / 1MB
    Write-Host "OK: Executable created: dist\BVH_Viewer.exe" -ForegroundColor Green
    Write-Host "Size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Build succeeded" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Executable:" -ForegroundColor Cyan
    Write-Host "  $(Resolve-Path 'dist\BVH_Viewer.exe')" -ForegroundColor White
    Write-Host ""
    Write-Host "User config will be saved to:" -ForegroundColor Cyan
    Write-Host "  $env:APPDATA\BVH_Viewer\bvh_viewer_config.json" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Double-click dist\BVH_Viewer.exe" -ForegroundColor White
    Write-Host "  2. Keep the full dist folder when sharing the build" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "ERROR: Executable was not found." -ForegroundColor Red
    Write-Host "Check the PyInstaller output above." -ForegroundColor Yellow
    exit 1
}
