import asyncio, os
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(locale='fr-FR', viewport={'width': 412, 'height': 900}, device_scale_factor=2)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(300)
        await pg.click('#chList .ch:nth-child(5) .pv'); await pg.wait_for_timeout(300)
        await pg.click('#pvRate button[data-r="4"]'); await pg.wait_for_timeout(3500)
        print('name', await pg.inner_text('#pvName'), '| time', await pg.inner_text('#pvTime'))
        await pg.screenshot(path='/home/claude/work/pv1.png')
        await pg.click('#pvClose')
        await pg.click('#chList .ch:nth-child(7) .pv'); await pg.wait_for_timeout(200)
        await pg.evaluate("PV.play=false; PV.w=17642"); await pg.wait_for_timeout(200)
        await pg.screenshot(path='/home/claude/work/pv2.png')
        await pg.click('#pvClose'); await pg.click('nav button[data-tab=tele]'); await pg.wait_for_timeout(300)
        print('errors', errs); await b.close()
asyncio.run(main())
