# PunarGati setup for Snapdragon-powered Windows PCs (Windows on ARM64).
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
# Creates .venv with a *native ARM64* Python, installs onnxruntime + the QNN (NPU)
# plugin, verifies the models and runs the doctor, which proves the NPU works.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Test-Arm64Python($exe) {
    try {
        $arch = & $exe -c "import os,sys;print(os.environ.get('PROCESSOR_ARCHITECTURE',''), sys.version_info[:2] >= (3,11))" 2>$null
        return ($arch -match "^ARM64 True")
    } catch { return $false }
}

# 1. Find a native ARM64 Python (x64 Python runs emulated and cannot load the NPU plugin).
$candidates = @()
foreach ($v in "3.13", "3.12", "3.11", "3.14") {
    $candidates += "$env:LOCALAPPDATA\Programs\Python\Python$($v.Replace('.',''))-arm64\python.exe"
}
$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) { foreach ($v in "3.13-arm64", "3.12-arm64", "3.11-arm64") {
    try { $p = (& py "-V:$v" -c "import sys;print(sys.executable)" 2>$null) } catch { $p = $null }
    if ($p) { $candidates += $p } } }
$cmd = Get-Command python -ErrorAction SilentlyContinue
if ($cmd) { $candidates += $cmd.Source }
$Python = $candidates | Where-Object { $_ -and (Test-Path $_) -and (Test-Arm64Python $_) } | Select-Object -First 1

if (-not $Python) {
    Write-Host "No native ARM64 Python found. Installing Python 3.12 (ARM64) with winget..." -ForegroundColor Yellow
    winget install --id Python.Python.3.12 --architecture arm64 --silent --accept-package-agreements --accept-source-agreements
    $Python = "$env:LOCALAPPDATA\Programs\Python\Python312-arm64\python.exe"
    if (-not (Test-Arm64Python $Python)) { throw "Please install Python 3.12 ARM64 from python.org, then re-run this script." }
}
Write-Host "[ok] native ARM64 Python: $Python" -ForegroundColor Green

# 2. Virtual environment + dependencies (numpy, onnxruntime, onnxruntime-qnn: all ship win_arm64 wheels).
if (-not (Test-Path ".venv\Scripts\python.exe")) { & $Python -m venv .venv }
$VPy = Join-Path $Root ".venv\Scripts\python.exe"
& $VPy -m pip install --upgrade pip --quiet
& $VPy -m pip install -r requirements-snapdragon.txt
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

# 3. Models (vendored in the repo; this verifies/re-downloads from Qualcomm AI Hub if missing).
& $VPy -m punargati.models download

# 4. Prove the NPU path end-to-end.
& $VPy -m punargati.doctor
Write-Host "`nSetup complete. Start PunarGati with:  scripts\run.ps1   (or double-click PunarGati.bat)" -ForegroundColor Green
Write-Host "Optional on-device LLM coach:           scripts\setup-llm.ps1  then  scripts\serve-llm.ps1"
