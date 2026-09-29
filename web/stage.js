// Camera / video source, the frame loop to the on-device engine, and the skeleton overlay.
const EDGES = [[5,6],[5,7],[7,9],[6,8],[8,10],[5,11],[6,12],[11,12],[11,13],[13,15],[12,14],[14,16],[0,5],[0,6],
  [15,19],[19,17],[15,17],[16,22],[22,20],[16,20]];   // feet (precision mode, COCO-WholeBody)
const JOINT_FOR = {             // exercise/test -> [left triple, right triple] (a, vertex, c)
  knee: [[11,13,15],[12,14,16]],
  hip: [[5,11,13],[6,12,14]],
  shoulder: [[11,5,7],[12,6,8]],
  elbow: [[5,7,9],[6,8,10]],
};
const REGION_JOINT = { squat: "knee", sit_to_stand: "knee", knee_extension: "knee", shoulder_flexion: "shoulder",
  shoulder_abduction: "shoulder", elbow_curl: "elbow", hip_abduction: "hip", marching: "hip",
  rom_shoulder_flexion: "shoulder", rom_shoulder_abduction: "shoulder", rom_knee_flexion: "knee",
  chair_stand_30s: "knee", heel_raise: "ankle" };

export class Stage {
  constructor({ video, overlay, onResult, onError }) {
    this.video = video;
    this.overlay = overlay;
    this.octx = overlay.getContext("2d");
    this.crop = null;
    this.canvas = document.createElement("canvas");
    this.size = 192;                 // 288 in precision mode (RTMPose needs more pixels)
    this.canvas.width = this.canvas.height = this.size;
    this.cctx = this.canvas.getContext("2d", { willReadFrequently: true });
    this.onResult = onResult;
    this.onError = onError;
    this.running = false;
    this.inflight = false;
    this.source = null;
    this.mirror = true;
    this.privacy = false;
    this.showCrop = false;
    this.focus = null;       // exercise/test id whose joint gets the angle arc
    this.last = null;
    this.errors = 0;
    new ResizeObserver(() => this.draw()).observe(overlay.parentElement);
  }

