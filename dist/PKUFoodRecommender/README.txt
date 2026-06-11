北大食堂智能推荐 - 分发说明
================================

【运行】
  双击 PKUFoodRecommender.exe

【创建快捷方式】
  在 PowerShell 中执行（将路径替换为实际安装目录）:
  powershell -ExecutionPolicy Bypass -File create_shortcut.ps1 -InstallDir "本目录完整路径"

【用户数据】
  设置、历史、足迹等保存在:
  %APPDATA%\PKUFoodRecommender\data\

【更新】
  安装新版安装包即可覆盖程序文件，用户数据会保留。

【开发者重新打包】
  1. pip install -r requirements.txt
  2. powershell -ExecutionPolicy Bypass -File packaging\build.ps1
  3. powershell -ExecutionPolicy Bypass -File packaging\build_installer.ps1
