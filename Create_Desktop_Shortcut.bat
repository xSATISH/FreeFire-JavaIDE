@echo off
title Create Desktop Shortcut for .DOOM JAVA IDE
cls
echo [!] Creating Desktop Shortcut for .DOOM JAVA IDE...

set "TARGET_BAT=%~dp0Run_DOOM_IDE.bat"

powershell -Command "$desk = [Environment]::GetFolderPath('Desktop'); $ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut((Join-Path $desk '.DOOM JAVA IDE.lnk')); $s.TargetPath = '%TARGET_BAT%'; $s.WorkingDirectory = '%~dp0'; $s.Description = '.DOOM JAVA IDE - Free Fire Edition'; $s.Save(); Write-Host '[SUCCESS] Shortcut placed at: ' (Join-Path $desk '.DOOM JAVA IDE.lnk')"

echo.
echo [!] Ready! You can double click .DOOM JAVA IDE right on your Desktop.
