import asyncio, os, re
from playwright.async_api import async_playwright
MOCK = open('t_page2.py').read().split('MOCK = r"""')[1].split('"""')[0]
MOCK = MOCK.replace("if (b[0] === 6) { const c = String.fromCharCode(b[1]);", """if (b[0] === 6) { const txt = new TextDecoder().decode(new Uint8Array(b.slice(1))).trim(); (window.__stdin = window.__stdin || []).push(txt);
  const say = (s, d) => setTimeout(() => notify([1, ...new TextEncoder().encode(s + '\\n')]), d || 50);
  if (txt === 'M') say('MAN 1');
  if (txt === 'B') { say('BON'); let k = 0; window.__jp = setInterval(() => { k++; const f = Math.min(1, k / 8);
      const P = [[3000, 1890 * f], [2000 - 100 * f, 2010 * f], [1000, 0], [2450 * f, 580 * f]];
      say('JP ' + P.flat().map(Math.round).join(' ') + ' 4 0', 1); }, 250); }
  if (txt === 'K') clearInterval(window.__jp);
  if (txt[0] === 'W') say('WOK', 300);
  if (txt === 'Z') say('JOK', 100);
  const c = txt[0];""")
TILT = "b=>window.dispatchEvent(Object.assign(new Event('deviceorientation'),{beta:b[0],gamma:b[1]}))"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(locale='fr-FR', viewport={'width': 412, 'height': 900}, device_scale_factor=2)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script(MOCK)
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(300)
        await pg.click('nav button[data-tab=envoi]'); await pg.click('#send4'); await pg.wait_for_timeout(1500)
        await pg.click('nav button[data-tab=tele]'); await pg.wait_for_timeout(800)
        print('button:', await pg.inner_text('#tiltGo'))
        await pg.click('#tiltGo'); await pg.wait_for_timeout(1200)
        await pg.evaluate(TILT, [30, 0]); await pg.wait_for_timeout(200)
        for _ in range(10): await pg.evaluate(TILT, [50, -12]); await pg.wait_for_timeout(100)
        print('msg:', await pg.inner_text('#manMsg'))
        print('button:', await pg.inner_text('#tiltGo'), '| joy', await pg.evaluate('M.joy'))
        await pg.wait_for_timeout(1500)
        await pg.screenshot(path='/home/claude/work/billes_board.png', full_page=True)
        print('V4 cmd from JP:', await pg.evaluate('M.cmd'), 'others', await pg.evaluate('JSON.stringify(GM.pos)'))
        await pg.click('#tiltGo')
        await pg.wait_for_function('!GM.on && !M.active', timeout=60000)
        await pg.wait_for_timeout(500); print('end msg:', await pg.inner_text('#manMsg'), '| button:', await pg.inner_text('#tiltGo'))
        st = await pg.evaluate('window.__stdin')
        i = st.index('B'); print('setup:', st[max(0, i - 6):i + 1])
        print('T sent:', len([t for t in st if t.startswith('T')]), [t for t in st if t.startswith('T')][:4])
        k = st.index('K'); print('after K:', st[k:])
        print('errors', errs); await b.close()
asyncio.run(main())
