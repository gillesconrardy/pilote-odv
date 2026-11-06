import asyncio, os
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 412, 'height': 900}, device_scale_factor=2)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(300)
        await pg.click('#edNew'); await pg.fill('#edName', 'Test atelier')
        async def drag(fr, to):
            await pg.locator('#edCv').scroll_into_view_if_needed(); box = await pg.locator('#edCv').bounding_box(); u = box['width'] / 44
            P = lambda x, y: (box['x'] + (37 - x) * u, box['y'] + (y + 7) * u)
            await pg.mouse.move(*P(*fr)); await pg.mouse.down(); await pg.mouse.move(*P(*to), steps=6); await pg.mouse.up(); await pg.wait_for_timeout(100)
        await pg.click('#edAdd')
        await drag((30, 0), (30, 20)); await drag((0, 0), (0, 20))
        await pg.click('#edAdd'); await drag((20, 0), (20, 12)); await drag((10, 0), (10, 12))   # V2,V3 down: V2 (20,12) vs V1 (30,20): dx 10 ok
        print('check after 2 steps:', (await pg.inner_text('#edCheck')).replace('\n', ' | '))
        # step with deliberate overlap: V3 onto V2
        await pg.click('#edAdd'); await drag((10, 12), (17, 12))
        print('overlap check:', (await pg.inner_text('#edCheck')).replace('\n', ' | '), '| save disabled:', await pg.is_disabled('#edSave'))
        await pg.click('#edDel')
        await pg.click('#edHome'); await pg.wait_for_timeout(200)
        print('after auto return:', (await pg.inner_text('#edCheck')).replace('\n', ' | '), '| chips:', await pg.inner_text('#edChips'))
        print(await pg.evaluate('edCode().src'))
        await pg.click('#edPlay'); await pg.wait_for_timeout(1500); await pg.screenshot(path='/home/claude/work/ed1.png', full_page=False)
        await pg.click('#edPlay')
        await pg.click('#edSave'); await pg.wait_for_timeout(300); await pg.click('#edClose')
        rows = await pg.locator('#chList .ch').all_inner_texts(); print('list last:', rows[-1].replace('\n', ' '))
        print('summary:', await pg.inner_text('#sumTxt'))
        src = await pg.evaluate("programText(1).length"); print('program V1 chars', src)
        # reopen for editing
        await pg.click('#chList .ch:last-child .edb'); await pg.wait_for_timeout(200)
        print('reopened steps:', await pg.inner_text('#edChips'), '| name', await pg.input_value('#edName'))
        await pg.screenshot(path='/home/claude/work/ed2.png', full_page=True)
        print('errors', errs); await b.close()
asyncio.run(main())
