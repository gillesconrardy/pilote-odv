from pybricks.hubs import TechnicHub
from pybricks.pupdevices import Motor, Remote
try:
    from pybricks.pupdevices import UltrasonicSensor
except ImportError:
    UltrasonicSensor = None
from pybricks.parameters import Port, Direction, Color, Button
from pybricks.tools import wait, StopWatch
from umath import sin, cos, pi
VEHICLE_ID = 1
SENDER_ID = 4
IS_SENDER = VEHICLE_ID == SENDER_ID
ME = VEHICLE_ID - 1
VHUE = (215, 28, 140, 270)[ME]
VCOL = Color(VHUE, 100, 100)
VDIM = Color(VHUE, 100, 30)
CHANNEL = 1
DO_HOMING = True
LOOP = False
GEAR = 80
LEAD = 1000
BCAST_MS = 250
COMP = 30
BIG = 1000000000
GEN = 132
HOME_X = 30
HOME_Y = 0
TOTAL = 500
NSEG = 1
BOUNDS = (0, 500)
SMODE = 0
MASK = ()
D = b'\x00\x00\xf4\x01\xb8\x0b\x00\x00\x00\x00\x00\x00\x00\x00'
if IS_SENDER:
    hub = TechnicHub(broadcast_channel=CHANNEL)
else:
    hub = TechnicHub(observe_channels=[CHANNEL])
x_motor = Motor(Port.C, Direction.CLOCKWISE, reset_angle=DO_HOMING)
y_motor = Motor(Port.A, Direction.CLOCKWISE, reset_angle=DO_HOMING)
def u16(o):
    return D[o] | (D[o + 1] << 8)
def i16(o):
    v = D[o] | (D[o + 1] << 8)
    return v - 65536 if v > 32767 else v
def seg_pos(o, t):
    k = D[o]
    d = u16(o + 2)
    f = t / d if d > 0 else 1.0
    if k == 1:
        x0 = i16(o + 4)
        y0 = i16(o + 6)
        return (x0 + (i16(o + 8) - x0) * f) / 100, (y0 + (i16(o + 10) - y0) * f) / 100
    if k == 2:
        a = (i16(o + 10) + i16(o + 12) * f) * (pi / 1800)
        r = i16(o + 8)
        return (i16(o + 4) + r * sin(a)) / 100, (i16(o + 6) + r * cos(a)) / 100
    return i16(o + 4) / 100, i16(o + 6) / 100
cur_i = 0
cur_t0 = 0
def pos_at(v):
    global cur_i, cur_t0
    while cur_i < NSEG - 1 and v >= cur_t0 + u16(cur_i * 14 + 2):
        cur_t0 += u16(cur_i * 14 + 2)
        cur_i += 1
    while cur_i > 0 and v < cur_t0:
        cur_i -= 1
        cur_t0 -= u16(cur_i * 14 + 2)
    t = v - cur_t0
    d = u16(cur_i * 14 + 2)
    if t > d:
        t = d
    if t < 0:
        t = 0
    return seg_pos(cur_i * 14, t)
def wrap(v):
    if LOOP:
        return v % TOTAL
    if v < 0:
        return 0
    if v > TOTAL:
        return TOTAL
    return v
P0 = [0, 0, 0, 0]
P1 = [0, 0, 0, 0]
def vt(raw):
    p = P1 if raw >= P1[0] else P0
    r = p[2]
    if r == 0 or r >= 9:
        return p[1]
    v = p[1] + r * (raw - p[0])
    if r > 0 and v > p[3]:
        v = p[3]
    if r < 0 and v < p[3]:
        v = p[3]
    return v
def chor_index(w):
    k = 0
    while k < len(BOUNDS) - 2 and w >= BOUNDS[k + 1]:
        k += 1
    return k
def battery_color():
    v = hub.battery.voltage()
    if v < 6500:
        return Color.RED
    if v < 7000:
        return Color.YELLOW
    return VCOL
def homing():
    y_motor.run_until_stalled(-200, duty_limit=35)
    print('HY')
    wait(200)
    y_motor.run_angle(1400, 110)
    wait(200)
    y_motor.reset_angle(0)
    x_motor.run_until_stalled(-200, duty_limit=35)
    wait(200)
    x_motor.run_angle(1400, 110)
    wait(200)
    x_motor.reset_angle(0)
