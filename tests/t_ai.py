import asyncio, os, json
from playwright.async_api import async_playwright
# réponse 1 : collision (V2 sur V1) ; réponse 2 : correcte mais sans retour (le bouton ⌂ est appliqué)
R1 = {"name": "Carré tournant", "steps": [{"pos": [[30,20],[25,0],[10,0],[0,0]], "speed": 60, "wait": 500}, {"pos": [[30,0],[20,0],[10,0],[0,0]], "speed": 60, "wait": 0}]}
R2 = {"name": "Carré tournant", "steps": [{"pos": [[30,20],[20,0],[10,0],[0,20]], "speed": 60, "wait": 500}, {"pos": [[20,20],[30,0],[0,0],[10,20]], "speed": 50, "wait": 333}]}
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 412, 'height': 900}, device_scale_factor=2)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        calls = []
        async def handle(route):
            body = json.loads(route.request.post_data); calls.append(body)
            h = route.request.headers
            assert h['x-api-key'] == 'sk-test' and h['anthropic-dangerous-direct-browser-access'] == 'true'
            r = R1 if len(calls) == 1 else R2
            await route.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin': '*'},
                                body=json.dumps({"content": [{"type": "text", "text": "Voici :\n" + json.dumps(r)}]}))
        await pg.route('https://api.anthropic.com/**', handle)
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(300)
        await pg.click('#edNew')
        await pg.fill('#aiTxt', 'un carré qui tourne'); await pg.click('#aiGo'); await pg.wait_for_timeout(300)
        print('sans clé:', await pg.inner_text('#toast'))
        await pg.fill('#aiKey', 'sk-test'); await pg.click('#aiGo'); await pg.wait_for_timeout(1500)
        print('appels:', len(calls), '| modèle', calls[0]['model'], '| 2e message:', calls[1]['messages'][-1]['content'][:160].replace('\n', ' / '))
        print('statut:', await pg.inner_text('#aiSt'))
        print('nom:', await pg.input_value('#edName'), '| étapes:', await pg.inner_text('#edChips'))
        print('contrôle:', (await pg.inner_text('#edCheck')).replace('\n', ' | '), '| save off:', await pg.is_disabled('#edSave'))
        print('clé gardée:', await pg.evaluate("localStorage.getItem('odv.aikey')"))
        await pg.click('#aiGo'); await pg.wait_for_timeout(200)  # confirm -> annulé par défaut
        await pg.locator('#aiTxt').scroll_into_view_if_needed(); await pg.screenshot(path='/home/claude/work/ai1.png')
        print('errors', errs); await b.close()
asyncio.run(main())
