; Inno Setup 安装脚本
; 需安装 Inno Setup 6: https://jrsoftware.org/isinfo.php

#define MyAppName "今天吃什么？"
#define MyAppPublisher "PKU Food Recommender"
#define MyAppExeName "PKUFoodRecommender.exe"
#define MyAppVersion "2.0.0"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\PKUFoodRecommender
DefaultGroupName=PKU Food Recommender
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=PKUFoodRecommender_Setup_{#MyAppVersion}
SetupIconFile=..\my_logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"; Flags: checkedonce

[Files]
Source: "..\dist\PKUFoodRecommender\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\my_logo.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\my_logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\PKUFoodRecommender"
