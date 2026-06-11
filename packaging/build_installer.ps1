# 一键构建：PyInstaller + Inno Setup 安装包
param(
    [switch]$Clean,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

& (Join-Path $PSScriptRoot "build.ps1") @PSBoundParameters

if ($SkipInstaller) {
    Write-Host "已跳过安装包生成（-SkipInstaller）" -ForegroundColor Yellow
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
    Write-Host "未检测到 Inno Setup 6，已跳过安装包编译。" -ForegroundColor Yellow
    Write-Host "可手动安装 Inno Setup 后运行:"
    Write-Host "  ISCC.exe packaging\installer.iss"
    Write-Host ""
    Write-Host "或仅分发文件夹: dist\PKUFoodRecommender"
    Write-Host "并使用 create_shortcut.ps1 创建快捷方式。"
    exit 0
}

& $iscc (Join-Path $PSScriptRoot "installer.iss")
if ($LASTEXITCODE -ne 0) { throw "Inno Setup 编译失败" }

Write-Host ""
Write-Host "安装包已生成: $Root\dist\PKUFoodRecommender_Setup_2.0.0.exe" -ForegroundColor Green
