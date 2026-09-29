@echo off
rem Double-click launcher for Windows on Snapdragon.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run.ps1" %*
pause
