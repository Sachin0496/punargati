// Builds deck/PunarGati.pptx with PptxGenJS (native, editable text/shapes/charts).
//   NODE_PATH=$(npm root -g) node deck/build_deck.js
const path = require("path");
const pptxgen = require("pptxgenjs");

const A = p => path.join(__dirname, "assets", p);
const IMG = p => path.join(__dirname, "..", "docs", "img", p);

const C = { bg: "F8FAFC", ink: "0F172A", muted: "475569", line: "E2E8F0", accent: "0F766E", accentSoft: "CCFBF1", gold: "B7791F", card: "FFFFFF", dark: "0B1220" };
const F = { head: "Aptos", body: "Aptos" };
const W = 13.333, H = 7.5, M = 0.6;

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Sachin";
pptx.title = "PunarGati: on-device AI physiotherapy coach for Snapdragon PCs";

let n = 0;
function base(kicker, title) {
  const s = pptx.addSlide();
  s.background = { color: C.bg };
  n += 1;
  if (kicker) s.addText(kicker.toUpperCase(), { x: M, y: 0.42, w: 9, h: 0.3, fontFace: F.body, fontSize: 12, bold: true, color: C.accent, charSpacing: 2 });
  if (title) s.addText(title, { x: M, y: 0.72, w: W - 2 * M, h: 1.0, fontFace: F.head, fontSize: 30, bold: true, color: C.ink, valign: "top", fit: "shrink" });
  s.addShape(pptx.shapes.LINE, { x: M, y: H - 0.45, w: W - 2 * M, h: 0, line: { color: C.line, width: 0.75 } });
  s.addText("PunarGati · Snapdragon AI Lab Build & Present 2026", { x: M, y: H - 0.42, w: 8, h: 0.3, fontFace: F.body, fontSize: 10, color: C.muted });
  s.addText(String(n), { x: W - M - 1, y: H - 0.42, w: 1, h: 0.3, fontFace: F.body, fontSize: 10, color: C.muted, align: "right" });
  return s;
}
function card(s, x, y, w, h, opts = {}) {
  s.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: opts.fill || C.card },
    line: { color: opts.line || C.line, width: 1 }, shadow: opts.shadow === false ? undefined : { type: "outer", blur: 6, offset: 1.5, angle: 90, color: "94A3B8", opacity: 0.18 } });
}
function note(s, text) {
  s.addText(text, { x: M, y: H - 0.85, w: W - 2 * M, h: 0.35, fontFace: F.body, fontSize: 10.5, color: C.muted, italic: true });
}

// 1 ─ Title
{
  const s = pptx.addSlide(); n += 1;
  s.background = { color: C.bg };
  s.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: 0.18, h: H, fill: { color: C.accent }, line: { color: C.accent } });
  s.addText("SNAPDRAGON AI LAB · BUILD & PRESENT CHALLENGE 2026", { x: M + 0.1, y: 0.7, w: 7, h: 0.3, fontFace: F.body, fontSize: 12, bold: true, color: C.accent, charSpacing: 2 });
  s.addText("PunarGati", { x: M + 0.1, y: 1.2, w: 6, h: 1.1, fontFace: F.head, fontSize: 60, bold: true, color: C.ink });
  s.addText("पुनर्गति · movement, restored", { x: M + 0.1, y: 2.3, w: 6, h: 0.5, fontSize: 20, color: C.muted });
  s.addText("A physiotherapist's eyes at home, running on the Snapdragon NPU.", { x: M + 0.1, y: 3.0, w: 5.6, h: 1.0, fontFace: F.head, fontSize: 24, bold: true, color: C.ink });
  s.addText("On-device pose tracking, clinical screening tests and coaching in 7 Indian languages. Offline, private, and with no subscription.",
    { x: M + 0.1, y: 4.05, w: 5.6, h: 1.0, fontFace: F.body, fontSize: 16, color: C.muted });
  s.addText([{ text: "Sachin", options: { bold: true, color: C.ink } }, { text: "  ·  github.com/Sachin0496/punargati", options: { color: C.accent } }],
    { x: M + 0.1, y: 6.3, w: 6.5, h: 0.4, fontFace: F.body, fontSize: 14 });
  card(s, 6.85, 1.15, 5.95, 4.15, { fill: C.dark, line: "1E293B" });
  s.addImage({ path: A("coach_crop.png"), x: 6.95, y: 1.25, w: 5.75, h: 5.75 * 582 / 1420 });
  s.addText("Live squat coaching: skeleton, knee angles, rep counter and form cues.", { x: 6.95, y: 3.75, w: 5.75, h: 0.4, fontFace: F.body, fontSize: 11, color: "CBD5E1" });
  const chips = ["Qualcomm AI Hub MoveNet", "Hexagon NPU · QNN EP", "Local LLM", "7 languages", "Offline"];
  let cx = 6.95, cy = 4.3;
  chips.forEach(t => {
    const w = 0.3 + t.length * 0.075;
    if (cx + w > 12.7) { cx = 6.95; cy += 0.44; }
    s.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: cx, y: cy, w, h: 0.36, rectRadius: 0.18, fill: { color: "134E4A" }, line: { color: "134E4A" } });
    s.addText(t, { x: cx, y: cy, w, h: 0.36, fontFace: F.body, fontSize: 10.5, color: "CCFBF1", align: "center", valign: "middle", margin: 0 });
    cx += w + 0.08;
  });
}

