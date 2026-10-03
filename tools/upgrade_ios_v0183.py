#!/usr/bin/env python3
"""v0.1.8.3 fail-closed rebase: v2.3.10 nav-polish baseline -> iOS v0.1.8.2 UX.
Does not access or modify production app, YAML, or server. No dependency on GitHub.
"""
from pathlib import Path
import hashlib, re, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web/index.html'; BASE=ROOT/'v2310_base.html'
BASE_SHA='87ce29b558b6e93073f9ffda944fc120597e2cb036bb59e134457125e3613858'
SOURCE_SHA_PREFIX='7b42bbb8' # documented v0.1.8.2 web bundle
IOS_MARKERS=('XB_IOS_V018_REBASE','XB_IOS_P0_BEGIN','XB_IOS_P1_V012','XB_IOS_P0B_V013','XB_IOS_P1C_V014','XB_IOS_P1D_V015','XB_IOS_P2A_V016','XB_IOS_P2B_V017')
V2310_MARKERS=('XB_V2310_DETAIL_WORKFLOW_FIX','XB_V2310_NAV_COMPACT_R1')
NEW='XB_IOS_V0183_DETAIL_REBASE'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def assert_one(s,needle,label):
    if s.count(needle)!=1:raise RuntimeError(f'{label}: expected once, got {s.count(needle)}')

def prepare(base):
    # Rebuild consistent origin handling, same as v0.1.8 shipped shim.
    shim=r'''
/* XB_IOS_V018_REBASE - Capacitor API endpoint adapter. */
const XB_SERVER_KEY='xbloom_ios_server_url';
function xbReadServer(){let s=localStorage.getItem(XB_SERVER_KEY)||'http://192.168.50.22:8088';return s.replace(/\/+$/,'');}
function absURL(path){if(typeof path!=='string')return path;if(/^(?:https?:|blob:|data:)/i.test(path))return path;return xbReadServer()+(path.startsWith('/')?path:'/'+path);}
function xbStoreServer(v){const u=new URL(v.trim());if(!['http:','https:'].includes(u.protocol)||!u.hostname||u.username||u.password||u.search||u.hash)throw Error('请输入有效的 HTTP(S) 服务器地址');localStorage.setItem(XB_SERVER_KEY,u.origin);return u.origin;}
(function(){function makeEditor(){if(!window.Capacitor||document.getElementById('xbIosServerButton'))return;
 let b=document.createElement('button');b.type='button';b.id='xbIosServerButton';b.textContent='🛜 服务器';b.style.cssText='position:fixed;right:12px;bottom:110px;z-index:60;border-radius:12px;padding:10px;background:var(--bg);color:#634936;border:1px solid #ddd0c2';
 b.addEventListener('click',function(){const v=prompt('服务器地址',xbReadServer());if(v===null)return;try{xbStoreServer(v);alert('地址已保存。请重新启动 App。')}catch(e){alert(e.message)}});
 document.body.classList.add('ios-app');document.body.appendChild(b);}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',makeEditor,{once:true});else makeEditor();})();
'''
    anchor='let beans=[],selected=null,selectedBean=null'
    assert_one(base,anchor,'globals');assert_one(base,'async function api(url,opt){','api')
    base=base.replace('async function api(url,opt){','async function api(url,opt){\n url=absURL(url);',1)
    base=base.replace(anchor,shim+'\n'+anchor,1)
    changes={
     'src="${esc(b.image_url)}"':'src="${esc(absURL(b.image_url))}"',
     'src="${esc(d.bean.image_url)}"':'src="${esc(absURL(d.bean.image_url))}"',
     'location.href=`/api/beans/${encodeURIComponent(selected.bean_id)}/recipes/${encodeURIComponent(currentVersion)}/download`;':'location.href=absURL(`/api/beans/${encodeURIComponent(selected.bean_id)}/recipes/${encodeURIComponent(currentVersion)}/download`);',
     'location.href=`/api/beans/${encodeURIComponent(selected.bean_id)}/bundle`;':'location.href=absURL(`/api/beans/${encodeURIComponent(selected.bean_id)}/bundle`);',
     '$("#qrImg").src=u;':'$("#qrImg").src=absURL(u);',
     'encodeURIComponent(location.origin)':'encodeURIComponent(xbReadServer())',
     'const url=location.origin+`/raw/recipes/':'const url=xbReadServer()+`/raw/recipes/'
    }
    for a,b in changes.items():
      assert_one(base,a,'API shim '+a[:36]);base=base.replace(a,b,1)
    return base

