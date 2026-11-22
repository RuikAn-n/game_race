@echo off
rem Run the latest Rupu build inside the Win11 VM.
rem Mac folder game_race/Builds is mounted as VMware shared folder "RupuBuilds".
rem Copy to local disk first (shared-folder exe can be slow / blocked by SmartScreen).
set "SRC=\\vmware-host\Shared Folders\RupuBuilds\Windows"
set "DST=%LOCALAPPDATA%\RupuTest"
if not exist "%SRC%\Rupu.exe" (
  echo [Rupu] Rupu.exe not found in %SRC%
  echo [Rupu] Run Tools/mac/build_win.sh on the Mac first.
  pause
  exit /b 1
)
robocopy "%SRC%" "%DST%" /MIR /NFL /NDL /NJH /NJS /NP >nul
type "%DST%\build_info.txt" 2>nul
start "" "%DST%\Rupu.exe"