// 2 ─ Problem
{
  const s = base("The problem", "Recovery happens at home: unsupervised, uncounted, unmeasured");
  const stats = [
    ["28.7%", "pooled prevalence of knee osteoarthritis in Indian studies", "Pal et al., Indian J Orthop 2016"],
    ["101 M", "Indians with diabetes. About 13% of them develop frozen shoulder", "ICMR-INDIAB 2023 · Zreik et al. 2016"],
    ["1 in 3", "adults over 65 fall every year, and fall-risk screening needs a trained assessor", "WHO Falls Prevention Report 2007"],
  ];
  stats.forEach(([big, txt, src], i) => {
    const x = M + i * 4.1;
    card(s, x, 1.9, 3.85, 2.6);
    s.addText(big, { x: x + 0.3, y: 2.05, w: 3.3, h: 1.0, fontFace: F.head, fontSize: 44, bold: true, color: C.accent });
    s.addText(txt, { x: x + 0.3, y: 3.05, w: 3.3, h: 0.95, fontFace: F.body, fontSize: 16, color: C.ink, valign: "top" });
    s.addText(src, { x: x + 0.3, y: 4.05, w: 3.3, h: 0.3, fontFace: F.body, fontSize: 10, color: C.muted, italic: true });
  });
  const flow = ["Patient gets an exercise sheet and a weekly visit", "Nobody counts reps, checks form or measures range at home", "The physio finds out a week later, or never"];
  flow.forEach((t, i) => {
    const x = M + i * 4.1;
    s.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x, y: 4.95, w: 3.85, h: 1.05, rectRadius: 0.08, fill: { color: i === 2 ? "FEF3C7" : "F1F5F9" }, line: { color: i === 2 ? "FCD34D" : C.line } });
    s.addText(t, { x: x + 0.2, y: 4.95, w: 3.45, h: 1.05, fontFace: F.body, fontSize: 16, color: C.ink, valign: "middle", bold: i === 2 });
    if (i < 2) s.addShape(pptx.shapes.RIGHT_TRIANGLE, { x: x + 3.9, y: 5.35, w: 0.16, h: 0.26, rotate: 90, fill: { color: C.muted }, line: { color: C.muted } });
  });
}

// 3 ─ Why on-device
{
  const s = base("Why on-device", "A camera in someone's bedroom must never stream to a server");
  const rows = [
    ["Privacy", "Home video of patients goes to a server: a DPDP-Act risk", "Frames live in RAM for ~1 ms on the NPU. Only numbers are saved; there's a skeleton-only privacy view"],
    ["Connectivity", "30 fps upload fails in tier-2/3 towns", "Fully offline. Models ship inside the repo"],
    ["Cost", "Per-minute inference makes free home rehab impossible", "One-time laptop, unlimited sessions"],
    ["Latency", "A network round trip breaks rep timing and live cues", "~1 ms pose inference and instant spoken feedback"],
  ];
  const x0 = M, colW = [2.0, 4.6, 5.53], y0 = 1.95;
  const hdr = ["", "Cloud AI coach", "PunarGati on a Snapdragon PC"];
  hdr.forEach((t, i) => s.addText(t, { x: x0 + colW.slice(0, i).reduce((a, b) => a + b, 0), y: y0, w: colW[i], h: 0.45, fontFace: F.body, fontSize: 15, bold: true, color: i === 2 ? C.accent : C.muted }));
  rows.forEach((r, j) => {
    const y = y0 + 0.55 + j * 1.05;
    s.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: x0 + colW[0] + colW[1] - 0.05, y: y - 0.02, w: colW[2] + 0.05, h: 0.95, rectRadius: 0.06, fill: { color: "F0FDFA" }, line: { color: "99F6E4" } });
    s.addText(r[0], { x: x0, y, w: colW[0], h: 0.9, fontFace: F.head, fontSize: 18, bold: true, color: C.ink, valign: "middle" });
    s.addText(r[1], { x: x0 + colW[0], y, w: colW[1] - 0.2, h: 0.9, fontFace: F.body, fontSize: 15, color: C.muted, valign: "middle" });
    s.addText(r[2], { x: x0 + colW[0] + colW[1] + 0.1, y, w: colW[2] - 0.2, h: 0.9, fontFace: F.body, fontSize: 15, color: C.ink, valign: "middle" });
  });
}

