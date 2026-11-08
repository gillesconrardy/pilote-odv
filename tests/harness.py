import os
"""Run the generated Pybricks programs of the 4 vehicles concurrently against mocked
pybricks modules: per-hub clocks (offset + drift), BLE broadcast with random latency/drops,
stdin commands to vehicle 4. Records each vehicle's show time and motor targets."""
import sys, types, threading, time, random, math, queue, json

SPEED = 2.0                     # simulation runs SPEED x faster than real time
T0 = time.monotonic()
def true_ms(): return (time.monotonic() - T0) * 1000 * SPEED

ctx = threading.local()
AIR = {}                        # channel -> list of (true_time, data)
AIR_LOCK = threading.Lock()
REC = {i: [] for i in range(1, 5)}   # vid -> [(true_ms, v, x, y)]
OUT = []                        # sender prints
STDINS = {v: queue.Queue() for v in range(1, 5)}
STOPPED = {}

def mod(name, **kw):
    m = types.ModuleType(name); m.__dict__.update(kw); sys.modules[name] = m; return m

class Color:
    def __init__(self, h=0, s=100, v=100): self.h, self.s, self.v = h, s, v
    def __repr__(self): return 'hsv(%d,%d,%d)' % (self.h, self.s, self.v)
    CYAN = 'cyan'; RED = 'red'; GREEN = 'green'; BLUE = 'blue'; WHITE = 'white'; YELLOW = 'yellow'; ORANGE = 'orange'; MAGENTA = 'magenta'
class Port: A = 'A'; B = 'B'; C = 'C'
class Button: LEFT_PLUS='L+'; LEFT_MINUS='L-'; RIGHT_PLUS='R+'; RIGHT_MINUS='R-'; CENTER='C'
REMOTE = {'pressed': set(), 'present': True}
class _RButtons:
    def pressed(self): return set(REMOTE['pressed'])
class Remote:
    def __init__(self, timeout=10000):
        time.sleep(0.5 / SPEED)
        if not REMOTE['present']: raise OSError('no remote')
        self.buttons = _RButtons(); self.light = _Light()
class Direction: CLOCKWISE = 1
SONAR = json.loads(os.environ.get('HARNESS_SONAR', '[]'))   # [[t_ms, mm], ...] : distance vue par le capteur du V4
class _SLights:
    def on(self, v): pass
class UltrasonicSensor:
    def __init__(self, port): self.lights = _SLights()
    def distance(self):
        t = true_ms(); d = 2000
        for a, b in SONAR:
            if t >= a: d = b
        return d

class StopWatch:
    def __init__(self):
        self.t0 = true_ms(); self.k = ctx.drift
    def time(self): return int((true_ms() - self.t0) * self.k)
    def reset(self): self.t0 = true_ms()

def wait(ms):
    if threading.current_thread().name in STOPPED: raise SystemExit
    time.sleep(ms / 1000 / SPEED)

class _Light:
    def on(self, c):
        ctx.light = c
        if hasattr(ctx, 'lights') and (not ctx.lights or ctx.lights[-1] != repr(c)): ctx.lights.append(repr(c))
    CYAN = 'cyan'
    def off(self): ctx.light = None
class _Battery:
    def voltage(self): return 7800
class _BLE:
    def __init__(self, bc, obs): self.bc = bc; self.obs = obs
    def broadcast(self, data):
        with AIR_LOCK: AIR.setdefault(self.bc, []).append((true_ms(), tuple(data)))
    def observe(self, ch):
        now = true_ms()
        if random.random() < 0.15: return None          # missed packets
        lat = random.uniform(15, 140)
        with AIR_LOCK:
            lst = [d for t, d in AIR.get(ch, []) if t <= now - lat]
        return lst[-1] if lst else None

class TechnicHub:
    def __init__(self, broadcast_channel=0, observe_channels=()):
        self.ble = _BLE(broadcast_channel, observe_channels); self.light = _Light(); self.battery = _Battery()

