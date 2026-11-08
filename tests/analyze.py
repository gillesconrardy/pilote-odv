import json, bisect
d = json.load(open('harness_out.json')); tl = json.load(open('tl.json'))
import math
def posAt(i, v):
    t0 = 0; segs = tl['segs'][i]
    for s in segs:
        if v < t0 + s['dur'] or s is segs[-1]:
            f = min(1, max(0, (v - t0) / s['dur']))
            if s['k'] == 1: return (s['x0'] + (s['x1']-s['x0'])*f, s['y0'] + (s['y1']-s['y0'])*f)
            if s['k'] == 2:
                a = math.radians(s['a0'] + s['rot']*f); return (s['cx'] + s['r']*math.sin(a), s['cy'] + s['r']*math.cos(a))
            return (s['x0'], s['y0'])
        t0 += s['dur']
R = {int(k): [r for r in v if not isinstance(r[0], str)] for k, v in d['rec'].items()}   # sans les entrées 'stopped' / 'lights'
m = R[4]; mt = [r[0] for r in m]
def mv(t):
    k = bisect.bisect_left(mt, t); k = min(max(k, 1), len(m)-1)
    a, b = m[k-1], m[k]
    if b[0] == a[0]: return a[1]
    return a[1] + (b[1]-a[1]) * (t - a[0]) / (b[0]-a[0])
print('sender prints:', [o[1] for o in d['out'] if not o[1].startswith('V4 ST')])
sts = [o for o in d['out'] if o[1].startswith('V4 ST')]
for t in (2500, 6000, 10000, 11500, 14000, 17500, 22000, 29000, 33000):
    s = min(sts, key=lambda o: abs(o[0]-t)); print('  status @%5d' % t, s[1])
for vid in (1, 2, 3):
    rr = [r for r in R[vid] if 2000 < r[0] < 33900]
    errs = [abs(r[1] - mv(r[0])) for r in rr]
    poserr = max(max(abs(r[2]-posAt(vid-1, r[1])[0]), abs(r[3]-posAt(vid-1, r[1])[1])) for r in rr)
    print('V%d: samples %d, |v - v_master| max %.0f ms, mean %.1f ms, pos vs timeline max %.3f' % (vid, len(rr), max(errs), sum(errs)/len(errs), poserr))
for vid in (1, 2, 3, 4):
    rr = R[vid]
    def at(t): return min(rr, key=lambda r: abs(r[0]-t))
    print('V%d v@ 9500=%d 11500=%d (pause const: %s)  v@29000=%d pos=(%.2f,%.2f)  v@32500=%d  last rec t=%d' % (
        vid, at(10500)[1], at(12500)[1], at(10500)[1] == at(12500)[1], at(29000)[1], at(29000)[2], at(29000)[3], at(32500)[1], rr[-1][0]))
print('stopped:', d['stopped'])
