#!/usr/bin/env python3
"""Safely rebuild v0.1.8 iOS web view from locked v2.3.9 baseline; never edit live Web."""
from pathlib import Path
import sys, hashlib, subprocess, shutil, re, json, os
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'/'index.html'
BASE=ROOT/'v239_base'/'index.html'
EXPECTED_BASE='4a939953'  # full SHA stored in manifest after verification
MARKERS=('XB_IOS_P0_BEGIN','XB_IOS_P1_V012','XB_IOS_P0B_V013','XB_IOS_P1C_V014','XB_IOS_P1D_V015','XB_IOS_P2A_V016','XB_IOS_P2B_V017')
if not BASE.is_file():sys.exit('FAIL v239_base/index.html missing')
base=BASE.read_text('utf-8')
if hashlib.sha256(BASE.read_bytes()).hexdigest()[:8]!=EXPECTED_BASE:sys.exit('FAIL wrong v2.3.9 base')
if not WEB.is_file():sys.exit('FAIL expected existing ios repo web/index.html')
old=WEB.read_text('utf-8')
if all(m in old for m in MARKERS) and 'XB_IOS_V018_REBASE' in old:
 print('NOOP: v0.1.8 already installed; SHA '+hashlib.sha256(WEB.read_bytes()).hexdigest());sys.exit(0)
if not all(m in old for m in MARKERS):sys.exit('FAIL: existing iOS seven-patch baseline not proven')
if base.count('async function api(url,opt)')!=1:sys.exit('FAIL unknown api() signature')
if any(m in base for m in MARKERS):sys.exit('FAIL base unexpectedly contains iOS patches')
backup=ROOT/'web'/'index.html.pre-v018.bak'
if backup.exists():sys.exit('FAIL previous backup exists; archive it before retry')
shutil.copy2(WEB,backup)
# API shim for bundled offline HTML; device URL persisted in localStorage.
shim='''\n/* XB_IOS_V018_REBASE - Capacitor API endpoint adapter. */
const XB_SERVER_KEY='xbloom_ios_server_url';
function xbReadServer(){let s=localStorage.getItem(XB_SERVER_KEY)||'http://192.168.50.22:8088';return s.replace(/\\/+$/,'');}
function absURL(path){if(typeof path!=='string')return path;if(/^(?:https?:|blob:|data:)/i.test(path))return path;return xbReadServer()+(path.startsWith('/')?path:'/'+path);}
function xbStoreServer(v){const u=new URL(v.trim());if(!['http:','https:'].includes(u.protocol)||!u.hostname||u.username||u.password||u.search||u.hash)throw Error('请输入有效的 HTTP(S) 服务器地址');localStorage.setItem(XB_SERVER_KEY,u.origin);return u.origin;}
(function(){function makeEditor(){if(!window.Capacitor||document.getElementById('xbIosServerButton'))return;
 let b=document.createElement('button');b.type='button';b.id='xbIosServerButton';b.textContent='🛜 服务器';b.style.cssText='position:fixed;right:12px;bottom:110px;z-index:60;border-radius:12px;padding:10px;background:#fffdf9;color:#634936;border:1px solid #ddd0c2';
 b.addEventListener('click',function(){const v=prompt('服务器地址',xbReadServer());if(v===null)return;try{xbStoreServer(v);alert('地址已保存。请重新启动 App。')}catch(e){alert(e.message)}});
 document.body.classList.add('ios-app');document.body.appendChild(b);}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',makeEditor,{once:true});else makeEditor();})();
'''
base=base.replace('async function api(url,opt){','async function api(url,opt){\n url=absURL(url);',1)
# Place shim at top of the main application script, directly preceding globals declaration
anchor='let beans=[],selected=null,selectedBean=null'
if base.count(anchor)!=1:sys.exit('FAIL globals anchor mismatch')
base=base.replace(anchor,shim+'\n'+anchor,1)
assertions={
 'image list':'src="${esc(b.image_url)}"',
 'image detail':'src="${esc(d.bean.image_url)}"',
 'download recipe':'location.href=`/api/beans/',
 'qr':'$("#qrImg").src=u;',
 'raw URL':'const url=location.origin+`/raw/recipes/',
}
for name,target in assertions.items():
 if target not in base:sys.exit('FAIL missing '+name)
base=base.replace('src="${esc(b.image_url)}"','src="${esc(absURL(b.image_url))}"')
base=base.replace('src="${esc(d.bean.image_url)}"','src="${esc(absURL(d.bean.image_url))}"')
base=base.replace('location.href=`/api/beans/${encodeURIComponent(selected.bean_id)}/recipes/${encodeURIComponent(currentVersion)}/download`;','location.href=absURL(`/api/beans/${encodeURIComponent(selected.bean_id)}/recipes/${encodeURIComponent(currentVersion)}/download`);')
base=base.replace('location.href=`/api/beans/${encodeURIComponent(selected.bean_id)}/bundle`;','location.href=absURL(`/api/beans/${encodeURIComponent(selected.bean_id)}/bundle`);')
base=base.replace('$("#qrImg").src=u;','$("#qrImg").src=absURL(u);')
base=base.replace('encodeURIComponent(location.origin)','encodeURIComponent(xbReadServer())')
base=base.replace('const url=location.origin+`/raw/recipes/', 'const url=xbReadServer()+`/raw/recipes/')
if base.count('const XB_SERVER_KEY')!=1:sys.exit('FAIL shim missing')
WEB.write_text(base,'utf-8')
try:
 stages=['apply_ios_p0.py','apply_ios_p1.py','apply_ios_p0b.py','apply_ios_p1c.py','apply_ios_p1d.py','apply_ios_p2a.py','apply_ios_p2b.py']
 for script in stages:
  p=subprocess.run([sys.executable,str(ROOT/'tools'/script)],cwd=ROOT,text=True,capture_output=True)
  print(script,p.returncode,p.stdout.strip(),p.stderr.strip());
  if p.returncode:raise RuntimeError(script+' failed')
 s=WEB.read_text('utf-8')
 # Established P0B status bar shield background should match body bg
 s=s.replace('height:var(--xb-safe-top);background:#f7f2eb;','height:var(--xb-safe-top);background:var(--bg);')
 if not all(x in s for x in MARKERS):raise RuntimeError('lost historical P0-P2B markers')
 if s.count('document.body.classList.add(\'ios-app\')')==0 and 'classList.add("ios-app")' not in s:raise RuntimeError('ios-app CSS activation lost')
 # P1 source adds activation at script, but future refactoring must re-run checks
 WEB.write_text(s,'utf-8')
 print('SUCCESS INDEX SHA256',hashlib.sha256(WEB.read_bytes()).hexdigest())
except Exception as e:
 shutil.copy2(backup,WEB)
 sys.exit('FAIL; restored prior iOS web/index.html: '+str(e))