// 4 ─ Solution
{
  const s = base("The solution", "PunarGati turns a Snapdragon laptop into a physiotherapist's eyes");
  const P = [
    ["Coach", "8 prescribed exercises. Reps per side, range of motion, tempo and a quality score for every rep. Spoken form corrections."],
    ["Test", "30-s chair stand (CDC fall-risk norms), single-leg balance, and shoulder / knee range of motion against AAOS reference values."],
    ["Track", "Recovery curves per joint, day streaks, and a printable report the patient hands to the physio."],
    ["Plan & ask", "Paste the physio's note to get a one-tap plan. The local LLM answers questions from your own data and escalates red flags."],
  ];
  P.forEach(([h, t], i) => {
    const x = M + i * 3.07;
    card(s, x, 1.95, 2.87, 3.7);
    s.addShape(pptx.shapes.OVAL, { x: x + 0.3, y: 2.2, w: 0.62, h: 0.62, fill: { color: C.accentSoft }, line: { color: C.accentSoft } });
    s.addText(String(i + 1), { x: x + 0.3, y: 2.2, w: 0.62, h: 0.62, fontFace: F.head, fontSize: 20, bold: true, color: C.accent, align: "center", valign: "middle" });
    s.addText(h, { x: x + 0.3, y: 2.95, w: 2.4, h: 0.5, fontFace: F.head, fontSize: 22, bold: true, color: C.ink });
    s.addText(t, { x: x + 0.3, y: 3.45, w: 2.35, h: 2.1, fontFace: F.body, fontSize: 14.5, color: C.muted, valign: "top" });
  });
  s.addText("Coaching languages: English, Hindi, Tamil, Telugu, Kannada, Marathi and Bengali, with offline Windows voices",
    { x: M, y: 5.95, w: W - 2 * M, h: 0.45, fontSize: 15, color: C.ink, bold: true });
}

// 5 ─ Live coaching screenshot
{
  const s = base("Live coaching", "Every rep measured: angle, tempo and quality, plus a spoken correction");
  card(s, M, 1.85, 8.6, 3.55 + 0.02, { fill: C.dark, line: "1E293B" });
  s.addImage({ path: A("coach_crop.png"), x: M + 0.08, y: 1.93, w: 8.44, h: 8.44 * 582 / 1420 });
  const pts = [
    ["Goniometer-style joint angles", "Knee, hip, shoulder, elbow and trunk, computed in isotropic pixel space"],
    ["Per-rep quality score", "Range reached × tempo × form, so a partial rep gets \"go a little further\""],
    ["View-aware form rules", "Knees caving in (front view), chest dropping (side view), elbow bending, shrugging"],
    ["Privacy view", "Hide the room and show only the skeleton"],
  ];
  pts.forEach(([h, t], i) => {
    const y = 1.85 + i * 0.95;
    s.addShape(pptx.shapes.RECTANGLE, { x: 9.5, y: y + 0.08, w: 0.06, h: 0.72, fill: { color: C.accent }, line: { color: C.accent } });
    s.addText(h, { x: 9.7, y, w: 3.1, h: 0.4, fontFace: F.body, fontSize: 15, bold: true, color: C.ink });
    s.addText(t, { x: 9.7, y: y + 0.38, w: 3.1, h: 0.5, fontFace: F.body, fontSize: 11.5, color: C.muted, valign: "top" });
  });
  note(s, "Validated on real footage: 3/3 stands on the CDC's own chair-stand video (front view) and 2/2 squats on the demo clip. Both are regression tests.");
}

