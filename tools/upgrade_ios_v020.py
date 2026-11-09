#!/usr/bin/env python3
"""v0.2.0 fail-closed rebase: production UI-v1.9.2 baseline -> iOS bundle.

Base: v192_base.html == production app/static/index.html (UI-v1.9.2 typography,
2721ce75...). Does not access or modify the production app, YAML, or server.

Why a new rebase instead of reusing v0.1.9:
  * the page CSS moved to a 7-step type scale (--fs-display/hero/value/section/
    body-lg/body/caption); every literal font-size is gone from the web page.
  * the iOS-only overrides written for v0.1.9 (and the older P0/P1/P1C/P1D
    patches) still carry literal sizes tuned to the pre-scale page (10px tags,
    11px muted, clamp() titles). Running them unchanged would put the App on a
    different scale than the web, which is exactly what v1.9.2 removed. So this
    rebase normalises every text rule of the merged bundle onto the same 7
    tokens, and only leaves glyph sizes (::before/::after icons) alone.
"""
from pathlib import Path
import hashlib, re, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web/index.html'
BASE = ROOT / 'v192_base.html'

BASE_SHA = '2721ce754acea460759d86f3f57dca7feaad34785719979925eb4ad83397d053'
PREV_SHA_PREFIX = 'e0ef9e17'          # v0.1.9 web bundle
NEW = 'XB_IOS_V020_REBASE'
IOS_MARKERS = ('XB_IOS_P0_BEGIN', 'XB_IOS_P1_V012', 'XB_IOS_P0B_V013',
               'XB_IOS_P1C_V014', 'XB_IOS_P1D_V015', 'XB_IOS_P2A_V016', 'XB_IOS_P2B_V017')
V19_CAPABILITIES = (
    ('async intake: request id', 'function createIntakeRequestId('),
    ('async intake: poll loop', 'async function pollIntake('),
    ('async intake: navigate on complete', 'async function finishIntakeNavigation('),
    ('navigate to extraction after save', 'showDetailPane("extraction")'),
    ('recipe tool target indirection', 'function recipeToolTarget('),
)
SCALE_TOKENS = ('display', 'hero', 'value', 'section', 'body-lg', 'body', 'caption')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def once(s, needle, label):
    n = s.count(needle)
    if n != 1:
        raise RuntimeError(f'{label}: expected exactly 1 occurrence, got {n}')


