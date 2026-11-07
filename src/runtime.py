# =====================================================================
#  ODV - programme genere par "Pilote ODV"   (vehicule %VID%)
#  Choregraphies : %NAMES%
#  Ne pas modifier a la main : regenerer depuis la page Pilote ODV.
# =====================================================================
from pybricks.hubs import TechnicHub
from pybricks.pupdevices import Motor, Remote
from pybricks.parameters import Port, Direction, Color, Button
from pybricks.tools import wait, StopWatch
from umath import sin, cos, pi

VEHICLE_ID = %VID%
SENDER_ID = 4                 # le vehicule 4 diffuse l'horloge et recoit les commandes du telephone
IS_SENDER = VEHICLE_ID == SENDER_ID
ME = VEHICLE_ID - 1            # indice du vehicule (0 a 3)
# couleur de la LED du hub = couleur du vehicule dans l'appli (V1 bleu, V2 orange, V3 vert, V4 violet)
VHUE = (215, 28, 140, 270)[ME]
VCOL = Color(VHUE, 100, 100)
VDIM = Color(VHUE, 100, 30)   # pulsation : couleur pleine / couleur attenuee
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
    return VCOL


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
hub.light.on(VCOL)
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


# Telecommande LEGO (vehicule 4) : connectee a la demande (commande C), active seulement en manuel.
remote = None
OBS = [None, None, None]      # positions des 3 autres vehicules (envoyees par l'appli : O1x,y O2x,y O3x,y)
MSPD = 0.006                  # vitesse a la telecommande (pas/ms), reglee par l'appli (commande V)
last_g = -10000               # derniere cible recue de l'appli (joystick ou retour) : prioritaire
rc_until = 0
next_pos = 0


def free_at(x, y):
    if x < 0 or x > 30 or y < 0 or y > 30:
        return False
    for o in OBS:
        if o is not None and abs(x - o[0]) < 10 - 1e-6 and abs(y - o[1]) < 10 - 1e-6:
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
    global manual, blend, tx, ty, MSPD, last_g, game, CSPD, g_round, g_catch, g_freeze, g_mover, g_stuck, b_ret, g_way
    if s[0] == 'D':
        try:
            CSPD = clamp(int(s[1:]) / 100000, 0.001, 0.012)
        except ValueError:
            pass
        return
    if s == 'J':
        b_ret = False
        if IS_SENDER and manual and game == 0 and None not in OBS:
            for k in range(3):
                GC[k][0] = OBS[k][0]
                GC[k][1] = OBS[k][1]
                GH[k] = OBS[k]
            game = 1
            g_catch = 0
            g_round = watch.time() + 1500
            g_freeze = g_round
            g_mover = -1
            g_stuck = False
            print('JON')
        else:
            print('JNO')
        return
    if s == 'B':
        # billes : les 4 vehicules roulent selon l'inclinaison du telephone (commande T)
        if IS_SENDER and manual and game == 0 and None not in OBS:
            for k in range(3):
                GC[k][0] = OBS[k][0]
                GC[k][1] = OBS[k][1]
                GH[k] = OBS[k]
                BV[k][0] = 0.0
                BV[k][1] = 0.0
            BV[3][0] = 0.0
            BV[3][1] = 0.0
            B4[0] = tx
            B4[1] = ty
            B4H[0] = tx
            B4H[1] = ty
            TILT[0] = 0.0
            TILT[1] = 0.0
            b_snapshot(watch.time(), True)
            game = 4
            g_mover = -1
            g_stuck = False
            print('BON')
        else:
            print('JNO')
        return
    if s[0] == 'T' and len(s) > 2:
        k = s.find(',')
        try:
            TILT[0] = clamp(int(s[1:k]) / 100, -1, 1)
            TILT[1] = clamp(int(s[k + 1:]) / 100, -1, 1)
        except (ValueError, IndexError):
            pass
        return
    if s == 'K':
        b_ret = game == 4
        if game == 4:
            TILT[0] = 0.0
            TILT[1] = 0.0
        if game in (1, 4):
            game = 2
            g_mover = -1
            print('JRET')
        return
    if s[0] == 'W' and len(s) > 3:
        # apres les billes : deplacer le vehicule s[1] (1..4) tout droit vers x,y (x100)
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
        if game in (1, 2, 4):
            print('BUSY')
            return
        game = 0
        manual = False
        blend = True
        print('MAN', 0)
    elif s[0] == 'G' and manual and game != 4:
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
                # pendant le jeu, la cible du joueur ne doit pas entrer dans un chasseur
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


