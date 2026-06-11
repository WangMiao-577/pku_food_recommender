# Full build: PyInstaller + Inno Setup installer
param(
    [switch]$Clean,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

& (Join-Path $PSScriptRoot "build.ps1") @PSBoundParameters

if ($SkipInstaller) {
    Write-Host "Skipped installer (-SkipInstaller)" -ForegroundColor Yellow
    exit 0
}

$isccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
    "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe"
)
$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $iscc) {
    Write-Host ""
    Write-Host "Inno Setup 6 not found. Install it, then run:" -ForegroundColor Yellow
    Write-Host "  ISCC.exe packaging\installer.iss"
    Write-Host ""
    Write-Host "Or distribute folder: dist\PKUFoodRecommender"
    exit 0
}

& $iscc (Join-Path $PSScriptRoot "installer.iss")
if ($LASTEXITCODE -ne 0) { throw "Inno Setup compile failed" }

$setup = Join-Path $Root "dist\PKUFoodRecommender_Setup_2.0.0.exe"
Write-Host ""
Write-Host "Installer ready: $setup" -ForegroundColor Green
