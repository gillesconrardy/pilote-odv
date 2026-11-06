import asyncio, json
from playwright.async_api import async_playwright
MOCK = r"""
window.__writes = {}; window.__progs = {};
window.ODV_COMPILE_OVERRIDE = async (name, src) => { (window.__all = window.__all || []).push([name, src]); window.__progs[name] = src; return { status: 0, mpy: new TextEncoder().encode(src.slice(0, 3000)) }; };
let devN = 0;
window.__picks = 0; navigator.bluetooth = { requestDevice: async (o) => { window.__picks++; (window.__filters=window.__filters||[]).push(o);
  const id = 'dev' + (++devN), name = 'Pybricks Hub ' + devN; const W = window.__writes[name] = [];
  const listeners = []; let running = false, timer = null;
  const notify = bytes => listeners.forEach(f => f({ target: { value: new DataView(new Uint8Array(bytes).buffer) } }));
  const status = () => { const b = new Uint8Array(5); new DataView(b.buffer).setUint32(1, running ? 64 : 0, true); notify(b); };
  const cmd = { addEventListener: (e, f) => listeners.push(f), startNotifications: async () => {},
    writeValueWithResponse: async v => { const b = Array.from(v); W.push(b);
      if (b[0] === 0) { running = false; clearInterval(timer); status(); }
      if (b[0] === 1) { running = true; status(); let w = 0, st = 'P';
        timer = setInterval(() => { if (st === 'F') w += 400; if (st === 'H') { st = 'S'; w = 0; } const line = `ST ${st} ${w} 0 0 7900\n`; notify([1, ...new TextEncoder().encode(line)]); }, 400);
        window.__setSt = s => st = s; }
      if (b[0] === 6) { const c = String.fromCharCode(b[1]); window.__setSt && window.__setSt(c === 'p' ? 'F' : c === 'z' ? 'P' : c === 'h' ? 'H' : 'P'); }
    } };
  const caps = { readValue: async () => { const b = new DataView(new ArrayBuffer(10)); b.setUint16(0, 20, true); b.setUint32(2, 2, true); b.setUint32(6, 32000, true); return b; } };
  const dev = { id, name, addEventListener(){}, gatt: { connected: false, async connect(){ this.connected = true; return { getPrimaryService: async () => ({ getCharacteristic: async u => u.endsWith('2-8280-46da-89f4-6d8051e4aeef') ? cmd : caps }) }; }, disconnect(){ this.connected = false; window.__disc = (window.__disc||0)+1; } } };
  return dev; } };
"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 412, 'height': 900}, device_scale_factor=2)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        await pg.add_init_script(MOCK)
        await pg.goto('file://' + __import__('os').path.abspath('../index.html') + ''); await pg.wait_for_timeout(400)
        await pg.screenshot(path='p1.png', full_page=True)
        await pg.click('nav button[data-tab=setup]'); await pg.wait_for_timeout(200)
        for v in (1, 2, 3, 4):
            await pg.click('#su%d' % v); await pg.wait_for_timeout(1500)
        print('mise en place:', (await pg.inner_text('#suNext')), '| aller visible', await pg.is_visible('#suGo'))
        await pg.screenshot(path='p2.png', full_page=True)
        w = await pg.evaluate('window.__writes')
        for name, ws in w.items():
            ram = [x for x in ws if x[0] == 4]
            print(name, 'writes', len(ws), 'first', ws[:2], 'ram chunks', len(ram), 'last meta', [x for x in ws if x[0] == 3][-1], 'start', [x for x in ws if x[0] == 1])
        progs = await pg.evaluate('window.__progs')
        for k, v in progs.items(): open('gen_' + k, 'w').write(v)
        print('progs', list(progs))
        await pg.click('nav button[data-tab=tele]'); await pg.wait_for_timeout(900)
        await pg.click('#bPlay'); await pg.wait_for_timeout(2500)
        await pg.screenshot(path='p3.png', full_page=True)
        print('state', await pg.inner_text('#stBig'), '|', await pg.inner_text('#stSub'), '|', await pg.inner_text('#stTime'))
        print('stdin writes V4', [x for x in w['Pybricks Hub 4'] if x[0] == 6], await pg.evaluate("window.__writes['Pybricks Hub 4'].filter(x=>x[0]==6)"))
        await pg.click('nav button[data-tab=choix]'); await pg.click('#chList .ch input'); await pg.wait_for_timeout(200)
        await pg.click('nav button[data-tab=envoi]'); await pg.click('#updAll'); await pg.wait_for_timeout(16000)
        print('updMsg:', await pg.inner_text('#updMsg'))
        allc = await pg.evaluate('window.__all'); import re
        for n, src in allc:
            print(n, 'GEN', re.search(r'GEN = (\d+)', src).group(1), 'HOMING', re.search(r'DO_HOMING = (\w+)', src).group(1), 'TOTAL', re.search(r'TOTAL = (\d+)', src).group(1))
        w4 = await pg.evaluate("window.__writes['Pybricks Hub 4'].map(x=>x[0]===4?'R':x.join(','))")
        import itertools; print('V4 seq:', [k + ('x%d' % len(list(g)) if k=='R' else '') for k, g in itertools.groupby(w4)])
        print('picks after update', await pg.evaluate('window.__picks'), 'tab', await pg.evaluate("document.querySelector('section.on').id"))
        await pg.click('#discAll2'); await pg.wait_for_timeout(200)
        print('disconnects', await pg.evaluate('window.__disc'), 'state', await pg.inner_text('#stBig'))
        await pg.click('nav button[data-tab=envoi]'); await pg.click('#send1'); await pg.wait_for_timeout(1500)
        print('picks after disconnect+send1', await pg.evaluate('window.__picks'))
        await pg.screenshot(path='p4.png', full_page=True)
        print('errors', errs); await b.close()
asyncio.run(main())
