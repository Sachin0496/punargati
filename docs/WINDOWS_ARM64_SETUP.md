# Setup on Snapdragon Windows PCs (Windows 11 on ARM64)

Tested target: Snapdragon X / X Plus / X Elite / X2 series laptops (HP OmniBook X / Ultra, Surface Laptop 7, and others).

## 1. Install

```powershell
git clone https://github.com/Sachin0496/punargati.git
cd punargati
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```

The script:

1. Finds a **native ARM64** Python 3.11–3.14, or installs Python 3.12 ARM64 with `winget`.
2. Creates `.venv` and installs `numpy`, `onnxruntime` and `onnxruntime-qnn`.
3. Verifies the Qualcomm AI Hub MoveNet builds in `models/` by SHA-256, re-downloading if missing.
4. Runs `python -m punargati.doctor`, which loads MoveNet on the NPU in strict mode and prints its latency.

Expected doctor output on a Snapdragon PC:

```
[ok] Hexagon NPU (QNN HTP): ~1 ms/inference (load …s) · 100% of ops on accelerator
Ready: pose tracking will run on the Hexagon NPU.
```

The first NPU load compiles the graph for the HTP, which takes a few seconds. The compiled context is cached next to the model, so later launches are fast.

## 2. Run

```powershell
scripts\run.ps1            # or double-click PunarGati.bat
scripts\run.ps1 -Target cpu   # force a unit, e.g. for comparison
```

The app opens at http://127.0.0.1:8765 in your default browser. Allow camera access when asked.

## 3. Optional: local LLM coach

```powershell
scripts\setup-llm.ps1   # llama.cpp b9964 win-cpu-arm64 + Qwen3-4B-Instruct-2507-Q4_0.gguf (~2.4 GB) into %USERPROFILE%\llm
scripts\serve-llm.ps1   # http://127.0.0.1:8080/v1
```

PunarGati probes loopback ports 8080, 8081, 1234, 11434, 5272 and 5273. Any OpenAI-compatible local server works: llama-server, GenieX, Foundry Local, LM Studio or Ollama. To point at a specific one: `$env:PUNARGATI_LLM_URL="http://127.0.0.1:5273/v1"`.

## 4. Optional: voices for Indian languages

Voice cues use Windows' offline speech voices. Add them in **Settings › Time & language › Language & region › Add a language** (Hindi, Tamil, Telugu, Kannada, Marathi, Bengali) and tick *Text-to-speech*. Without a voice for the chosen language, cues still appear as on-screen text.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `OSError: [WinError 193] %1 is not a valid Win32 application` or doctor says "x64 emulation" | The venv was built from an x64 Python | `winget install --id Python.Python.3.12 --architecture arm64`, delete `.venv`, re-run `setup.ps1`. Check with `python -c "import os;print(os.environ['PROCESSOR_ARCHITECTURE'])"`, which must print `ARM64` |
| Doctor: `no QNN device found for target 'npu'` | NPU driver missing or outdated | Run Windows Update, including *optional driver updates*, then install the latest Qualcomm Hexagon NPU driver from your OEM (HP Support Assistant) |
| Doctor fails with the 2.x plugin EP | Plugin EP/driver mismatch | `setup.ps1` automatically retries with `onnxruntime-qnn==1.24.4` (ORT with QNN built in), which PunarGati also supports. Manual: `pip uninstall -y onnxruntime onnxruntime-qnn; pip install onnxruntime-qnn==1.24.4` |
| NPU strict mode fails, app runs as "partial / unknown" | An operator isn't supported by this QAIRT version | The app still runs with QNN plus CPU fallback. Upgrade with `pip install -U onnxruntime-qnn` |
| First launch slow | QNN graph compilation | One time only. Cached as `models/movenet-w8a16/movenet.npu_ctx.onnx` |
| Camera doesn't start | Browser permission, or another app holds the camera | Allow the camera in the browser's site settings and close Teams or Zoom |
| No voice | No Windows voice for that language | See step 4, or switch the coaching language to English |
| `llama-server` doesn't start | Port 8080 busy | `scripts\serve-llm.ps1 -Port 8081` |
| Large files in OneDrive folders stall | OneDrive "files on demand" | Keep the repo and `%USERPROFILE%\llm` outside OneDrive |

## Useful commands

```powershell
.venv\Scripts\python.exe -m punargati.doctor                    # environment + NPU check
.venv\Scripts\python.exe -m punargati.bench --write-docs        # NPU vs GPU vs CPU → docs/BENCHMARKS.md
.venv\Scripts\python.exe -m unittest discover -s tests          # 27 tests (video ones need ffmpeg)
.venv\Scripts\python.exe -m punargati.offline web\demo\squat.webm --exercise squat   # needs ffmpeg on PATH
```
