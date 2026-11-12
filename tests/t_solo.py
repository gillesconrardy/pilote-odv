import asyncio, os
from playwright.async_api import async_playwright
exec(open('t_manual.py').read().split('async def main')[0])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 412, 'height': 900})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        await pg.add_init_script(MOCK)
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(500)
        await pg.click('nav button[data-tab=setup]'); await pg.wait_for_timeout(300)
        await pg.click('#suSolo')
        for _ in range(60):
            if await pg.evaluate('M.active'): break
            await pg.wait_for_timeout(300)
        print('onglet', await pg.evaluate("document.querySelector('section.on').id"), 'main prise', await pg.evaluate('M.active'), '| msg', await pg.inner_text('#manMsg'))
        print('autres', await pg.evaluate('M.others'), 'V4', await pg.evaluate('M.cmd'), 'main btn', await pg.evaluate("!$('handGo').disabled"))
        st = await pg.evaluate('window.__stdin'); print('envoyé au V4:', [t for n, t in st][:10])
        jb = await pg.locator('#joy').bounding_box(); cx, cy = jb['x'] + jb['width']/2, jb['y'] + jb['height']/2
        await pg.mouse.move(cx, cy); await pg.mouse.down(); await pg.mouse.move(cx, cy + 70, steps=3); await pg.wait_for_timeout(1500); await pg.mouse.up()
        print('après joystick', await pg.evaluate('M.cmd'))
        await pg.screenshot(path='/tmp/solo.png')
        print('errors', errs); await b.close()
asyncio.run(main())
