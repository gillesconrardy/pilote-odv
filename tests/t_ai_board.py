import asyncio, os, json
from playwright.async_api import async_playwright
# v1.93 : l'IA reçoit le plateau validé + la décharge ; l'éditeur signale HORS ZONE et l'IA doit corriger
H = [[30,0],[20,0],[10,0],[0,0]]
R1 = {"name": "Livraison", "steps": [{"pos": [[30,0],[20,0],[10,0],[0,40]], "speed": 60, "wait": 0}, {"pos": [[30,0],[20,0],[10,0],[10,40]], "speed": 60, "wait": 0}, {"pos": [[30,0],[20,0],[10,0],[0,40]], "speed": 60, "wait": 0}, {"pos": H, "speed": 60, "wait": 0}]}
R2 = {"name": "Livraison", "steps": [{"pos": [[30,0],[20,0],[10,0],[0,50]], "speed": 60, "wait": 3000}, {"pos": H, "speed": 60, "wait": 0}]}
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(locale='fr-FR', viewport={'width': 412, 'height': 900})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        reqs = []
        async def handle(route):
            body = json.loads(route.request.post_data); reqs.append(body)
            out = R1 if len(reqs) == 1 else R2
            await route.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin': '*'},
                                body=json.dumps({"content": [{"type": "text", "text": json.dumps(out)}]}))
        await pg.route('https://api.anthropic.com/**', handle)
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(300)
        # plateau validé : 4×4 + colonne sous le coin, décharge au bout
        await pg.evaluate("BD.cells = bdSquare().concat(['0,4','0,5']); BD.d = [0,5]; bdChanged()")
        await pg.click('nav button[data-tab=choix]'); await pg.click('#edNew')
        await pg.fill('#aiKey', 'sk-test'); await pg.fill('#aiTxt', 'le 4 va livrer à la décharge')
        await pg.click('#aiGo'); await pg.wait_for_timeout(2500)
        sysp = reqs[0]['system']
        print('\n'.join(l for l in sysp.split('\n') if 'PLATEAU' in l or l.strip().startswith(('#', '.')) or 'DÉCHARGE' in l))
        assert 'DÉCHARGE : bloc (0,5)' in sysp and '...D' in sysp
        fb = reqs[1]['messages'][-1]['content']; print('correction demandée :', fb)
        assert 'HORS ZONE' in fb
        print('statut :', await pg.inner_text('#aiSt'))
        assert '✓' in await pg.inner_text('#aiSt')
        print('errors', errs); await b.close()
asyncio.run(main())