class Motor:
    def __init__(self, port, direction, reset_angle=True):
        self.port = port; self.angle = 0
    def run_until_stalled(self, *a, **k): self.angle = 0
    def run_angle(self, s, a): self.angle += a
    def reset_angle(self, a): self.angle = a
    def run_target(self, s, a): self.angle = a
    def track_target(self, a):
        self.angle = a
        r = ctx.last
        if self.port == 'C': r[0] = a / 80
        else:
            r[1] = a / 80
    def stop(self): ctx.stopped = True
    def hold(self): ctx.stopped = True

class _Stdin:
    def read(self, n): return STDINS[ctx.vid].get_nowait()
class _Poll:
    def register(self, s): pass
    def poll(self, t): return not STDINS[ctx.vid].empty()

mod('pybricks'); mod('pybricks.hubs', TechnicHub=TechnicHub); mod('pybricks.pupdevices', Motor=Motor, Remote=Remote, UltrasonicSensor=UltrasonicSensor)
mod('pybricks.parameters', Port=Port, Direction=Direction, Color=Color, Button=Button)
mod('pybricks.tools', wait=wait, StopWatch=StopWatch)
mod('umath', sin=math.sin, cos=math.cos, pi=math.pi)
mod('usys', stdin=_Stdin()); mod('uselect', poll=_Poll)

def run_vehicle(vid, src, delay_ms, drift):
    time.sleep(delay_ms / 1000 / SPEED)
    ctx.vid = vid; ctx.drift = drift; ctx.last = [0, 0]; ctx.stopped = False; ctx.light = None
    ctx.lights = []
    src = src.replace("    last_loop = local\n    x_motor.track_target",
                      "    _REC.append((_true(), wrap(vt(raw)), x, y))\n    last_loop = local\n    x_motor.track_target")
    assert '_REC.append' in src
    g = {'__name__': '__main__', '_REC': REC[vid], '_true': true_ms,
         'print': (lambda *a: OUT.append((true_ms(), 'V%d ' % vid + ' '.join(str(x) for x in a))))}
    try:
        exec(compile(src, 'vehicle%d.py' % vid, 'exec'), g)
    except SystemExit:
        pass
    REC[vid].append(('stopped', ctx.stopped))
    REC[vid].append(('lights', ctx.lights[:8]))

if __name__ == '__main__':
    progs = json.load(open(sys.argv[1]))
    script = json.loads(sys.argv[2])       # [[true_ms, char], ...]
    end = float(sys.argv[3])
    ths = []
    for vid in range(1, 5):
        th = threading.Thread(target=run_vehicle, name='v%d' % vid,
                              args=(vid, progs[str(vid)], [0, 400, 900, 1500][vid - 1], [1.0002, 0.9998, 1.0001, 1.0][vid - 1]), daemon=True)
        th.start(); ths.append(th)
    for t_ms, ch in script:
        while true_ms() < t_ms: time.sleep(0.002)
        if isinstance(ch, str) and ch.startswith('BTN'):
            REMOTE['pressed'] = set(ch[3:].split()) ; continue
        if ch == 'RESTART4':
            STOPPED['v4'] = True; time.sleep(0.3)
            with AIR_LOCK: AIR.clear()
            th = threading.Thread(target=run_vehicle, name='v4b', args=(4, progs['4'], 0, 1.0), daemon=True); th.start(); ths.append(th)
            continue
        tgt, txt = (4, ch) if isinstance(ch, str) else ch
        for c in txt + '\n': STDINS[tgt].put(c)
    while true_ms() < end: time.sleep(0.01)
    for th in ths: STOPPED[th.name] = True
    time.sleep(0.2)
    json.dump({'rec': {k: [r for r in v if r[0] != 'stopped'] for k, v in REC.items()},
               'stopped': {k: [r for r in v if r[0] == 'stopped'] for k, v in REC.items()},
               'out': OUT}, open('harness_out.json', 'w'))
    print('done', {k: len(v) for k, v in REC.items()})
