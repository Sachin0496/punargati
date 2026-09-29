// Tiny dependency-free SVG charts (the app must work fully offline).
const NS = "http://www.w3.org/2000/svg";
const el = (tag, attrs = {}, text) => {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (text != null) e.textContent = text;
  return e;
};

export function lineChart(points, { width = 520, height = 180, unit = "°", ref = null, color = "#2dd4bf" } = {}) {
  const svg = el("svg", { viewBox: `0 0 ${width} ${height}`, class: "chart", role: "img" });
  const pad = { l: 40, r: 14, t: 14, b: 26 };
  const vals = points.map(p => p.value).filter(v => typeof v === "number");
  if (!vals.length) { svg.append(el("text", { x: width / 2, y: height / 2, "text-anchor": "middle", class: "muted" }, "No data yet")); return svg; }
  let lo = Math.min(...vals, ref ?? Infinity), hi = Math.max(...vals, ref ?? -Infinity);
  if (hi - lo < 10) { lo -= 5; hi += 5; }
  lo = Math.floor(lo / 10) * 10; hi = Math.ceil(hi / 10) * 10;
  const X = i => pad.l + (points.length === 1 ? (width - pad.l - pad.r) / 2 : i * (width - pad.l - pad.r) / (points.length - 1));
  const Y = v => height - pad.b - (v - lo) / (hi - lo) * (height - pad.t - pad.b);
  for (let g = 0; g <= 4; g++) {
    const v = lo + (hi - lo) * g / 4, y = Y(v);
    svg.append(el("line", { x1: pad.l, x2: width - pad.r, y1: y, y2: y, class: "grid" }));
    svg.append(el("text", { x: pad.l - 6, y: y + 4, "text-anchor": "end", class: "axis" }, `${Math.round(v)}${unit}`));
  }
  if (ref != null) {
    svg.append(el("line", { x1: pad.l, x2: width - pad.r, y1: Y(ref), y2: Y(ref), class: "ref" }));
    svg.append(el("text", { x: width - pad.r, y: Y(ref) - 5, "text-anchor": "end", class: "axis ref-t" }, `reference ${ref}${unit}`));
  }
  const d = points.map((p, i) => `${i ? "L" : "M"}${X(i).toFixed(1)},${Y(p.value).toFixed(1)}`).join(" ");
  const area = `${d} L${X(points.length - 1)},${height - pad.b} L${X(0)},${height - pad.b} Z`;
  svg.append(el("path", { d: area, fill: color, opacity: 0.12 }));
  svg.append(el("path", { d, fill: "none", stroke: color, "stroke-width": 2.5, "stroke-linejoin": "round" }));
  points.forEach((p, i) => {
    const c = el("circle", { cx: X(i), cy: Y(p.value), r: 4, fill: color });
    c.append(el("title", {}, `${p.t?.slice(0, 16).replace("T", " ")} — ${p.value}${unit}`));
    svg.append(c);
  });
  const step = Math.max(1, Math.ceil(points.length / 6));
  points.forEach((p, i) => {
    if (i % step && i !== points.length - 1) return;
    svg.append(el("text", { x: X(i), y: height - 8, "text-anchor": "middle", class: "axis" }, (p.t || "").slice(5, 10)));
  });
  return svg;
}

export function barChart(rows, { width = 520, height = 200, unit = "", better = "lower", fmt = v => v } = {}) {
  const svg = el("svg", { viewBox: `0 0 ${width} ${height}`, class: "chart", role: "img" });
  const valid = rows.filter(r => typeof r.value === "number");
  if (!valid.length) { svg.append(el("text", { x: width / 2, y: height / 2, "text-anchor": "middle", class: "muted" }, "n/a")); return svg; }
  const max = Math.max(...valid.map(r => r.value)) * 1.15 || 1;
  const bh = Math.min(38, (height - 20) / rows.length - 10);
  const best = better === "lower" ? Math.min(...valid.map(r => r.value)) : Math.max(...valid.map(r => r.value));
  rows.forEach((r, i) => {
    const y = 10 + i * (bh + 12);
    svg.append(el("text", { x: 0, y: y + bh / 2 + 5, class: "axis lbl" }, r.label));
    const w = typeof r.value === "number" ? Math.max(2, (r.value / max) * (width - 240)) : 0;
    svg.append(el("rect", { x: 160, y, width: w, height: bh, rx: 6, fill: r.value === best ? "#2dd4bf" : "#475569" }));
    svg.append(el("text", { x: 160 + w + 8, y: y + bh / 2 + 5, class: "val" },
      typeof r.value === "number" ? `${fmt(r.value)}${unit}` : "n/a"));
  });
  return svg;
}

export function ring(el_, frac, color = "#2dd4bf") {
  const c = 2 * Math.PI * 52;
  el_.querySelector(".ring-fg").setAttribute("stroke-dasharray", `${Math.max(0, Math.min(1, frac)) * c} ${c}`);
  el_.querySelector(".ring-fg").setAttribute("stroke", color);
}
