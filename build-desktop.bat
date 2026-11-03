@echo off
chcp 65001 >nul
REM ============================================================
REM  益禄加油工具 —— 一键构建 Windows 桌面端
REM
REM  流程：自动定位 HBuilderX → 发行 H5 → 同步进 Electron
REM        → 打包 NSIS 安装包。
REM  前置：已安装 HBuilderX（建议 D:\.appdata\HBuilderX）。
REM  用法：右键本文件 →「以管理员身份运行」。
REM ============================================================
set PROJ=C:\Users\HUAWEI\WorkBuddy\2026-10-31-07-42-15\memory-app
set ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
set ELECTRON_BUILDER_BINARIES_MIRROR=https://npmmirror.com/mirrors/electron-builder-binaries/

REM 自动定位 HBuilderX cli
set "HBX="
if exist "D:\.appdata\HBuilderX\cli.exe" set "HBX=D:\.appdata\HBuilderX\cli.exe"
if not defined HBX if exist "C:\Program Files (x86)\HBuilderX\cli.exe" set "HBX=C:\Program Files (x86)\HBuilderX\cli.exe"
if not defined HBX if exist "C:\Program Files\HBuilderX\cli.exe" set "HBX=C:\Program Files\HBuilderX\cli.exe"
if not defined HBX (
  echo [错误] 未找到 HBuilderX\cli.exe，请确认已安装 HBuilderX。
  pause & exit /b 1
)
echo 使用 HBuilderX: %HBX%

echo ============================================
echo   益禄加油工具 - Windows 桌面端构建
echo ============================================

echo [1/3] 启动 HBuilderX 并发行 H5 产物 ...
start "" "%HBX%" open "%PROJ%"
timeout /t 30 >nul
"%HBX%" publish web --project "%PROJ%"
if errorlevel 1 (
  echo [错误] H5 发行失败。请确认 HBuilderX 已正常启动并完成登录/手机号绑定。
  pause & exit /b 1
)
if not exist "%PROJ%\unpackage\dist\build\web\index.html" (
  echo [错误] 未找到 H5 产物：%PROJ%\unpackage\dist\build\web\index.html
  pause & exit /b 1
)
echo        H5 产物 OK

echo.
echo [1.5] 拷贝书籍内容到 H5 静态目录（供运行时按需读取）...
if not exist "%PROJ%\unpackage\dist\build\web\static\content" mkdir "%PROJ%\unpackage\dist\build\web\static\content"
if exist "%PROJ%\content\manifest.json" (
  robocopy "%PROJ%\content\books" "%PROJ%\unpackage\dist\build\web\static\content\books" /E /NFL /NDL /NJH /NJS
  copy /Y "%PROJ%\content\manifest.json" "%PROJ%\unpackage\dist\build\web\static\content\manifest.json" >nul
) else (
  echo        警告：未找到 content\manifest.json，请先运行 python scripts/import_library.py
)
ver >nul
echo        内容同步完成

echo.
echo [2/3] 同步 H5 到 Electron 资源目录 ...
set "WIN=%PROJ%\electron\dist\win-unpacked"
if not exist "%WIN%" (
  echo        未找到 win-unpacked，先生成 Electron 外壳 ...
  cd /d "%PROJ%\electron"
  if not exist node_modules call npm install --no-audit --no-fund
  call npm run pack -- --dir
  if not exist "%WIN%" ( echo [错误] 未能生成 win-unpacked & pause & exit /b 1 )
)
robocopy "%PROJ%\unpackage\dist\build\web" "%WIN%\resources\h5" /E /NFL /NDL /NJH /NJS
echo        同步完成

echo.
echo [3/3] 打包 Windows 安装包 ...
set "MAKENSIS=%LOCALAPPDATA%\electron-builder\Cache\nsis\nsis-3.0.4.1\makensis.exe"
if exist "%MAKENSIS%" (
  "%MAKENSIS%" "%PROJ%\electron\installer.nsi"
) else (
  echo        makensis 未找到，改用 electron-builder 打包 ...
  cd /d "%PROJ%\electron"
  call npm run pack
)
if errorlevel 1 ( echo [错误] 安装包打包失败 & pause & exit /b 1 )

echo.
echo ============================================
echo   构建完成！
echo   安装包位于：%PROJ%\electron\dist\益禄加油 Setup 1.0.0.exe
echo ============================================
pause
