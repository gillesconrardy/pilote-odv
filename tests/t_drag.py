import asyncio, os
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 412, 'height': 900}, device_scale_factor=2, has_touch=True)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(300)
        names = lambda: pg.eval_on_selector_all('#chList .ch .nm b', 'e => e.map(x => x.textContent)')
        print('avant :', await names(), '|', await pg.inner_text('#sumTxt'))
        g = await pg.locator('#chList .ch .grip').nth(0).bounding_box(); r = await pg.locator('#chList .ch').nth(2).bounding_box()
        x, y = g['x'] + g['width'] / 2, g['y'] + g['height'] / 2
        await pg.mouse.move(x, y); await pg.mouse.down()
        for k in range(1, 21): await pg.mouse.move(x, y + (r['y'] + r['height'] * 0.8 - y) * k / 20); await pg.wait_for_timeout(15)
        await pg.screenshot(path='/home/claude/work/drag.png'); await pg.mouse.up(); await pg.wait_for_timeout(200)
        print('après :', await names())
        await pg.reload(); await pg.wait_for_timeout(300); print('rechargé :', await names())
        # remonter le dernier tout en haut
        n = await pg.locator('#chList .ch').count()
        g = await pg.locator('#chList .ch .grip').nth(n - 1).bounding_box(); t = await pg.locator('#chList .ch').nth(0).bounding_box()
        x, y = g['x'] + g['width'] / 2, g['y'] + g['height'] / 2
        await pg.mouse.move(x, y); await pg.mouse.down()
        for k in range(1, 31): await pg.mouse.move(x, y + (t['y'] - 5 - y) * k / 30); await pg.wait_for_timeout(15)
        await pg.mouse.up(); await pg.wait_for_timeout(200); print('dernier en haut :', await names())
        print('errors', errs); await b.close()
asyncio.run(main())
