# Benchmarks

PunarGati's always-on workload is one MoveNet inference per camera frame, 30 times a second, for a whole exercise session. What matters is how little of the machine that consumes, and whether it keeps up. Raw speed is secondary.

## Published: Qualcomm AI Hub device profiles (MoveNet v0.63.0, ONNX runtime)

These numbers come from Qualcomm AI Hub's own profiling jobs on reference hardware (`perf.yaml` in [qualcomm/ai-hub-models](https://github.com/qualcomm/ai-hub-models/tree/main/src/qai_hub_models/models/movenet)).

| Device | Precision | Inference | Layers on NPU |
|---|---|---:|---:|
| Snapdragon X Elite CRD | float | 1.04 ms | 214 / 214 |
| Snapdragon X Elite CRD | w8a16 | 1.05 ms | 249 / 249 |
| Snapdragon X2 Elite CRD | float | 0.47 ms | 214 / 214 |
| Snapdragon X2 Elite CRD | w8a16 | 0.44 ms | 249 / 249 |

At 30 fps the NPU is busy for about **3% of each 33 ms frame**, so it has room to add the wholebody and Whisper models on the roadmap.

## Reference: a non-Snapdragon machine (CPU fallback)

Apple M4, macOS, ORT CPU EP, MoveNet float: **2.4 ms p50**, 10.6% app CPU load at 30 fps. This shows the fallback path is comfortably real-time for reviewers without Snapdragon hardware.

## Measured on this device

Run this on the Snapdragon laptop. It benchmarks every available unit (NPU → QNN HTP, GPU → QNN GPU, CPU) and rewrites the block below:

```powershell
.venv\Scripts\python.exe -m punargati.bench --write-docs
```

Unplug the charger first to also get **battery draw at 30 fps**, which comes from the Windows battery driver (`root\wmi BatteryStatus.DischargeRate`). The same benchmark runs from the app's **NPU & performance** tab.

<!-- bench:begin -->
_Not yet run on the Snapdragon device. Run the command above._
<!-- bench:end -->

## How it's measured

- **Latency**: 20 warm-up runs, then 300 timed runs, reported as p50, p90 and p99.
- **CPU load @30 fps**: process CPU time ÷ wall time ÷ logical cores during a paced 30 fps loop, as a share of the whole machine like Task Manager shows it.
- **Battery draw**: mean of `DischargeRate` samples taken every 2 s during the paced loop, on battery only.
- **Full offload**: `✓` means the session was created with `session.disable_cpu_ep_fallback=1`, which proves every operator runs on the NPU.
