# Start PunarGati (pose on the Hexagon NPU; falls back to GPU/CPU automatically).
#   powershell -ExecutionPolicy Bypass -File scripts\run.ps1 [-Target npu|gpu|cpu]
param([ValidateSet("npu", "gpu", "cpu")] [string]$Target = "npu", [int]$Port = 8765)
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$VPy = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VPy)) { & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "setup.ps1"); }
& $VPy -m punargati --target $Target --port $Port
