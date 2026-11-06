import math

L = []
def mv(*p, speed=None, c=None):
    if c: L.append('    # ' + c)
    s = ', '.join('%.2f' % v if abs(v - round(v)) > 1e-9 else '%d' % round(v) for v in p)
    if speed: s += ', speed=%d' % speed
    L.append('    mvc.move(%s)' % s)
def w(ms):
    L.append('    mvc.wait_sync_ms(%d)' % ms)
def blank(): L.append('')

L.append('    # ===== Nouvelle chorégraphie : Vague + Spirale + Pulsation =====')
L.append('    # Départ et arrivée : (30,0) (20,0) (10,0) (0,0)')
blank()
L.append('    # --- 1. Vague : ligne horizontale, onde progressive en Y (déphasage 90° entre véhicules)')
mv(30, 15, 20, 15, 10, 15, 0, 15)
w(800)
XS = [30, 20, 10, 0]
SP = 12  # pas par période
for k in range(1, 4 * SP + 1):
    phi = k * 2 * math.pi / SP
    if k <= SP: A = 10 * k / SP
    elif k >= 3 * SP: A = 10 * (4 * SP - k) / SP
    else: A = 10
    p = []
    for i, x in enumerate(XS):
        p += [x, 15 + A * math.sin(phi - i * math.pi / 2)]
    mv(*p)
w(800)
blank()
L.append('    # --- 2. Spirale : carré tournant qui se resserre (R 15 -> 10.5) puis s\'ouvre, 2 tours')
mv(30, 15, 20, 30, 10, 15, 0, 0, c='mise en place (en deux temps pour éviter les croisements)')
mv(30, 15, 15, 30, 0, 15, 15, 0)
w(800)
STEP = 12
for k in range(1, 720 // STEP + 1):
    th = math.radians(k * STEP)
    R = 12.75 + 2.25 * math.cos(th / 2)
    p = []
    for i in range(4):
        a = th + i * math.pi / 2
        p += [15 + R * math.cos(a), 15 + R * math.sin(a)]
    mv(*p)
w(800)
blank()
L.append('    # --- 3. Pulsation : le carré se contracte et se dilate deux fois')
for _ in range(2):
    mv(25, 15, 15, 25, 5, 15, 15, 5, speed=60)
    w(300)
    mv(30, 15, 15, 30, 0, 15, 15, 0, speed=60)
    w(300)
blank()
L.append('    # --- Retour en position de départ')
mv(30, 0, 15, 30, 0, 15, 0, 0)
mv(30, 0, 20, 15, 10, 15, 0, 0)
mv(30, 0, 20, 0, 10, 0, 0, 0)
w(1000)

open('nouvelle_choregraphie.py', 'w').write('\n'.join(L) + '\n')
print(len(L), 'lines')
