#!/usr/bin/env python3
"""Static release gate for v0.1.8.3. Does not claim device tests."""
from pathlib import Path
import subprocess,hashlib,re,plistlib,sys
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'web/index.html';s=p.read_text('utf8')
base=ROOT/'v2310_base.html'
expected='87ce29b558b6e93073f9ffda944fc120597e2cb036bb59e134457125e3613858'
assert hashlib.sha256(base.read_bytes()).hexdigest()==expected,'base SHA mismatch'
markers=['XB_V2310_DETAIL_WORKFLOW_FIX','XB_V2310_NAV_COMPACT_R1','XB_IOS_V018_REBASE','XB_IOS_P0_BEGIN','XB_IOS_P1_V012','XB_IOS_P0B_V013','XB_IOS_P1C_V014','XB_IOS_P1D_V015','XB_IOS_P2A_V016','XB_IOS_P2B_V017','XB_IOS_V0183_DETAIL_REBASE']
for m in markers:assert m in s,'missing '+m
assert s.count('XB_IOS_V0183_DETAIL_REBASE')==2
assert 'async function createBeanFromForm(generateAfter=false)' in s
start=s.index('async function createBeanFromForm(generateAfter=false)');end=s.index('$("#newBeanForm").onsubmit=',start);fn=s[start:end]
assert fn.index('await openBean(created.bean.bean_id)')<fn.index('/auto-recipe-candidate'),'async AI navigation regressed'
assert '4 首版配方生成中…' in fn and '候选配方 v${candidate.version} 已生成。请到萃取页确认配方' in fn
for m in ['id="detailInfoTab"','id="detailExtractionTab"','id="detailAdjustTab"','id="navAddBtn"','id="navWarehouseBtn"','id="navSyncBtn"','id="navSettingsBtn"','id="validateBtn"','id="recordTastingTopBtn"']:
 assert s.count(m)==1,(m,s.count(m))
assert 'id="tastingBtn"' not in s
assert 'XB_V2310_NAV_COMPACT_R1' in s and 'repeat(5,minmax(0,1fr))' in s
assert '整理</button>' in s
assert 'url=absURL(url)' in s and 'function xbReadServer()' in s
assert 'src="${esc(absURL(b.image_url))}"' in s and 'src="${esc(absURL(d.bean.image_url))}"' in s
assert '$("#qrImg").src=absURL(u)' in s
assert 'document.body.classList.add(\'ios-app\')' in s
assert s.count('</head>')==1 and s.count('</body>')==1
ids=re.findall(r'(?<![\w-])id="([^"]+)"',s)
assert len(ids)==len(set(ids)), 'duplicate ids '+repr([x for x in ids if ids.count(x)>1][:5])
assert len(ids)>270,len(ids)
bad=[(i,ord(c)) for i,c in enumerate(s) if ord(c)<32 and c not in '\r\n\t'];assert not bad,bad[:5]
scripts=re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>',s,re.S)
for i,js in enumerate(scripts):
  r=subprocess.run(['node','--check','-'],input=js,capture_output=True,text=True)
  assert r.returncode==0,f'script {i+1} {r.stderr}'
plist=plistlib.loads((ROOT/'ios/App/App/Info.plist').read_bytes())
for k in ('NSCameraUsageDescription','NSPhotoLibraryUsageDescription','NSPhotoLibraryAddUsageDescription','NSLocalNetworkUsageDescription'):
 assert plist.get(k),k
print('PASS base provenance, v2310 dual markers, 7 iOS stages, async flow, navigation, API routing, 4 privacy keys')
print('PASS DOM IDs',len(ids),'script blocks',len(scripts),'control chars 0')
print('INDEX_SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
