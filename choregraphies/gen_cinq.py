"""Generate 5 choreographies for the 4 ODV vehicles. Each starts and ends at
(30,0) (20,0) (10,0) (0,0), so they can be chained inside the main loop."""
import math

def fmt(v):
    v = round(v, 2) + 0.0
    return '%d' % round(v) if abs(v - round(v)) < 1e-9 else '%.2f' % v

class Block:
    def __init__(self, title, desc):
        self.L = ['    # ' + '=' * 70, '    # ' + title]
        for d in desc: self.L.append('    #   ' + d)
        self.L.append('    # ' + '=' * 70)
    def c(self, txt): self.L.append('    # ' + txt)
    def mv(self, P, speed=None):
        s = ', '.join('%s,%s' % (fmt(x), fmt(y)) for x, y in P)
        s = s.replace(',', ', ')
        self.L.append('    mvc.move(%s%s)' % (s, ', speed=%d' % speed if speed else ''))
    def circ(self, r, d, rot, angles, speed=None):
        self.L.append('    mvc.move_circ(%s, "%s", %s, %s%s)' % (fmt(r), d, fmt(rot), ', '.join(fmt(a) for a in angles),
                                                              ', speed=%d' % speed if speed else ''))
    def w(self, ms): self.L.append('    mvc.wait_sync_ms(%d)' % ms)
    def text(self): return '\n'.join(self.L) + '\n'

HOME = [(30, 0), (20, 0), (10, 0), (0, 0)]
out = []

# ---------------------------------------------------------------- 1. Carrousel
b = Block('1. CARROUSEL : 4 véhicules sur un anneau de 8 cases, pas à pas',
          ['Les véhicules occupent une case sur deux et avancent ensemble d\'une case.',
           'Lent avec des pauses, puis rapide, puis demi-tour.'])
RING = [(5, 5), (15, 5), (25, 5), (25, 15), (25, 25), (15, 25), (5, 25), (5, 15)]
start_idx = [2, 4, 6, 0]          # V1 (25,5)  V2 (25,25)  V3 (5,25)  V4 (5,5)
b.c('mise en place')
b.mv([(30, 0), (20, 25), (10, 25), (0, 0)])
b.mv([RING[k] for k in start_idx])
b.w(600)
idx = start_idx[:]
b.c('un tour lent, case par case')
for _ in range(8):
    idx = [(k + 1) % 8 for k in idx]; b.mv([RING[k] for k in idx], speed=45); b.w(150)
b.c('un tour rapide')
for _ in range(8):
    idx = [(k + 1) % 8 for k in idx]; b.mv([RING[k] for k in idx])
b.w(500)
b.c('demi-tour : un tour dans l\'autre sens')
for _ in range(8):
    idx = [(k - 1) % 8 for k in idx]; b.mv([RING[k] for k in idx], speed=80)
b.w(500)
b.c('retour')
b.mv([(30, 0), (20, 25), (10, 25), (0, 0)])
b.mv(HOME)
b.w(1000)
out.append(('Carrousel', b.text()))

# ---------------------------------------------------------------- 2. Kaléidoscope
b = Block('2. KALÉIDOSCOPE : symétries en miroir puis en rotation',
          ['V1 dessine une courbe dans son quart de plateau, les trois autres en sont',
           'les reflets (miroir), puis les copies tournées de 90° (moulin).'])
def mirror(P):  x, y = P; return [(x, y), (x, 30 - y), (30 - x, 30 - y), (30 - x, y)]
def rot(P):     x, y = P; return [(x, y), (30 - y, x), (30 - x, 30 - y), (y, 30 - x)]
b.c('mise en place aux quatre coins')
b.mv([(30, 0), (20, 30), (10, 30), (0, 0)])
b.mv([(30, 0), (30, 30), (0, 30), (0, 0)])
b.w(600)
b.c('miroir : courbe de Lissajous 2:3')
n = 60
for k in range(1, n + 1):
    u = 2 * math.pi * k / n
    b.mv(mirror((25 + 5 * math.cos(2 * u), 5 - 5 * math.cos(3 * u))))
b.w(600)
b.c('moulin : cercle de rayon 5, copies tournées de 90°, deux tours')
b.mv(rot((30, 5)))
n = 36
for k in range(1, 2 * n + 1):
    u = 2 * math.pi * k / n
    b.mv(rot((25 + 5 * math.cos(u), 5 + 5 * math.sin(u))))
b.w(600)
b.c('retour')
b.mv([(30, 0), (30, 30), (0, 30), (0, 0)])
b.mv([(30, 0), (20, 30), (10, 30), (0, 0)])
b.mv(HOME)
b.w(1000)
out.append(('Kaléidoscope', b.text()))

# ---------------------------------------------------------------- 3. Tourbillons
b = Block('3. TOURBILLONS : chaque véhicule tourne sur son propre petit cercle',
          ['Quatre cercles de rayon 5 (move_circ), d\'abord en décalage de phase comme',
           'des engrenages, puis tous en phase, puis en vague.'])
CENT = [(25, 5), (25, 25), (5, 25), (5, 5)]
def on_circle(phases):
    return [(cx + 5 * math.sin(math.radians(a)), cy + 5 * math.cos(math.radians(a))) for (cx, cy), a in zip(CENT, phases)]
