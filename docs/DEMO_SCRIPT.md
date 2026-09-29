# Demo video script (≈3 minutes)

Record on the Snapdragon laptop with Windows' Snipping Tool (screen record) or Xbox Game Bar (Win + Alt + R). Put the laptop 2–3 m away on a table or chair so your whole body is in frame. Wear clothes that contrast with the wall.

**Before recording**
1. `scripts\run.ps1` and wait for the NPU badge (top right) to show *Hexagon NPU · ~1 ms*.
2. Profile tab: name, age (use a parent's age, e.g. 64, to make the fall-risk norms meaningful), condition "Right knee replacement, week 4", physio name, language Hindi.
3. Optional: `scripts\serve-llm.ps1` in another window so the AI summary and Q&A are live.
4. Do one short squat set and one chair-stand test off camera so the Progress tab already has two points.

## Shot list

| Time | Screen | What to say |
|---|---|---|
| 0:00–0:15 | Title card or the start screen | "After a knee replacement, recovery happens at home: hundreds of reps nobody counts or checks. PunarGati is a physiotherapist's eyes on a Snapdragon PC, and it runs entirely on the NPU." |
| 0:15–0:45 | Coach → **Mini squat** live | Do 5 squats. Point at the skeleton, the knee-angle arcs and the ring counting. Do one shallow rep so it says "go a little further", and lean forward on one so it says "keep your chest up". "Every frame is processed on the Hexagon NPU in about a millisecond. The telemetry strip shows it." |
| 0:45–0:55 | Coach → **Heel raise** (precision mode switches on automatically) | "Precision mode adds a second AI Hub model, RTMPose-WholeBody with 133 keypoints, on the same NPU. It tracks the feet, and the telemetry shows both models: about 1 ms plus 2 ms." |
| 0:55–1:05 | Toggle **Privacy view** | "In a bedroom you may not want a camera feed on screen. Privacy view shows only the skeleton, and nothing is ever recorded or uploaded." |
| 1:05–1:20 | **Finish & save** → summary dialog (Hindi) | "The summary is in the patient's language, and the local LLM writes the coach note. No internet." Click *Read aloud*. |
| 1:20–1:50 | Tests → **30-second chair stand** | Sit, 3-2-1, stand and sit repeatedly. "This is the CDC's fall-risk test. It's scored against age and sex norms automatically." Show the result card. |
| 1:50–2:10 | Plan → paste a prescription → **Read prescription** → Save → Coach shows *Today's plan* | "The physio's note becomes a one-tap plan." |
| 2:10–2:30 | Progress → charts → **Open report for my physio** | "Recovery curves, and a printable report for the next visit." |
| 2:30–2:50 | **NPU & performance** → Run benchmark | "Same model on NPU, GPU and CPU. The NPU keeps the CPU almost idle, and on battery you can see the power difference. Strict mode proves 100% of the graph is on the NPU." |
| 2:50–3:00 | Back to Coach | "PunarGati: private, offline, multilingual home rehab on Snapdragon." |

## Tips
- Keep the browser window full-screen at 100% zoom so the telemetry strip is visible.
- Speak over the video afterwards if the voice cues and your narration overlap.
- If the room is dim, turn on a light facing you. MoveNet is robust, but light helps the tracker lock on quickly.
