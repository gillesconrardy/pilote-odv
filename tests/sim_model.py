"""Faithful model of MultiVehicleController.move / move_circ / wait_sync_ms.
Produces per-4ms-step positions (in grid pitch) for 4 vehicles."""
import math, re, sys

GEAR = 80
VMAX = 1400
N = 4


def parse(src):
    """Return list of (lineno, cmd, args, kwargs) with for/while expanded once (while True -> once)."""
    lines = src.split('\n')
    items = []
    for i, raw in enumerate(lines):
        s = raw.split('#')[0].rstrip()
        if not s.strip():
            continue
        ind = len(s) - len(s.lstrip())
        items.append((i + 1, ind, s.strip()))

    def block(idx, base):
        out = []
        while idx < len(items):
            ln, ind, s = items[idx]
            if ind < base:
                break
            m = re.match(r'for\s+\w+\s+in\s+range\((\d+)\)\s*:', s)
            if m or re.match(r'while\s+True\s*:', s):
                reps = int(m.group(1)) if m else 1
                inner_base = items[idx + 1][1] if idx + 1 < len(items) else ind + 1
                body, idx = block(idx + 1, inner_base)
                out += body * reps
                continue
            m = re.match(r'mvc\.(move_circ|move|wait_sync_ms|wait_ms)\((.*)\)\s*$', s)
            if m:
                cmd, a = m.group(1), m.group(2)
                args, kw = [], {}
                for p in a.split(','):
                    p = p.strip()
                    if not p:
                        continue
                    if '=' in p:
                        k, v = p.split('=')
                        kw[k.strip()] = float(v)
                    elif p[0] in '"\'':
                        args.append(p.strip('"\''))
                    else:
                        args.append(float(p))
                out.append((ln, cmd, args, kw))
            idx += 1
        return out, idx

    return block(0, items[0][1] if items else 0)[0]


class Sim:
    def __init__(self, start):
        self.cx = [0.0] + [p[0] * GEAR for p in start]
        self.cy = [0.0] + [p[1] * GEAR for p in start]
        self.t = 0.0
        self.frames = []  # (t_ms, [(x,y)...], lineno)

    def snap(self, ln):
        self.frames.append((self.t, [(self.cx[i] / GEAR, self.cy[i] / GEAR) for i in range(1, N + 1)], ln))

    def move(self, targets, speed=100, ln=0):
        tx = [0] + [targets[i] * GEAR for i in range(0, 2 * N, 2)]
        ty = [0] + [targets[i] * GEAR for i in range(1, 2 * N, 2)]
        xd = [0] + [abs(tx[i] - self.cx[i]) for i in range(1, N + 1)]
        yd = [0] + [abs(ty[i] - self.cy[i]) for i in range(1, N + 1)]
        velo = VMAX * speed * 0.01
        time = max(xd[1:] + yd[1:]) / velo * 1000
        if time <= 4:
            return
        t0 = self.t
        steps = int(time * 0.25)
        xs = [d / steps for d in xd]
        ys = [d / steps for d in yd]
        n = steps
        while n > 0:
            for i in range(1, N + 1):
                if self.cx[i] < tx[i]: self.cx[i] += xs[i]
                elif self.cx[i] > tx[i]: self.cx[i] -= xs[i]
                if self.cy[i] < ty[i]: self.cy[i] += ys[i]
                elif self.cy[i] > ty[i]: self.cy[i] -= ys[i]
            n -= 1
            self.t = t0 + time - 4 * n
            self.snap(ln)
        self.t = t0 + time

    def move_circ(self, radius, direction, rot, starts, speed=100, ln=0):
        d = 1 if str(direction).upper() == 'CW' else 2
        velo = VMAX * speed * 0.01
        time = 2 * math.pi * radius * rot / 360 * GEAR / velo * 1000
        t0 = self.t
        steps = int(time * 0.25)
        sstep = rot / steps
        s = 0
        st = [0] + list(starts)
        x0 = [0] * (N + 1); y0 = [0] * (N + 1)
        for i in range(1, N + 1):
            a = math.radians(st[i] + 180 * (d - 1))
            x0[i] = self.cx[i] - radius * GEAR * math.sin(a)
            y0[i] = self.cy[i] - radius * GEAR * math.cos(a)
        n = steps
        while n > 0:
            for i in range(1, N + 1):
                a = math.radians(s + st[i] + 180 * (d - 1))
                self.cx[i] = radius * GEAR * math.sin(a) + x0[i]
                self.cy[i] = radius * GEAR * math.cos(a) + y0[i]
            s = s + sstep if d == 1 else s - sstep
            n -= 1
            self.t = t0 + time - 4 * n
            self.snap(ln)
        self.t = t0 + time

    def wait(self, ms, ln=0):
        self.t += ms
        self.snap(ln)

    def run(self, prog):
        self.snap(0)
        for ln, cmd, a, kw in prog:
            sp = kw.get('speed', 100)
            if cmd == 'move':
                self.move(a, sp, ln)
            elif cmd == 'move_circ':
                self.move_circ(a[0], a[1], a[2], a[3:], sp, ln)
            else:
                self.wait(a[0], ln)
        return self


def collisions(frames, fp=10.0, tol=0.3):
    """Square footprint fp; overlap when |dx|<fp-tol and |dy|<fp-tol."""
    out = []
    lim = fp - tol
    for t, p, ln in frames:
        for i in range(4):
            for j in range(i + 1, 4):
                dx = abs(p[i][0] - p[j][0]); dy = abs(p[i][1] - p[j][1])
                if dx < lim and dy < lim:
                    out.append((t, ln, i + 1, j + 1, round(dx, 2), round(dy, 2)))
    return out


def summarize(col):
    # group consecutive by (ln,i,j)
    seen = {}
    for t, ln, i, j, dx, dy in col:
        k = (ln, i, j)
        pen = min(10 - dx, 10 - dy)
        if k not in seen or pen > seen[k][1]:
            seen[k] = (t, pen, dx, dy)
    return seen


if __name__ == '__main__':
    src = open(sys.argv[1]).read()
    start_line = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    src = '\n'.join(src.split('\n')[start_line - 1:])
    prog = parse(src)
    s = Sim([(30, 0), (20, 0), (10, 0), (0, 0)]).run(prog)
    print('commands', len(prog), 'duration ms', round(s.t))
    fp = float(sys.argv[3]) if len(sys.argv) > 3 else 10
    sm = summarize(collisions(s.frames, fp))
    print('collisions (line, i, j): max penetration')
    for k, v in sorted(sm.items()):
        print(k, 't=%.0f pen=%.2f dx=%.2f dy=%.2f' % (v[0], v[1], v[2], v[3]))
    xs = [c for f in s.frames for p in f[1] for c in p]
    print('range', min(xs), max(xs))
