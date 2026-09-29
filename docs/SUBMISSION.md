# Submission text (copy-paste for the Unstop form)

Adjust wording to the form's fields. Every claim here is backed by code in this repo or a cited source.

**Project title**
PunarGati: on-device AI physiotherapy coach for Snapdragon PCs

**One-line summary**
A private, offline home-rehab coach. It tracks your body on the Snapdragon Hexagon NPU, counts reps, measures joint angles, corrects your form by voice in 7 Indian languages, runs clinical fall-risk and range-of-motion tests, and writes a report for your physiotherapist with a local LLM.

**Problem**
Recovery after a knee replacement, a frozen shoulder, a fracture or a fall happens mostly at home, unsupervised. Patients don't know whether they're doing the exercises correctly or whether they're improving. The physiotherapist sees them weekly at best, and in tier-2/3 India often not at all. Cloud AI isn't an answer: it means streaming video from inside people's homes, needs connectivity, and costs money per minute.

**Solution**
PunarGati turns a Snapdragon-powered HP laptop into a physiotherapist's eyes:
- Live coaching for 9 prescribed exercises: reps per side, range of motion, tempo, a quality score, and spoken form corrections ("keep your chest up", "push your knees out", "don't shrug"). It's fatigue-aware: when range drops across a set, it suggests a rest.
- Standard screening tests, timed and scored automatically: the 30-second chair stand (CDC STEADI fall-risk norms), single-leg stance, and shoulder/knee range of motion against AAOS references.
- Recovery curves, a printable physio report, prescription import (physio's note → one-tap plan), and a Q&A coach grounded in the patient's own data, with red-flag safety escalation.
- 7 coaching languages with offline Windows voices, and a full Hindi interface for the patient-facing screens. It works with no internet, and no video is ever stored or transmitted.

**Use of Snapdragon / Qualcomm AI Hub**
- **MoveNet from Qualcomm AI Hub** (v0.63.0, w8a16 quantized) runs on the **Hexagon NPU** through ONNX Runtime's **QNN execution provider** (`onnxruntime-qnn` 2.x plugin EP, HTP backend). The session is created in strict mode (`session.disable_cpu_ep_fallback`), so when it loads, 100% of operators are proven to run on the NPU. Any fallback is verified with ORT profiling and shown honestly in the UI. AI Hub profiles this at about 1 ms per frame on Snapdragon X Elite. The compiled QNN context is cached for instant relaunch.
- **Precision mode** cascades a second AI Hub model, **RTMPose-Body2d (w8a16, 133 keypoints)**, on the NPU after MoveNet (about 1.8 ms on X Elite per AI Hub). It gives more accurate joints and feet tracking for ankle exercises.
- The same model runs on the **Adreno GPU** (QNN GPU backend) and the CPU for a built-in benchmark that compares latency, CPU load and battery draw.
- The optional local LLM is **Qwen3-4B-Instruct-2507 Q4_0**, the GGUF that Qualcomm AI Hub lists for Qwen3-4B, served by llama.cpp's native ARM64 build (i8mm-optimised). Any OpenAI-compatible local server works, including GenieX or Foundry Local on the NPU.

**Technical implementation highlights**
MoveNet crop tracking; One-Euro keypoint filtering in body-scale units; goniometry in isotropic pixel space; per-side hysteresis rep state machines with duration and timeout guards; view-aware form rules with persistence; median-filtered ROM tests; quantized uint16 I/O using AI Hub metadata; NPU → GPU → CPU fallback ladder with the reason shown in the UI; a loopback-only server with a DNS-rebinding guard; SHA-256-pinned model downloads; 31 automated tests, including HTTP integration with the real model. Validated on real footage: 3/3 stands on the CDC's own 30-second chair stand video (front view, using a view-independent self-calibrating sit/stand signal) and 2/2 squats on a demo clip.

**Deployment & accessibility**
Continuous integration on a native Windows-on-ARM64 runner runs the exact install script, the NPU plugin registration and fallbacks, the local-LLM scripts and all tests on every push.
One PowerShell script: it finds or installs native ARM64 Python, installs 3 packages (numpy, onnxruntime, onnxruntime-qnn), verifies the AI Hub models by SHA-256 (MoveNet ships in the repo), and self-tests the NPU. It launches by double-clicking `PunarGati.bat`. It runs fully offline, has no account or subscription, supports 7 Indian languages with offline voices, and has a privacy view that shows only the skeleton. On non-Snapdragon machines it falls back to CPU automatically, and a bundled demo clip lets anyone try it without a webcam.

**Impact**
- Patients get supervised-quality home exercise, objective progress numbers and early fall-risk flags.
- Physiotherapists get measured adherence and range-of-motion trends between visits.
- It reaches tier-2/3 towns without connectivity or cloud costs.

**Links**
- Code: https://github.com/Sachin0496/punargati
- Demo video: <add YouTube/Drive link after recording, see docs/DEMO_SCRIPT.md>
- Deck: `deck/PunarGati.pdf` / `deck/PunarGati.pptx` (in the repo)
