# 创建桌面与开始菜单快捷方式
param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir,
    [switch]$Desktop = $true,
    [switch]$StartMenu = $true
)

$ErrorActionPreference = "Stop"
$exe = Join-Path $InstallDir "PKUFoodRecommender.exe"
$icon = Join-Path $InstallDir "my_logo.ico"

if (-not (Test-Path $exe)) {
    throw "未找到可执行文件: $exe"
}

$shell = New-Object -ComObject WScript.Shell

if ($Desktop) {
    $desktop = [Environment]::GetFolderPath("Desktop")
    $lnk = Join-Path $desktop "今天吃什么.lnk"
    $shortcut = $shell.CreateShortcut($lnk)
    $shortcut.TargetPath = $exe
    $shortcut.WorkingDirectory = $InstallDir
    if (Test-Path $icon) { $shortcut.IconLocation = "$icon,0" }
    $shortcut.Description = "北大食堂智能推荐"
    $shortcut.Save()
    Write-Host "已创建桌面快捷方式: $lnk"
}

if ($StartMenu) {
    $menuDir = Join-Path ([Environment]::GetFolderPath("Programs")) "PKU Food Recommender"
    New-Item -ItemType Directory -Force -Path $menuDir | Out-Null
    $lnk = Join-Path $menuDir "今天吃什么.lnk"
    $shortcut = $shell.CreateShortcut($lnk)
    $shortcut.TargetPath = $exe
    $shortcut.WorkingDirectory = $InstallDir
    if (Test-Path $icon) { $shortcut.IconLocation = "$icon,0" }
    $shortcut.Description = "北大食堂智能推荐"
    $shortcut.Save()
    Write-Host "已创建开始菜单快捷方式: $lnk"
}
