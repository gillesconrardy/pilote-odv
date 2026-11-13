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
        # v1.84 : main devant le capteur pendant le spectacle -> l'appli donne la position des 3 autres et suit le V4
        n0 = len(await pg.evaluate('window.__stdin || []'))
        await pg.evaluate("R.hub.onLine('SP 1 5000')"); await pg.wait_for_timeout(600)
        o = [t for n, t in (await pg.evaluate('window.__stdin'))[n0:] if t[0] == 'O']
        print('O envoyés', o, '| SP', await pg.evaluate('JSON.stringify(SP)'))
        assert len(o) == 3 and all(',' in t for t in o)
        await pg.evaluate("R.hub.onLine('POS 300 1500 1')"); await pg.wait_for_timeout(300)
        print('pos suivie', await pg.evaluate('SP.pos'))
        assert await pg.evaluate('SP.pos[0] === 3 && SP.pos[1] === 15')
        await pg.evaluate("R.hub.onLine('SP 0')"); await pg.wait_for_timeout(200)
        assert not await pg.evaluate('SP.on')
        print('errors', errs); await b.close()
asyncio.run(main())