def preserve_async(old,new):
    # v0.1.8.2 fix: save bean -> display detail immediately -> await AI.
    begin='async function createBeanFromForm(generateAfter=false){'
    end='$("#newBeanForm").onsubmit='
    for s,label in [(old,'old 0182'),(new,'new v2310')]:
      assert_one(s,begin,label+' function begin')
      assert_one(s,end,label+' function end')
    old_piece=old[old.index(begin):old.index(end)]
    if '4 首版配方生成中…' not in old_piece or 'if(candidate){alert(`咖啡豆已保存，候选配方 v' not in old_piece:
        raise RuntimeError('v0.1.8.2 async fix not present; do not silently regress')
    if 'await openBean(created.bean.bean_id);showDetailPane("extraction")' not in old_piece:raise RuntimeError('missing async navigation')
    new_piece=new[new.index(begin):new.index(end)]
    # Confirm v2310 has not modified the backend-facing form contract beyond old iOS fix.
    old_piece_slim=re.sub(r'\s+',' ',old_piece)
    if '/auto-recipe-candidate' not in new_piece or 'obj.flavor_notes' not in new_piece:raise RuntimeError('unknown v2310 intake contract')
    new=new.replace(new_piece,old_piece,1)
    return new

def main():
    if not BASE.is_file() or not WEB.is_file():sys.exit('FAIL missing v2310_base.html or current web/index.html')
    if sha(BASE)!=BASE_SHA:sys.exit('FAIL wrong verified v2310 nav baseline: '+sha(BASE))
    base=BASE.read_text('utf8');old=WEB.read_text('utf8')
    if NEW in old:
       if all(k in old for k in IOS_MARKERS+V2310_MARKERS) and old.count(NEW)==2:
          print('NOOP v0.1.8.3 SHA',sha(WEB));return
       sys.exit('FAIL partially installed v0.1.8.3')
    if not all(k in old for k in IOS_MARKERS):sys.exit('FAIL v0.1.8.2 iOS markers incomplete')
    if not all(k in base for k in V2310_MARKERS):sys.exit('FAIL wrong v2310 feature baseline')
    if all(k in base for k in IOS_MARKERS):sys.exit('FAIL production base contains iOS patches')
    if '首版配方生成中…' not in old:sys.exit('FAIL original v0.1.8.2 async flow not present')
    # Ensure preexisting old page matches uploaded v0182 source if in repo; fail closed for unexpected future files.
    if not sha(WEB).startswith(SOURCE_SHA_PREFIX):sys.exit('FAIL existing web file not expected v0.1.8.2: '+sha(WEB))
    plist=ROOT/'ios/App/App/Info.plist'
    if not plist.is_file() or not all(x in plist.read_text('utf8') for x in ('NSCameraUsageDescription','NSPhotoLibraryUsageDescription','NSPhotoLibraryAddUsageDescription')):
       sys.exit('FAIL v0.1.8.1 camera permission regression')
    bak=ROOT/'web/index.html.pre-v0183.bak'
    if bak.exists():sys.exit('FAIL backup already exists; archive it before re-running')
    shutil.copy2(WEB,bak)
    try:
      s=preserve_async(old,prepare(base))
      WEB.write_text(s,'utf8')
      for name in ('apply_ios_p0.py','apply_ios_p1.py','apply_ios_p0b.py','apply_ios_p1c.py','apply_ios_p1d.py','apply_ios_p2a.py','apply_ios_p2b.py'):
        p=subprocess.run([sys.executable,str(ROOT/'tools'/name)],capture_output=True,text=True,cwd=ROOT)
        print(name,p.returncode,p.stdout.strip(),p.stderr.strip())
        if p.returncode:raise RuntimeError(f'{name} failed: {p.stderr or p.stdout}')
      s=WEB.read_text('utf8')
      s=s.replace('height:var(--xb-safe-top);background:#f7f2eb;', 'height:var(--xb-safe-top);background:var(--bg);')
      # The new backend has made tab state selection and UX compact; keep them as-is.
      css='''\n<style id="XB_IOS_V0183_DETAIL_REBASE">\n/* iOS-only: align detail navigation after entering without changing server render logic. */\nhtml.xb-ios-p0 body.ios-app #detailView .detail-top-tabs{scroll-margin-top:calc(max(54px,env(safe-area-inset-top,0px)) + 8px)}\n</style>\n'''
      script='''\n<script>/* XB_IOS_V0183_DETAIL_REBASE: v2310 nav and v0182 async preserved. */</script>\n'''
      s=s.replace('</head>',css+'</head>',1).replace('</body>',script+'</body>',1)
      WEB.write_text(s,'utf8')
      if not all(k in s for k in IOS_MARKERS+V2310_MARKERS):raise RuntimeError('lost markers')
      if s.count(NEW)!=2:raise RuntimeError('marker count wrong')
      print('SUCCESS v0.1.8.3 SHA',sha(WEB))
    except Exception as exc:
      shutil.copy2(bak,WEB)
      sys.exit('FAIL rolled back HTML: '+str(exc))
if __name__=='__main__':main()
