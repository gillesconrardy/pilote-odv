// ===== Pilote ODV : construit la ligne du temps et le programme Pybricks de chaque véhicule =====
// Dépend de ODV (core.js) pour l'analyse des commandes mvc.*
const ODVGEN = (() => {
  const GEAR = 80, VMAX = 1400, N = 4;
  const HOME = [[30, 0], [20, 0], [10, 0], [0, 0]];

  function prepare(src) {
    const lines = src.replace(/\r/g, '').split('\n');
    const k = lines.findIndex(l => /^mvc\.init_20sec_sync_process\(\)/.test(l.trim()) && !/^\s/.test(l));
    return (k >= 0 ? lines.map((l, i) => i <= k ? '' : l) : lines).join('\n');
  }

  // playlist: [{name, src}] -> { segs: [[{k,dur,a..}] x N], bounds, total, names, warnings, endPos }
  function buildTimeline(playlist, start = HOME) {
    const cur = start.map(p => [p[0], p[1]]);
    const segs = [[], [], [], []];
    const warnings = [];
    let T = 0;            // exact time (ms, float)
    let Tr = 0;           // rounded time already emitted
    const bounds = [];
    const push = (dur, perVehicle) => {
      const t1 = T + dur, d = Math.round(t1) - Tr;
      T = t1;
      if (d <= 0) return;
      for (let i = 0; i < N; i++) segs[i].push({ ...perVehicle(i), dur: d });
      Tr += d;
    };
    playlist.forEach((ch, ci) => {
      bounds.push(Tr);
      const { prog, warnings: w } = ODV.parse(prepare(ch.src), N);
      w.forEach(x => warnings.push({ chor: ci, ...x }));
      const s0 = cur.map(p => p.slice());
      for (const c of prog) {
        const sp = c.kw.speed ?? 100, velo = VMAX * sp * 0.01;
        if (c.cmd === 'move') {
          const tg = [];
          for (let i = 0; i < N; i++) tg.push([c.args[2 * i], c.args[2 * i + 1]]);
          let md = 0;
          for (let i = 0; i < N; i++) md = Math.max(md, Math.abs(tg[i][0] - cur[i][0]) * GEAR, Math.abs(tg[i][1] - cur[i][1]) * GEAR);
          const time = md / velo * 1000;
          if (time <= 4) continue;
          const from = cur.map(p => p.slice());
          push(time, i => ({ k: 1, x0: from[i][0], y0: from[i][1], x1: tg[i][0], y1: tg[i][1] }));
          for (let i = 0; i < N; i++) cur[i] = tg[i].slice();
        } else if (c.cmd === 'move_circ') {
          const [radius, dirS, rot, ...sa] = c.args;
          const ds = String(dirS).toUpperCase();
          const d = ds === 'CW' ? 1 : ds === 'CCW' ? 2 : (dirS <= 1 ? 1 : 2);
          const time = 2 * Math.PI * radius * rot / 360 * GEAR / velo * 1000;
          const steps = Math.trunc(time * 0.25);
          if (steps < 1) continue;
          const sstep = rot / steps;
          const rotEff = (d === 1 ? 1 : -1) * (steps - 1) * sstep;   // le code d'origine s'arrête un pas avant
          const rad = a => a * Math.PI / 180;
          const arcs = [];
          for (let i = 0; i < N; i++) {
            const a0 = sa[i] + 180 * (d - 1);
            const cx = cur[i][0] - radius * Math.sin(rad(a0)), cy = cur[i][1] - radius * Math.cos(rad(a0));
            arcs.push({ cx, cy, a0 });
          }
          // découpe si la rotation dépasse ce que l'enregistrement peut coder (±3000°)
          const parts = Math.max(1, Math.ceil(Math.abs(rotEff) / 3000));
          for (let p = 0; p < parts; p++) {
            push(time / parts, i => ({ k: 2, cx: arcs[i].cx, cy: arcs[i].cy, r: radius,
              a0: arcs[i].a0 + rotEff * p / parts, rot: rotEff / parts }));
          }
          for (let i = 0; i < N; i++) {
            const a = rad(arcs[i].a0 + rotEff);
            cur[i] = [arcs[i].cx + radius * Math.sin(a), arcs[i].cy + radius * Math.cos(a)];
          }
        } else {
          let ms = c.args[0];
          const at = cur.map(p => p.slice());
          while (ms > 0) { const m = Math.min(ms, 60000); push(m, i => ({ k: 0, x0: at[i][0], y0: at[i][1] })); ms -= m; }
        }
      }
      const off = cur.map((p, i) => Math.max(Math.abs(p[0] - s0[i][0]), Math.abs(p[1] - s0[i][1])));
      if (Math.max(...off) > 0.05) warnings.push({ chor: ci, ln: 0, msg: 'ne revient pas à sa position de départ (écart ' + Math.max(...off).toFixed(2) + ' pas)' });
    });
    bounds.push(Tr);
    return { segs, bounds, total: Tr, warnings, start: start.map(p => p.slice()) };
  }

  function i16(v, what) {
    const r = Math.round(v);
    if (r < -32768 || r > 32767) throw new Error('valeur hors limites (' + what + ') : ' + v);
    return r & 0xffff;
  }
  function encode(segs) {
    const b = new Uint8Array(segs.length * 14);
    segs.forEach((s, n) => {
      const o = n * 14, put = (k, v) => { b[o + k] = v & 255; b[o + k + 1] = (v >> 8) & 255; };
      b[o] = s.k;
      if (s.dur > 65535) throw new Error('segment trop long');
      put(2, s.dur);
      if (s.k === 1) { put(4, i16(s.x0 * 100, 'x')); put(6, i16(s.y0 * 100, 'y')); put(8, i16(s.x1 * 100, 'x')); put(10, i16(s.y1 * 100, 'y')); }
      else if (s.k === 2) {
        let a0 = ((s.a0 % 360) + 540) % 360 - 180;
        put(4, i16(s.cx * 100, 'cx')); put(6, i16(s.cy * 100, 'cy')); put(8, i16(s.r * 100, 'r'));
        put(10, i16(a0 * 10, 'a0')); put(12, i16(s.rot * 10, 'rot'));
      } else { put(4, i16(s.x0 * 100, 'x')); put(6, i16(s.y0 * 100, 'y')); }
    });
    return b;
  }
  function pyBytes(b) {
    let s = "b'";
    for (const v of b) s += '\\x' + v.toString(16).padStart(2, '0');
    return s + "'";
  }

  // enleve les commentaires et les lignes vides d'un programme Python (sans toucher aux chaines)
  function stripPy(src) {
    return src.split('\n').map(l => {
      if (/^\s*#/.test(l)) return '';
      let q = null;
      for (let k = 0; k < l.length; k++) {
        const c = l[k];
        if (q) { if (c === q) q = null; }
        else if (c === '"' || c === "'") q = c;
        else if (c === '#') return l.slice(0, k).replace(/\s+$/, '');
      }
      return l.replace(/\s+$/, '');
    }).filter(l => l.trim()).join('\n') + '\n';
  }
  function buildProgram(template, tl, vid, opts) {
    const i = vid - 1;
    const data = encode(tl.segs[i]);
    const names = (opts.names || []).join(', ').replace(/[^\x20-\x7e]/g, c => ({ 'é': 'e', 'è': 'e', 'ê': 'e', 'à': 'a', 'ç': 'c', 'ô': 'o', 'É': 'E', '·': '-', '×': 'x' }[c] || '?'));
    // les jeux (poursuite, billes) sont retires de l'appli : on enleve leur code pour que le programme tienne dans le hub
    if (!opts.games) template = template.replace(/^#\[JEUX\n[\s\S]*?^#\]JEUX\n/gm, '');
    // les commentaires et lignes vides ne servent a rien sur le hub
    template = stripPy(template);
    return template
      .replace(/%VID%/g, String(vid))
      .replace('%GEN%', String(opts.gen || 0))
      .replace('%NAMES%', names)
      .replace('%HOMING%', opts.homing ? 'True' : 'False')
      .replace('%LOOP%', opts.loop ? 'True' : 'False')
      .replace('%HX%', String(+tl.start[i][0].toFixed(2)))
      .replace('%HY%', String(+tl.start[i][1].toFixed(2)))
      .replace('%TOTAL%', String(tl.total))
      .replace('%NSEG%', String(tl.segs[i].length))
      .replace('%BOUNDS%', '(' + tl.bounds.join(', ') + (tl.bounds.length === 1 ? ',' : '') + ')')
      .replace('%SMODE%', String(vid === 4 ? (opts.smode || 0) : 0))
      .replace('%MASK%', '(' + (vid === 4 && opts.smode ? sonarMask(tl) : []).join(', ') + ')')
      .replace('%DATA%', pyBytes(data));
  }

  // Position (pour l'aperçu) au temps v à partir des segments
  // intervalles (ms) ou un autre vehicule passe devant le capteur du vehicule 4 (tourne vers +Y), elargis de 300 ms
  function sonarMask(tl) {
    const out = [], step = 50, pad = 300; let on = -1;
    for (let v = 0; v <= tl.total + step; v += step) {
      const t = Math.min(v, tl.total), p4 = posAt(tl, 3, t);
      let m = false;
      for (let k = 0; k < 3; k++) { const q = posAt(tl, k, t); if (Math.abs(q[0] - p4[0]) < 12 && q[1] > p4[1] + 0.5 && (q[1] - p4[1] - 10) * 12.25 < 350) m = true; }
      if (m && on < 0) on = t;
      if ((!m || v > tl.total) && on >= 0) { const a = Math.max(0, on - pad), b = Math.min(tl.total, t + pad);
        if (out.length && a <= out[out.length - 1]) out[out.length - 1] = b; else out.push(a, b); on = -1; }
    }
    return out.map(x => Math.round(x));
  }
  function posAt(tl, i, v) {
    const segs = tl.segs[i];
    let t0 = 0;
    for (const s of segs) {
      if (v < t0 + s.dur || s === segs[segs.length - 1]) {
        const f = Math.min(1, Math.max(0, (v - t0) / s.dur));
        if (s.k === 1) return [s.x0 + (s.x1 - s.x0) * f, s.y0 + (s.y1 - s.y0) * f];
        if (s.k === 2) { const a = (s.a0 + s.rot * f) * Math.PI / 180; return [s.cx + s.r * Math.sin(a), s.cy + s.r * Math.cos(a)]; }
        return [s.x0, s.y0];
      }
      t0 += s.dur;
    }
    return tl.start[i];
  }

  // Programme multi-fichier Pybricks : taille (u32 LE) + nom + \0 + mpy
  function multiMpy(mpy) {
    const name = new TextEncoder().encode('__main__');
    const out = new Uint8Array(4 + name.length + 1 + mpy.length);
    new DataView(out.buffer).setUint32(0, mpy.length, true);
    out.set(name, 4); out[4 + name.length] = 0; out.set(mpy, 5 + name.length);
    return out;
  }

  return { HOME, buildTimeline, buildProgram, encode, posAt, multiMpy, prepare, sonarMask };
})();
if (typeof module !== 'undefined') module.exports = ODVGEN;
