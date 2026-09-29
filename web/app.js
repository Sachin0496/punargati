import { Stage } from "./stage.js";
import { LANGS, setLang, getLang, setVoice, cueText, speak, speakCue, voiceFor, localSummary, tr } from "./i18n.js";
import { lineChart, barChart, ring } from "./charts.js";

const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const api = async (path, body) => {
  const r = await fetch(path, body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const j = await r.json();
  if (!r.ok || j.error) throw new Error(j.error || r.statusText);
  return j;
};
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const SIDE_EN = { l: "Left", r: "Right", b: "" };
const SIDE = new Proxy(SIDE_EN, { get: (o, k) => (o[k] ? tr(o[k]) : o[k]) });
const ofTarget = (n, each) => getLang() === "hi" ? `${n} में से${each ? " (हर तरफ़)" : ""}` : `of ${n}${each ? " per side" : ""}`;
function applyUI() {
  document.querySelectorAll("[data-t]").forEach(el => {
    if (!el.dataset.en) el.dataset.en = el.textContent.trim();
    el.textContent = tr(el.dataset.en);
  });
}
const UNIT_CLASS = { npu: "npu", gpu: "gpu", cpu: "cpu" };
const SHORT = { npu: "Hexagon NPU", gpu: "Adreno GPU", cpu: "CPU" };

const state = { lib: null, profile: {}, plan: { items: [] }, system: null, active: null, lastCount: 0, halfSaid: false, doneSaid: false };

// ---------------------------------------------------------------- stage ----
const stage = new Stage({
  video: $("#video"), overlay: $("#overlay"),
  onResult: onFrame,
  onError: e => showCue(`Engine error: ${e.message}`, false),
});

async function startCamera() {
  try {
    await stage.useCamera();
    sourceStarted();
  } catch (e) {
    showCue("Camera unavailable — allow camera access or use a video file", false);
  }
}
function sourceStarted() {
  $("#stageEmpty").hidden = true;
  $("#btnSource").hidden = false;
  $("#stage").classList.toggle("mirror", stage.mirror);
}
$("#btnCam").onclick = startCamera;
$("#fileInput").onchange = async e => {
  const f = e.target.files[0];
  if (!f) return;
  await stage.useFile(f);
  sourceStarted();
};
$("#btnDemo").onclick = async () => { await stage.useUrl("demo/squat.webm"); sourceStarted(); };
$("#btnSource").onclick = () => { stage.stopSource(); $("#stageEmpty").hidden = false; $("#btnSource").hidden = true; };
$("#optPrivacy").onchange = e => { stage.privacy = e.target.checked; $("#stage").classList.toggle("privacy", stage.privacy); stage.draw(); };
$("#optCrop").onchange = e => { stage.showCrop = e.target.checked; stage.draw(); };
function setPrecisionUI(on) { $("#optPrecision").checked = on; stage.size = on ? 288 : 192; }
$("#optPrecision").onchange = async e => {
  try { const r = await api("/api/precision", { on: e.target.checked }); setPrecisionUI(r.on);
    if (r.on) showCue(`Precision: ${r.model.model} on ${SHORT[r.model.target]}`, true); }
  catch (err) { setPrecisionUI(false); showCue(`Precision mode unavailable: ${err.message.slice(0, 80)}`, false); }
};
$("#optVoice").onchange = e => setVoice(e.target.checked);

// ---------------------------------------------------------------- tabs -----
function show(view) {
  $$("#tabs button").forEach(b => b.classList.toggle("active", b.dataset.view === view));
  $$(".view").forEach(v => v.classList.toggle("active", v.id === `view-${view}`));
  if (view === "progress") loadProgress();
  if (view === "perf") loadPerf();
  if (view === "plan") renderPlan();
  if (view === "ask") refreshLLM();
  if (view === "coach") stage.draw();
}
$$("#tabs button").forEach(b => (b.onclick = () => show(b.dataset.view)));

// ------------------------------------------------------------- telemetry ---
let cueTimer;
function showCue(text, good = false) {
  const c = $("#cue");
  c.textContent = text;
  c.classList.toggle("good", good);
  c.classList.add("show");
  clearTimeout(cueTimer);
  cueTimer = setTimeout(() => c.classList.remove("show"), 2600);
}
function bigFlash(text, cls = "pop") {
  const b = $("#bigOverlay");
  b.textContent = text;
  b.className = "big-overlay";
  void b.offsetWidth;
  b.classList.add(cls);
}
function setBadge(perf) {
  const b = $("#npuBadge");
  b.className = `badge ${UNIT_CLASS[perf.target] || ""}`;
  const name = { npu: "Hexagon NPU", gpu: "Adreno GPU", cpu: "CPU" }[perf.target] || perf.target;
  b.textContent = perf.p50_ms != null ? `${name} · ${perf.p50_ms} ms` : name;
}

function onFrame(r) {
  const p = r.perf;
  $("#tUnit").textContent = SHORT[p.target] || p.label;
  $("#tUnit").title = p.label;
  $("#tUnit").className = p.target === "npu" ? "npu" : "";
  $("#tInfer").textContent = p.infer_ms != null ? `${p.infer_ms}${p.wb_ms != null ? ` + ${p.wb_ms}` : ""} ms` : "—";
  $("#tInfer").title = p.wb_ms != null ? "MoveNet + RTMPose-WholeBody" : "MoveNet";
  $("#tEngine").textContent = `${p.engine_ms} ms`;
  $("#tFps").textContent = p.fps ? `${p.fps} fps` : "—";
  $("#tCpu").textContent = `${p.cpu}%`;
  $("#tView").textContent = r.confidence < 0.2 ? "no person" : r.view;
  setBadge(p);
  for (const ev of r.events || []) handleEvent(ev);
  if (r.activity) renderActivity(r.activity);
}

function handleEvent(ev) {
  if (ev.type === "cue") {
    const good = ev.cue === "great_rep" || ev.cue === "test_start";
    const side = ev.side && SIDE[ev.side] ? `${SIDE[ev.side]}: ` : "";
    showCue(side + cueText(ev.cue), good);
    speakCue(ev.cue);
    if (ev.cue === "test_start") bigFlash(cueText("test_start"));
  } else if (ev.type === "rep") {
    const total = Object.values(ev.count).reduce((a, b) => a + b, 0);
    bigFlash(String(total));
    speak(String(total), { priority: true });
    addHistory(ev.rep);
    renderLastRep(ev.rep);
    const tgt = state.active?.target_reps || 10;
    const perSide = state.active?.sides === "each" ? Math.max(...Object.values(ev.count)) : total;
    if (!state.halfSaid && perSide === Math.ceil(tgt / 2) && tgt >= 6) { state.halfSaid = true; setTimeout(() => speakCue("halfway"), 900); }
    if (!state.doneSaid && perSide >= tgt) { state.doneSaid = true; setTimeout(() => { speakCue("set_done"); showCue(cueText("set_done"), true); }, 900); }
  } else if (ev.type === "count") {
    bigFlash(String(ev.count));
    speak(String(ev.count), { priority: true });
  } else if (ev.type === "result") {
    renderTestResult(ev.result);
  }
}

// ------------------------------------------------------------- activity ----
function exercise(id) { return state.lib.exercises.find(e => e.id === id); }
const unitOf = label => (label || "").includes("%") ? "%" : "°";
function test(id) { return state.lib.tests.find(t => t.id === id); }

async function startActivity(kind, id, opts = {}) {
  if (!stage.running) { await startCamera(); if (!stage.running) return; }
  show("coach");
  const target_reps = opts.reps || 10;
  const started = await api("/api/start", { kind, id, side: opts.side || "auto", target_reps }).catch(e => { showCue(e.message.slice(0, 120), false); return null; });
  if (!started) return;
  setPrecisionUI(!!started.precision);
  const spec = kind === "exercise" ? exercise(id) : test(id);
  state.active = { kind, id, target_reps, sides: spec.sides, spec };
  state.halfSaid = state.doneSaid = false;
  stage.focus = id;
  $("#pickPanel").hidden = true;
  $("#livePanel").hidden = false;
  $("#liveKind").textContent = kind === "exercise" ? `Exercise · ${spec.view === "any" ? "any view" : spec.view + " view"}` : `Clinical test · ${spec.view} view`;
  $("#liveName").textContent = tr(spec.name);
  $("#liveExercise").hidden = kind !== "exercise";
  $("#liveTest").hidden = kind !== "assessment";
  $("#steps").innerHTML = spec.steps.map(s => `<li>${esc(tr(s))}</li>`).join("");
  $("#purpose").textContent = tr(spec.purpose || spec.measures || "");
  if (kind === "exercise") {
    $("#repCount").textContent = "0";
    $("#repTarget").textContent = ofTarget(target_reps, spec.sides === "each");
    $("#repHistory").innerHTML = "";
    $("#lastRep").innerHTML = `<span class="muted">${esc(tr("Complete a rep to see its range, tempo and quality."))}</span>`;
    $("#gaugeLabel").textContent = tr(spec.rom_label);
    ring($("#repRing"), 0);
  } else {
    $("#testResult").innerHTML = "";
    $("#testBig").textContent = "—";
    $("#testTimer").textContent = "";
  }
  speakCue("start_ex");
  // Keep the laptop awake mid-session: nobody touches the keyboard while exercising.
  try { state.wakeLock = await navigator.wakeLock?.request("screen"); } catch { /* not critical */ }
}

function renderActivity(a) {
  if (a.kind === "exercise") {
    const counts = a.counts;
    const keys = Object.keys(counts);
    const perSide = keys.length > 1 ? Math.max(...Object.values(counts)) : a.total;
    $("#repCount").textContent = keys.length > 1 ? keys.map(k => counts[k]).join(" · ") : a.total;
    $("#sideCounts").innerHTML = keys.length > 1 ? keys.map(k => `${SIDE[k]} <b>${counts[k]}</b>`).join(" &nbsp;·&nbsp; ") : "";
    ring($("#repRing"), perSide / a.target_reps, perSide >= a.target_reps ? "#4ade80" : "#2dd4bf");
    // gauge: the side that is currently moving the most
    const vals = Object.entries(a.value).filter(([, v]) => v != null);
    const [side, v] = vals.sort((x, y) => y[1] - x[1])[0] || [null, null];
    const spec = state.active?.spec;
    const lo = Math.min(0, a.rest - 10), hi = Math.max(a.goal * 1.15, a.goal + 10);
    const pct = x => `${Math.max(0, Math.min(100, (x - lo) / (hi - lo) * 100))}%`;
    $("#gaugeFill").style.width = v == null ? "0%" : pct(v);
    $("#markEnter").style.left = pct(a.enter);
    $("#markGoal").style.left = pct(a.goal);
    const u = unitOf(spec?.rom_label);
    const shown = v == null ? "—" : (spec?.id === "knee_extension" ? `${Math.round(Math.max(0, 90 - v))}° from straight` : `${Math.round(v)}${u}`);
    $("#gaugeVal").textContent = `${side && SIDE[side] ? SIDE[side] + " " : ""}${shown}`;
    $("#gaugeGoal").textContent = spec?.id === "knee_extension" ? `${tr("goal")}: 0–10°` : `${tr("goal")} ${a.goal}${u}`;
    const moving = side && a.phase[side] === "moving";
    $("#phase").textContent = tr(v == null ? "Not visible" : moving ? "Moving" : "Rest");
    $("#phase").className = moving ? "moving" : "";
  } else {
    const labels = { ready: "Get into position", countdown: "Get ready…", running: "Go!", done: "Done" };
    $("#testState").textContent = tr(labels[a.state] || a.state);
    if (a.state === "ready") {
      $("#testTimer").textContent = tr(a.id === "chair_stand_30s" ? "Sit on the chair, whole body in view" : "Stand in view to begin");
    } else if (a.state === "countdown") {
      $("#testBig").textContent = Math.ceil(a.countdown);
      $("#testUnit").textContent = "";
      $("#testTimer").textContent = "";
    } else if (a.state === "running") {
      if (a.id === "chair_stand_30s") { $("#testBig").textContent = a.stands; $("#testUnit").textContent = tr("stands"); $("#testTimer").textContent = `${Math.ceil(a.remaining)} ${tr("s left")}`; }
      else if (a.id === "single_leg_stance") { $("#testBig").textContent = (a.elapsed || 0).toFixed(1); $("#testUnit").textContent = tr("seconds on one leg"); $("#testTimer").textContent = a.elapsed ? "" : tr("Lift one foot to start the clock"); }
      else { const b = Math.max(a.best.l || 0, a.best.r || 0); $("#testBig").textContent = `${Math.round(b)}°`; $("#testUnit").textContent = tr("best so far"); $("#testTimer").textContent = `${Math.ceil(a.remaining)} ${tr("s left")}`; }
    }
  }
}

function renderLastRep(rep) {
  const q = rep.quality, cls = q >= 80 ? "" : q >= 55 ? "mid" : "low";
  const spec = state.active?.spec;
  const romTxt = spec?.id === "knee_extension" ? `${rep.rom}° short` : `${rep.rom}${unitOf(spec?.rom_label)}`;
  $("#lastRep").innerHTML = `
    <div class="grid3">
      <div><span>${tr("Quality")}</span><b class="q" style="color:${cls === "" ? "var(--good)" : cls === "mid" ? "var(--warn)" : "var(--bad)"}">${q}</b></div>
      <div><span>${esc(tr(spec?.rom_label || "Range"))}</span><b>${romTxt}</b></div>
      <div><span>${tr("Tempo")}</span><b>${rep.duration}s</b></div>
    </div>
    ${rep.faults.length ? `<div class="faults">⚠ ${rep.faults.map(f => esc(cueText(f, getLang() === "hi" ? "hi" : "en"))).join(" · ")}</div>` : ""}`;
}
function addHistory(rep) {
  const i = document.createElement("i");
  i.style.height = `${Math.max(12, rep.quality)}%`;
  i.className = rep.quality >= 80 ? "" : rep.quality >= 55 ? "mid" : "low";
  i.title = `${rep.quality}/100 · ${rep.rom}${unitOf(state.active?.spec?.rom_label)}`;
  $("#repHistory").append(i);
}
function renderTestResult(r) {
  const flagTxt = tr({ ok: "Within typical range", below_average: "Below average", fall_risk: "Fall-risk flag", limited: "Limited range" }[r.flag] || "Recorded");
  let ref = "";
  if (r.threshold != null) ref = `Fall-risk threshold for your age/sex: below ${r.threshold}`;
  else if (r.reference != null) ref = r.unit === "degrees" ? `Reference ${r.reference}° · you reached ${r.percent_of_reference}%` : `Typical for your age: ~${r.reference} s`;
  $("#testBig").textContent = r.unit === "degrees" ? `${Math.round(r.score)}°` : r.score;
  $("#testUnit").textContent = r.unit;
  $("#testTimer").textContent = "";
  $("#testResult").innerHTML = `<div class="result-card"><span class="flag ${esc(r.flag)}">${flagTxt}</span>
    <p style="margin-top:8px">${esc(ref)}</p>${r.by_side ? `<p class="muted">${Object.entries(r.by_side).map(([k, v]) => `${k}: ${v}°`).join(" · ")}</p>` : ""}
    <p class="tiny">${esc(r.note || "")}</p></div>`;
}

$("#btnStop").onclick = async () => {
  const btn = $("#btnStop");
  btn.disabled = true;
  try {
    const rec = await api("/api/stop", {});
    state.wakeLock?.release?.().catch(() => {});
    state.wakeLock = null;
    $("#livePanel").hidden = true;
    $("#pickPanel").hidden = false;
    stage.focus = null;
    state.active = null;
    renderPlanToday();
    if (rec.saved) openSummary(rec);
    else showCue("Nothing to save yet — no reps or result recorded", false);
  } finally { btn.disabled = false; }
};

async function openSummary(rec) {
  const d = $("#summaryDlg");
  $("#sumTitle").textContent = `${tr(rec.name)} — ${tr("saved")}`;
  let cells = [];
  if (rec.kind === "exercise") {
    const s = rec.summary;
    const sides = Object.entries(s.by_side);
    cells.push([tr("Reps"), s.reps], [tr("Avg quality"), `${s.avg_quality}/100`]);
    sides.forEach(([k, v]) => cells.push([`${tr("Best")} ${k === "both" ? "" : tr(k[0].toUpperCase() + k.slice(1))} ${getLang() === "hi" ? tr(s.rom_label) : s.rom_label.toLowerCase()}`.replace(/\s+/g, " "), `${v.best_rom}${unitOf(s.rom_label)}`]));
  } else {
    const r = rec.result;
    cells.push([tr("Score"), `${r.score} ${r.unit}`], [tr("Flag"), r.flag || "—"]);
  }
  cells.push([tr("Computed on"), SHORT[rec.compute.target] || rec.compute.label]);
  $("#sumGrid").innerHTML = cells.slice(0, 6).map(([k, v]) => `<div><b>${esc(v)}</b><span>${esc(k)}</span></div>`).join("");
  $("#sumText").textContent = "Writing summary on-device…";
  $("#sumSource").textContent = "";
  d.showModal();
  try {
    const s = await api("/api/summary", { id: rec.id, lang: getLang() });
    const local = getLang() !== "en" && s.text_lang !== getLang() ? localSummary({ ...s.facts, name: tr(s.facts.name) }, getLang()) : null;
    $("#sumText").textContent = local ? `${local}\n\nCoach note (English): ${s.text}` : s.text;
    $("#sumText").dataset.speak = local || s.text;
    $("#sumSource").textContent = s.source === "llm" ? `on-device LLM · ${s.model}${s.latency_s ? ` · ${s.latency_s}s` : ""}` : "template (no LLM running)";
  } catch (e) { $("#sumText").textContent = "Summary unavailable."; }
}
$("#btnSpeakSum").onclick = () => speak($("#sumText").dataset.speak || $("#sumText").textContent, { priority: true });

// --------------------------------------------------------------- picker ----
function renderExercises() {
  const regionIcon = { knee: "Knee", functional: "Function", shoulder: "Shoulder", elbow: "Elbow", hip: "Hip", ankle: "Ankle · precision" };
  $("#exGrid").innerHTML = state.lib.exercises.map(e => `
    <button class="ex" data-id="${e.id}"><span class="tag">${esc(tr(regionIcon[e.region] || e.region))}</span>
      <b>${esc(tr(e.name))}</b><span>${esc(tr(e.purpose))}</span></button>`).join("");
  $$("#exGrid .ex").forEach(b => (b.onclick = () => startActivity("exercise", b.dataset.id)));
}
function planName(it) { return tr(it.kind === "exercise" ? exercise(it.id)?.name : test(it.id)?.name); }
function renderPlanToday() {
  const items = state.plan.items || [];
  if (!items.length) { $("#planToday").innerHTML = ""; return; }
  $("#planToday").innerHTML = `<div class="plan-today"><h3>${esc(tr("Today's plan from"))} ${esc(state.profile.physio_name || tr("your physio"))}</h3>
    ${items.map((it, i) => `<div class="plan-item"><span>${esc(planName(it))} <span class="muted">${it.kind === "exercise" ? `${it.sets}×${it.reps}` : "test"}${it.side !== "auto" ? " · " + esc(it.side) : ""}</span></span>
    <button class="ghost small" data-i="${i}">${esc(tr("Start"))}</button></div>`).join("")}</div>`;
  $$("#planToday button").forEach(b => (b.onclick = () => {
    const it = items[+b.dataset.i];
    startActivity(it.kind, it.id, { reps: it.reps, side: it.side === "both" ? "auto" : it.side });
  }));
}

// ---------------------------------------------------------------- tests ----
function renderTests() {
  $("#testCards").innerHTML = state.lib.tests.map(t => `
    <div class="card"><div class="row-between"><h3>${esc(tr(t.name))}</h3><span class="badge small">${t.view} view · ${t.duration}s</span></div>
      <p class="muted">${esc(tr(t.measures))}</p><ol>${t.steps.map(s => `<li>${esc(tr(s))}</li>`).join("")}</ol>
      <button class="primary" data-id="${t.id}">${esc(tr("Start test"))}</button></div>`).join("");
  $$("#testCards button").forEach(b => (b.onclick = () => startActivity("assessment", b.dataset.id)));
}

// ------------------------------------------------------------- progress ----
const AAOS = { rom_shoulder_flexion: 180, rom_shoulder_abduction: 180, rom_knee_flexion: 135 };
async function loadProgress() {
  const [p, sessions] = await Promise.all([api("/api/progress"), api("/api/sessions")]);
  $("#kpis").innerHTML = [
    [p.total_sessions, "sessions"], [p.total_reps, "reps measured"], [p.streak_days, "day streak"],
    [p.days.length ? p.days[p.days.length - 1].avg_quality ?? "—" : "—", "latest avg quality"],
  ].map(([v, l]) => `<div><b>${esc(v)}</b><span>${esc(tr(l))}</span></div>`).join("");
  const cards = $("#progressCards");
  cards.innerHTML = "";
  if (!p.series.length) cards.innerHTML = `<div class="card"><p class="muted">No sessions yet. Do an exercise or a test and your recovery curve appears here.</p></div>`;
  for (const s of p.series) {
    const c = document.createElement("div");
    c.className = "card";
    const last = s.points[s.points.length - 1].value, first = s.points[0].value;
    const delta = typeof last === "number" && typeof first === "number" ? last - first : null;
    const unit = s.kind === "exercise" ? unitOf(s.label) : (s.label === "degrees" ? "°" : "");
    c.innerHTML = `<div class="row-between"><h3>${esc(s.name)}${s.side && s.side !== "both" ? ` <span class="muted">(${esc(s.side)})</span>` : ""}</h3>
      <span class="badge small">${delta == null ? "" : (delta >= 0 ? "+" : "") + delta.toFixed(1) + unit} since first</span></div>
      <p class="tiny">${esc(s.kind === "exercise" ? "Best " + s.label.toLowerCase() + " per session" : s.label)}</p>`;
    c.append(lineChart(s.points, { unit, ref: AAOS[s.item] ?? null }));
    cards.append(c);
  }
  const rows = sessions.slice(0, 25).map(s => {
    const what = s.kind === "exercise" ? `${s.summary.reps} reps · quality ${s.summary.avg_quality}` : `${s.result.score} ${s.result.unit} <span class="flag ${esc(s.result.flag)}">${esc(s.result.flag || "")}</span>`;
    return `<tr><td>${esc(s.started.replace("T", " ").slice(0, 16))}</td><td>${esc(s.name)}</td><td>${what}</td><td>${esc(s.compute.label)}</td></tr>`;
  }).join("");
  $("#sessionTable").innerHTML = `<tr><th>When</th><th>Activity</th><th>Result</th><th>Computed on</th></tr>${rows || '<tr><td colspan="4" class="muted">None yet</td></tr>'}`;
}
$("#btnReport").onclick = () => window.open("/report?ai=1", "_blank");

// ----------------------------------------------------------------- plan ----
function renderPlan() {
  const items = state.plan.items || [];
  $("#planList").innerHTML = items.length ? `<table class="table"><tr><th>Activity</th><th>Dose</th><th>Side</th><th>When</th><th></th></tr>
    ${items.map((it, i) => `<tr><td>${esc(planName(it))}</td><td>${it.kind === "exercise" ? `${it.sets} × ${it.reps}` : "test"}</td><td>${esc(it.side)}</td><td>${esc(it.frequency)}</td>
    <td><button class="ghost small" data-i="${i}">Start</button></td></tr>`).join("")}</table>
    <p class="tiny">Imported ${esc((state.plan.updated || "").replace("T", " "))} · parsed by ${esc(state.plan.source || "—")}</p>`
    : `<p class="muted">No plan yet. Import one from your physiotherapist's note →</p>`;
  $$("#planList button").forEach(b => (b.onclick = () => {
    const it = items[+b.dataset.i];
    startActivity(it.kind, it.id, { reps: it.reps, side: it.side === "both" ? "auto" : it.side });
  }));
}
let parsed = null;
$("#btnParse").onclick = async () => {
  const btn = $("#btnParse");
  btn.disabled = true;
  $("#parseInfo").textContent = "Reading on-device…";
  try {
    parsed = await api("/api/plan/parse", { text: $("#rxText").value });
    const how = { "llm": "on-device LLM", "rules+llm": "rule engine + on-device LLM", "rules (LLM agreed)": "rule engine, confirmed by on-device LLM", "rules": "rule engine (no LLM running)" }[parsed.source] || parsed.source;
    $("#parseInfo").textContent = `Parsed by ${how}${parsed.model ? ` · ${parsed.model}` : ""}`;
    $("#parsePreview").innerHTML = parsed.items.length ? `<table class="table" style="margin-top:12px"><tr><th>Activity</th><th>Dose</th><th>Side</th><th>When</th></tr>
      ${parsed.items.map(it => `<tr><td>${esc(planName(it))}</td><td>${it.kind === "exercise" ? `${it.sets} × ${it.reps}` : "test"}</td><td>${esc(it.side)}</td><td>${esc(it.frequency)}</td></tr>`).join("")}</table>
      <div class="row" style="margin-top:10px"><button class="primary" id="btnSavePlan">Save as my plan</button></div>`
      : `<p class="muted">Couldn't match any exercises in that text.</p>`;
    const sp = $("#btnSavePlan");
    if (sp) sp.onclick = async () => {
      state.plan = await api("/api/plan", { items: parsed.items, source: parsed.source, text: $("#rxText").value });
      renderPlan(); renderPlanToday();
      $("#parsePreview").innerHTML = `<p class="muted">Saved ✓</p>`;
    };
  } catch (e) { $("#parseInfo").textContent = e.message; }
  finally { btn.disabled = false; }
};

// ------------------------------------------------------------------ ask -----
const CHIPS = ["How is my range of motion changing?", "Which exercise should I focus on?", "Is my chair-stand score normal for my age?", "My knee feels swollen today"];
$("#chatChips").innerHTML = CHIPS.map(c => `<button>${esc(c)}</button>`).join("");
$$("#chatChips button").forEach(b => (b.onclick = () => { $("#chatInput").value = b.textContent; $("#chatForm").requestSubmit(); }));
function addMsg(text, who, meta = "") {
  const m = document.createElement("div");
  m.className = `msg ${who}`;
  m.textContent = text;
  if (meta) { const s = document.createElement("span"); s.className = "meta"; s.textContent = meta; m.append(s); }
  $("#chatLog").append(m);
  $("#chatLog").scrollTop = 1e9;
  return m;
}
$("#chatForm").onsubmit = async e => {
  e.preventDefault();
  const q = $("#chatInput").value.trim();
  if (!q) return;
  $("#chatInput").value = "";
  addMsg(q, "me");
  const pending = addMsg("Thinking on-device…", "bot");
  try {
    const r = await api("/api/chat", { message: q, lang: getLang() });
    pending.remove();
    addMsg(r.text, "bot", r.source === "llm" ? `on-device · ${r.model}${r.latency_s ? ` · ${r.latency_s}s` : ""}` : "no local LLM running — showing your data");
  } catch (err) { pending.textContent = err.message; }
};
async function refreshLLM() {
  try {
    const s = await api("/api/llm/status");
    const b = $("#llmBadge");
    b.className = `badge ${s.available ? "ok" : "off"}`;
    b.textContent = s.available ? `${s.model} · local` : "No local LLM (template mode)";
  } catch { /* ignore */ }
}

// ------------------------------------------------------------------ perf ----
async function loadPerf() {
  const s = state.system = await api("/api/system");
  const pose = s.pose;
  $$("#unitSeg button").forEach(b => {
    b.disabled = !s.targets.includes(b.dataset.t);
    b.classList.toggle("active", b.dataset.t === pose.target);
  });
  const offload = pose.full_offload === true ? "100% of operators on the accelerator (strict mode)" : pose.target === "cpu" ? "n/a (CPU)" : "partial: some operators on CPU (verified by profiling)";
  $("#poseInfo").innerHTML = [
    ["Model", pose.model], ["Running on", pose.label], ["Graph placement", offload],
    ["Load / compile", `${pose.compile_s} s${pose.from_cache ? " (QNN context cache)" : ""}`],
    ["Latency p50 / p95", pose.p50_ms != null ? `${pose.p50_ms} / ${pose.p95_ms} ms` : "run the camera first"],
    ["Providers", pose.providers.join(", ")],
  ].map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("") +
    (s.load_errors?.length ? `<dt>Fallbacks</dt><dd class="tiny">${esc(s.load_errors.join(" | ")).slice(0, 400)}</dd>` : "");
  const m = s.machine;
  $("#machineInfo").innerHTML = [
    ["Processor", m.processor], ["OS", m.os], ["Python", `${m.python} (${m.python_arch})`],
    ["onnxruntime", m.onnxruntime], ["onnxruntime-qnn", m.onnxruntime_qnn || "not installed"],
    ["Compute units", s.targets.map(t => t.toUpperCase()).join(" · ")],
    ["Local LLM", s.llm.available ? `${s.llm.model} @ ${s.llm.base}` : "not running"],
  ].map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("");
  $("#modelTable").innerHTML = `<tr><th>Model</th><th>Precision</th><th>Role</th><th>License</th><th>Status</th></tr>` +
    s.models.map(x => `<tr><td>${esc(x.source)}</td><td>${esc(x.precision)}</td><td>${x.key.startsWith("rtmpose") ? "Precision mode: 133 keypoints incl. feet" : ""}${x.key.startsWith("rtmpose") ? "" : (x.precision === "float" ? "GPU / CPU pose" : "NPU pose (quantized)")}${x.key.startsWith("rtmpose") ? (x.precision === "float" ? " · GPU/CPU" : " · NPU") : ""}</td><td>${esc(x.license)}</td><td>${x.present ? "✓ installed" : "missing"}</td></tr>`).join("") +
    `<tr><td>Local LLM (llama.cpp / GenieX / Foundry Local)</td><td>Q4_0 / w4a16</td><td>Summaries, plan import, Q&amp;A</td><td>per model</td><td>${s.llm.available ? "✓ " + esc(s.llm.model) : "optional"}</td></tr>`;
  const last = await api("/api/bench");
  if (last.results) renderBench(last);
}
$$("#unitSeg button").forEach(b => (b.onclick = async () => {
  b.disabled = true;
  try { await api("/api/compute", { target: b.dataset.t }); } catch (e) { alert(e.message); }
  loadPerf();
}));
$("#btnBench").onclick = async () => {
  const btn = $("#btnBench");
  btn.disabled = true;
  $("#benchInfo").textContent = "Benchmarking each compute unit (latency, then 8 s of sustained 30 fps)…";
  try { renderBench(await api("/api/bench", { seconds: 8 })); }
  catch (e) { $("#benchInfo").textContent = e.message; }
  finally { btn.disabled = false; }
};
function renderBench(res) {
  const ok = res.results.filter(r => !r.error);
  $("#benchInfo").textContent = `Run ${res.when.replace("T", " ")} · ${res.model}` + (res.idle_battery_watts ? ` · idle battery draw ${res.idle_battery_watts} W` : "");
  const g = $("#benchCharts");
  g.innerHTML = "";
  const chart = (title, key, unit, better, fmt) => {
    const d = document.createElement("div");
    d.innerHTML = `<h4>${title}</h4>`;
    d.append(barChart(ok.map(r => ({ label: `${r.model || "MoveNet"} ${r.target.toUpperCase()}${r.perf_mode === "power_saver" ? " saver" : ""}`, value: r[key] })), { unit, better, fmt, height: 30 + 44 * ok.length }));
    g.append(d);
  };
  chart("Inference latency (p50)", "p50_ms", " ms", "lower", v => v.toFixed(2));
  chart("App CPU load while coaching @30 fps", "cpu_percent_at_30fps", "%", "lower", v => v.toFixed(1));
  if (ok.some(r => r.battery_watts_at_30fps)) chart("Battery draw @30 fps", "battery_watts_at_30fps", " W", "lower", v => v.toFixed(1));
  else chart("Max throughput", "max_fps", " fps", "higher", v => Math.round(v));
  $("#benchTable").innerHTML = `<tr><th>Model</th><th>Unit</th><th>Precision</th><th>p50</th><th>p99</th><th>Max FPS</th><th>CPU @30fps</th><th>Battery @30fps</th><th>Full offload</th></tr>` +
    res.results.map(r => r.error ? `<tr><td>${r.model || "MoveNet"}</td><td>${r.target}${r.perf_mode === "power_saver" ? " (power saver)" : ""}</td><td colspan="7" class="muted">${esc(r.error.slice(0, 120))}</td></tr>` :
      `<tr><td>${esc(r.model || "MoveNet")}</td><td>${esc(r.label)}</td><td>${r.precision}</td><td>${r.p50_ms} ms</td><td>${r.p99_ms} ms</td><td>${r.max_fps}</td><td>${r.cpu_percent_at_30fps}%</td><td>${r.battery_watts_at_30fps ?? "n/a"}${r.battery_watts_at_30fps ? " W" : ""}</td><td>${r.full_offload === true ? "✓" : "—"}</td></tr>`).join("");
}

// -------------------------------------------------------------- profile ----
function fillLangSelect(sel) { sel.innerHTML = Object.entries(LANGS).map(([k, v]) => `<option value="${k}">${v.name}</option>`).join(""); }
fillLangSelect($("#langSel"));
fillLangSelect($("#profLang"));
function applyLang(l) {
  setLang(l);
  document.documentElement.lang = l === "hi" ? "hi" : "en";
  applyUI();
  if (state.lib) { renderExercises(); renderTests(); renderPlanToday(); }
  $("#langSel").value = l;
  $("#profLang").value = l;
  const v = voiceFor(l);
  $("#voiceInfo").textContent = v ? `Voice: ${v.name}` : (l === "en" ? "" : `No ${LANGS[l].name} voice installed — cues will show as text. Add it in Windows Settings › Time & language › Speech.`);
}
$("#langSel").onchange = async e => {
  applyLang(e.target.value);
  state.profile = await api("/api/profile", { language: e.target.value });
};
$("#profileForm").onsubmit = async e => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));
  data.age = data.age ? Number(data.age) : null;
  state.profile = await api("/api/profile", data);
  applyLang(state.profile.language || "en");
  $("#profSaved").textContent = "Saved ✓";
  renderPlanToday();
  setTimeout(() => ($("#profSaved").textContent = ""), 2000);
};
function fillProfile() {
  const f = $("#profileForm");
  for (const [k, v] of Object.entries(state.profile)) if (f.elements[k]) f.elements[k].value = v ?? "";
}

// ----------------------------------------------------------------- boot ----
(async function boot() {
  const [lib, profile, plan, system] = await Promise.all([api("/api/library"), api("/api/profile"), api("/api/plan"), api("/api/system")]);
  Object.assign(state, { lib, profile, plan, system });
  renderExercises();
  renderTests();
  renderPlanToday();
  fillProfile();
  applyLang(profile.language || "en");
  setBadge({ target: system.pose.target, p50_ms: null });
  if (window.speechSynthesis) speechSynthesis.addEventListener("voiceschanged", () => applyLang(getLang()));
})();