// 6 ─ Clinical tests
{
  const s = base("Clinical screening", "Standard fall-risk and mobility tests, scored against published norms");
  const tests = [
    ["30-second chair stand", "Counts full stands in 30 s and flags fall risk using CDC STEADI thresholds by age and sex"],
    ["Single-leg balance", "Times the stance until the foot touches down. Under 5 s flags fall risk (Vellas 1997); age means from Springer 2007"],
    ["Range of motion", "Shoulder flexion and abduction, knee flexion. Median-of-5 frames, compared with AAOS 180° / 180° / 135°"],
  ];
  tests.forEach(([h, t], i) => {
    const y = 1.9 + i * 1.35;
    card(s, M, y, 6.2, 1.2);
    s.addText(h, { x: M + 0.25, y: y + 0.1, w: 5.8, h: 0.4, fontFace: F.head, fontSize: 18, bold: true, color: C.ink });
    s.addText(t, { x: M + 0.25, y: y + 0.5, w: 5.8, h: 0.65, fontFace: F.body, fontSize: 13.5, color: C.muted, valign: "top" });
  });
  const hdr = [["Age", "Men", "Women"].map(t => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: C.accent } } }))];
  const data = [["60–64", "< 14", "< 12"], ["65–69", "< 12", "< 11"], ["70–74", "< 12", "< 10"], ["75–79", "< 11", "< 10"], ["80–84", "< 10", "< 9"], ["85–89", "< 8", "< 8"], ["90–94", "< 7", "< 4"]];
  s.addText("30-s chair stand: stands that indicate fall risk (CDC STEADI)", { x: 7.3, y: 1.9, w: 5.4, h: 0.4, fontFace: F.body, fontSize: 14, bold: true, color: C.ink });
  s.addTable(hdr.concat(data), { x: 7.3, y: 2.35, w: 5.4, colW: [1.8, 1.8, 1.8], fontFace: F.body, fontSize: 14, color: C.ink, align: "center",
    border: { type: "solid", color: C.line, pt: 0.75 }, fill: { color: C.card }, rowH: 0.42 });
  s.addText("Automatic countdown, timing and counting. The result card compares the score with the patient's age band.", { x: 7.3, y: 5.85, w: 5.4, h: 0.6, fontFace: F.body, fontSize: 12.5, color: C.muted, italic: true });
}

