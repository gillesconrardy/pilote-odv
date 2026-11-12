import asyncio, os
from playwright.async_api import async_playwright
exec(open('t_manual.py').read().split('async def main')[0])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--autoplay-policy=no-user-gesture-required'])
        pg = await b.new_page(viewport={'width': 412, 'height': 900})
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
        # plateau : le 4×4 + une colonne de 2 blocs sous le coin, décharge au bout
        await pg.evaluate("BD.cells = bdSquare().concat(['0,4','0,5']); BD.d = [0,5]; bdChanged(); drawBoard && drawBoard()")
        print('V4', await pg.evaluate('JSON.stringify(M.cmd)'), 'autres', await pg.evaluate('JSON.stringify(M.others)'))
        n0 = len(await pg.evaluate('window.__stdin || []'))
        # toucher le V4 sur le plateau
        await pg.evaluate("""(() => { const c = $('cv'), r = c.getBoundingClientRect(), G = plateGeo(c.width), x = G.X(M.cmd[0]) * r.width / c.width + r.left, y = G.Y(M.cmd[1]) * r.height / c.height + r.top;
          c.dispatchEvent(new PointerEvent('pointerdown', {pointerId: 5, clientX: x, clientY: y, bubbles: true})); c.dispatchEvent(new PointerEvent('pointerup', {pointerId: 5, clientX: x, clientY: y, bubbles: true})); })()""")
        await pg.wait_for_timeout(300)
        st = [t for n, t in (await pg.evaluate('window.__stdin'))[n0:]]
        print('armé', await pg.evaluate('M.arm'), st); assert 'A1' in st
        await pg.screenshot(path='/tmp/dump_arm.png')
        await pg.evaluate("R.hub.onLine('DG')"); await pg.wait_for_timeout(200)
        print('auto', await pg.evaluate('JSON.stringify(M.auto && M.auto.pts)'))
        assert await pg.evaluate('!!M.auto')
        best = 0
        for k in range(60):
            await pg.wait_for_timeout(500)
            y = await pg.evaluate('M.cmd[1]'); best = max(best, y)
            if k == 8: await pg.screenshot(path='/tmp/dump_go.png')
            if not await pg.evaluate('!!M.auto'): break
        print('plus bas atteint', round(best, 2), '| fin', await pg.evaluate('JSON.stringify(M.cmd)'), '| msg', await pg.inner_text('#fMsg'))
        assert best > 49.9 and await pg.evaluate('Math.hypot(M.cmd[0], M.cmd[1]) < 0.1')
        g = [t for n, t in (await pg.evaluate('window.__stdin'))[n0:] if t.startswith('G')]
        print('G envoyés', len(g), g[:2], g[-1:])
        print('errors', errs); await b.close()
asyncio.run(main())