SHIM = r'''
/* XB_IOS_V020_SHIM - Capacitor API endpoint adapter + iOS-safe server editor.
   Sizes use the page type tokens so the App shares the web's 7-step scale. */
const XB_SERVER_KEY='xbloom_ios_server_url';
function xbReadServer(){let s=localStorage.getItem(XB_SERVER_KEY)||'http://192.168.50.22:8088';return s.replace(/\/+$/,'');}
function absURL(path){if(typeof path!=='string')return path;if(/^(?:https?:|blob:|data:)/i.test(path))return path;return xbReadServer()+(path.startsWith('/')?path:'/'+path);}
function xbStoreServer(v){const u=new URL(String(v).trim());if(!['http:','https:'].includes(u.protocol)||!u.hostname||u.username||u.password)throw Error('请输入有效的 HTTP(S) 服务器地址');localStorage.setItem(XB_SERVER_KEY,u.origin);return u.origin;}
(function(){
 /* WKWebView has no prompt(); use an inline panel. Keep the trigger a fixed button so
    apply_ios_p0b.py can still proxy it to 设置 → 服务器连接设置. */
 var panel=null,input=null;
 function closePanel(){if(panel&&panel.parentNode)panel.parentNode.removeChild(panel);panel=null;input=null;}
 function openPanel(){
   if(panel){input.focus();input.select();return;}
   panel=document.createElement('div');panel.id='xbIosServerPanel';
   panel.style.cssText='position:fixed;left:12px;right:12px;bottom:calc(96px + env(safe-area-inset-bottom,0px));z-index:10001;background:#fff;border:1px solid #ddd0c2;border-radius:14px;padding:12px;box-shadow:0 8px 24px rgba(0,0,0,.18)';
   var label=document.createElement('div');label.textContent='服务器地址';label.style.cssText='font-size:var(--fs-body);color:var(--muted);margin-bottom:6px';
   input=document.createElement('input');input.type='url';input.id='xbIosServerInput';input.value=xbReadServer();
   input.setAttribute('inputmode','url');input.setAttribute('autocapitalize','off');input.setAttribute('autocorrect','off');input.setAttribute('spellcheck','false');input.setAttribute('aria-label','服务器地址');
   /* 16px is not arbitrary: iOS zooms the viewport when a focused input is smaller,
      and --fs-body-lg is exactly 16px. */
   input.style.cssText='width:100%;box-sizing:border-box;font-size:var(--fs-body-lg);padding:10px;border:1px solid #ddd0c2;border-radius:10px;background:#fff;color:#111';
   var row=document.createElement('div');row.style.cssText='display:flex;gap:8px;margin-top:10px';
   var save=document.createElement('button');save.type='button';save.id='xbIosServerSave';save.textContent='保存';
   save.style.cssText='flex:1;padding:11px;border-radius:10px;border:0;background:#634936;color:#fff;font-size:var(--fs-body-lg)';
   var cancel=document.createElement('button');cancel.type='button';cancel.id='xbIosServerCancel';cancel.textContent='取消';
   cancel.style.cssText='flex:1;padding:11px;border-radius:10px;border:1px solid #ddd0c2;background:#fff;color:#634936;font-size:var(--fs-body-lg)';
   save.onclick=function(){try{xbStoreServer(input.value);location.reload();}catch(e){alert(e.message);}};
   cancel.onclick=closePanel;
   input.addEventListener('keydown',function(ev){if(ev.key==='Enter'){ev.preventDefault();save.click();}});
   row.appendChild(save);row.appendChild(cancel);panel.appendChild(label);panel.appendChild(input);panel.appendChild(row);
   document.body.appendChild(panel);input.focus();input.select();
 }
 function mount(){
   if(!window.Capacitor)return;
   if(document.getElementById('xbIosServerButton'))return;
   var b=document.createElement('button');b.type='button';b.id='xbIosServerButton';b.textContent='🛜 服务器';
   b.setAttribute('aria-label','打开服务器地址设置');
   b.style.cssText='position:fixed;right:12px;bottom:110px;z-index:60;border-radius:12px;padding:10px;background:var(--bg);color:#634936;border:1px solid #ddd0c2;font-size:var(--fs-body)';
   b.addEventListener('click',openPanel);
   document.body.classList.add('ios-app');document.body.appendChild(b);
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
})();
'''

RETARGET = (
    ('src="${esc(b.image_url)}"', 'src="${esc(absURL(b.image_url))}"', 'bean card image'),
    ('src="${esc(d.bean.image_url)}"', 'src="${esc(absURL(d.bean.image_url))}"', 'detail hero image'),
    ('location.href=`/api/beans/${encodeURIComponent(target.beanId)}/recipes/${encodeURIComponent(target.version)}/download`;',
     'location.href=absURL(`/api/beans/${encodeURIComponent(target.beanId)}/recipes/${encodeURIComponent(target.version)}/download`);',
     'recipe download'),
    ('image.src=`/api/beans/${encodeURIComponent(target.beanId)}/recipes/${encodeURIComponent(target.version)}/qr?base_url=${encodeURIComponent(location.origin)}`;',
     'image.src=absURL(`/api/beans/${encodeURIComponent(target.beanId)}/recipes/${encodeURIComponent(target.version)}/qr?base_url=${encodeURIComponent(xbReadServer())}`);',
     'recipe QR'),
    ('$("#rawUrlText").textContent=location.origin+`/raw/recipes/${encodeURIComponent(target.beanId)}/${encodeURIComponent(target.version)}.yaml`;',
     '$("#rawUrlText").textContent=xbReadServer()+`/raw/recipes/${encodeURIComponent(target.beanId)}/${encodeURIComponent(target.version)}.yaml`;',
     'raw recipe URL'),
)


