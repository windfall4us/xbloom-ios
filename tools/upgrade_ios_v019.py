#!/usr/bin/env python3
"""v0.1.9 fail-closed rebase: production UI-v1.9 baseline -> iOS bundle.

Base: v19_base.html == production app/static/index.html (UI-v1.9, e1346409...).
Does not access or modify the production app, YAML, or server. No GitHub dependency here.

What changed vs the v0.1.8.3 rebase (v2.3.10 base):
  * recipe tools were refactored to a `recipeToolTarget()` object
    (target.beanId / target.version), so download / QR / raw-URL shims retarget.
  * QR base_url and the raw-URL text used location.origin -> now use the configured server.
  * intake flow is already asynchronous server-side (createIntakeRequestId + pollIntake +
    finishIntakeNavigation), so the old v0.1.8.2 `preserve_async()` transplant is REMOVED.
    Re-injecting the old code would call endpoints that no longer exist.
  * the server editor no longer uses prompt() (WKWebView does not implement it); it is an
    inline panel, still a fixed-position button so P0B can proxy it into Settings.
"""
from pathlib import Path
import hashlib, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web/index.html'
BASE = ROOT / 'v19_base.html'

BASE_SHA = 'e134640984d17bf1639a882c2fbff138cd76dfacf3c031de51595389e1fd4d7d'
PREV_SHA_PREFIX = '21775037'          # v0.1.8.3 web bundle
NEW = 'XB_IOS_V019_REBASE'
IOS_MARKERS = ('XB_IOS_P0_BEGIN', 'XB_IOS_P1_V012', 'XB_IOS_P0B_V013',
               'XB_IOS_P1C_V014', 'XB_IOS_P1D_V015', 'XB_IOS_P2A_V016', 'XB_IOS_P2B_V017')
# Capabilities the v1.9 baseline must still provide for the iOS bundle to be honest.
V19_CAPABILITIES = (
    ('async intake: request id', 'function createIntakeRequestId('),
    ('async intake: poll loop', 'async function pollIntake('),
    ('async intake: navigate on complete', 'async function finishIntakeNavigation('),
    ('navigate to extraction after save', 'showDetailPane("extraction")'),
    ('recipe tool target indirection', 'function recipeToolTarget('),
)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def once(s, needle, label):
    n = s.count(needle)
    if n != 1:
        raise RuntimeError(f'{label}: expected exactly 1 occurrence, got {n}')


SHIM = r'''
/* XB_IOS_V019_SHIM - Capacitor API endpoint adapter + iOS-safe server editor. */
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
   var label=document.createElement('div');label.textContent='服务器地址';label.style.cssText='font-size:13px;color:#666;margin-bottom:6px';
   input=document.createElement('input');input.type='url';input.id='xbIosServerInput';input.value=xbReadServer();
   input.setAttribute('inputmode','url');input.setAttribute('autocapitalize','off');input.setAttribute('autocorrect','off');input.setAttribute('spellcheck','false');input.setAttribute('aria-label','服务器地址');
   input.style.cssText='width:100%;box-sizing:border-box;font-size:16px;padding:10px;border:1px solid #ddd0c2;border-radius:10px;background:#fff;color:#111';
   var row=document.createElement('div');row.style.cssText='display:flex;gap:8px;margin-top:10px';
   var save=document.createElement('button');save.type='button';save.id='xbIosServerSave';save.textContent='保存';
   save.style.cssText='flex:1;padding:11px;border-radius:10px;border:0;background:#634936;color:#fff;font-size:15px';
   var cancel=document.createElement('button');cancel.type='button';cancel.id='xbIosServerCancel';cancel.textContent='取消';
   cancel.style.cssText='flex:1;padding:11px;border-radius:10px;border:1px solid #ddd0c2;background:#fff;color:#634936;font-size:15px';
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
   b.style.cssText='position:fixed;right:12px;bottom:110px;z-index:60;border-radius:12px;padding:10px;background:var(--bg);color:#634936;border:1px solid #ddd0c2';
   b.addEventListener('click',openPanel);
   document.body.classList.add('ios-app');document.body.appendChild(b);
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
})();
'''

