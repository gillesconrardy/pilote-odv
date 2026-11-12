import asyncio, os
from playwright.async_api import async_playwright
# éditeur de plateau (v1.89) : poser/enlever des blocs, point de décharge, mémorisé
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 412, 'height': 900}, device_scale_factor=2)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(600)
        await pg.click('nav button[data-tab=setup]'); await pg.wait_for_timeout(1200); await pg.evaluate("document.getElementById('boardCard').open = true"); await pg.wait_for_timeout(300)
        cv = pg.locator('#bdCv'); await cv.scroll_into_view_if_needed(); bb = await cv.bounding_box()
        M = 18 / 640 * bb['width']
        async def view(): return await pg.evaluate('bdView()')
        def at(V, bx, by):
            C = (bb['width'] - 2 * M) / V['n']
            return (bb['x'] + M + (V['x1'] - bx + .5) * C, bb['y'] + M + (by - V['y0'] + .5) * C)
        print('départ', await pg.evaluate('BDE.cells.length'))
        # couloir : du bloc (3,3) vers la gauche jusqu'à (6,3), puis vers le bas jusqu'à (6,6)
        V = await view(); print('vue', V)
        x0, y0 = at(V, 4, 3); x1, y1 = at(V, 5, 3); x2, y2 = at(V, 5, 5)
        await pg.mouse.move(x0, y0); await pg.mouse.down(); await pg.mouse.move(x1, y1, steps=8); await pg.mouse.move(x2, y2, steps=8); await pg.mouse.up()
        # la grille s'est agrandie : on continue le couloir plus loin, puis un bloc à droite du coin (x négatif) et au-dessus (y négatif)
        V = await view(); print('vue', V)
        x0, y0 = at(V, 5, 6); x1, y1 = at(V, 5, 7); await pg.mouse.move(x0, y0); await pg.mouse.down(); await pg.mouse.move(x1, y1, steps=6); await pg.mouse.up()
        V = await view(); await pg.mouse.click(*at(V, -1, 0)); V = await view(); await pg.mouse.click(*at(V, 0, -1))
        print('zone rouge refusée', not await pg.evaluate('bdeHas(-1,0) || bdeHas(0,-1)')); assert not await pg.evaluate('bdeHas(-1,0) || bdeHas(0,-1)')
        V = await view(); await pg.mouse.click(*at(V, -1, 1)); V = await view(); await pg.mouse.click(*at(V, 2, -1))
        V = await view(); print('vue', V, 'blocs', await pg.evaluate('BDE.cells.length'))
        assert await pg.evaluate("bdeHas(5,7) && bdeHas(-1,1) && bdeHas(2,-1)")
        await pg.mouse.click(*at(V, 0, 0)); print('coin gardé', await pg.evaluate('bdeHas(0,0)'))
        await pg.click('#bdMode button[data-m=d]'); V = await view(); await pg.mouse.click(*at(V, 7, 7))
        print('hors bloc', await pg.evaluate('JSON.stringify(BDE.d)'))
        V = await view(); await pg.mouse.click(*at(V, 5, 7))
        print('décharge', await pg.evaluate('JSON.stringify(BDE.d)'), '|', await pg.inner_text('#bdInfo'))
        assert await pg.evaluate('BDE.d[0] === 5 && BDE.d[1] === 7')
        print('avant validation', await pg.inner_text('#bdSum'), '| plateau utilisé', await pg.evaluate('BD.cells.length'))
        assert await pg.evaluate('BD.cells.length') == 16
        await pg.click('#bdOk'); await pg.wait_for_timeout(200)
        print('après validation', await pg.inner_text('#bdSum'), '| plateau utilisé', await pg.evaluate('BD.cells.length'), '| programme V4 :', await pg.evaluate("(progFor ? 1 : 0)") if False else '')
        assert await pg.evaluate('BD.cells.length') == 24
        src = await pg.evaluate("ODVGEN.buildProgram(RUNTIME, idleTL(), 4, {board: bdPairs()})")
        line = [l for l in src.split('\n') if l.startswith('BOARD')][0]; print(line[:80], '…'); assert '(5, 7)' in line
        await pg.reload(); await pg.wait_for_timeout(600)
        print('mémorisé', await pg.evaluate('BDE.cells.length'), await pg.evaluate('JSON.stringify(BDE.d)'))
        await pg.click('nav button[data-tab=setup]'); await pg.wait_for_timeout(1200); await pg.evaluate("document.getElementById('boardCard').open = true"); await pg.wait_for_timeout(300)
        await pg.locator('#boardCard').screenshot(path='/tmp/board.png')
        print('errors', errs); await b.close()
asyncio.run(main())