def prepare(base):
    once(base, 'let beans=[],selected=null,selectedBean=null', 'globals anchor')
    once(base, 'async function api(url,opt){', 'api()')
    base = base.replace('async function api(url,opt){',
                        'async function api(url,opt){\n url=absURL(url);', 1)
    base = base.replace('let beans=[],selected=null,selectedBean=null',
                        SHIM + '\nlet beans=[],selected=null,selectedBean=null', 1)
    for old, new, label in RETARGET:
        once(base, old, 'shim ' + label)
        base = base.replace(old, new, 1)
    return base


# ---------------------------------------------------------------- type normalise
def token_for(px):
    if px <= 12:
        return 'caption'
    if px <= 14.5:
        return 'body'
    if px <= 16:
        return 'body-lg'
    if px <= 18:
        return 'section'
    if px <= 22:
        return 'value'
    if px <= 25:
        return 'hero'
    return 'display'


FS_PX = re.compile(r'font-size:\s*([\d.]+)px')
FS_CLAMP = re.compile(r'font-size:\s*clamp\([^)]*\)')
FS_ANY = re.compile(r'font-size:\s*[^;}]+;?')
RULE = re.compile(r'(?P<sel>(?:(?!@)[^{}])+)\{(?P<body>[^{}]*)\}')

# ---------------------------------------------------------------------------
# iOS-only overrides written for the pre-scale page. Each one either inherits the
# base page's token (ALIGN value None -> drop the declaration) or is pinned to the
# token that matches its role on the web. Without this the App would render body
# copy at 12px, page titles at 14px and section titles at 16px while the web shows
# 14 / 32 / 18 -- i.e. a second type scale, which v1.9.2 exists to remove.
ALIGN = {
    '.dripper-registry-head b': 'body-lg',       # 卡片标题
    '.dripper-registry-meta': 'body',            # 次要说明
    '#warehouse .bean-title b': None,            # 继承 base: section 18
    '#warehouse .tag': 'caption',
    '#warehouse .intro': None,                   # 继承 base: body 14
    '#warehouse .muted': None,                   # 继承 base: body 14
    '.intake-step': 'caption',
    '.top h1': None,                             # 继承 base: display 32
    '.settings-back': 'body-lg',                 # 按钮
    '.bottom-nav button': 'body-lg',             # 底部导航按钮
    '#settingsStatusPane .row > :first-child': 'body',
    '#settingsStatusPane .row > :last-child': 'body',
    '#settingsStatusPane .validation>b': 'body-lg',
    '#detailExtractionPane h3': None,            # 继承 base: section 18
    '#extractionSourceHint': 'body',
    '#detailExtractionPane .session-dripper b': 'body',
    '#extractMetricCards .extract-metric-card span': 'body',
    '#extractMetricCards .extract-metric-card b': 'value',   # 参数数值 22
    '#detailAdjustPane .adjust-context .status': 'caption',
    '#reason': 'body',
    '#xbP2AToast': 'body',
    '#xbP2ANetwork': 'caption',
    '#xbP2ARetry': 'body-lg',
    '#xbP2BViewer .xb-p2b-close': 'hero',
    '#xbP2BViewer .xb-p2b-hint': 'caption',
}
IOS_PREFIXES = ('html.xb-ios-p0 body.ios-app ', 'html.xb-ios-p0 ', 'body.ios-app ')


def norm_sel(sel):
    """First comma part, iOS prefixes stripped, whitespace collapsed."""
    part = sel.split(',')[0]
    part = re.sub(r'<[^>]+>', ' ', part)        # selector may start after a </style><style>
    part = ' '.join(part.split())
    for p in IOS_PREFIXES:
        if part.startswith(p.strip()):
            part = part[len(p.strip()):].strip()
    return ' '.join(part.split())


