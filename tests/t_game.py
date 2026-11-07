import asyncio, os, re
from playwright.async_api import async_playwright
MOCK = open('t_page2.py').read().split('MOCK = r"""')[1].split('"""')[0]
MOCK = MOCK.replace("if (b[0] === 6) { const c = String.fromCharCode(b[1]);", """if (b[0] === 6) { const txt = new TextDecoder().decode(new Uint8Array(b.slice(1))).trim(); (window.__stdin = window.__stdin || []).push(txt);
  const say = (s, d) => setTimeout(() => notify([1, ...new TextEncoder().encode(s + '\\n')]), d || 50);
  if (txt === 'M') say('MAN 1');
  if (txt === 'P') say('PON');
  if (txt[0] === 'W') say('WOK', 200);
  if (txt === 'Z') say('JOK', 100);
  if (txt === 'J') { say('JON'); let k = 0; window.__jp = setInterval(() => { k++; const y = Math.min(1500, 100 * k); say('JP 3000 ' + y + ' 2000 ' + y + ' 1000 ' + y + ' 0 2500 1 0', 1); }, 250); say('CATCH 1 1900', 2500); }
  if (txt === 'K') { clearInterval(window.__jp); say('JRET', 100); }
  const c = txt[0];""")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 412, 'height': 900}, device_scale_factor=2)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script(MOCK)
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(300)
        await pg.click('nav button[data-tab=envoi]'); await pg.click('#send4'); await pg.wait_for_timeout(1500)
        await pg.click('nav button[data-tab=tele]'); await pg.wait_for_timeout(800)
        await pg.click('#gDiff button[data-s="7"]')
        await pg.click('#gRoles button[data-k="1"][data-r="g"]'); await pg.click('#gRoles button[data-k="2"][data-r="o"]')
        await pg.locator('#gameCard').screenshot(path='/home/claude/work/game_card0.png')
        await pg.click('#gGo'); await pg.wait_for_function('GM.phase === 1', timeout=30000); await pg.wait_for_timeout(300)
        print('msg:', await pg.inner_text('#gMsg'), '| button:', await pg.inner_text('#gGo'))
        print('stdin:', await pg.evaluate('window.__stdin'))
        # le joueur s'échappe vers le bas avec le joystick
        jb = await pg.locator('#joy').bounding_box(); cx, cy = jb['x'] + jb['width']/2, jb['y'] + jb['height']/2
        await pg.mouse.move(cx, cy); await pg.mouse.down(); await pg.mouse.move(cx, cy + 80, steps=3); await pg.wait_for_timeout(2500); await pg.mouse.up()
        print('after 2.5 s: time', await pg.inner_text('#gTime'), 'catches', await pg.inner_text('#gCatch'), 'best', await pg.inner_text('#gBest'), 'V4', await pg.evaluate('M.cmd'), 'others', await pg.evaluate('JSON.stringify(M.others)'))
        await pg.locator('#cv').screenshot(path='/home/claude/work/game_board.png')
        await pg.click('#gGo'); await pg.wait_for_function('GM.phase === 0', timeout=60000)
        print('end msg:', await pg.inner_text('#gMsg'), '| manual active:', await pg.evaluate('M.active'))
        st = await pg.evaluate('window.__stdin'); print('last stdin:', st[-4:])
        gs = [tuple(map(int, re.findall(r'-?\d+', t))) for t in st if t.startswith('G')]
        print('V4 G collision-free vs chasers (moving) checked on page; count', len(gs))
        await pg.locator('#gameCard').screenshot(path='/home/claude/work/game_card.png')
        print('errors', errs); await b.close()
asyncio.run(main())
