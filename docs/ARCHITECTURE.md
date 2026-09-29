# Architecture

## Design goals

1. **Every AI computation on the device**, with the continuous work on the Hexagon NPU.
2. **Installs on Windows on ARM64 without native-wheel pain.** Only `numpy`, `onnxruntime` and `onnxruntime-qnn` are needed, and all three publish `win_arm64` wheels. The browser handles camera, rendering and speech, which removes OpenCV, PortAudio and PyTorch from the dependency list.
3. **The demo can't break.** Every AI feature has a deterministic fallback: NPU → GPU → CPU for pose, and a rule engine or template when no LLM is running.

## Per-frame pipeline (≈30 fps)

```
browser                                         python engine (127.0.0.1:8765)
───────                                         ──────────────────────────────
video frame ─► drawImage(crop → 192×192) ─► POST /api/frame (147 KB RGBA + crop rect)
                                                 │ RGBA → RGB → [0,1] → uint16 quantize (AI Hub scale/zero-point)
                                                 │ MoveNet on Hexagon NPU (QNN HTP)       ~1 ms
                                                 │ [precision] RTMPose-WholeBody on NPU on the
                                                 │   MoveNet person box (192×256)        ~1.8 ms
                                                 │ dequantize → map crop → frame pixels
                                                 │ next crop (MoveNet crop tracker)
                                                 │ One-Euro filter (body-scale units)
                                                 │ kinematics: 14 angles, view, body scale
                                                 │ RepCounter / Assessment → events
                                                 ▼ JSON: keypoints, angles, activity, events, perf
skeleton + angle arcs ◄── rep ring, gauge, cue banner, speechSynthesis (7 languages)
```

The browser keeps one request in flight. At about 5 ms per round trip on the NPU path, the camera sets the frame rate, not the engine.

## Compute placement

| Workload | Unit | How |
|---|---|---|
| Wholebody pose (precision mode) | **Hexagon NPU** | RTMPose-Body2d w8a16, same ladder; 288 px crop from the browser |
| Pose (continuous) | **Hexagon NPU** | `onnxruntime-qnn` 2.x plugin EP, `backend_path=QnnHtp.dll`, `htp_performance_mode=burst`, strict no-CPU-fallback session, QNN context cache |
| Pose (comparison) | Adreno GPU | same plugin EP, `QnnGpu.dll`, float model |
| Pose (fallback) | Oryon CPU | ORT CPU EP, float model, 4 intra-op threads |
| LLM (on demand) | Oryon CPU (llama.cpp Q4_0, i8mm repack) or NPU (GenieX/QAIRT) | any OpenAI-compatible server on loopback |
| UI, voice | browser | Canvas 2D, Web Speech synthesis with offline Windows voices |

Why the LLM defaults to the CPU: on Snapdragon X Elite, llama.cpp's ARM i8mm kernels decode Q4_0 faster than its NPU or GPU backends (Gemma 4 E4B: CPU 19.1, GPU 14.2, NPU 12.3 tok/s, measured in [Gaja-alert's engineering log](https://github.com/Team-Highest/Gaja-alert/blob/main/docs/LOCAL_INFERENCE.md)). The LLM also runs only after a session, while the NPU handles the real-time vision, so the two never compete.

## HTTP API (loopback only)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/system` | machine info, compute units, live pose session, models, LLM status |
| GET | `/api/library` | exercises and tests |
| POST | `/api/start` | `{kind: exercise\|assessment, id, side, target_reps}` |
| POST | `/api/frame?x&y&size&w&h&t` | body = 192×192×4 RGBA crop, returns keypoints, angles, activity, events, perf |
| POST | `/api/stop` | saves the session (if reps or a result exist) and returns the record |
| POST | `/api/compute` | `{target: npu\|gpu\|cpu}` hot-swaps the pose model |
| GET/POST | `/api/profile`, `/api/plan` | local JSON store |
| POST | `/api/plan/parse` | prescription text → plan items (rules + LLM) |
| POST | `/api/summary` | LLM narrative + structured facts for localized summaries |
| POST | `/api/chat` | grounded Q&A with red-flag safety net |
| GET | `/api/progress`, `/api/sessions` | recovery curves |
| POST/GET | `/api/bench` | NPU vs GPU vs CPU benchmark / last result |
| GET | `/report?ai=1` | printable physiotherapist report |

The server rejects any `Host` header other than `127.0.0.1`, `localhost` or `[::1]` on its port, which guards against DNS rebinding. Static file serving is confined to `web/`.

## Data model (`./data`, JSON)

- `profile.json`: name, age, sex, condition, affected side, physio, language.
- `plan.json`: `{items: [{kind, id, sets, reps, side, frequency, note}], source, updated}`.
- `sessions/<timestamp>.json`: kind, item, timing, compute unit and p50 latency, profile snapshot, plus either `summary` (reps, per-side best/avg ROM, quality, tempo, faults, per-rep log) or `result` (score, unit, flag, reference).
- `bench/<timestamp>.json`: benchmark results.

Frames are never written anywhere.

## Robustness details

- **QNN session ladder**: cached context → strict + cache build → strict → permissive. The permissive rung is accepted only if an ORT profiling run shows the QNN EP executing at least one node, because a failed backend otherwise falls back to the CPU silently. The UI shows which rung succeeded (`full_offload`). Stale caches, for example after a QAIRT upgrade, are deleted and rebuilt.
- **Timebase**: the client's clock (`video.currentTime` or `performance.now()`) drives filters and rep timing, so recorded videos replay correctly at any speed. A backwards jump (looping video) resets the filter.
- **Cue throttling**: each cue type and side speaks at most once every 4 s, and rep counts interrupt lower-priority speech.
- **No-LLM mode**: summaries are composed from measured facts. Indic-language summaries always use vetted templates because small local models produce unreliable Indic prose. Setting `PUNARGATI_LLM_INDIC=1` allows a capable model to write them.