def emergency():
    x_motor.stop()
    y_motor.stop()
    hub.light.on(Color.RED)
    while True:
        if IS_SENDER:
            hub.ble.broadcast((watch.time() + COMP, P1[0], P1[1], 10 + 16 * GEN, 0))
        wait(BCAST_MS)
hub.light.on(VCOL)
print('BAT', hub.battery.voltage())
if DO_HOMING:
    homing()
    a = 0.0
    clr = False
    while a < HOME_X * GEAR:
        a = min(HOME_X * GEAR, a + 16)
        x_motor.track_target(a)
        if not clr and a >= 12 * GEAR:
            print('CLR')
            clr = True
        wait(20)
    if not clr:
        print('CLR')
x_motor.run_target(1000, HOME_X * GEAR)
y_motor.run_target(1000, HOME_Y * GEAR)
watch = StopWatch()
from usys import stdin
from uselect import poll
keyboard = poll()
keyboard.register(stdin)
line = ''
VMAN = 0.016
manual = False
blend = False
mx = HOME_X
my = HOME_Y
tx = HOME_X
ty = HOME_Y
last_loop = 0
count = 0
def clamp(v, a, b):
    return a if v < a else (b if v > b else v)
remote = None
OBS = [None, None, None]
MSPD = 0.006
last_g = -10000
rc_until = 0
next_pos = 0
def free_at(x, y):
    if x < 0 or x > 30 or y < 0 or y > 30:
        return False
    for o in OBS:
        if o is not None and abs(x - o[0]) < 10 - 1e-6 and abs(y - o[1]) < 10 - 1e-6:
            return False
    if game == 5:
        for k in range(3):
            o = BOLD[k]
            if abs(x - o[0]) < 10.5 and abs(y - o[1]) < 10.5:
                return False
    return True
def remote_connect():
    global remote
    hub.light.on(Color.CYAN)
    try:
        remote = Remote(timeout=6000)
        remote.light.on(Color.ORANGE)
        print('RC', 1)
    except OSError:
        remote = None
        print('RC', 0)
    hub.light.on(VCOL)
def manual_line(s):
    global manual, blend, tx, ty, MSPD, last_g, game, CSPD, g_round, g_catch, g_freeze, g_mover, g_stuck, b_ret, g_way, g_placed, hand, h_state, SMODE
    if s == 'E':
        if IS_SENDER and manual and game == 0 and None not in OBS:
            for k in range(3):
                GC[k][0] = OBS[k][0]
                GC[k][1] = OBS[k][1]
                GH[k] = (OBS[k][0], OBS[k][1])
            B4[0] = tx
            B4[1] = ty
            g_placed = False
            b_ret = False
            game = 5
            b_snapshot(watch.time(), True)
            print('EON')
        else:
            print('JNO')
        return
    if s == 'K':
        hand = False
        b_ret = game in (4, 5) or (game == 1 and g_placed)
        if game == 5 or (game == 1 and g_placed):
            B4[0] = tx
            B4[1] = ty
        if game in (1, 4, 5):
            game = 2
            g_mover = -1
            print('JRET')
        return
    if s[0] == 'W' and len(s) > 3:
        k = s.find(',')
        if game == 2 and b_ret and g_mover < 0:
            try:
                g_way = [(clamp(int(s[2:k]) / 100, 0, 30), clamp(int(s[k + 1:]) / 100, 0, 30))]
                g_mover = clamp(int(s[1]), 1, 4) - 1
            except (ValueError, IndexError):
                print('WNO')
        else:
            print('WNO')
        return
    if s == 'Z':
        if game == 2 and b_ret and g_mover < 0:
            game = 3
            print('JOK')
        return
    if s == 'C':
        if manual:
            remote_connect()
        return
    if s[0] == 'V':
        try:
            MSPD = clamp(int(s[1:]) / 100000, 0.0005, 0.016)
        except ValueError:
            pass
        return
    if s[0] == 'O' and len(s) > 2:
        k = s.find(',')
        try:
            OBS[int(s[1]) - 1] = (int(s[2:k]) / 100, int(s[k + 1:]) / 100)
        except (ValueError, IndexError):
            pass
        return
    if s == 'M':
        manual = True
        blend = False
        tx = mx
        ty = my
        hub.light.on(VCOL)
        print('MAN', 1)
    elif s == 'Q':
        if game in (1, 2, 4, 5):
            print('BUSY')
            return
        game = 0
        manual = False
        blend = True
        print('MAN', 0)
    elif len(s) == 2 and s[0] == 'S' and s[1] in '012':
        SMODE = int(s[1])
        print('SMODE', SMODE)
    elif s == 'H1' or s == 'H0':
        if s == 'H1' and IS_SENDER and game == 5 and sonar is not None:
            hand = True
            h_buf.clear()
            h_state = 2
            print('HON')
        else:
            if s == 'H1':
                print('HNO')
            hand = False
            sonar_eyes(0)
    elif s[0] == 'G' and manual and game != 4 and not hand:
        k = s.find(',')
        if k > 1:
            try:
                nx = int(s[1:k]) / 100
                ny = int(s[k + 1:]) / 100
            except ValueError:
                return
            nx = clamp(nx, -1, 31)
            ny = clamp(ny, -1, 31)
            if game:
                if not free_at(nx, ny):
                    if free_at(nx, ty):
                        ny = ty
                    elif free_at(tx, ny):
                        nx = tx
                    else:
                        return
            tx = nx
            ty = ny
            last_g = watch.time()