# ---------------------------------------------------------------- jeu de poursuite
# Le vehicule 4 (joue par Gilles) calcule les deplacements des chasseurs V1..V3 et les leur diffuse.
game = 0                      # 0 non, 1 poursuite, 2 retour des chasseurs, 3 chasseurs rentres
GC = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]   # positions prevues des chasseurs
GH = [(0, 0), (0, 0), (0, 0)]                # leur place au debut du jeu
CSPD = 0.005                  # vitesse des chasseurs (pas/ms), reglee par l'appli (commande D)
g_freeze = 0
g_round = 0
g_catch = 0
g_mover = -1
g_way = []
g_stuck = False
g_next_jp = 0
game_rx = False               # (vehicules 1 a 3) on suit les positions diffusees par le vehicule 4
grate = 0.006
last_game = 0
# billes (game 4) : B4 = position prevue du vehicule 4, BV = vitesses (pas/ms), TILT = inclinaison -1..1
B4 = [0.0, 0.0]
BV = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
TILT = [0.0, 0.0]
BK = (0.7, 1.0, 1.3, 0.85)    # chaque bille a son poids (elan et vitesse max), pour qu'elles s'etalent


B4H = [0.0, 0.0]
b_ret = False


def b_pos(k):
    return B4 if k == 3 else GC[k]


def b_home(k):
    return B4H if k == 3 else GH[k]


BOLD = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]   # positions d'il y a 250 a 500 ms
BNOW = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
b_snap = 0


def b_ok(k, x, y):
    # les suiveurs ont jusqu'a ~250 ms de retard radio : on garde 11 pas avec la position prevue
    # ET avec celle d'il y a un quart de seconde ; en dessous, on ne peut que s'eloigner
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


def billes_tick(dt):
    # la +X du plateau est vers la gauche : pencher a droite (TILT[0] > 0) fait diminuer x
    if dt > 50:
        dt = 50
    acc = CSPD / 450
    ax = -TILT[0] * acc
    ay = TILT[1] * acc
    fr = 1 - dt / (700 if (TILT[0] == 0 and TILT[1] == 0) else 2500)
    for k in range(4):
        v = BV[k]
        c = b_pos(k)
        v[0] = (v[0] + ax * BK[k] * dt) * fr
        v[1] = (v[1] + ay * BK[k] * dt) * fr
        n = (v[0] * v[0] + v[1] * v[1]) ** 0.5
        vm = CSPD * BK[k]
        if n > vm:
            v[0] *= vm / n
            v[1] *= vm / n
        nx = c[0] + v[0] * dt
        ny = c[1] + v[1] * dt
        # rebond amorti contre la cloture
        if nx < 0:
            nx = 0
            v[0] = -v[0] * 0.3
        elif nx > 30:
            nx = 30
            v[0] = -v[0] * 0.3
        if ny < 0:
            ny = 0
            v[1] = -v[1] * 0.3
        elif ny > 30:
            ny = 30
            v[1] = -v[1] * 0.3
        if b_ok(k, nx, ny):
            c[0] = nx
            c[1] = ny
        elif b_ok(k, nx, c[1]):
            c[0] = nx
            v[1] = 0.0
        elif b_ok(k, c[0], ny):
            c[1] = ny
            v[0] = 0.0
        else:
            v[0] = 0.0
            v[1] = 0.0


def cheb(ax, ay, bx, by):
    dx = ax - bx
    dy = ay - by
    return max(dx if dx > 0 else -dx, dy if dy > 0 else -dy)


def g_ok(k, x, y):
    # un chasseur peut-il aller en (x, y) ? jamais a moins de 10 pas d'un autre vehicule ; sous la marge
    # (11 pas entre chasseurs, 10,5 du joueur) il ne peut que s'eloigner ou rester a distance egale
    if x < 0 or x > 30 or y < 0 or y > 30:
        return False
    cx = GC[k][0]
    cy = GC[k][1]
    for j in range(4):
        if j == k:
            continue
        if j == 3:
            ox = mx
            oy = my
            mg = 10.5
        else:
            ox = GC[j][0]
            oy = GC[j][1]
            mg = 11
        dn = cheb(x, y, ox, oy)
        if dn < 10 or (dn < mg and dn < cheb(cx, cy, ox, oy) - 1e-9):
            return False
    if cheb(x, y, tx, ty) < 10:
        return False
    return True


def seg_clear(ax, ay, bx, by, obs):
    # le trajet a->b reste-t-il a 10 pas ou plus (Chebyshev) de chaque obstacle ?
    m = 10 - 1e-6
    for o in obs:
        lo = 0.0
        hi = 1.0
        inside = True
        for s0, s1 in ((ax - o[0], bx - o[0]), (ay - o[1], by - o[1])):
            d = s1 - s0
            if -1e-12 < d < 1e-12:
                if s0 >= m or s0 <= -m:
                    inside = False
                    break
                continue
            u1 = (-m - s0) / d
            u2 = (m - s0) / d
            if u1 > u2:
                u1, u2 = u2, u1
            lo = max(lo, u1)
            hi = min(hi, u2)
            if hi - lo <= 1e-9:
                inside = False
                break
        if inside and hi - lo > 1e-9:
            return False
    return True


