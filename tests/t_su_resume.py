import asyncio, os, time
from playwright.async_api import async_playwright
exec(open('t_manual.py').read().split('async def main')[0])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(locale='fr-FR', viewport={'width': 412, 'height': 900})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script(MOCK + "\nif(!sessionStorage.x){sessionStorage.x=1;localStorage.setItem('odv.su',JSON.stringify({t:Date.now(),ok:[1,2,3]}));}")
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(500)
        await pg.click('nav button[data-tab=setup]'); await pg.wait_for_timeout(300)
        print('verts', await pg.evaluate("document.querySelectorAll('#suList .surow.ok').length"), 'V4 actif', await pg.evaluate("!$('su4').disabled"), '|', await pg.inner_text('#suNext'))
        await pg.click('#su4', force=True)
        for _ in range(60):
            if await pg.evaluate('!!SU.done[4]'): break
            await pg.wait_for_timeout(300)
        print('V4 fait', await pg.evaluate('!!SU.done[4]'), 'sauvé', await pg.evaluate("localStorage.getItem('odv.su')"))
        await pg.evaluate("$('suReset').onclick()"); print('après Recommencer', await pg.evaluate("localStorage.getItem('odv.su')"))
        print('errors', errs); await b.close()
asyncio.run(main())
