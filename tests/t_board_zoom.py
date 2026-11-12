import asyncio, os
from playwright.async_api import async_playwright
# éditeur de plateau : zoom / dézoom à 2 doigts (événements pointer simulés), sans toucher aux blocs ; ⤢ réajuste
JS = """([id, type, x, y]) => { const cv = document.getElementById('bdCv'), r = cv.getBoundingClientRect();
  cv.dispatchEvent(new PointerEvent(type, {pointerId: id, clientX: r.left + x * r.width, clientY: r.top + y * r.height, bubbles: true, pointerType: 'touch'})); }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 412, 'height': 900})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(600)
        await pg.click('nav button[data-tab=setup]'); await pg.wait_for_timeout(1200); await pg.evaluate("document.getElementById('boardCard').open = true"); await pg.wait_for_timeout(300)
        n0 = await pg.evaluate('BDE.cells.length'); v0 = await pg.evaluate('bdView().n')
        ev = lambda *a: pg.evaluate(JS, list(a))
        await ev(1, 'pointerdown', .45, .5); await ev(2, 'pointerdown', .55, .5)
        for k in range(1, 11): await ev(1, 'pointermove', .45 - .02 * k, .5); await ev(2, 'pointermove', .55 + .02 * k, .5)
        await ev(1, 'pointerup', .25, .5); await ev(2, 'pointerup', .75, .5)
        v1 = await pg.evaluate('bdView().n'); print('zoom', v0, '->', round(v1, 2))
        assert v1 < v0 / 2 and await pg.evaluate('BDE.cells.length') == n0
        await ev(1, 'pointerdown', .2, .5); await ev(2, 'pointerdown', .8, .5)
        for k in range(1, 11): await ev(1, 'pointermove', .2 + .025 * k, .5); await ev(2, 'pointermove', .8 - .025 * k, .5)
        await ev(1, 'pointerup', .45, .5); await ev(2, 'pointerup', .55, .5)
        v2 = await pg.evaluate('bdView().n'); print('dézoom', round(v2, 2)); assert v2 > v1 * 3
        await pg.click('#bdFit'); assert await pg.evaluate('bdView().n') == v0 and not await pg.is_visible('#bdFit')
        print('errors', errs); await b.close()
asyncio.run(main())