// 7 ─ Architecture
{
  const s = base("Architecture", "The browser sees, the NPU understands, and nothing leaves the PC");
  const lane = (x, w, label, color) => {
    s.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x, y: 1.85, w, h: 4.55, rectRadius: 0.06, fill: { color }, line: { color: C.line } });
    s.addText(label, { x: x + 0.15, y: 1.92, w: w - 0.3, h: 0.35, fontFace: F.body, fontSize: 12, bold: true, color: C.muted, charSpacing: 1 });
  };
  lane(M, 3.1, "BROWSER UI (OFFLINE)", "F1F5F9");
  lane(3.95, 5.35, "PYTHON ENGINE · 127.0.0.1 · numpy + onnxruntime", "F0FDFA");
  lane(9.5, 3.23, "LOCAL INTELLIGENCE", "FFFBEB");
  const node = (x, y, w, h, t, sub, hl) => {
    s.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: hl ? C.accent : C.card }, line: { color: hl ? C.accent : "CBD5E1", width: 1 } });
    s.addText([{ text: t, options: { bold: true, fontSize: 13.5, color: hl ? "FFFFFF" : C.ink, breakLine: true } },
      { text: sub, options: { fontSize: 10.5, color: hl ? "CCFBF1" : C.muted } }], { x: x + 0.1, y, w: w - 0.2, h, fontFace: F.body, valign: "middle", align: "center" });
  };
  const arrow = (x1, y1, x2, y2) => s.addShape(pptx.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.001, h: Math.abs(y2 - y1) || 0.001,
    flipH: x2 < x1, flipV: y2 < y1, line: { color: "64748B", width: 1.5, endArrowType: "triangle" } });
  // Browser lane
  node(M + 0.2, 2.4, 2.7, 0.8, "Webcam / video", "getUserMedia, 30 fps");
  node(M + 0.2, 3.55, 2.7, 0.8, "Crop to person", "192×192 RGBA, tracked");
  node(M + 0.2, 5.25, 2.7, 0.9, "Overlay + voice", "skeleton, angle arcs, cues in 7 languages");
  arrow(M + 1.55, 3.2, M + 1.55, 3.55);
  // Engine lane: a straight pipeline
  node(4.15, 2.4, 2.45, 1.0, "MoveNet · Qualcomm AI Hub", "w8a16 on Hexagon NPU (QNN EP, HTP), ~1 ms", true);
  node(6.75, 2.4, 2.35, 1.0, "Crop tracker + One-Euro", "stable keypoints, next crop");
  node(6.75, 3.75, 2.35, 1.0, "Goniometry", "knee · hip · shoulder · elbow · trunk");
  node(4.15, 3.75, 2.45, 1.0, "Clinical tests", "CDC · Springer · AAOS norms");
  node(6.75, 5.1, 2.35, 1.0, "Reps + form rules", "per-side hysteresis, quality score");
  arrow(3.5, 3.95, 4.15, 2.9);        // crop -> MoveNet
  arrow(6.6, 2.9, 6.75, 2.9);         // MoveNet -> filter
  arrow(7.92, 3.4, 7.92, 3.75);       // filter -> goniometry
  arrow(6.75, 4.25, 6.6, 4.25);       // goniometry -> tests
  arrow(7.92, 4.75, 7.92, 5.1);       // goniometry -> reps
  arrow(6.75, 5.7, 3.5, 5.7);         // reps -> overlay
  arrow(4.6, 4.75, 3.5, 5.4);         // tests -> overlay
  // Local intelligence lane (bottom-up)
  node(9.7, 5.1, 2.85, 1.0, "./data (JSON)", "angles, reps, scores. Never frames");
  node(9.7, 3.7, 2.85, 1.1, "Local LLM (optional)", "Qwen3-4B Q4_0 · llama.cpp on Oryon CPU, or GenieX / Foundry Local");
  node(9.7, 2.4, 2.85, 1.0, "Summaries · plan · Q&A", "templates if no LLM; red-flag safety");
  arrow(9.1, 5.6, 9.7, 5.6);          // reps -> data
  arrow(11.12, 5.1, 11.12, 4.8);      // data -> LLM
  arrow(11.12, 3.7, 11.12, 3.4);      // LLM -> outputs
  note(s, "Only 3 native dependencies (numpy, onnxruntime, onnxruntime-qnn), all with Windows-on-ARM64 wheels. No OpenCV, PyTorch or npm build.");
}

// 8 ─ Snapdragon compute
{
  const s = base("Snapdragon compute", "Continuous vision runs on the Hexagon NPU in ~1 ms, about 3% of each frame");
  s.addChart(pptx.charts.BAR, [{ name: "MoveNet inference (ms)", labels: ["X Elite · float", "X Elite · w8a16", "X2 Elite · float", "X2 Elite · w8a16"], values: [1.04, 1.054, 0.469, 0.44] }], {
    x: M, y: 1.85, w: 6.3, h: 3.9, barDir: "bar", chartColors: [C.accent], catAxisLabelFontFace: F.body, catAxisLabelFontSize: 13, valAxisLabelFontSize: 11,
    valAxisTitle: "ms per frame (lower is better)", showValAxisTitle: true, valAxisTitleFontSize: 11, valAxisMinVal: 0, valAxisMaxVal: 1.2, valAxisMajorUnit: 0.2,
    dataLabelFontSize: 12, showValue: true, dataLabelFormatCode: "0.00", valGridLine: { color: C.line, size: 0.5 }, catGridLine: { style: "none" },
    showTitle: true, title: "MoveNet latency on the Hexagon NPU (all layers on NPU)", titleFontSize: 14, titleColor: C.ink,
  });
  s.addText("Source: Qualcomm AI Hub device profiles, MoveNet v0.63.0 (ONNX). Budget at 30 fps: 33 ms per frame.", { x: M, y: 5.8, w: 6.3, h: 0.4, fontFace: F.body, fontSize: 10.5, color: C.muted, italic: true });
  const rows = [
    ["Always-on pose", "Hexagon NPU", "onnxruntime-qnn plugin EP, HTP. Strict session proves 100% of ops on the NPU; context cache for instant relaunch"],
    ["Benchmark / fallback", "Adreno GPU · CPU", "Same model through the QNN GPU backend or the ORT CPU EP, with the fallback reason shown in the UI"],
    ["LLM, after a session", "Oryon CPU", "llama.cpp Q4_0 with i8mm repack. It decoded faster than the NPU/GPU backends in our earlier X Elite tests"],
  ];
  rows.forEach(([a, b, c], i) => {
    const y = 1.85 + i * 1.35;
    card(s, 7.2, y, 5.53, 1.2);
    s.addText(a, { x: 7.4, y: y + 0.08, w: 2.6, h: 0.35, fontFace: F.body, fontSize: 14, bold: true, color: C.ink });
    s.addText(b, { x: 10.0, y: y + 0.08, w: 2.6, h: 0.35, fontFace: F.body, fontSize: 14, bold: true, color: C.accent, align: "right" });
    s.addText(c, { x: 7.4, y: y + 0.45, w: 5.2, h: 0.7, fontFace: F.body, fontSize: 12, color: C.muted, valign: "top" });
  });
  s.addText("Built-in benchmark (NPU vs GPU vs CPU): latency, CPU load at 30 fps, and battery watts on the user's own device.", { x: 7.2, y: 5.95, w: 5.53, h: 0.5, fontFace: F.body, fontSize: 12.5, bold: true, color: C.ink });
}

