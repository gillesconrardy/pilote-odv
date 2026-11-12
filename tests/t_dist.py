import asyncio
from playwright.async_api import async_playwright
MOCK = open('t_manual.py').read().split('MOCK = open')[0]
exec(open('t_manual.py').read().split('async def main')[0])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 412, 'height': 900}, device_scale_factor=2)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        await pg.add_init_script(MOCK)
        await pg.goto('file://' + __import__('os').path.abspath('../index.html')); await pg.wait_for_timeout(300)
        await pg.click('nav button[data-tab=envoi]'); await pg.click('#send4'); await pg.wait_for_timeout(1500)
        await pg.click('nav button[data-tab=tele]'); await pg.wait_for_timeout(2200)
        st = await pg.evaluate('window.__stdin'); print('U envoyés:', [t for n, t in st if t[0] == 'U'])
        await pg.evaluate("R.hub.onLine('DS 182')"); print('affiché:', await pg.inner_text('#dsVal'), '|', await pg.inner_text('#dsTxt'))
        await pg.locator('#dsCard').screenshot(path='ds.png')
        await pg.evaluate("R.hub.onLine('DS 2000')"); print('loin:', await pg.inner_text('#dsVal'))
        await pg.click('nav button[data-tab=stats]'); await pg.wait_for_timeout(1500)
        st = await pg.evaluate('window.__stdin'); print('après changement d onglet:', [t for n, t in st if t[0] == 'U'])
        print('errors', errs); await b.close()
asyncio.run(main())
