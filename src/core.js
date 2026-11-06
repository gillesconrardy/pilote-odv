// ===== ODV simulation core: faithful port of MultiVehicleController (move / move_circ / wait) =====
const ODV = (() => {
  const GEAR = 80, VMAX = 1400;

  function parseArgs(a) {
    const args = [], kw = {};
    for (let p of a.split(',')) {
      p = p.trim();
      if (!p) continue;
      const eq = p.indexOf('=');
      if (eq > 0) kw[p.slice(0, eq).trim()] = parseFloat(p.slice(eq + 1));
      else if (p[0] === '"' || p[0] === "'") args.push(p.replace(/["']/g, ''));
      else {
        const v = parseFloat(p);
        if (isNaN(v)) throw new Error('valeur non numérique : ' + p);
        args.push(v);
      }
    }
    return { args, kw };
  }

  // Returns { prog: [{ln, cmd, args, kw}], warnings: [] }
  function parse(src, nVeh) {
    const items = [], warnings = [];
    src.split('\n').forEach((raw, i) => {
      const s = raw.split('#')[0].replace(/\s+$/, '');
      if (!s.trim()) return;
      items.push({ ln: i + 1, ind: s.length - s.trimStart().length, s: s.trim() });
    });
    function block(idx, base) {
      let out = [];
      while (idx < items.length) {
        const { ln, ind, s } = items[idx];
        if (ind < base) break;
        const mFor = s.match(/^for\s+\w+\s+in\s+range\(\s*(\d+)\s*\)\s*:$/);
        const mWhile = /^while\s+True\s*:$/.test(s);
        if (mFor || mWhile) {
          const reps = mFor ? parseInt(mFor[1]) : 1;
          const innerBase = idx + 1 < items.length ? items[idx + 1].ind : ind + 1;
          if (innerBase <= ind) { idx++; continue; }
          const r = block(idx + 1, innerBase);
          for (let k = 0; k < reps; k++) out = out.concat(r.out);
          idx = r.idx;
          continue;
        }
        const m = s.match(/^mvc\.(move_circ|move|wait_sync_ms|wait_ms)\((.*)\)$/);
        if (m) {
          try {
            const { args, kw } = parseArgs(m[2]);
            const cmd = m[1];
            if (cmd === 'move' && args.length !== nVeh * 2)
              warnings.push({ ln, msg: `move : ${args.length} valeurs au lieu de ${nVeh * 2}, ligne ignorée` });
            else if (cmd === 'move_circ' && args.length !== 3 + nVeh)
              warnings.push({ ln, msg: `move_circ : ${args.length - 3} angles au lieu de ${nVeh}, ligne ignorée` });
            else {
              const sp = kw.speed ?? 100;
              if (sp < 1 || sp > 100) warnings.push({ ln, msg: `speed=${sp} hors 1..100 : le robot lèverait une erreur` });
              out.push({ ln, cmd, args, kw });
            }
          } catch (e) { warnings.push({ ln, msg: e.message }); }
        } else if (!/^(mvc\.homing|mvc\.init_20sec_sync_process|pass)\b/.test(s)) {
          warnings.push({ ln, msg: 'ligne non simulée : ' + s.slice(0, 60) });
        }
        idx++;
      }
      return { out, idx };
    }
    const prog = items.length ? block(0, items[0].ind).out : [];
    return { prog, warnings };
  }

  // frames: Float64Array rows of [t, x1,y1,...,xN,yN, ln]
  function simulate(prog, start) {
    const N = start.length, W = 2 + 2 * N;
    const cx = [0, ...start.map(p => p[0] * GEAR)], cy = [0, ...start.map(p => p[1] * GEAR)];
    let t = 0;
    const rows = [], cmds = [];
    const snap = (ln) => {
      const r = [t];
      for (let i = 1; i <= N; i++) r.push(cx[i] / GEAR, cy[i] / GEAR);
      r.push(ln);
      rows.push(r);
    };
    snap(0);
    for (const c of prog) {
      const t0 = t, sp = c.kw.speed ?? 100, velo = VMAX * sp * 0.01;
      if (c.cmd === 'move') {
        const tx = [0], ty = [0];
        for (let i = 0; i < 2 * N; i += 2) { tx.push(c.args[i] * GEAR); ty.push(c.args[i + 1] * GEAR); }
        const xd = [0], yd = [0];
        let md = 0;
        for (let i = 1; i <= N; i++) {
          xd.push(Math.abs(tx[i] - cx[i])); yd.push(Math.abs(ty[i] - cy[i]));
          md = Math.max(md, xd[i], yd[i]);
        }
        const time = md / velo * 1000;
        if (time > 4) {
          let steps = Math.trunc(time * 0.25);
          const xs = xd.map(d => d / steps), ys = yd.map(d => d / steps);
          let n = steps;
          while (n > 0) {
            for (let i = 1; i <= N; i++) {
              if (cx[i] < tx[i]) cx[i] += xs[i]; else if (cx[i] > tx[i]) cx[i] -= xs[i];
              if (cy[i] < ty[i]) cy[i] += ys[i]; else if (cy[i] > ty[i]) cy[i] -= ys[i];
            }
            n--;
            t = t0 + time - 4 * n;
            snap(c.ln);
          }
          t = t0 + time;
        }
      } else if (c.cmd === 'move_circ') {
        const [radius, dirS, rot, ...sa] = c.args;
        const d = String(dirS).toUpperCase() === 'CW' ? 1 : (String(dirS).toUpperCase() === 'CCW' ? 2 : (dirS <= 1 ? 1 : 2));
        const time = 2 * Math.PI * radius * rot / 360 * GEAR / velo * 1000;
        const steps = Math.trunc(time * 0.25);
        const sstep = rot / steps;
        let s = 0;
        const st = [0, ...sa], x0 = [0], y0 = [0];
        const rad = a => a * Math.PI / 180;
        for (let i = 1; i <= N; i++) {
          const a = rad(st[i] + 180 * (d - 1));
          x0.push(cx[i] - radius * GEAR * Math.sin(a));
          y0.push(cy[i] - radius * GEAR * Math.cos(a));
        }
        let n = steps;
        while (n > 0) {
          for (let i = 1; i <= N; i++) {
            const a = rad(s + st[i] + 180 * (d - 1));
            cx[i] = radius * GEAR * Math.sin(a) + x0[i];
            cy[i] = radius * GEAR * Math.cos(a) + y0[i];
          }
          s = d === 1 ? s + sstep : s - sstep;
          n--;
          t = t0 + time - 4 * n;
          snap(c.ln);
        }
        t = t0 + time;
      } else {
        t += c.args[0];
        snap(c.ln);
      }
      cmds.push({ ln: c.ln, t0, t1: t });
    }
    const frames = new Float64Array(rows.length * W);
    rows.forEach((r, k) => frames.set(r, k * W));
    return { frames, W, N, count: rows.length, duration: t, cmds };
  }

  // Overlap of square footprints. Returns grouped events with max penetration.
  function collisions(sim, fp) {
    const { frames, W, N, count } = sim;
    const groups = new Map();
    for (let k = 0; k < count; k++) {
      const o = k * W;
      for (let i = 0; i < N; i++) for (let j = i + 1; j < N; j++) {
        const dx = Math.abs(frames[o + 1 + 2 * i] - frames[o + 1 + 2 * j]);
        const dy = Math.abs(frames[o + 2 + 2 * i] - frames[o + 2 + 2 * j]);
        const pen = Math.min(fp - dx, fp - dy);
        if (pen > 0.05) {
          const ln = frames[o + W - 1], key = ln + ':' + i + ':' + j;
          const g = groups.get(key);
          if (!g) groups.set(key, { ln, i: i + 1, j: j + 1, pen, t: frames[o], tStart: frames[o] });
          else if (pen > g.pen) { g.pen = pen; g.t = frames[o]; }
        }
      }
    }
    return [...groups.values()].sort((a, b) => a.t - b.t);
  }

  return { parse, simulate, collisions };
})();
if (typeof module !== 'undefined') module.exports = ODV;
