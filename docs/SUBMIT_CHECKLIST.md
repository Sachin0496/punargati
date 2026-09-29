# Submission-day checklist (deadline: 30 Sep 2026, 11:59 PM IST)

Everything below runs on **your Snapdragon laptop**. Start with the downloads, because they take the longest.

1. **Install** (≈5 min):
   ```powershell
   git clone https://github.com/Sachin0496/punargati.git; cd punargati
   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
   ```
   The doctor must print `Hexagon NPU (QNN HTP): ~1 ms/inference … 100% of ops on accelerator`. If it doesn't, save the full doctor output. The script already retries with onnxruntime-qnn 1.x automatically.
2. **Local LLM** (optional, ≈2.4 GB): `scripts\setup-llm.ps1`, then leave `scripts\serve-llm.ps1` running in its own window.
3. **Run**: `scripts\run.ps1`. The top-right badge should read *Hexagon NPU · ~1 ms*. Fill in the **Profile** tab (age matters for test norms).
4. **Seed a little history** so Progress isn't empty: one squat set, one 30-s chair stand test, and one prescription import in the Plan tab.
5. **Benchmark on battery** (unplug the charger): NPU & performance → *Run benchmark*, then
   `.venv\Scripts\python.exe -m punargati.bench --write-docs` to write real numbers into `docs/BENCHMARKS.md`.
6. **Screenshots with the NPU badge** (Win + Shift + S), replacing:
   - `docs/img/coach.png` (Coach tab mid-exercise)
   - `deck/assets/coach_crop.png` (the same view, without the header). In PowerPoint, right-click the picture → *Change Picture* on slides 1 and 5, then export the PDF again
   - optionally add `docs/img/perf.png` (benchmark results) to the README
7. **Record the 3-minute demo** following `docs/DEMO_SCRIPT.md`. (Fallback if you run out of time: `deck/PunarGati_reel.mp4` is a ready 66-s silent product reel, but a real Snapdragon recording scores far better.) Upload it (YouTube unlisted or Drive, anyone with the link) and paste the link into `README.md` and `docs/SUBMISSION.md`.
8. **Commit and push**: `git add -A; git commit -m "Snapdragon benchmarks, screenshots, demo link"; git push`
9. **Submit on Unstop.** Copy the text from `docs/SUBMISSION.md`, then attach `deck/PunarGati.pdf` (or .pptx), the GitHub link and the video link. Only one submission is allowed and it **can't be edited**, so check every field before submitting.
