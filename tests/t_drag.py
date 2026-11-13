# glisser-déposer des chorégraphies (v1.98) : vers le haut et vers le bas, mouvements rapides, défilement automatique
import asyncio, os, sys
from playwright.async_api import async_playwright
PAGE = sys.argv[1] if len(sys.argv) > 1 else '../index.html'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        ctx = await b.new_context(locale='fr-FR', viewport={'width': 412, 'height': 520}, reduced_motion='reduce')
        await ctx.add_init_script("localStorage.setItem('odv.tab','\"choix\"')")
        pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://' + os.path.abspath(PAGE)); await pg.wait_for_timeout(600)
        names = lambda: pg.evaluate("[...document.querySelectorAll('#chList .ch')].map(c=>c.dataset.id).join(' ')")
        async def drag(src, dy, steps):
            g = pg.locator('#chList .ch .grip').nth(src); await g.scroll_into_view_if_needed()
            bb = await g.bounding_box(); x, y = bb['x'] + 15, bb['y'] + 20
            await pg.mouse.move(x, y); await pg.mouse.down()
            for k in range(1, steps + 1): await pg.mouse.move(x, y + dy * k / steps)
            await pg.wait_for_timeout(400); await pg.mouse.up(); await pg.wait_for_timeout(200)
        print('départ   ', await names())
        await drag(5, -260, 2); print('haut vite', await names())
        await drag(0, 200, 3); print('bas      ', await names())
        await drag(1, -70, 6); print('haut lent', await names())
        # défilement : depuis la dernière ligne, le doigt tenu en haut de l'écran
        g = pg.locator('#chList .ch .grip').last; await g.scroll_into_view_if_needed(); bb = await g.bounding_box()
        await pg.mouse.move(bb['x'] + 15, bb['y'] + 20); await pg.mouse.down(); await pg.mouse.move(bb['x'] + 15, 20, steps=5)
        await pg.wait_for_timeout(2500); await pg.mouse.up(); await pg.wait_for_timeout(200)
        print('défilé   ', await names())
        print('mémorisé ', await pg.evaluate("JSON.parse(localStorage.getItem('odv.order')).join(' ')"))
        print('drag restant', await pg.evaluate("document.querySelectorAll('.ch.drag').length"), 'errors', errs)
        await b.close()
asyncio.run(main())
