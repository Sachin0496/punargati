# Optional: local LLM coach (session summaries, prescription import, Q&A) — fully offline.
# Downloads the official llama.cpp Windows-ARM64 build and Qwen3-4B-Instruct-2507 Q4_0,
# the GGUF that Qualcomm AI Hub lists for Qwen3-4B on Snapdragon (geniex_llamacpp asset).
# Files go to %USERPROFILE%\llm (outside OneDrive: multi-GB files and sync don't mix).
param(
    [string]$ModelUrl = "https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/main/Qwen3-4B-Instruct-2507-Q4_0.gguf",
    [string]$ModelFile = "Qwen3-4B-Instruct-2507-Q4_0.gguf"
)
$ErrorActionPreference = "Stop"
$LlmRoot = Join-Path $env:USERPROFILE "llm"
$Tag = "b9964"   # validated on Snapdragon X Elite (see Team-Highest/Gaja-alert docs/LOCAL_INFERENCE.md)
New-Item -ItemType Directory -Force "$LlmRoot\models", "$LlmRoot\llama.cpp" | Out-Null

function Get-File($Url, $Dest) {
    if (Test-Path $Dest) { Write-Host "[skip] $Dest"; return }
    Write-Host "[down] $Url"
    curl.exe -L --fail --retry 5 --retry-delay 3 -C - -o "$Dest.part" $Url
    if ($LASTEXITCODE -ne 0) { throw "download failed: $Url" }
    Move-Item "$Dest.part" $Dest
}
$zip = "$LlmRoot\llama-$Tag-bin-win-cpu-arm64.zip"
Get-File "https://github.com/ggml-org/llama.cpp/releases/download/$Tag/llama-$Tag-bin-win-cpu-arm64.zip" $zip
if (-not (Test-Path "$LlmRoot\llama.cpp\llama-server.exe")) { Expand-Archive -Force $zip "$LlmRoot\llama.cpp" }
Get-File $ModelUrl "$LlmRoot\models\$ModelFile"
Write-Host "`nDone. Start it with: scripts\serve-llm.ps1  (PunarGati detects it automatically on :8080)"
