import asyncio, os
from playwright.async_api import async_playwright
MOCK = open('t_page2.py').read().split('MOCK = r"""')[1].split('"""')[0]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 412, 'height': 900}, device_scale_factor=1.5)
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script(MOCK)
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(400)
        await pg.click('nav button[data-tab=stats]'); await pg.wait_for_timeout(300)
        await pg.screenshot(path='/home/claude/work/st_vide.png', full_page=True)
        await pg.click('nav button[data-tab=setup]')
        for v in (1,2,3,4): await pg.click('#su%d' % v); await pg.wait_for_timeout(1400)
        await pg.click('nav button[data-tab=choix]'); await pg.click('#updAll2')
        for _ in range(40):
            await pg.wait_for_timeout(500)
            if 'nouvelle sélection' in await pg.inner_text('#updMsg'): break
        # le faux hub V4 ne fait pas avancer l'horloge : on simule un état « lecture » qui avance
        await pg.evaluate("""(() => { let w = 0; setInterval(() => { w += 200; R.st = { s: 'F', w, k: Math.max(0, R.tl.bounds.findIndex(b => b > w) - 1), pend: false, mv: 7900 - w / 100, gen: genId() }; R.at = performance.now(); }, 200); })()""")
        await pg.wait_for_timeout(25000)
        await pg.click('nav button[data-tab=stats]'); await pg.wait_for_timeout(2500)
        print('kpi:', (await pg.inner_text('#stKpi')).replace('\n', ' | '))
        print('podium:', (await pg.inner_text('#stPod')).replace('\n', ' '))
        print('chor:', (await pg.inner_text('#stChor')).replace('\n', ' '))
        await pg.screenshot(path='/home/claude/work/st_plein.png', full_page=True)
        await pg.evaluate('statSave()'); print('jours:', await pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('odv.stDays')))"))
        await pg.click('#stPer button[data-p=a]'); await pg.wait_for_timeout(300); print('tout:', (await pg.inner_text('#stKpi')).split('\n')[1])
        await pg.click('#stHeatV button[data-v="2"]'); await pg.wait_for_timeout(300)
        print(errs); await b.close()
asyncio.run(main())
