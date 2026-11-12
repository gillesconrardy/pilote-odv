import asyncio, os
from playwright.async_api import async_playwright
# v1.90 : chorégraphies bloquées si elles sortent du plateau dessiné ; plateau dessiné dans l'Atelier
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 412, 'height': 900}, device_scale_factor=2)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(600)
        print('4×4 : compatibles', await pg.evaluate('items.filter(i => i.fit).length'), '/', await pg.evaluate('items.length'))
        assert await pg.evaluate('items.every(i => i.fit !== false)')
        await pg.evaluate("BD.cells = BD.cells.filter(c => c !== '3,3'); bdChanged()")
        bad = await pg.evaluate('items.filter(i => i.fit === false).map(i => i.name)')
        print('sans le bloc (3,3) : bloquées', bad, '| jouées', await pg.evaluate('PLAY.map(i => i.name)'))
        assert bad and await pg.evaluate('PLAY.every(i => i.fit)')
        await pg.click('nav button[data-tab=choix]'); await pg.wait_for_timeout(1200)
        await pg.locator('#chList').screenshot(path='/tmp/fit_list.png')
        print('cases désactivées', await pg.evaluate("[...document.querySelectorAll('#chList input:disabled')].length"))
        await pg.click('#edNew'); await pg.wait_for_timeout(800)
        await pg.locator('#edCv').screenshot(path='/tmp/fit_editor.png')
        await pg.evaluate("BD.cells = bdSquare(); bdChanged()")
        assert await pg.evaluate('items.every(i => i.fit !== false)')
        print('errors', errs); await b.close()
asyncio.run(main())
