# Serve the local LLM on http://127.0.0.1:8080/v1 (OpenAI-compatible; loopback only).
#   -t 8      decode is memory-bandwidth bound on Snapdragon X: 8 threads beat 12 (measured)
#   Q4_0      llama.cpp repacks Q4_0 into i8mm-optimised ARM layouts at load time
#   --no-mmap guarantees that repack applies and avoids first-token page-fault stutter
param([int]$Port = 8080, [int]$Threads = 8, [string]$Model = "Qwen3-4B-Instruct-2507-Q4_0.gguf")
$LlmRoot = Join-Path $env:USERPROFILE "llm"
$Gguf = Join-Path "$LlmRoot\models" $Model
if (-not (Test-Path $Gguf)) { throw "Missing $Gguf - run scripts\setup-llm.ps1 first" }
& "$LlmRoot\llama.cpp\llama-server.exe" -m $Gguf --alias qwen3-4b-instruct -t $Threads -c 8192 -fa on --no-mmap --jinja --host 127.0.0.1 --port $Port
