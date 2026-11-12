import asyncio, os
from playwright.async_api import async_playwright
# éditeur de plateau (v1.89) : poser/enlever des blocs, point de décharge, mémorisé
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 412, 'height': 900}, device_scale_factor=2)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(600)
        await pg.click('nav button[data-tab=setup]'); await pg.wait_for_timeout(1200)
        cv = pg.locator('#bdCv'); await cv.scroll_into_view_if_needed(); bb = await cv.bounding_box()
        M = 18 / 640 * bb['width']
        async def view(): return await pg.evaluate('bdView()')
        def at(V, bx, by):
            C = (bb['width'] - 2 * M) / V['n']
            return (bb['x'] + M + (V['x1'] - bx + .5) * C, bb['y'] + M + (by - V['y0'] + .5) * C)
        print('départ', await pg.evaluate('BD.cells.length'))
        # couloir : du bloc (3,3) vers la gauche jusqu'à (6,3), puis vers le bas jusqu'à (6,6)
        V = await view(); print('vue', V)
        x0, y0 = at(V, 4, 3); x1, y1 = at(V, 5, 3); x2, y2 = at(V, 5, 5)
        await pg.mouse.move(x0, y0); await pg.mouse.down(); await pg.mouse.move(x1, y1, steps=8); await pg.mouse.move(x2, y2, steps=8); await pg.mouse.up()
        # la grille s'est agrandie : on continue le couloir plus loin, puis un bloc à droite du coin (x négatif) et au-dessus (y négatif)
        V = await view(); print('vue', V)
        x0, y0 = at(V, 5, 6); x1, y1 = at(V, 5, 7); await pg.mouse.move(x0, y0); await pg.mouse.down(); await pg.mouse.move(x1, y1, steps=6); await pg.mouse.up()
        V = await view(); await pg.mouse.click(*at(V, -1, 0)); V = await view(); await pg.mouse.click(*at(V, 0, -1))
        print('zone rouge refusée', not await pg.evaluate('bdHas(-1,0) || bdHas(0,-1)')); assert not await pg.evaluate('bdHas(-1,0) || bdHas(0,-1)')
        V = await view(); await pg.mouse.click(*at(V, -1, 1)); V = await view(); await pg.mouse.click(*at(V, 2, -1))
        V = await view(); print('vue', V, 'blocs', await pg.evaluate('BD.cells.length'))
        assert await pg.evaluate("bdHas(5,7) && bdHas(-1,1) && bdHas(2,-1)")
        await pg.mouse.click(*at(V, 0, 0)); print('coin gardé', await pg.evaluate('bdHas(0,0)'))
        await pg.click('#bdMode button[data-m=d]'); V = await view(); await pg.mouse.click(*at(V, 7, 7))
        print('hors bloc', await pg.evaluate('JSON.stringify(BD.d)'))
        V = await view(); await pg.mouse.click(*at(V, 5, 7))
        print('décharge', await pg.evaluate('JSON.stringify(BD.d)'), '|', await pg.inner_text('#bdInfo'))
        assert await pg.evaluate('BD.d[0] === 5 && BD.d[1] === 7')
        await pg.reload(); await pg.wait_for_timeout(600)
        print('mémorisé', await pg.evaluate('BD.cells.length'), await pg.evaluate('JSON.stringify(BD.d)'))
        await pg.click('nav button[data-tab=setup]'); await pg.wait_for_timeout(1200)
        await pg.locator('#boardCard').screenshot(path='/tmp/board.png')
        print('errors', errs); await b.close()
asyncio.run(main())