RETARGET = (
    # bean card thumbnail
    ('src="${esc(b.image_url)}"', 'src="${esc(absURL(b.image_url))}"', 'bean card image'),
    # detail hero image
    ('src="${esc(d.bean.image_url)}"', 'src="${esc(absURL(d.bean.image_url))}"', 'detail hero image'),
    # recipe download (v1.9 goes through recipeToolTarget())
    ('location.href=`/api/beans/${encodeURIComponent(target.beanId)}/recipes/${encodeURIComponent(target.version)}/download`;',
     'location.href=absURL(`/api/beans/${encodeURIComponent(target.beanId)}/recipes/${encodeURIComponent(target.version)}/download`);',
     'recipe download'),
    # recipe QR (relative src + origin-based base_url)
    ('image.src=`/api/beans/${encodeURIComponent(target.beanId)}/recipes/${encodeURIComponent(target.version)}/qr?base_url=${encodeURIComponent(location.origin)}`;',
     'image.src=absURL(`/api/beans/${encodeURIComponent(target.beanId)}/recipes/${encodeURIComponent(target.version)}/qr?base_url=${encodeURIComponent(xbReadServer())}`);',
     'recipe QR'),
    # raw YAML link, shown as text
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


def assert_capabilities(s):
    for label, needle in V19_CAPABILITIES:
        if needle not in s:
            raise RuntimeError(f'v1.9 capability missing ({label}): {needle}')
    # The old transplant must NOT be re-injected: it rewrote the intake submit path and
    # labelled the step "4 首版配方生成中…", which no longer exists in v1.9.
    # (/api/.../auto-recipe-candidate itself is still a live endpoint elsewhere; do not grep for it.)
    for retired in ('首版配方生成中…',):
        if retired in s:
            raise RuntimeError(f'retired v0.1.8.2 intake path present: {retired}')


def main():
    if not BASE.is_file() or not WEB.is_file():
        sys.exit('FAIL missing v19_base.html or web/index.html')
    if sha(BASE) != BASE_SHA:
        sys.exit('FAIL wrong v1.9 baseline: ' + sha(BASE))
    base = BASE.read_text('utf8')
    old = WEB.read_text('utf8')

    if NEW in old:
        if all(k in old for k in IOS_MARKERS) and old.count(NEW) == 2:
            print('NOOP v0.1.9 SHA', sha(WEB))
            return
        sys.exit('FAIL partially installed v0.1.9')

    if not sha(WEB).startswith(PREV_SHA_PREFIX):
        sys.exit('FAIL existing web bundle is not v0.1.8.3: ' + sha(WEB))
    if any(k in base for k in IOS_MARKERS) or NEW in base:
        sys.exit('FAIL production base already contains iOS patches')
    assert_capabilities(base)

    plist = ROOT / 'ios/App/App/Info.plist'
    if not plist.is_file() or not all(
            x in plist.read_text('utf8') for x in
            ('NSCameraUsageDescription',
             'NSPhotoLibraryUsageDescription',
             'NSPhotoLibraryAddUsageDescription',
             'NSAllowsArbitraryLoads',
             'NSLocalNetworkUsageDescription')):
        sys.exit('FAIL Info.plist permission/ATS regression')

    bak = ROOT / 'web/index.html.pre-v019.bak'
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
            print(name, p.returncode, p.stdout.strip(), p.stderr.strip())
            if p.returncode:
                raise RuntimeError(f'{name} failed: {p.stderr or p.stdout}')

        s = WEB.read_text('utf8')
        # P0B shield colour must follow the page token, not a hardcoded v2.3.10 value.
        s = s.replace('height:var(--xb-safe-top);background:#f7f2eb;',
                      'height:var(--xb-safe-top);background:var(--bg);')

        css = '''
<style id="XB_IOS_V019_REBASE">
/* iOS-only alignment after the v1.9 UI (param grid / merged adjust pane / AI band grid).
   Additive: every rule is gated on html.xb-ios-p0 body.ios-app. */
html.xb-ios-p0 body.ios-app #detailView .detail-top-tabs{scroll-margin-top:calc(max(54px,env(safe-area-inset-top,0px)) + 8px)}
html.xb-ios-p0 body.ios-app #aiAdvancedRecord > summary{min-height:44px;display:flex;align-items:center}
html.xb-ios-p0 body.ios-app .param-grid{max-width:100%}
html.xb-ios-p0 body.ios-app .param-cell{padding:12px 6px}
html.xb-ios-p0 body.ios-app .param-cell .param-v{font-size:20px}
@media(max-width:520px){
  html.xb-ios-p0 body.ios-app .ai-band-grid{grid-template-columns:1fr}
  html.xb-ios-p0 body.ios-app .ai-route{padding:8px}
}
</style>
'''
        script = '''
<script>/* XB_IOS_V019_REBASE: v1.9 baseline + v0.1.9 iOS shims. Server editor uses an inline panel (no prompt()). */</script>
'''
        s = s.replace('</head>', css + '</head>', 1).replace('</body>', script + '</body>', 1)
        WEB.write_text(s, 'utf8')

        if not all(k in s for k in IOS_MARKERS):
            raise RuntimeError('lost iOS markers')
        if s.count(NEW) != 2:
            raise RuntimeError('V019 marker count wrong: %d' % s.count(NEW))
        assert_capabilities(s)
        print('SUCCESS v0.1.9 SHA', sha(WEB))
    except Exception as exc:
        shutil.copy2(bak, WEB)
        sys.exit('FAIL rolled back HTML: ' + str(exc))


if __name__ == '__main__':
    main()
