Unicode true
!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "益禄加油"
OutFile "C:\Users\HUAWEI\WorkBuddy\2026-10-31-07-42-15\memory-app\electron\dist\益禄加油 Setup 1.0.0.exe"
InstallDir "$LOCALAPPDATA\Programs\益禄加油"
RequestExecutionLevel user

VIProductVersion "1.0.0.0"
VIAddVersionKey  "ProductName" "益禄加油"
VIAddVersionKey  "FileVersion" "1.0.0"
VIAddVersionKey  "FileDescription" "益禄加油 - 间隔重复记忆复习工具"
VIAddVersionKey  "LegalCopyright" "益禄加油"

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"

Section "Main" SecMain
  SetOutPath "$INSTDIR"
  File /r "C:\Users\HUAWEI\WorkBuddy\2026-10-31-07-42-15\memory-app\electron\dist\win-unpacked\*"

  CreateDirectory "$SMPROGRAMS\益禄加油"
  CreateShortcut "$SMPROGRAMS\益禄加油\益禄加油.lnk" "$INSTDIR\益禄加油.exe" "" "$INSTDIR\益禄加油.exe" 0
  CreateShortcut "$DESKTOP\益禄加油.lnk" "$INSTDIR\益禄加油.exe" "" "$INSTDIR\益禄加油.exe" 0
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; 注册到“程序和功能”，便于标准卸载
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\益禄加油" "DisplayName" "益禄加油"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\益禄加油" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\益禄加油" "QuietUninstallString" "$INSTDIR\Uninstall.exe /S"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\益禄加油" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\益禄加油" "DisplayIcon" "$INSTDIR\益禄加油.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\益禄加油" "DisplayVersion" "1.0.0"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\益禄加油" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\益禄加油" "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\益禄加油.lnk"
  RMDir /r "$SMPROGRAMS\益禄加油"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\益禄加油"
SectionEnd
