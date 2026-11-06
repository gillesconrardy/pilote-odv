# =====================================================================
#  ODV - programme genere par "Pilote ODV"   (vehicule %VID%)
#  Choregraphies : %NAMES%
#  Ne pas modifier a la main : regenerer depuis la page Pilote ODV.
# =====================================================================
from pybricks.hubs import TechnicHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Color
from pybricks.tools import wait, StopWatch
from umath import sin, cos, pi

VEHICLE_ID = %VID%
SENDER_ID = 4                 # le vehicule 4 diffuse l'horloge et recoit les commandes du telephone
IS_SENDER = VEHICLE_ID == SENDER_ID
CHANNEL = 1
DO_HOMING = %HOMING%          # True : recalage contre la cloture au demarrage
LOOP = %LOOP%                 # True : la suite de choregraphies tourne en boucle
GEAR = 80                     # degres moteur par pas de grille
LEAD = 1000                   # ms : delai avant application d'une commande (tous en meme temps)
BCAST_MS = 250                # ms : intervalle de diffusion de l'horloge
COMP = 30                     # ms : compensation du delai radio
BIG = 1000000000
GEN = %GEN%                   # numero de version : les 4 vehicules d'un meme envoi ont le meme
HOME_X = %HX%
HOME_Y = %HY%
TOTAL = %TOTAL%               # ms : duree totale de la suite
NSEG = %NSEG%
BOUNDS = %BOUNDS%             # ms : debut de chaque choregraphie, puis TOTAL
D = %DATA%
# Enregistrement de 14 octets par segment :
#   [0] type (0 attente, 1 ligne, 2 arc)  [2:4] duree ms
#   ligne : x0 y0 x1 y1 (x100)   arc : cx cy r (x100) a0 rot (degres x10)

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
    # position du vehicule au temps de spectacle v (ms, deja ramene dans 0..TOTAL)
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


# Horloge de spectacle : v = V + R * (t - A), bornee par S.  R : 1 lecture, 0 pause, -1 retour, 9 urgence
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
    return Color.BLUE


def homing():
    y_motor.run_until_stalled(-200, duty_limit=35)
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


# ---------------------------------------------------------------- demarrage
hub.light.on(Color.ORANGE)
print('BAT', hub.battery.voltage())
if DO_HOMING:
    homing()
x_motor.run_target(1000, HOME_X * GEAR)
y_motor.run_target(1000, HOME_Y * GEAR)
watch = StopWatch()

# Commandes du telephone (une par ligne) :
#   p lecture, z pause, h retour au depart, x urgence   (vehicule 4 seulement)
#   M prise en main manuelle, Gx,y aller en (x/100, y/100), Q rendre la main   (tous)
from usys import stdin
from uselect import poll
keyboard = poll()
keyboard.register(stdin)
line = ''
VMAN = 0.016                  # pas de grille par ms en manuel (16 pas/s au maximum)
manual = False
blend = False                 # True : retour progressif vers la choregraphie apres Q
mx = HOME_X
my = HOME_Y
tx = HOME_X
ty = HOME_Y
last_loop = 0
count = 0


def clamp(v, a, b):
    return a if v < a else (b if v > b else v)


def manual_line(s):
    global manual, blend, tx, ty
    if s == 'M':
        manual = True
        blend = False
        tx = mx
        ty = my
        hub.light.on(Color.MAGENTA)
        print('MAN', 1)
    elif s == 'Q':
        manual = False
        blend = True
        print('MAN', 0)
    elif s[0] == 'G' and manual:
        k = s.find(',')
        if k > 1:
            try:
                nx = int(s[1:k]) / 100
                ny = int(s[k + 1:]) / 100
            except ValueError:
                return
            tx = clamp(nx, -1, 31)
            ty = clamp(ny, -1, 31)


if IS_SENDER:
    next_bcast = 0
    next_status = 0

    def command(c, raw):
        global P0, P1, next_bcast
        if c == 'x':
            v = vt(raw)
            P0 = [raw, v, 9, 0]
            P1 = [raw, v, 9, 0]
            emergency()
        if c == 'e':
            # fin des programmes : les vehicules 1 a 3 s'arretent sur place (pour recevoir un nouveau programme)
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
    # Synchronisation de l'horloge sur celle du vehicule 4 (meme methode que le programme d'origine)
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
            # le vehicule 4 a redemarre : on repart de zero
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

    hub.light.on(Color.GREEN)

while True:
    local = watch.time()
    while keyboard.poll(0):
        c = stdin.read(1)
        if c == '\n':
            if line:
                if IS_SENDER and line in ('p', 'z', 'h', 'x', 'e'):
                    command(line, local)
                else:
                    manual_line(line)
            line = ''
        elif len(line) < 24:
            line += c
    if IS_SENDER:
        raw = local
        if raw >= next_bcast:
            hub.ble.broadcast((raw + COMP, P1[0], P1[1], P1[2] + 1 + 16 * GEN, P1[3]))
            # pendant la conduite manuelle, la radio est soulagee (les autres sont immobiles)
            next_bcast = raw + (BCAST_MS * 2 if manual else BCAST_MS)
            count += 1
            if not manual:
                hub.light.on(battery_color() if count % 2 else Color.WHITE)
        if raw >= next_status:
            next_status = raw + (1000 if manual else 400)
            v = vt(raw)
            p = P1 if raw >= P1[0] else P0
            st = 'E' if p[2] >= 9 else ('P' if p[2] == 0 else ('S' if v == p[3] else ('F' if p[2] > 0 else 'B')))
            w = wrap(v)
            print('ST', st, w, chor_index(w), 1 if raw < P1[0] else 0, hub.battery.voltage(), GEN)
    else:
        data = hub.ble.observe(CHANNEL)
        if data is not None and len(data) == 5 and data[3] // 16 == GEN:
            if feed(data[0]):
                count += 1
                if not manual:
                    hub.light.on(battery_color() if count % 2 else Color.WHITE)
            q = [data[1], data[2], data[3] % 16 - 1, data[4]]
            if q != P1:
                P0 = P1
                P1 = q
            if P1[2] == 9:
                emergency()
            if P1[2] == 12:
                # le vehicule 4 demande la fin du programme : on s'arrete sur place
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
    if manual or blend:
        # deplacement a vitesse limitee vers la cible manuelle (ou vers la choregraphie apres Q)
        gx = tx if manual else x
        gy = ty if manual else y
        step = VMAN * (local - last_loop)
        dx = gx - mx
        dy = gy - my
        d = (dx * dx + dy * dy) ** 0.5
        if d <= step:
            mx = gx
            my = gy
            if blend:
                blend = False
        else:
            mx += dx * step / d
            my += dy * step / d
        x = mx
        y = my
    else:
        mx = x
        my = y
    last_loop = local
    x_motor.track_target(x * GEAR)
    y_motor.track_target(y * GEAR)
    wait(5)