game = 0
GC = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
GH = [(0, 0), (0, 0), (0, 0)]
GR = [0, 0, 0]
GS = [1, 1, 1]
GW = [None, None, None]
hand = False
h_buf = []
h_next = 0
h_print = 0
h_dist = 2000
h_state = 2
h_lost = 0
h_cx = 0.0
h_wp = 0
h_dir = 1
sonar = None
if IS_SENDER and UltrasonicSensor is not None:
    try:
        sonar = UltrasonicSensor(Port.B)
    except Exception:
        sonar = None
GT = [0, 0, 0]
GB = [0, 0, 0]
GQ = [99.0, 99.0, 99.0]
g_placed = False
CSPD = 0.005
g_freeze = 0
g_round = 0
g_catch = 0
g_mover = -1
g_way = []
g_stuck = False
g_next_jp = 0
g_role = -1
game_rx = False
grate = 0.006
last_game = 0
B4 = [0.0, 0.0]
BV = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
TILT = [0.0, 0.0]
BK = (0.7, 1.0, 1.3, 0.85)
B4H = [0.0, 0.0]
b_ret = False
def b_pos(k):
    return B4 if k == 3 else GC[k]
def b_home(k):
    return B4H if k == 3 else GH[k]
BOLD = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
BNOW = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
b_snap = 0
def b_ok(k, x, y):
    c = b_pos(k)
    for j in range(4):
        if j == k:
            continue
        o = b_pos(j)
        q = BOLD[j]
        dn = cheb(x, y, o[0], o[1])
        do = cheb(x, y, q[0], q[1])
        if dn < 11 and dn < cheb(c[0], c[1], o[0], o[1]) - 1e-9:
            return False
        if do < 11 and do < cheb(c[0], c[1], q[0], q[1]) - 1e-9:
            return False
    return True
def b_snapshot(local, reset):
    global b_snap
    if reset or local >= b_snap:
        b_snap = local + 250
        for k in range(4):
            p = b_pos(k)
            o = BNOW[k] if not reset else p
            BOLD[k][0] = o[0]
            BOLD[k][1] = o[1]
            BNOW[k][0] = p[0]
            BNOW[k][1] = p[1]
def cheb(ax, ay, bx, by):
    dx = ax - bx
    dy = ay - by
    return max(dx if dx > 0 else -dx, dy if dy > 0 else -dy)
RXO = [[0.0, 0.0], [0.0, 0.0]]
def rx_ok(x, y):
    for o in RXO:
        dn = cheb(x, y, o[0], o[1])
        if dn < 10 and dn < cheb(mx, my, o[0], o[1]) - 1e-9:
            return False
    return True
def v4_ok(x, y):
    for o in OBS:
        if o is not None:
            dn = cheb(x, y, o[0], o[1])
            if dn < 10 and dn < cheb(mx, my, o[0], o[1]) - 1e-9:
                return False
    return True
def sonar_eyes(v):
    try:
        sonar.lights.on([v, v, v, v])
    except Exception:
        pass
