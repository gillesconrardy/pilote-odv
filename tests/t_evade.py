# conduite manuelle : les 3 autres s'écartent (E/EON, JP), puis « Rendre la main » les range (K, W…, Z) et rend la main (Q)
import asyncio, os
from playwright.async_api import async_playwright
MOCK = open('t_page2.py').read().split('MOCK = r"""')[1].split('"""')[0]
MOCK = MOCK.replace("if (b[0] === 6) { const c = String.fromCharCode(b[1]);", """if (b[0] === 6) { const txt = new TextDecoder().decode(new Uint8Array(b.slice(1))).trim(); (window.__stdin = window.__stdin || []).push(txt);
  const say = (s, d) => setTimeout(() => notify([1, ...new TextEncoder().encode(s + '\\n')]), d || 50);
  if (txt === 'M') say('MAN 1');
  if (txt === 'E') { say('EON'); let k = 0; window.__jp = setInterval(() => { k++; const y = Math.min(1500, 100 * k); say('JP 3000 0 2000 ' + y + ' 1000 0 0 0 5 0', 1); }, 250); }
  if (txt[0] === 'W') say('WOK', 150);
  if (txt === 'Z') say('JOK', 100);
  if (txt === 'K') { clearInterval(window.__jp); say('JRET', 100); }
  if (txt === 'Q') say('MAN 0');
  if (txt === 'H1') { say('HON'); say('HD 2000 1', 400); }
  const c = txt[0];""")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(locale='fr-FR', viewport={'width': 412, 'height': 900})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script(MOCK)
        await pg.goto('file://' + os.path.abspath('../index.html')); await pg.wait_for_timeout(300)
        await pg.click('nav button[data-tab=envoi]'); await pg.click('#send4'); await pg.wait_for_timeout(1500)
        await pg.click('nav button[data-tab=tele]'); await pg.wait_for_timeout(800)
        await pg.click('#manGo'); await pg.wait_for_timeout(2500)
        print('actif', await pg.evaluate('M.active'), '| évitement', await pg.evaluate('M.evade'), '| autres', await pg.evaluate('JSON.stringify(M.others)'))
        await pg.locator('#cv').screenshot(path='/home/claude/work/evade.png')
        await pg.click('#handGo'); await pg.wait_for_timeout(800)
        print('main :', await pg.evaluate('M.hand'), '|', await pg.inner_text('#handSt'), '| bouton', await pg.inner_text('#handGo'), '| joystick', await pg.evaluate("document.getElementById('joyBox').style.display"))
        await pg.locator('#manCard').screenshot(path='/home/claude/work/hand.png') if await pg.locator('#manCard').count() else None
        await pg.click('#manGo'); await pg.wait_for_function('!M.active', timeout=30000)
        st = await pg.evaluate('window.__stdin'); print('stdin:', [s for s in st if s[0] in 'MEKWZQ'])
        print('message:', await pg.inner_text('#manMsg')); print('erreurs', errs); await b.close()
asyncio.run(main())
