# Setup : calibrage en colonne, chaque véhicule devient disponible quand le précédent a quitté la colonne (CLR)
import asyncio, os
from playwright.async_api import async_playwright
MOCK = open('t_page2.py').read().split('MOCK = r"""')[1].split('"""')[0].replace("encode('HY\\n')]), 300)", "encode('HY\\n')]), 800)").replace("encode('CLR\\n')]), 600)", "encode('CLR\\n')]), 6000)")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(locale='fr-FR', viewport={'width': 412, 'height': 900})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script(MOCK); await pg.add_init_script("try{localStorage.setItem('odv.tab','setup')}catch(e){}")
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(300); await pg.mouse.click(200, 450); await pg.wait_for_timeout(1500)
        en = lambda: pg.evaluate("[1,2,3,4].map(v=>document.getElementById('su'+v).disabled?0:1).join('')")
        print('départ          ', await en())
        await pg.click('#su1', force=True); await pg.wait_for_timeout(300)
        print('V1 en cours     ', await en())
        await pg.wait_for_function("SU.hy[1]", timeout=20000); await pg.wait_for_timeout(200)
        print('V1 a touché     ', await en(), '|', await pg.inner_text('#suNext'))
        await pg.click('#su2', force=True); await pg.wait_for_timeout(1500)
        print('V2 en attente   ', await en(), '|', await pg.inner_text('#st2') if await pg.locator('#st2').count() else '', '| V1 sorti ?', await pg.evaluate('!!SU.clr[1]'))
        await pg.wait_for_function("SU.clr[1]", timeout=20000)
        await pg.wait_for_function("SU.done[2]", timeout=20000); await pg.wait_for_timeout(200)
        print('V2 a quitté     ', await en(), '(V1 « Refaire » bloqué)')
        print('erreurs', errs); await b.close()
asyncio.run(main())
