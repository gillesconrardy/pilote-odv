import asyncio, os
from playwright.async_api import async_playwright
MOCK = open('t_page2.py').read().split('MOCK = r"""')[1].split('"""')[0]
MOCK = MOCK.replace("window.__picks = 0;", "window.__picks = 0; window.__names = [];").replace("const id = 'dev' + (++devN), name = 'Pybricks Hub ' + devN;",
  "const id = 'dev' + (++devN), name = (o && o.filters && o.filters[0].name) || ('Pybricks Hub ' + devN); window.__names.push(name);")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 412, 'height': 900})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.add_init_script(MOCK)
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(300)
        await pg.click('nav button[data-tab=envoi]'); await pg.click('#updAll')
        for k in range(4):
            await pg.wait_for_selector('#pickDlg[open]', timeout=20000)
            print('dialog for vehicle', await pg.inner_text('#pickV'), 'hub', await pg.inner_text('#pickName'))
            await pg.click('#pickGo')
        await pg.wait_for_timeout(6000)
        print('updMsg:', await pg.inner_text('#updMsg'))
        print('hubs picked:', await pg.evaluate('window.__names'))
        w = await pg.evaluate('window.__writes'); print({n: [x[0] for x in ws if x[0] in (0,1,6)] for n, ws in w.items()})
        print('errors', errs); await b.close()
asyncio.run(main())
