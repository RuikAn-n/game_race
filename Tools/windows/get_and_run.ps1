# Download the latest Rupu build from the Mac (Tools/mac/serve_build.sh) and run it.
$ErrorActionPreference = 'Stop'
$hostUrl = if ($env:RUPU_HOST) { $env:RUPU_HOST } else { $null }
if (-not $hostUrl) {
  foreach ($ip in '192.168.214.1','172.16.52.1') {
    try { Invoke-WebRequest "http://${ip}:8624/Rupu_Windows.zip" -Method Head -UseBasicParsing -TimeoutSec 3 | Out-Null; $hostUrl = "http://${ip}:8624"; break } catch {}
  }
}
if (-not $hostUrl) { Write-Host '[Rupu] Mac build server not reachable. Run Tools/mac/serve_build.sh on the Mac.'; pause; exit 1 }
$dst = Join-Path $env:LOCALAPPDATA 'RupuTest'
$zip = Join-Path $env:TEMP 'Rupu_Windows.zip'
Write-Host "[Rupu] Downloading from $hostUrl ..."
Invoke-WebRequest "$hostUrl/Rupu_Windows.zip" -OutFile $zip -UseBasicParsing
Get-Process Rupu -ErrorAction SilentlyContinue | Stop-Process -Force
if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
Expand-Archive $zip -DestinationPath $dst -Force
Get-Content (Join-Path $dst 'build_info.txt') -ErrorAction SilentlyContinue
Start-Process (Join-Path $dst 'Rupu.exe')