// 9 ─ Engineering
{
  const s = base("Technical implementation", "Engineered to be accurate, provable, and impossible to break in a demo");
  const E = [
    ["Provable NPU offload", "Sessions are built with session.disable_cpu_ep_fallback=1. Success means every operator is on the Hexagon NPU."],
    ["Exact quantized I/O", "The w8a16 AI Hub build uses uint16 tensors; scale and zero-point come from AI Hub's metadata.json."],
    ["Accuracy from 192 px", "MoveNet crop tracking keeps the person large; One-Euro filtering in body-scale units."],
    ["Honest rep counting", "Per-side hysteresis state machines, duration/timeout guards, form rules that must persist 4 frames."],
    ["Robust clinical scores", "Median-of-5 ROM, server-side test timelines, age/sex norms, flags instead of diagnoses."],
    ["Never dead in a demo", "NPU → GPU → CPU ladder, rule/template fallbacks for the LLM, 27 tests incl. real-video regressions."],
  ];
  E.forEach(([h, t], i) => {
    const x = M + (i % 3) * 4.1, y = 1.9 + Math.floor(i / 3) * 2.15;
    card(s, x, y, 3.85, 1.95);
    s.addText(h, { x: x + 0.25, y: y + 0.15, w: 3.4, h: 0.45, fontFace: F.head, fontSize: 17, bold: true, color: C.accent });
    s.addText(t, { x: x + 0.25, y: y + 0.62, w: 3.4, h: 1.25, fontFace: F.body, fontSize: 13.5, color: C.ink, valign: "top" });
  });
}

