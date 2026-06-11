# PyInstaller onedir build
param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> PKU Food Recommender - PyInstaller build" -ForegroundColor Cyan
Write-Host "Root: $Root"

if ($Clean) {
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
}

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
    python -m pip install pyinstaller
}

pyinstaller --noconfirm main.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }

$outDir = Join-Path $Root "dist\PKUFoodRecommender"
$exePath = Join-Path $outDir "PKUFoodRecommender.exe"
if (-not (Test-Path $exePath)) {
    throw "Missing output: $exePath"
}

Copy-Item (Join-Path $Root "packaging\create_shortcut.ps1") $outDir -Force
Copy-Item (Join-Path $Root "packaging\README.txt") $outDir -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Build OK: $outDir" -ForegroundColor Green
Write-Host "Run: $exePath"