ph = [0, 90, 180, 270]
b.c('mise en place')
b.mv([(30, 0), (20, 25), (10, 25), (0, 0)])
b.mv(on_circle(ph))
b.w(600)
b.c('engrenages : phases décalées de 90°')
b.circ(5, 'CW', 720, ph, speed=70)
b.w(400)
ph = [0, 0, 0, 0]
b.c('tous en phase')
b.mv(on_circle(ph))
b.w(300)
b.circ(5, 'CW', 720, ph, speed=80)
b.w(400)
ph = [0, 45, 90, 135]
b.c('en vague (45° de décalage), sens inverse')
b.mv(on_circle([a + 180 for a in ph]))  # en CCW, move_circ ajoute 180° à l'angle de départ
b.w(300)
b.circ(5, 'CCW', 720, ph, speed=80)
b.w(400)
b.c('retour')
b.mv([(30, 0), (20, 25), (10, 25), (0, 0)])
b.mv(HOME)
b.w(1000)
out.append(('Tourbillons', b.text()))

# ---------------------------------------------------------------- 4. Petit train
b = Block('4. PETIT TRAIN : les véhicules se suivent sur un circuit sinueux',
          ['Départ échelonné (écart de 20 pas pour passer les virages), deux tours,',
           'puis les wagons se resserrent en gare au point de départ.'])
CIRC = [(30, 0), (0, 0), (0, 30), (30, 30), (30, 20), (10, 20), (10, 10), (30, 10), (30, 0)]
SEG = [math.dist(CIRC[i], CIRC[i + 1]) for i in range(len(CIRC) - 1)]
LAP = sum(SEG)
def at(s):
    s %= LAP
    for i, l in enumerate(SEG):
        if s <= l + 1e-9:
            (x0, y0), (x1, y1) = CIRC[i], CIRC[i + 1]; f = s / l
            return (x0 + f * (x1 - x0), y0 + f * (y1 - y0))
        s -= l
home_s = [0, 10, 20, 30]           # V1..V4 along the circuit
LAPS, DS, GAP = 2, 5, 20
s = home_s[:]
end4 = home_s[3] + LAPS * LAP
b.c('départ échelonné et deux tours')
while s[3] < end4:
    s[3] += DS
    for j in (2, 1, 0):
        s[j] = max(s[j], s[j + 1] - GAP)
    b.mv([at(v) for v in s])
b.c('arrivée en gare : les wagons se resserrent')
while any(s[j] < home_s[j] + LAPS * LAP for j in range(3)):
    for j in (2, 1, 0):
        s[j] = min(home_s[j] + LAPS * LAP, s[j] + DS, s[j + 1] - 10)
    b.mv([at(v) for v in s])
b.w(1000)
out.append(('Petit train', b.text()))

# ---------------------------------------------------------------- 5. Formation
b = Block('5. FORMATION : un bloc 2×2 qui voyage, explose et se reforme',
          ['Les quatre véhicules collés se déplacent comme un seul objet (carré puis',
           'cercle avec move_circ), s\'écartent vers les coins, tournent, et se regroupent.'])
def blk(cx, cy): return [(cx + 5, cy - 5), (cx - 5, cy - 5), (cx + 5, cy + 5), (cx - 5, cy + 5)]
b.c('assemblage du bloc')
b.mv([(30, 0), (20, 0), (10, 10), (0, 10)])
b.mv(blk(25, 5))
b.w(600)
b.c('le bloc fait le tour du plateau')
for c in [(5, 5), (5, 25), (25, 25), (25, 5)]:
    b.mv(blk(*c), speed=70)
b.w(400)
b.c('le bloc décrit un cercle')
b.mv(blk(25, 15))
b.circ(10, 'CW', 360, [90, 90, 90, 90], speed=70)  # angle 90 : centre du cercle en (15,15)
b.w(300)
b.c('explosion vers les coins, deux fois')
CORN = [(30, 0), (0, 0), (30, 30), (0, 30)]
b.mv(blk(15, 15))
for sp in (60, 100):
    b.w(400); b.mv(CORN, speed=sp); b.w(400); b.mv(blk(15, 15), speed=sp)
b.w(300)
b.mv(CORN)
b.c('ronde des coins')
ring = [(30, 0), (0, 0), (0, 30), (30, 30)]
pos = [ring.index(p) for p in CORN]
for _ in range(4):
    pos = [(k + 1) % 4 for k in pos]; b.mv([ring[k] for k in pos], speed=90)
b.w(400)
b.c('regroupement et retour')
b.mv(blk(15, 15))
b.mv(blk(25, 5))
b.mv([(30, 0), (20, 0), (10, 10), (0, 10)])
b.mv(HOME)
b.w(1000)
out.append(('Formation', b.text()))

for i, (name, txt) in enumerate(out, 1):
    open('choreo%d.py' % i, 'w').write(txt)
open('cinq_choregraphies.py', 'w').write(
    '# Cinq chorégraphies pour ODV_Cfg05 (4 véhicules).\n'
    '# Chacune part de (30,0) (20,0) (10,0) (0,0) et y revient : colle celles que tu veux\n'
    '# dans la boucle "while True:" des 4 fichiers, avec la même indentation (4 espaces).\n\n'
    + '\n'.join(t for _, t in out))
print('ok')
