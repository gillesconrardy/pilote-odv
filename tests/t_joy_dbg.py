import asyncio, re
from playwright.async_api import async_playwright
MOCK = open('t_manual.py').read().split('MOCK = open')[0]
exec(open('t_manual.py').read().split('async def main')[0])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(locale='fr-FR', viewport={'width': 412, 'height': 900}, device_scale_factor=2)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        await pg.add_init_script(MOCK)
        await pg.goto('file://' + __import__('os').path.abspath('../index.html') + ''); await pg.wait_for_timeout(300)
        await pg.click('nav button[data-tab=envoi]')
        for v in (1, 2, 3, 4): await pg.click('#send%d' % v); await pg.wait_for_timeout(1200)
        await pg.click('nav button[data-tab=tele]'); await pg.wait_for_timeout(1000)
        await pg.click('#manGo'); await pg.wait_for_timeout(900)
        print('msg:', await pg.inner_text('#manMsg'))
        jb = await pg.locator('#joy').bounding_box(); cx, cy = jb['x'] + jb['width']/2, jb['y'] + jb['height']/2
        await pg.mouse.move(cx, cy); await pg.mouse.down(); await pg.mouse.move(cx, cy + 70, steps=3); await pg.wait_for_timeout(2000)
        await pg.mouse.move(cx - 70, cy, steps=3); await pg.wait_for_timeout(1500); await pg.mouse.up()
        print('cmd after down 2s then left (blocked by V3 at x=10?):', await pg.evaluate('M.cmd'))
        await pg.screenshot(path='j1.png', full_page=True)
        await pg.click('#manGo'); await pg.wait_for_timeout(6000)
        print('after return:', await pg.evaluate('[M.active, M.cmd]'))
        st = await pg.evaluate('window.__stdin'); hubs = sorted(set(n for n, t in st)); print('hubs receiving stdin:', hubs)
        gs = [tuple(map(int, re.findall(r'-?\d+', t))) for n, t in st if t.startswith('G')]
        bad=[(x,y) for x,y in gs if any(max(abs(x/100-o[0]),abs(y/100-o[1]))<9.99 for o in [(30,0),(20,0),(10,0)])]; print('bad', bad[:10]); print('G count', len(gs), 'collision-free:', all(max(abs(x/100-o[0]), abs(y/100-o[1])) >= 9.99 for x, y in gs for o in [(30,0),(20,0),(10,0)]))
        print('errors', errs); await b.close()
asyncio.run(main())