def align_ios_type(html):
    """Pin every iOS-only text rule to the shared scale (or let the base win)."""
    stats = {'dropped': 0, 'pinned': 0, 'unmapped': []}

    def sub_rule(m):
        sel, body = m.group('sel'), m.group('body')
        if 'font-size' not in body:
            return m.group(0)
        if '::before' in sel or '::after' in sel:
            return m.group(0)                     # icon glyph
        if 'ios-app' not in sel and 'xb-ios-p0' not in sel:
            return m.group(0)                     # base page rule, untouched
        key = norm_sel(sel)
        if key not in ALIGN:
            stats['unmapped'].append(key)
            return m.group(0)
        target = ALIGN[key]
        body2 = FS_ANY.sub('', body).rstrip(';')
        if target is None:
            stats['dropped'] += 1
        else:
            body2 = body2 + (';' if body2 else '') + 'font-size:var(--fs-%s)' % target
            stats['pinned'] += 1
        return sel + '{' + body2 + '}'

    return RULE.sub(sub_rule, html), stats



def normalise_type(html):
    """Rewrite every text rule's literal font-size onto the 7 tokens.

    Glyph sizes (icon pseudo-elements) are left alone: they size a pictograph,
    not a letterform, so they are not part of the type scale.
    Returns (html, stats).
    """
    stats = {'rules': 0, 'glyphs_skipped': 0, 'clamped': 0}

    def sub_rule(m):
        sel, body = m.group('sel'), m.group('body')
        if 'font-size' not in body:
            return m.group(0)
        if '::before' in sel or '::after' in sel:
            stats['glyphs_skipped'] += 1
            return m.group(0)
        if 'content:' in body and re.search(r'content:\s*["\']', body):
            stats['glyphs_skipped'] += 1
            return m.group(0)
        body2 = FS_CLAMP.sub(lambda _: 'font-size:var(--fs-body)', body)
        stats['clamped'] += len(FS_CLAMP.findall(body))

        def one(mm):
            px = float(mm.group(1))
            stats['rules'] += 1
            return 'font-size:var(--fs-%s)' % token_for(px)
        return sel + '{' + FS_PX.sub(one, body2) + '}'

    out = RULE.sub(sub_rule, html)
    # weights: the scale allows 400 / 600 / 700 only
    out = re.sub(r'font-weight:\s*(?:800|900|650|750)', 'font-weight:700', out)
    return out, stats


def assert_capabilities(s):
    for label, needle in V19_CAPABILITIES:
        if needle not in s:
            raise RuntimeError(f'v1.9.2 capability missing ({label}): {needle}')
    for retired in ('首版配方生成中…',):
        if retired in s:
            raise RuntimeError(f'retired v0.1.8.2 intake path present: {retired}')


