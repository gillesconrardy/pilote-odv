import asyncio, os
from playwright.async_api import async_playwright
exec(open('t_manual.py').read().split('async def main')[0])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--autoplay-policy=no-user-gesture-required'])
        pg = await b.new_page(locale='fr-FR', viewport={'width': 412, 'height': 900})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        await pg.add_init_script(MOCK)
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(500)
        await pg.click('nav button[data-tab=envoi]')
        for v in (1, 2, 3): await pg.click('#send%d' % v); await pg.wait_for_timeout(1500)
        for _ in range(40):
            if not await pg.evaluate('[1,2,3,4].some(u => V[u].busy)'): break
            await pg.wait_for_timeout(300)
        await pg.click('nav button[data-tab=setup]'); await pg.click('#suSolo')     # V4 en programme sans chorégraphie (idle)
        for _ in range(60):
            if await pg.evaluate('M.active'): break
            await pg.wait_for_timeout(300)
        await pg.evaluate("M.active=false; M.returning=false; manUI()")             # comme après « Rendre la main »
        print('onglet', await pg.evaluate("document.querySelector('section.on').id"), 'R.hub', await pg.evaluate('!!(R.hub && R.hub.connected)')); await pg.evaluate('watchStart()'); await pg.wait_for_timeout(400)
        print('idle', await pg.evaluate('R.idle'), 'montre', await pg.evaluate('WATCH.on'))
        n0 = len(await pg.evaluate('window.__stdin || []'))
        await pg.evaluate('WATCH.h.play()'); await pg.wait_for_timeout(300)
        print('sans les 4 calibrés :', [t for n, t in (await pg.evaluate('window.__stdin'))[n0:] if len(t) == 1])
        await pg.evaluate('SU.done = {1: true, 2: true, 3: true, 4: true}')
        await pg.evaluate('WATCH.h.play()')
        for _ in range(120):
            await pg.wait_for_timeout(500)
            st = [t for n, t in (await pg.evaluate('window.__stdin'))[n0:]]
            if 'p' in st: break
        print('noms', await pg.evaluate('R.names'), '| durée routine', await pg.evaluate('idleTL().total'))
        print('commandes', [t for t in st if len(t) == 1], '| msg', await pg.inner_text('#updMsg'))
        print('errors', errs); await b.close()
asyncio.run(main())
