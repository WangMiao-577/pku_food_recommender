# 使用 PyInstaller 打包应用（onedir 模式）
param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> 北大食堂智能推荐 - 构建可分发程序" -ForegroundColor Cyan
Write-Host "项目目录: $Root"

if ($Clean) {
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
}

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "正在安装 PyInstaller..." -ForegroundColor Yellow
    python -m pip install pyinstaller
}

pyinstaller --noconfirm main.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller 构建失败" }

$outDir = Join-Path $Root "dist\PKUFoodRecommender"
if (-not (Test-Path (Join-Path $outDir "PKUFoodRecommender.exe"))) {
    throw "未找到输出: $outDir\PKUFoodRecommender.exe"
}

Copy-Item (Join-Path $Root "packaging\create_shortcut.ps1") $outDir -Force
Copy-Item (Join-Path $Root "packaging\README.txt") $outDir -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "构建完成: $outDir" -ForegroundColor Green
Write-Host "运行测试: $outDir\PKUFoodRecommender.exe"
Write-Host "创建快捷方式: powershell -ExecutionPolicy Bypass -File `"$outDir\create_shortcut.ps1`" -InstallDir `"$outDir`""