  async useCamera() {
    this.stopSource();
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 }, frameRate: { ideal: 30 } }, audio: false });
    this.video.srcObject = stream;
    this.video.loop = false;
    this.source = "camera";
    this.mirror = true;
    await this.video.play();
    this.start();
  }

  async useFile(file) { return this.useUrl(URL.createObjectURL(file)); }

  async useUrl(url) {
    this.stopSource();
    this.video.srcObject = null;
    this.video.src = url;
    this.video.loop = true;
    this.video.muted = true;
    this.source = "file";
    this.mirror = false;
    await this.video.play();
    this.start();
  }

  stopSource() {
    const s = this.video.srcObject;
    if (s) s.getTracks().forEach(t => t.stop());
    this.video.srcObject = null;
    if (this.video.src) { if (this.video.src.startsWith("blob:")) URL.revokeObjectURL(this.video.src); this.video.removeAttribute("src"); }
    this.running = false;
    this.crop = null;
    this.last = null;
    this.draw();
  }

  start() {
    if (this.running) return;
    this.running = true;
    const tick = () => {
      if (!this.running) return;
      this.send();
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  send() {
    const v = this.video;
    if (this.inflight || v.readyState < 2 || !v.videoWidth) return;
    const w = v.videoWidth, h = v.videoHeight;
    if (!this.crop) { const size = Math.max(w, h); this.crop = { x: (w - size) / 2, y: (h - size) / 2, size }; }
    const S = this.size;
    if (this.canvas.width !== S) this.canvas.width = this.canvas.height = S;
    const c = this.crop, k = S / c.size;
    this.cctx.fillStyle = "#000";
    this.cctx.fillRect(0, 0, S, S);
    const sx0 = Math.max(0, c.x), sy0 = Math.max(0, c.y);
    const sx1 = Math.min(w, c.x + c.size), sy1 = Math.min(h, c.y + c.size);
    if (sx1 > sx0 && sy1 > sy0) {
      this.cctx.drawImage(v, sx0, sy0, sx1 - sx0, sy1 - sy0, (sx0 - c.x) * k, (sy0 - c.y) * k, (sx1 - sx0) * k, (sy1 - sy0) * k);
    }
    const px = this.cctx.getImageData(0, 0, S, S).data;
    const t = this.source === "file" ? v.currentTime : performance.now() / 1000;
    const q = `x=${c.x.toFixed(1)}&y=${c.y.toFixed(1)}&size=${c.size.toFixed(1)}&w=${w}&h=${h}&t=${t.toFixed(4)}`;
    this.inflight = true;
    const sent = { ...c };
    fetch(`/api/frame?${q}`, { method: "POST", body: px, headers: { "Content-Type": "application/octet-stream" } })
      .then(r => r.json())
      .then(res => {
        if (res.error) throw new Error(res.error);
        this.errors = 0;
        this.crop = res.crop;
        this.last = { ...res, w, h, sent };
        this.draw();
        this.onResult?.(res);
      })
      .catch(e => { if (++this.errors === 5) this.onError?.(e); })
      .finally(() => { this.inflight = false; });
  }

  // --- drawing -------------------------------------------------------------
  layout() {
    const box = this.overlay.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    if (this.overlay.width !== Math.round(box.width * dpr) || this.overlay.height !== Math.round(box.height * dpr)) {
      this.overlay.width = Math.round(box.width * dpr);
      this.overlay.height = Math.round(box.height * dpr);
    }
    const vw = this.video.videoWidth || 16, vh = this.video.videoHeight || 9;
    const s = Math.min(box.width / vw, box.height / vh);
    return { dpr, s, ox: (box.width - vw * s) / 2, oy: (box.height - vh * s) / 2, bw: box.width, bh: box.height, vw };
  }

  draw() {
    const g = this.octx, L = this.layout();
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.clearRect(0, 0, this.overlay.width, this.overlay.height);
    g.setTransform(L.dpr, 0, 0, L.dpr, 0, 0);
    if (this.privacy) {
      g.fillStyle = "#0b1220";
      g.fillRect(0, 0, L.bw, L.bh);
      g.strokeStyle = "rgba(148,163,184,.08)";
      g.lineWidth = 1;
      for (let x = 0; x < L.bw; x += 32) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, L.bh); g.stroke(); }
      for (let y = 0; y < L.bh; y += 32) { g.beginPath(); g.moveTo(0, y); g.lineTo(L.bw, y); g.stroke(); }
    }
    const r = this.last;
    if (!r) return;
    const P = (x, y) => {
      const px = L.ox + x * L.s;
      return [this.mirror ? L.bw - px : px, L.oy + y * L.s];
    };
    const k = r.kps;
    if (this.showCrop && r.sent) {
      const [a, b] = P(r.sent.x, r.sent.y), [c, d] = P(r.sent.x + r.sent.size, r.sent.y + r.sent.size);
      g.strokeStyle = "rgba(250,204,21,.6)"; g.setLineDash([6, 6]); g.lineWidth = 1.5;
      g.strokeRect(Math.min(a, c), b, Math.abs(c - a), d - b); g.setLineDash([]);
    }
    g.lineCap = "round";
    for (const [i, j] of EDGES) {
      if (k[i][2] < 0.25 || k[j][2] < 0.25) continue;
      const [x1, y1] = P(k[i][0], k[i][1]), [x2, y2] = P(k[j][0], k[j][1]);
      g.strokeStyle = "rgba(45,212,191,.35)"; g.lineWidth = 10;
      g.beginPath(); g.moveTo(x1, y1); g.lineTo(x2, y2); g.stroke();
      g.strokeStyle = "#5eead4"; g.lineWidth = 3.5;
      g.beginPath(); g.moveTo(x1, y1); g.lineTo(x2, y2); g.stroke();
    }
    for (let i = 5; i < k.length; i++) {
      if (k[i][2] < 0.25) continue;
      const [x, y] = P(k[i][0], k[i][1]);
      g.fillStyle = "#f8fafc"; g.beginPath(); g.arc(x, y, 5, 0, 7); g.fill();
      g.strokeStyle = "#0f766e"; g.lineWidth = 2; g.stroke();
    }
    if (k[0][2] > 0.3) {
      const [x, y] = P(k[0][0], k[0][1]);
      g.fillStyle = "rgba(248,250,252,.9)"; g.beginPath(); g.arc(x, y, 7, 0, 7); g.fill();
    }
    this.drawAngles(g, P, k, r);
  }

  drawAngles(g, P, k, r) {
    const joint = REGION_JOINT[this.focus];
    if (!joint) return;
    if (joint === "ankle") return this.drawFeet(g, P, k, r);
    const angles = r.angles || {};
    const keyFor = { knee: "knee_flex", hip: this.focus === "hip_abduction" ? "hip_abd" : "hip_flex",
      shoulder: "shoulder", elbow: "elbow_flex" }[joint];
    JOINT_FOR[joint].forEach((tri, idx) => {
      const [a, b, c] = tri;
      if (k[a][2] < 0.3 || k[b][2] < 0.3 || k[c][2] < 0.3) return;
      const val = angles[`${keyFor}_${idx === 0 ? "l" : "r"}`];
      if (val == null) return;
      const [bx, by] = P(k[b][0], k[b][1]);
      const [ax, ay] = P(k[a][0], k[a][1]);
      const [cx, cy] = P(k[c][0], k[c][1]);
      let a1 = Math.atan2(ay - by, ax - bx), a2 = Math.atan2(cy - by, cx - bx);
      let d = a2 - a1;
      while (d > Math.PI) d -= 2 * Math.PI;
      while (d < -Math.PI) d += 2 * Math.PI;
      g.fillStyle = "rgba(251,191,36,.18)"; g.strokeStyle = "#fbbf24"; g.lineWidth = 3;
      g.beginPath(); g.moveTo(bx, by); g.arc(bx, by, 34, a1, a1 + d, d < 0); g.closePath(); g.fill();
      g.beginPath(); g.arc(bx, by, 34, a1, a1 + d, d < 0); g.stroke();
      const mid = a1 + d / 2, tx = bx - Math.cos(mid) * 58, ty = by - Math.sin(mid) * 58;
      const label = `${Math.round(val)}°`;
      g.font = "700 18px 'Segoe UI Variable', system-ui, sans-serif";
      const w = g.measureText(label).width + 14;
      g.fillStyle = "rgba(15,23,42,.85)"; roundRect(g, tx - w / 2, ty - 15, w, 30, 8); g.fill();
      g.fillStyle = "#fde68a"; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(label, tx, ty + 1);
    });
  }
}

Stage.prototype.drawFeet = function (g, P, k, r) {
  [["l", 19, 17], ["r", 22, 20]].forEach(([s, heel, toe]) => {
    if (!k[heel] || k[heel][2] < 0.3 || k[toe][2] < 0.3) return;
    const v = r.angles?.[`foot_pitch_${s}`];
    if (v == null) return;
    const [hx, hy] = P(k[heel][0], k[heel][1]);
    const label = `${Math.round(v)}°`;
    g.font = "700 16px 'Segoe UI Variable', system-ui, sans-serif";
    const w = g.measureText(label).width + 12;
    g.fillStyle = "rgba(15,23,42,.85)"; roundRect(g, hx - w / 2, hy + 10, w, 26, 7); g.fill();
    g.fillStyle = "#fde68a"; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(label, hx, hy + 23);
  });
};

function roundRect(g, x, y, w, h, r) {
  g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath();
}
