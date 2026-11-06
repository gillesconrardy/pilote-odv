import asyncio, re
from playwright.async_api import async_playwright
MOCK = open('t_page2.py').read().split('MOCK = r"""')[1].split('"""')[0]
# mock: answer 'M' with MAN 1 on stdout ; record stdin lines
MOCK = MOCK.replace("if (b[0] === 6) { const c = String.fromCharCode(b[1]);",
 "if (b[0] === 6) { const txt = new TextDecoder().decode(new Uint8Array(b.slice(1))); (window.__stdin = window.__stdin || []).push([name, txt.trim()]); if (txt.startsWith('M')) setTimeout(() => notify([1, ...new TextEncoder().encode('MAN 1\\n')]), 50); const c = txt[0];")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 412, 'height': 900}, device_scale_factor=2, has_touch=False)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        await pg.add_init_script(MOCK)
        await pg.goto('file://' + __import__('os').path.abspath('../index.html') + ''); await pg.wait_for_timeout(300)
        await pg.click('nav button[data-tab=envoi]')
        for v in (1, 2, 3, 4): await pg.click('#send%d' % v); await pg.wait_for_timeout(1200)
        await pg.click('nav button[data-tab=tele]'); await pg.wait_for_timeout(1000)
        # status P at w=0 -> home positions. take control of V2 (drag)
        await pg.click('#vpick button[data-v="2"]'); await pg.click('#manGo'); await pg.wait_for_timeout(800)
        print('msg:', await pg.inner_text('#manMsg')); print('play disabled:', await pg.is_disabled('#bPlay'))
        await pg.wait_for_timeout(600); box = await pg.locator('#cv').bounding_box()
        def px(x, y):
            u = box['width'] / 44; return box['x'] + (37 - x) * u, box['y'] + (y + 7) * u
        # drag to (20,15) then try to push left into V1 at x=30? V1 is at (30,0); drag to (28,15) allowed (dy 15), then (28,3) must be blocked by V1 (dx 2, dy<10)
        await pg.mouse.move(*px(20, 2)); await pg.mouse.down()
        await pg.mouse.move(*px(20, 15), steps=5); await pg.wait_for_timeout(2600)
        c1 = await pg.evaluate('M.cmd'); 
        await pg.mouse.move(*px(28, 15), steps=5); await pg.wait_for_timeout(1500)
        c2 = await pg.evaluate('M.cmd')
        await pg.mouse.move(*px(28, 3), steps=5); await pg.wait_for_timeout(2500)
        c3 = await pg.evaluate('M.cmd'); await pg.mouse.up()
        print('cmd after (20,15):', c1, ' after (28,15):', c2, ' after (28,3) [V1 at (30,0) blocks]:', c3)
        await pg.screenshot(path='m1.png', full_page=True)
        # switch to joystick
        await pg.click('.seg button[data-m="joy"]')
        await pg.wait_for_timeout(300); await pg.locator('#joy').scroll_into_view_if_needed(); jb = await pg.locator('#joy').bounding_box(); cx, cy = jb['x'] + jb['width']/2, jb['y'] + jb['height']/2
        await pg.mouse.move(cx, cy); await pg.mouse.down(); await pg.mouse.move(cx + 70, cy, steps=3); await pg.wait_for_timeout(1000); await pg.mouse.up()
        c4 = await pg.evaluate('M.cmd'); print('joystick right 1s:', c4)
        await pg.screenshot(path='m2.png', full_page=True)
        await pg.click('#manGo'); await pg.wait_for_timeout(9000)
        print('after return:', await pg.evaluate('[M.active, M.cmd]'), await pg.inner_text('#manMsg'))
        st = await pg.evaluate('window.__stdin'); lines = [t for n, t in st if n == 'Pybricks Hub 2']
        print('V2 stdin count', len(lines), 'first', lines[:3], 'last', lines[-3:])
        gs = [tuple(map(int, re.findall(r'-?\d+', t))) for t in lines if t.startswith('G')]
        ok = all(max(abs(x/100-o[0]), abs(y/100-o[1])) >= 9.99 for x, y in gs for o in [(30,0),(10,0),(0,0)])
        print('all sent targets collision-free:', ok, 'in bounds:', all(0 <= x <= 3000 and 0 <= y <= 3000 for x, y in gs))
        print('errors', errs); await b.close()
asyncio.run(main())
