@echo off
rem AGENT34 kit launcher: double-click to start Claude Code with the kit attached.
setlocal
set "KIT=%~dp0AGENT34-KIT.md"
if not exist "%KIT%" (
  echo AGENT34-KIT.md not found next to this file: %KIT%
  pause
  exit /b 1
)
where claude >nul 2>nul
if errorlevel 1 (
  echo Claude Code ^(claude command^) was not found. Install Claude Code first.
  pause
  exit /b 1
)
echo Starting Claude Code with the AGENT34 kit...
echo Allow only writes under %USERPROFILE%\.claude and the kit scripts. Reply in Japanese.
claude "Follow the procedure in this kit file to build it, and report in Japanese. Kit path: %KIT%"
pause
