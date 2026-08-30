@echo off
title .DOOM JAVA IDE - Free Fire Edition
color 0C
cls
echo =================================================================
echo        ____  ____  ____  __  __       __  ___ _   __ ___ 
echo       / __ \/ __ \/ __ \/ / / /      / / /   ^| ^| / //   ^|
echo      / / / / / / / / / / / / /  __  / / / /^| ^| ^|/ // /^| ^|
echo     / /_/ / /_/ / /_/ / /_/ /  / /_/ / / ___ ^| / // ___ ^|
echo    /_____/\____/\____/\____/   \____/_/_/  ^|_^|/_//_/  ^|_^|
echo                                                          
echo              --- FREE FIRE BATTLE ROYALE EDITION ---      
echo =================================================================
echo.
echo [!] Initializing .DOOM JAVA IDE Core Engine...
echo [!] Starting local server and launching Battle Royale Interface...
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH!
    echo Please ensure Python 3 is installed.
    pause
    exit /b 1
)

python "%~dp0app.py"

if %errorlevel% neq 0 (
    echo.
    echo [!] Server exited with an issue.
    pause
)