def main():
    if not BASE.is_file() or not WEB.is_file():
        sys.exit('FAIL missing v192_base.html or web/index.html')
    if sha(BASE) != BASE_SHA:
        sys.exit('FAIL wrong v1.9.2 baseline: ' + sha(BASE))
    base = BASE.read_text('utf8')
    old = WEB.read_text('utf8')

    if NEW in old:
        if all(k in old for k in IOS_MARKERS) and old.count(NEW) == 2:
            print('NOOP v0.2.0 SHA', sha(WEB))
            return
        sys.exit('FAIL partially installed v0.2.0')

    if not sha(WEB).startswith(PREV_SHA_PREFIX):
        sys.exit('FAIL existing web bundle is not v0.1.9: ' + sha(WEB))
    if any(k in base for k in IOS_MARKERS) or NEW in base:
        sys.exit('FAIL production base already contains iOS patches')
    if '--fs-display' not in base:
        sys.exit('FAIL baseline is not the v1.9.2 type-scale page')
    assert_capabilities(base)

    plist = ROOT / 'ios/App/App/Info.plist'
    if not plist.is_file() or not all(
            x in plist.read_text('utf8') for x in
            ('NSCameraUsageDescription', 'NSPhotoLibraryUsageDescription',
             'NSPhotoLibraryAddUsageDescription', 'NSAllowsArbitraryLoads',
             'NSLocalNetworkUsageDescription')):
        sys.exit('FAIL Info.plist permission/ATS regression')

    bak = ROOT / 'web/index.html.pre-v020.bak'
    if bak.exists():
        sys.exit('FAIL backup already exists; archive it before re-running')
    shutil.copy2(WEB, bak)
    try:
        WEB.write_text(prepare(base), 'utf8')

        for name in ('apply_ios_p0.py', 'apply_ios_p1.py', 'apply_ios_p0b.py',
                     'apply_ios_p1c.py', 'apply_ios_p1d.py', 'apply_ios_p2a.py',
                     'apply_ios_p2b.py'):
            p = subprocess.run([sys.executable, str(ROOT / 'tools' / name)],
                               capture_output=True, text=True, cwd=ROOT)
            print(name, p.returncode, p.stdout.strip()[:120], p.stderr.strip()[:160])
            if p.returncode:
                raise RuntimeError(f'{name} failed: {p.stderr or p.stdout}')

        s = WEB.read_text('utf8')
        s = s.replace('height:var(--xb-safe-top);background:#f7f2eb;',
                      'height:var(--xb-safe-top);background:var(--bg);')

        css = '''
<style id="XB_IOS_V020_REBASE">
/* iOS-only alignment after the v1.9.2 type scale. Additive: every rule is gated on
   html.xb-ios-p0 body.ios-app, and no rule overrides a font-size token -- the App
   must render on the same 7-step scale as the web. */
html.xb-ios-p0 body.ios-app #detailView .detail-top-tabs{scroll-margin-top:calc(max(54px,env(safe-area-inset-top,0px)) + 8px)}
html.xb-ios-p0 body.ios-app #aiAdvancedRecord > summary{min-height:44px;display:flex;align-items:center}
html.xb-ios-p0 body.ios-app .param-grid{max-width:100%}
html.xb-ios-p0 body.ios-app .param-cell{padding:12px 6px}
@media(max-width:520px){
  html.xb-ios-p0 body.ios-app .ai-band-grid{grid-template-columns:1fr}
  html.xb-ios-p0 body.ios-app .ai-route{padding:8px}
}
</style>
'''
        script = '''
<script>/* XB_IOS_V020_REBASE: v1.9.2 type scale + v0.2.0 iOS shims. Server editor uses an inline panel (no prompt()). */</script>
'''
        s = s.replace('</head>', css + '</head>', 1).replace('</body>', script + '</body>', 1)

        s, astats = align_ios_type(s)
        print('ios align:', astats)
        if astats['unmapped']:
            raise RuntimeError('unmapped iOS type rule: %s' % astats['unmapped'][:3])
        s, stats = normalise_type(s)
        print('type normalise:', stats)
        WEB.write_text(s, 'utf8')

        if not all(k in s for k in IOS_MARKERS):
            raise RuntimeError('lost iOS markers')
        if s.count(NEW) != 2:
            raise RuntimeError('V020 marker count wrong: %d' % s.count(NEW))
        assert_capabilities(s)

        # every *text* font-size in the bundle must now be a token; icon glyphs
        # (::before/::after) are allowed to keep a pictograph size
        leftovers = []
        for m in re.finditer(r'(?P<sel>(?:(?!@)[^{}])+)\{(?P<body>[^{}]*)\}', s):
            if 'font-size' not in m.group('body'):
                continue
            sel = m.group('sel')
            if '::before' in sel or '::after' in sel:
                continue
            leftovers += [x.group(0) for x in
                          re.finditer(r'font-size:\s*[\d.]+px', m.group('body'))]
        if leftovers:
            raise RuntimeError('literal font-size survived: %s' % leftovers[:6])

        print('SUCCESS v0.2.0 SHA', sha(WEB))
    except Exception as exc:
        shutil.copy2(bak, WEB)
        sys.exit('FAIL rolled back HTML: ' + str(exc))


if __name__ == '__main__':
    main()