// 10 ─ Deployment & accessibility
{
  const s = base("Deployment & accessibility", "One script to install, one click to run, and no internet after that");
  const steps = [
    ["scripts\\setup.ps1", "Finds or installs native ARM64 Python, installs 3 packages, verifies AI Hub models by SHA-256, and self-tests the NPU"],
    ["PunarGati.bat", "Double-click. The browser opens on 127.0.0.1 and the NPU badge shows the live latency"],
    ["scripts\\setup-llm.ps1 (optional)", "llama.cpp win-arm64 + Qwen3-4B Q4_0. Auto-detected, or use GenieX, Foundry Local or LM Studio"],
  ];
  steps.forEach(([h, t], i) => {
    const y = 1.9 + i * 1.3;
    s.addShape(pptx.shapes.OVAL, { x: M, y: y + 0.12, w: 0.6, h: 0.6, fill: { color: C.accent }, line: { color: C.accent } });
    s.addText(String(i + 1), { x: M, y: y + 0.12, w: 0.6, h: 0.6, fontFace: F.head, fontSize: 18, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
    s.addText(h, { x: M + 0.8, y, w: 5.6, h: 0.4, fontFace: "Consolas", fontSize: 15, bold: true, color: C.ink });
    s.addText(t, { x: M + 0.8, y: y + 0.4, w: 5.6, h: 0.75, fontFace: F.body, fontSize: 13.5, color: C.muted, valign: "top" });
  });
  const acc = ["7 Indian languages, offline voices", "Privacy view: skeleton only", "Runs on any laptop (CPU fallback)", "Bundled demo clip, no webcam needed", "No account, no subscription", "Data stays in ./data on the PC"];
  card(s, 7.3, 1.9, 5.43, 3.9);
  s.addText("Accessible by default", { x: 7.55, y: 2.0, w: 5, h: 0.45, fontFace: F.head, fontSize: 18, bold: true, color: C.ink });
  acc.forEach((t, i) => {
    const y = 2.55 + i * 0.52;
    s.addShape(pptx.shapes.OVAL, { x: 7.6, y: y + 0.13, w: 0.18, h: 0.18, fill: { color: C.accent }, line: { color: C.accent } });
    s.addText(t, { x: 7.95, y, w: 4.6, h: 0.45, fontFace: F.body, fontSize: 15, color: C.ink, valign: "middle" });
  });
}

// 11 ─ Roadmap
{
  const s = base("Impact & roadmap", "Next: hands, feet and voice, all on the same NPU");
  const R = [
    ["Now", "Pose coach, 8 exercises, 5 tests, reports, local LLM, 7 languages"],
    ["Next", "RTMPose wholebody (AI Hub, 133 keypoints) for ankle, wrist and finger ROM"],
    ["Then", "Whisper on the NPU for hands-free \"next / stop / pain\" commands"],
    ["Pilot", "Validate against a goniometer with a physio clinic; FHIR/ABDM export; Arduino UNO Q haptic rep band"],
  ];
  s.addShape(pptx.shapes.LINE, { x: M + 0.3, y: 2.55, w: W - 2 * M - 0.6, h: 0, line: { color: C.accent, width: 2 } });
  R.forEach(([h, t], i) => {
    const x = M + i * 3.07;
    s.addShape(pptx.shapes.OVAL, { x: x + 0.15, y: 2.4, w: 0.3, h: 0.3, fill: { color: i === 0 ? C.accent : C.card }, line: { color: C.accent, width: 2 } });
    s.addText(h, { x, y: 1.85, w: 2.8, h: 0.45, fontFace: F.head, fontSize: 18, bold: true, color: C.accent });
    s.addText(t, { x, y: 2.9, w: 2.8, h: 1.4, fontFace: F.body, fontSize: 14, color: C.ink, valign: "top" });
  });
  const I = [["Patients", "supervised-quality home exercise, visible progress, early fall-risk flags"],
    ["Physiotherapists", "measured adherence and ROM trends between visits"],
    ["Tier-2/3 India", "works with no connectivity and no cloud bill"]];
  I.forEach(([h, t], i) => {
    const x = M + i * 4.1;
    card(s, x, 4.55, 3.85, 1.55, { fill: "F0FDFA", line: "99F6E4", shadow: false });
    s.addText(h, { x: x + 0.25, y: 4.65, w: 3.4, h: 0.4, fontFace: F.head, fontSize: 16, bold: true, color: C.ink });
    s.addText(t, { x: x + 0.25, y: 5.05, w: 3.4, h: 0.95, fontFace: F.body, fontSize: 13.5, color: C.muted, valign: "top" });
  });
}

// 12 ─ Close
{
  const s = pptx.addSlide(); n += 1;
  s.background = { color: C.dark };
  s.addText("Private. Offline. Multilingual. Measured.", { x: M, y: 2.0, w: W - 2 * M, h: 1.0, fontFace: F.head, fontSize: 40, bold: true, color: "FFFFFF", align: "center" });
  s.addText("PunarGati puts a physiotherapist's eyes in every home that has a Snapdragon PC.", { x: M, y: 3.05, w: W - 2 * M, h: 0.6, fontFace: F.body, fontSize: 20, color: "CBD5E1", align: "center" });
  s.addText("github.com/Sachin0496/punargati", { x: M, y: 4.2, w: W - 2 * M, h: 0.5, fontFace: F.body, fontSize: 20, bold: true, color: "5EEAD4", align: "center" });
  s.addText("MoveNet via Qualcomm AI Hub · ONNX Runtime QNN EP · llama.cpp · Qwen3 · MIT licensed", { x: M, y: 6.4, w: W - 2 * M, h: 0.4, fontFace: F.body, fontSize: 12, color: "94A3B8", align: "center" });
}

pptx.writeFile({ fileName: path.join(__dirname, "PunarGati.pptx") }).then(f => console.log("wrote", f));
