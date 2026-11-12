import asyncio, os
from playwright.async_api import async_playwright
exec(open('t_manual.py').read().split('async def main')[0])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 412, 'height': 900}, device_scale_factor=2)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        await pg.add_init_script(MOCK)
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(500)
        await pg.click('nav button[data-tab=setup]'); await pg.click('#suSolo')
        for _ in range(60):
            if await pg.evaluate('M.active'): break
            await pg.wait_for_timeout(300)
        print('axGo actif', await pg.evaluate("!$('axGo').disabled"))
        await pg.evaluate("R.hub.onLine('HON')"); await pg.wait_for_timeout(600)   # « Pousser » s'active tout seul à la prise en main
        print('mode', await pg.evaluate('[M.hand, M.hmode]'), 'joystick caché', await pg.evaluate("$('joyBox').style.display"), '| suivre', await pg.evaluate("$('handGo').disabled"))
        print('envoyé', [t for n, t in await pg.evaluate('window.__stdin') if t[0] == 'H'])
        await pg.evaluate("R.hub.onLine('HD 240 6')"); print('1:', await pg.inner_text('#handSt'))
        await pg.evaluate("R.hub.onLine('HD 30 5')"); print('2:', await pg.inner_text('#handSt'))
        await pg.evaluate("R.hub.onLine('HD 30 6')"); print('3:', await pg.inner_text('#handSt'))
        await pg.evaluate("R.hub.onLine('HD 30 7')"); await pg.wait_for_timeout(700); await pg.evaluate("R.hub.onLine('HD 30 7')"); print('4:', await pg.inner_text('#handSt'))
        await pg.locator('#cv').screenshot(path='/tmp/hold.png')
        await pg.locator('#manCard').screenshot(path='/tmp/push.png')
        await pg.click('#axGo'); await pg.wait_for_timeout(300)
        print('arrêt', await pg.evaluate('M.hand'), [t for n, t in await pg.evaluate('window.__stdin') if t[0] == 'H'])
        print('errors', errs); await b.close()
asyncio.run(main())
