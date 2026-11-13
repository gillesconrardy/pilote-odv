// ---------------------------------------------------------------- traduction FR / EN (v1.95)
// Le français est la langue du code. En anglais, tout texte affiché passe par tr() : dictionnaire exact,
// puis modèles avec variables {0} {1}… (les morceaux variables sont eux-mêmes traduits). Le DOM est traduit au
// chargement puis à chaque changement (MutationObserver), ainsi que les textes du canvas, confirm/alert et la montre.
const LANG = (() => { let l = null; try { l = localStorage.getItem('odv.lang'); } catch (e) {} return l === 'en' || l === 'fr' ? l : /^fr\b/i.test(navigator.language || 'fr') ? 'fr' : 'en'; })();
const I18N = /*I18N*/;
const I18N_X = new Map(Object.entries(I18N.exact || {}).map(([k, v]) => [k.replace(/\s+/g, ' ').trim(), v]));
const I18N_P = (I18N.pat || []).map(([f, e]) => {
  const parts = f.split(/\{(\d+)\}/), order = [];
  let re = '^';
  parts.forEach((p, i) => { if (i % 2) { re += '([\\s\\S]*?)'; order.push(+p); } else re += p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); });
  return { re: new RegExp(re + '$'), order, en: e };
});
// phrases (au moins 3 caractères, hors HTML) à remplacer dans un texte plus long, les plus longues d'abord, sur des limites de mots
const I18N_RE = (() => {
  const ks = [...I18N_X.keys()].filter(k => k.length >= 2 && !/[<>]/.test(k)).sort((a, b) => b.length - a.length)
    .map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  return ks.length ? new RegExp('(?<![A-Za-zÀ-ÿ])(?:' + ks.join('|') + ')(?![A-Za-zÀ-ÿ])', 'g') : /$^/;
})();
const I18N_C = new Map();
window.__i18nMiss = new Set();
function tr(s, whole) {
  // whole = true : seulement le texte entier (dictionnaire ou modèle), sans remplacer des phrases à l'intérieur
  if (LANG !== 'en' || s == null) return s;
  s = String(s);
  const lead = s.match(/^\s*/)[0], trail = s.match(/\s*$/)[0], k = s.replace(/\s+/g, ' ').trim();
  if (!k || !/[A-Za-zÀ-ÿ]/.test(k)) return s;
  const ck = (whole ? '\u0001' : '') + k;
  if (I18N_C.has(ck)) { const r = I18N_C.get(ck); return r == null ? s : lead + r + trail; }
  let r = I18N_X.has(k) ? I18N_X.get(k) : null;
  if (r == null) for (const P of I18N_P) {
    const m = k.match(P.re); if (!m) continue;
    const v = []; P.order.forEach((n, i) => { v[n] = m[i + 1]; });
    r = P.en.replace(/\{(\d+)\}/g, (_, n) => { const x = v[+n] ?? ''; const t = tr(x); return t; });
    break;
  }
  if (r == null && whole) { I18N_C.set(ck, null); return s; }
  if (r == null) {
    // préfixe de symboles / emoji (✨ ⚠ ● …) : on traduit le reste
    const m = k.match(/^([^A-Za-zÀ-ÿ0-9<]+)([\s\S]+)$/);
    if (m) { const t = tr(m[2]); if (t !== m[2]) r = m[1] + t; }
  }
  if (r == null) {
    // phrases connues à l'intérieur du texte (messages composés, HTML avec balises) ; puis décimales 6,5 cm → 6.5 cm
    let t = k.replace(I18N_RE, m => I18N_X.get(m) ?? m);
    t = t.replace(/(\d),(\d+)(?=\s?(cm|mm|m|V|s|%|pas|steps|km)\b|\s?cm\/s|<span>)/g, '$1.$2');
    if (t !== k) r = t;
    if (/[àâçéèêëîïôûùüœ]|\b(le|la|les|des|du|une|un|et|est|pour|avec|sur|dans|pas|véhicule|chorégraphie)\b/i.test(t)) window.__i18nMiss.add(k);
  }
  I18N_C.set(ck, r);
  return r == null ? s : lead + r + trail;
}
const I18N_INLINE = new Set(['B', 'I', 'EM', 'STRONG', 'BR', 'SPAN', 'A', 'CODE', 'SMALL', 'U', 'SUB', 'SUP', 'KBD']);
const I18N_SKIP = new Set(['SCRIPT', 'STYLE', 'TEXTAREA', 'CANVAS', 'INPUT', 'path', 'rect', 'circle', 'line', 'polyline']);
const I18N_ATTR = ['title', 'aria-label', 'placeholder', 'data-tip', 'alt', 'data-t'];
function trAttrs(el) {
  for (const a of I18N_ATTR) { const v = el.getAttribute && el.getAttribute(a); if (v) { const t = tr(v); if (t !== v) el.setAttribute(a, t); } }
}
function trNode(n) {
  if (LANG !== 'en' || !n) return;
  if (n.nodeType === 3) { const t = tr(n.nodeValue); if (t !== n.nodeValue) n.nodeValue = t; return; }
  if (n.nodeType !== 1 || n.closest && n.closest('[data-noi18n]')) return;
  if (I18N_SKIP.has(n.tagName)) { if (n.tagName === 'INPUT' || n.tagName === 'TEXTAREA') trAttrs(n); return; }
  trAttrs(n);
  if (n.tagName === 'OPTION') { const t = tr(n.textContent); if (t !== n.textContent) n.textContent = t; return; }
  // élément qui ne contient que du texte et des balises de mise en forme : on traduit son contenu d'un bloc
  const kids = [...n.childNodes];
  if (kids.length > 1 && kids.some(c => c.nodeType === 3 && /\S/.test(c.nodeValue)) && kids.every(c => c.nodeType === 3 || (c.nodeType === 1 && I18N_INLINE.has(c.tagName) && !c.id && !c.querySelector('svg,canvas,input,button')))) {
    const h = n.innerHTML, t = tr(h, true);
    if (t !== h) { n.innerHTML = t; return; }
  }
  kids.forEach(trNode);
}
if (LANG === 'en') {
  document.documentElement.lang = 'en';
  const fill = CanvasRenderingContext2D.prototype.fillText;
  CanvasRenderingContext2D.prototype.fillText = function (t, ...a) { return fill.call(this, tr(String(t)), ...a); };
  const cf = window.confirm.bind(window), al = window.alert.bind(window);
  window.confirm = m => cf(tr(m)); window.alert = m => al(tr(m));
  const go = () => {
    trNode(document.body); document.title = tr(document.title);
    new MutationObserver(ms => {
      for (const m of ms) {
        if (m.type === 'characterData') trNode(m.target);
        else if (m.type === 'attributes') trAttrs(m.target);
        else { trNode(m.target); }
      }
    }).observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: I18N_ATTR });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
}
function setLang(l) {
  try { localStorage.setItem('odv.lang', l); } catch (e) {}
  const busy = typeof V !== 'undefined' && [1, 2, 3, 4].some(v => V[v] && V[v].hub && V[v].hub.connected);
  if (busy && !confirm(l === 'en' ? 'Recharger l\'appli ? Le téléphone se déconnecte des véhicules (leurs programmes continuent).' : 'Reload the app? The phone disconnects from the vehicles (their programs keep running).')) return;
  location.reload();
}