def hand_tick(dt, local):
    global tx, ty, h_next, h_print, h_dist, h_state, h_lost, h_cx, h_wp, h_dir
    if local >= h_next:
        h_next = local + 40
        try:
            d = sonar.distance()
        except Exception:
            d = 2000
        h_buf.append(d)
        if len(h_buf) > 4:
            h_buf.pop(0)
        h_dist = sorted(h_buf)[len(h_buf) // 2]
    d = h_dist
    vmax = 0.016
    veh = False
    for o in OBS:
        if o is not None and abs(o[0] - mx) < 10 and o[1] > my and abs((o[1] - my - 10) * 12.25 - d) < 25:
            d = 2000
            veh = True
    if d <= 300:
        if h_state == 1 and abs(tx - h_cx) > 0.5:
            h_dir = 1 if tx > h_cx else -1
        h_state = 0
        h_lost = local
        h_cx = tx
    elif h_state == 0 and not veh and local - h_lost > 150:
        h_state = 1
        h_wp = 0
    if h_state == 1:
        offs = (4, -4, 8, -8, 12, -12)
        if h_wp >= len(offs):
            h_state = 2
        else:
            gx = clamp(h_cx + offs[h_wp] * h_dir, 0, 30)
            ex = gx - tx
            stp = 0.010 * dt
            if abs(ex) <= stp:
                tx = gx
                h_wp += 1
            else:
                nx = tx + (stp if ex > 0 else -stp)
                if free_at(nx, ty):
                    tx = nx
                else:
                    h_wp += 1
    if d < 60:
        v = -vmax
    elif d < 130:
        v = -vmax * (130 - d) / 70
    elif d <= 170:
        v = 0
    elif d <= 300:
        v = vmax * (d - 170) / 130
    else:
        v = 0
    if local >= h_print:
        h_print = local + 250
        print('HD', int(d), h_state)
        sonar_eyes(100 if d <= 300 else 15)
    if v != 0:
        ny = clamp(ty + v * dt, 0, 30)
        if free_at(tx, ny):
            ty = ny
def evade_tick(dt):
    global CSPD
    if dt > 50:
        dt = 50
    CSPD = min(MSPD * 1.4, 0.0165)
    st = CSPD * dt
    B4[0] = tx
    B4[1] = ty
    for k in range(3):
        c = GC[k]
        dt4 = min(cheb(c[0], c[1], tx, ty), cheb(c[0], c[1], mx, my))
        if dt4 < 14:
            ux = c[0] - tx
            uy = c[1] - ty
            d = (ux * ux + uy * uy) ** 0.5
            if d < 0.01:
                ux = 1.0
                uy = 0.0
                d = 1.0
            ux /= d
            uy /= d
            for vx, vy in ((ux, uy), (1 if ux > 0 else -1, 0), (0, 1 if uy > 0 else -1), (-uy, ux), (uy, -ux)):
                nx = clamp(c[0] + vx * st, 0, 30)
                ny = clamp(c[1] + vy * st, 0, 30)
                if abs(nx - c[0]) + abs(ny - c[1]) < st * 0.3:
                    continue
                if b_ok(k, nx, ny) and min(cheb(nx, ny, tx, ty), cheb(nx, ny, mx, my)) >= dt4 - 1e-6:
                    c[0] = nx
                    c[1] = ny
                    break
        elif dt4 > 17:
            hx = GH[k][0] - c[0]
            hy = GH[k][1] - c[1]
            d = (hx * hx + hy * hy) ** 0.5
            if d > 0.01:
                sk = min(st * 0.6, d)
                for vx, vy in ((hx / d, hy / d), (hx / d, 0), (0, hy / d)):
                    nx = c[0] + vx * sk
                    ny = c[1] + vy * sk
                    if abs(nx - c[0]) + abs(ny - c[1]) < sk * 0.3:
                        continue
                    if b_ok(k, nx, ny) and min(cheb(nx, ny, tx, ty), cheb(nx, ny, mx, my)) >= 15:
                        c[0] = nx
                        c[1] = ny
                        break
    for k in range(3):
        OBS[k] = (GC[k][0], GC[k][1])
def game_tick(dtg, local):
    global game, g_freeze, g_round, g_catch, g_mover, g_way, g_stuck
    if game == 2:
        sp = max(CSPD, 0.006) * dtg
        if g_mover >= 0:
            c = b_pos(g_mover)
            w = g_way[0]
            dx = w[0] - c[0]
            dy = w[1] - c[1]
            d = (dx * dx + dy * dy) ** 0.5
            if d <= sp:
                c[0] = w[0]
                c[1] = w[1]
                g_way.pop(0)
                if not g_way:
                    g_mover = -1
                    g_stuck = False
                    if b_ret:
                        print('WOK')
            else:
                c[0] += dx * sp / d
                c[1] += dy * sp / d
    for k in range(3):
        OBS[k] = (GC[k][0], GC[k][1])
if IS_SENDER:
    next_bcast = 0
    next_status = 0
    next_tgt = [-1]
    def masked(w):
        if w in BOUNDS:
            return False
        i = 0
        while i + 1 < len(MASK):
            if MASK[i] <= w <= MASK[i + 1]:
                return True
            i += 2
        return False
    gs = [0, 0, 0, 0, 0, 0, 0, 2000]
    def gesture_tick(raw):
        if raw < gs[0]:
            return
        gs[0] = raw + 40
        try:
            d = sonar.distance()
        except Exception:
            return
        p = P1 if raw >= P1[0] else P0
        if masked(wrap(vt(raw))):
            d = 2000
        if SMODE == 2:
            if d < 250:
                if not gs[1]:
                    gs[1] = 1
                    gs[2] = raw
                elif not gs[6] and raw - gs[2] > 150 and p[2] == 1 and vt(raw) != p[3] and raw >= P1[0]:
                    command('z', raw)
                    gs[6] = 1
                    print('GST S')
                    sonar_eyes(100)
            else:
                if gs[1]:
                    gs[1] = 0
                    gs[2] = raw
                elif gs[6] and raw - gs[2] > 1000 and raw >= P1[0]:
                    command('p', raw)
                    gs[6] = 0
                    print('GST R')
                    sonar_eyes(0)
            return
        near = d < 120 if not gs[1] else d < 200
        if near and not gs[1]:
            gs[1] = 1
            gs[2] = raw
            sonar_eyes(60)
        elif near and not gs[5] and raw - gs[2] >= 2000:
            gs[5] = 1
            gs[3] = 0
            if raw >= P1[0]:
                command('h', raw)
                print('GST H')
        elif not near and gs[1]:
            gs[1] = 0
            sonar_eyes(0)
            if not gs[5] and 60 <= raw - gs[2] <= 900:
                gs[3] += 1
                gs[4] = raw
            gs[5] = 0
        elif not gs[1] and gs[3] and raw - gs[4] > 700:
            n = gs[3]
            gs[3] = 0
            if raw < P1[0]:
                return
            if n >= 2:
                command('n', raw)
                print('GST 2')
            else:
                command('z' if p[2] == 1 and vt(raw) != p[3] else 'p', raw)
                print('GST 1')
    def command(c, raw):
        global P0, P1, next_bcast
        if c != 'n':
            next_tgt[0] = -1
        if c == 'x':
            v = vt(raw)
            P0 = [raw, v, 9, 0]
            P1 = [raw, v, 9, 0]
            emergency()
        if c == 'e':
            P0 = P1
            P1 = [raw, vt(raw), 12, 0]
            next_bcast = 0
            print('ACK e 0')
            return
        if raw < P1[0]:
            print('BUSY')
            return
        A = raw + LEAD
        V = vt(A)
        if c == 'p':
            R = 1
            S = BIG if LOOP else TOTAL
            if not LOOP and V >= TOTAL:
                V = 0
        elif c == 'z':
            R = 0
            S = 0
        elif c == 'n':
            w = wrap(V)
            k = chor_index(w)
            back = w - BOUNDS[k]
            fwd = BOUNDS[k + 1] - w
            if back == 0 or fwd == 0:
                tgt = BOUNDS[k + 1] if back == 0 else 0
                if tgt >= TOTAL:
                    tgt = 0
                V = V - w + tgt
                R = 1
                S = BIG if LOOP else TOTAL
                next_tgt[0] = -1
            else:
                next_tgt[0] = BOUNDS[k + 1] if BOUNDS[k + 1] < TOTAL else 0
                if back <= fwd:
                    R = -1
                    S = V - back
                else:
                    R = 1
                    S = V + fwd
        elif c == 'h':
            w = wrap(V)
            k = chor_index(w)
            back = w - BOUNDS[k]
            fwd = BOUNDS[k + 1] - w
            if back == 0 or fwd == 0:
                R = 0
                S = 0
            elif back <= fwd:
                R = -1
                S = V - back
            else:
                R = 1
                S = V + fwd
        else:
            return
        P0 = P1
        P1 = [A, V, R, S]
        next_bcast = 0
        print('ACK', c, A - raw)
else:
    rt_buf = []
    df_buf = []
    last_m = -1
    slope = 0.0
    icpt = 0
    synced = False
    i0 = False
    i0t = 0
    i0d = 0
    def feed(m):
        global last_m, slope, icpt, synced, i0, i0t, i0d
        if m < last_m - 3000:
            del rt_buf[:]
            del df_buf[:]
            last_m = -1
            slope = 0.0
            i0 = False
        if m <= last_m:
            return False
        last_m = m
        t = watch.time()
        rt_buf.append(t)
        df_buf.append(m - t)
        if len(rt_buf) > 30:
            rt_buf.pop(0)
            df_buf.pop(0)
        mx_ = max(df_buf)
        rt = rt_buf[df_buf.index(mx_)]
        if watch.time() < 60000 or not i0 or rt == i0t:
            icpt = mx_
            if len(rt_buf) == 30 and not i0:
                i0 = True
                i0t = rt
                i0d = mx_
        else:
            slope = (mx_ - i0d) / (rt - i0t)
            icpt = i0d - slope * i0t
        synced = True
        return True
    hub.light.on(VCOL)
while True:
    local = watch.time()
    while keyboard.poll(0):
        c = stdin.read(1)
        if c == '\n':
            if line:
                if IS_SENDER and line in ('p', 'z', 'h', 'x', 'e', 'n'):
                    command(line, local)
                else:
                    manual_line(line)
            line = ''
        elif len(line) < 24:
            line += c
    if IS_SENDER:
        raw = local
        if raw >= next_bcast and game:
            b = [int(clamp(GC[k // 2][k % 2], 0, 31) * 8 + 0.5) for k in range(6)]
            b.append(int(clamp(max(CSPD * (1.3 if game == 4 else 1), 0.006) * 10000, 1, 255)))
            b.append(255 if game == 4 or not g_placed else GR[0] + 3 * GR[1] + 9 * GR[2])
            hub.ble.broadcast((raw + COMP, 7 + 16 * GEN, bytes(b)))
            next_bcast = raw + 150
        elif raw >= next_bcast:
            hub.ble.broadcast((raw + COMP, P1[0], P1[1], P1[2] + 1 + 16 * GEN, P1[3]))
            next_bcast = raw + (BCAST_MS * 2 if manual else BCAST_MS)
            count += 1
            if not manual:
                hub.light.on(battery_color() if count % 2 else VDIM)
        if raw >= next_status:
            next_status = raw + (1000 if manual else 400)
            v = vt(raw)
            p = P1 if raw >= P1[0] else P0
            st = 'E' if p[2] >= 9 else ('P' if p[2] == 0 else ('S' if v == p[3] else ('F' if p[2] > 0 else 'B')))
            w = wrap(v)
            print('ST', st, w, chor_index(w), 1 if raw < P1[0] else 0, hub.battery.voltage(), GEN)
    else:
        data = hub.ble.observe(CHANNEL)
        if data is not None and len(data) == 3 and data[1] // 16 == GEN and data[1] % 16 == 7:
            feed(data[0])
            gb = data[2]
            if len(gb) >= 7:
                tx = gb[2 * ME] / 8
                ty = gb[2 * ME + 1] / 8
                n = 0
                for j in range(3):
                    if j != ME:
                        RXO[n][0] = gb[2 * j] / 8
                        RXO[n][1] = gb[2 * j + 1] / 8
                        n += 1
                grate = gb[6] / 10000 * 1.25
                role = 255
                if len(gb) >= 8 and gb[7] < 27:
                    role = (gb[7] // (1, 3, 9)[ME]) % 3
                if not game_rx or role != g_role:
                    game_rx = True
                    g_role = role
                    hub.light.on(Color.RED if role == 0 else (Color.BLUE if role == 1 else (VDIM if role == 2 else VCOL)))
        elif data is not None and len(data) == 5 and data[3] // 16 == GEN:
            if game_rx:
                game_rx = False
                g_role = -1
                blend = True
                hub.light.on(VCOL)
            if feed(data[0]):
                count += 1
                if not manual:
                    hub.light.on(battery_color() if count % 2 else VDIM)
            q = [data[1], data[2], data[3] % 16 - 1, data[4]]
            if q != P1:
                P0 = P1
                P1 = q
            if P1[2] == 9:
                emergency()
            if P1[2] == 12:
                x_motor.hold()
                y_motor.hold()
                hub.light.off()
                wait(300)
                raise SystemExit
        if not synced:
            last_loop = local
            wait(20)
            continue
        raw = int((1 + slope) * watch.time() + icpt)
    x, y = pos_at(wrap(vt(raw)))
    if manual and remote is not None and not hand:
        try:
            pr = remote.buttons.pressed()
        except OSError:
            remote = None
            pr = ()
            print('RC', 0)
        vx = 1 if Button.LEFT_PLUS in pr else (-1 if Button.LEFT_MINUS in pr else 0)
        vy = -1 if Button.RIGHT_PLUS in pr else (1 if Button.RIGHT_MINUS in pr else 0)
        if (vx or vy) and local - last_g > 400:
            step = MSPD * (local - last_loop)
            if vx and vy:
                step *= 0.7071
            nx = clamp(tx + vx * step, 0, 30)
            ny = clamp(ty + vy * step, 0, 30)
            if free_at(nx, ny):
                tx = nx
                ty = ny
            elif free_at(nx, ty):
                tx = nx
            elif free_at(tx, ny):
                ty = ny
            rc_until = local + 300
    if IS_SENDER and next_tgt[0] >= 0 and local >= P1[0] and vt(local) == P1[3]:
        A = local + LEAD
        V = vt(A)
        P0 = P1
        P1 = [A, V - wrap(V) + next_tgt[0], 1, BIG if LOOP else TOTAL]
        next_tgt[0] = -1
        next_bcast = 0
        print('ACK n', LEAD)
    if IS_SENDER and SMODE and sonar is not None and not manual and game == 0:
        gesture_tick(local)
    if IS_SENDER and game == 5:
        b_snapshot(local, False)
        if hand:
            hand_tick(min(local - last_loop, 50), local)
        evade_tick(local - last_loop)
    elif IS_SENDER and game:
        game_tick(local - last_loop, local)
        if b_ret and game in (2, 3):
            tx = B4[0]
            ty = B4[1]
    if IS_SENDER and game:
        if local >= g_next_jp:
            g_next_jp = local + 250
            print('JP', int(GC[0][0] * 100), int(GC[0][1] * 100), int(GC[1][0] * 100), int(GC[1][1] * 100),
                  int(GC[2][0] * 100), int(GC[2][1] * 100), int(mx * 100), int(my * 100), game, g_catch)
    if manual and IS_SENDER and local >= next_pos:
        moving = local < rc_until
        next_pos = local + (200 if moving else 1000)
        print('POS', int(mx * 100), int(my * 100), 1 if moving else 0)
    if manual or blend or game_rx:
        gx = tx if (manual or game_rx) else x
        gy = ty if (manual or game_rx) else y
        step = (grate if game_rx else VMAN) * (local - last_loop)
        dx = gx - mx
        dy = gy - my
        d = (dx * dx + dy * dy) ** 0.5
        if d <= step:
            nx = gx
            ny = gy
        else:
            nx = mx + dx * step / d
            ny = my + dy * step / d
        if game_rx and not rx_ok(nx, ny):
            if rx_ok(nx, my):
                ny = my
            elif rx_ok(mx, ny):
                nx = mx
            else:
                nx = mx
                ny = my
        if IS_SENDER and game == 5 and not v4_ok(nx, ny):
            if v4_ok(nx, my):
                ny = my
            elif v4_ok(mx, ny):
                nx = mx
            else:
                nx = mx
                ny = my
        mx = nx
        my = ny
        if blend and mx == gx and my == gy:
            blend = False
        x = mx
        y = my
    else:
        mx = x
        my = y
    last_loop = local
    x_motor.track_target(x * GEAR)
    y_motor.track_target(y * GEAR)
    wait(5)
