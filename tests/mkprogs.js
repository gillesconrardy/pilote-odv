global.ODV = require('../src/core.js'); const G = require('../src/odvgen.js'); const fs = require('fs');
const files = process.argv[2].split(','), loop = process.argv[3]==='1', homing = process.argv[4]==='1';
const pl = files.map(f=>({name:f, src:fs.readFileSync(f,'utf8')}));
const tl = G.buildTimeline(pl); const tpl = fs.readFileSync('../src/runtime.py','utf8');
const out = {}; for (let v=1; v<=4; v++) out[v] = G.buildProgram(tpl, tl, v, {loop, homing, gen: +(process.argv[5]||7), names: pl.map(p=>p.name), smode: +(process.env.SMODE||0)});
fs.writeFileSync('progs.json', JSON.stringify(out)); fs.writeFileSync('tl.json', JSON.stringify(tl));
fs.writeFileSync('sample_vehicle1.py', out[1]);
console.log('total', tl.total, 'bounds', tl.bounds, 'chars', out[1].length);
