"""Construit les deux pages du projet a partir des sources.
   python build.py   ->  index.html (Pilote ODV) et simulateur/index.html
"""
import json, os, sys
from datetime import datetime
from zoneinfo import ZoneInfo
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# Version : "python build.py --publier" augmente le numero et note l'heure (Bruxelles)
VF = 'version.json'
ver = json.load(open(VF)) if os.path.exists(VF) else {'majeur': 1, 'num': 0, 'date': ''}
if '--publier' in sys.argv:
    ver['num'] += 1
    ver['date'] = datetime.now(ZoneInfo('Europe/Brussels')).strftime('%d/%m/%Y %H:%M')
    json.dump(ver, open(VF, 'w'), indent=1)
VERSION = '%d.%d' % (ver['majeur'], ver['num'])
BUILT = ('publiée le ' + ver['date']) if ver['date'] else 'version locale'
import base64
ICON = 'data:image/png;base64,' + base64.b64encode(open('icons/logo-96.png', 'rb').read()).decode()

rd = lambda f: open(f, encoding='utf-8', newline='').read().replace('\r', '')
js = lambda o: json.dumps(o, ensure_ascii=False).replace('</', '<\\/')
C = 'choregraphies/'
CHORS = [  # (nom, fichier, coche par defaut dans Pilote ODV)
    ('Carrousel', '1_carrousel.py', 1), ('Kaléidoscope', '2_kaleidoscope.py', 1),
    ('Tourbillons', '3_tourbillons.py', 1), ('Petit train', '4_petit_train.py', 1),
    ('Formation', '5_formation.py', 1),
    ("Chorégraphie d'origine (8, boucles, cercles…)", '7_origine_corrigee.py', 0)]
core = rd('src/core.js')

# --- Pilote ODV (index.html)
pre = [{'name': n, 'src': rd(C + f), 'def': d} for n, f, d in CHORS]
page = rd('src/page.html').replace('/*CORE*/', core).replace('/*GEN*/', rd('src/odvgen.js')) \
    .replace('/*RUNTIME*/', js(rd('src/runtime.py'))).replace('/*PRESETS*/', js(pre)) \
    .replace('/*VERSION*/', VERSION).replace('/*BUILT*/', BUILT).replace('/*ICON*/', ICON) \
    .replace('/*ROUTINE*/', js(rd(C + 'routine_spirale_pulsation.py')))   # routine spéciale, toujours chargée (montre)
def i18n_dict():
    # traduction anglaise (v1.95) : src/i18n/*.txt, une ligne « français<TAB>anglais » ; {0} {1}… = morceaux variables (modèles)
    import glob, re
    ex, pat = {}, []
    for f in sorted(glob.glob('src/i18n/*.txt')):
        for ln in rd(f).split('\n'):
            if not ln.strip() or ln.startswith('#'):
                continue
            fr, en = ln.split('\t')
            (pat.append([fr, en]) if re.search(r'\{\d+\}', fr) else ex.__setitem__(fr, en))
    return js({'exact': ex, 'pat': pat})
I18N_JS = rd('src/i18n.js').replace('/*I18N*/', i18n_dict())
page = page.replace('/*I18NJS*/', I18N_JS)
open('index.html', 'w', encoding='utf-8').write(page)

# --- Simulateur (simulateur/index.html)
five = '\n'.join(rd(C + f) for _, f, _ in CHORS[:5])
sim = [{'name': '%d · %s' % (i + 1, n), 'src': rd(C + f)} for i, (n, f, _) in enumerate(CHORS[:5])]
sim += [{'name': 'Les 5 à la suite', 'src': five}, {'name': 'Routine Spirale + Pulsation', 'src': rd(C + 'routine_spirale_pulsation.py')},
        {'name': CHORS[5][0], 'src': rd(C + CHORS[5][1])}]
s = rd('simulateur/template.html').replace('/*CORE*/', core).replace('/*PRESETS*/', js(sim)) \
    .replace('/*VERSION*/', VERSION).replace('/*BUILT*/', BUILT).replace('/*I18NJS*/', I18N_JS)
open('simulateur/index.html', 'w', encoding='utf-8').write(s)
print('v' + VERSION, BUILT, '| index.html', len(page), '| simulateur/index.html', len(s))