def game_tick(dtg, local):
    global game, g_freeze, g_round, g_catch, g_mover, g_way, g_stuck
    if game == 1 and local >= g_freeze:
        st = CSPD * dtg
        for k in range(3):
            c = GC[k]
            dx = mx - c[0]
            dy = my - c[1]
            d = (dx * dx + dy * dy) ** 0.5
            if d > 0.01:
                nx = c[0] + dx * st / d
                ny = c[1] + dy * st / d
                if g_ok(k, nx, ny):
                    c[0] = nx
                    c[1] = ny
                elif g_ok(k, nx, c[1]):
                    c[0] = nx
                elif g_ok(k, c[0], ny):
                    c[1] = ny
        for k in range(3):
            if cheb(GC[k][0], GC[k][1], mx, my) < 10.8:
                g_catch += 1
                print('CATCH', g_catch, local - g_round)
                g_freeze = local + 2500
                g_round = g_freeze
                break
    elif game == 1:
        # pause apres une prise : les chasseurs reculent pour laisser le joueur s'echapper
        st = CSPD * dtg
        for k in range(3):
            c = GC[k]
            dx = c[0] - mx
            dy = c[1] - my
            if cheb(c[0], c[1], mx, my) >= 15:
                continue
            d = (dx * dx + dy * dy) ** 0.5
            if d < 0.01:
                dx = 0
                dy = -1
                d = 1
            nx = c[0] + dx * st / d
            ny = c[1] + dy * st / d
            if g_ok(k, nx, ny):
                c[0] = nx
                c[1] = ny
            elif g_ok(k, nx, c[1]):
                c[0] = nx
            elif g_ok(k, c[0], ny):
                c[1] = ny
    elif game == 2:
        # retour un par un ; apres les billes, le vehicule 4 fait partie du retour (B4 -> B4H)
        sp = max(CSPD, 0.006) * dtg
        n = 4 if b_ret else 3
        if g_mover < 0 and b_ret:
            pass                  # apres les billes, l'appli envoie les deplacements un par un (W, puis Z)
        elif g_mover < 0:
            if all(cheb(b_pos(k)[0], b_pos(k)[1], b_home(k)[0], b_home(k)[1]) < 0.02 for k in range(n)):
                game = 3
                print('JOK')
            else:
                for k in range(n):
                    c = b_pos(k)
                    h = b_home(k)
                    if cheb(c[0], c[1], h[0], h[1]) < 0.02:
                        continue
                    obs = [(b_pos(j)[0], b_pos(j)[1]) for j in range(n) if j != k]
                    if not b_ret:
                        obs.append((mx, my))
                    for path in ([h], [(h[0], c[1]), h], [(c[0], h[1]), h]):
                        ok = True
                        ax = c[0]
                        ay = c[1]
                        for w in path:
                            if not seg_clear(ax, ay, w[0], w[1], obs):
                                ok = False
                                break
                            ax = w[0]
                            ay = w[1]
                        if ok:
                            g_mover = k
                            g_way = list(path)
                            break
                    if g_mover >= 0:
                        break
                if g_mover < 0 and not g_stuck:
                    g_stuck = True
                    print('JSTUCK')
        else:
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

    hub.light.on(VCOL)

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
        if raw >= next_bcast and game:
            # jeu : positions prevues des 3 chasseurs (en 1/8 de pas) + leur vitesse (en 0,1 pas/s)
            b = [int(clamp(GC[k // 2][k % 2], 0, 31) * 8 + 0.5) for k in range(6)]
            b.append(int(clamp(max(CSPD * (1.3 if game == 4 else 1), 0.006) * 10000, 1, 255)))
            hub.ble.broadcast((raw + COMP, 7 + 16 * GEN, bytes(b)))
            next_bcast = raw + 150
        elif raw >= next_bcast:
            hub.ble.broadcast((raw + COMP, P1[0], P1[1], P1[2] + 1 + 16 * GEN, P1[3]))
            # pendant la conduite manuelle, la radio est soulagee (les autres sont immobiles)
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
                grate = gb[6] / 10000 * 1.25
                if not game_rx:
                    game_rx = True
                    hub.light.on(VCOL)
        elif data is not None and len(data) == 5 and data[3] // 16 == GEN:
            if game_rx:
                # fin du jeu : on rejoint (en douceur) sa place dans la choregraphie
                game_rx = False
                blend = True
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
    if manual and remote is not None:
        try:
            pr = remote.buttons.pressed()
        except OSError:
            remote = None
            pr = ()
            print('RC', 0)
        # memes boutons que le programme telecommande : gauche = moteur port C (X), droite = moteur port A (Y)
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
    if IS_SENDER and game == 4:
        b_snapshot(local, False)
        billes_tick(local - last_loop)
        tx = B4[0]
        ty = B4[1]
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
        # position du vehicule pour l'appli (souvent si la telecommande bouge, sinon toutes les secondes)
        moving = local < rc_until
        next_pos = local + (200 if moving else 1000)
        print('POS', int(mx * 100), int(my * 100), 1 if moving else 0)
    if manual or blend or game_rx:
        # deplacement a vitesse limitee vers la cible manuelle (ou vers la choregraphie apres Q)
        gx = tx if (manual or game_rx) else x
        gy = ty if (manual or game_rx) else y
        step = (grate if game_rx else VMAN) * (local - last_loop)
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
