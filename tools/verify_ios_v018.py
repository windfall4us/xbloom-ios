#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
import re,sys,hashlib,subprocess
s=Path(sys.argv[1]).read_text('utf8')
markers=['XB_IOS_V018_REBASE','XB_IOS_P0_BEGIN','XB_IOS_P1_V012','XB_IOS_P0B_V013','XB_IOS_P1C_V014','XB_IOS_P1D_V015','XB_IOS_P2A_V016','XB_IOS_P2B_V017']
missing=[x for x in markers if x not in s]
assert not missing,missing
assert s.count('async function api(url,opt)')==1
assert 'url=absURL(url)' in s
assert s.count('const XB_SERVER_KEY')==1
assert 'document.body.classList.add(\'ios-app\')' in s
assert s.count('id="navAddBtn"')==1
assert s.count('id="navWarehouseBtn"')==1
assert s.count('id="navSyncBtn"')==1
assert s.count('id="navSettingsBtn"')==1
assert 'tasteBrewTime' in s and 'v239-version-card' in s
assert '旧版实验 Profile（历史兼容）' in s
assert 'src="${esc(absURL(b.image_url))}"' in s
assert 'src="${esc(absURL(d.bean.image_url))}"' in s
assert '$("#qrImg").src=absURL(u);' in s
assert 'getComputedStyle(original).position' in s
assert s.count('</head>')==1 and s.count('</body>')==1
controls=[(i,ord(x)) for i,x in enumerate(s) if ord(x)<32 and x not in '\n\r\t'];assert not controls,controls[:10]
ids=re.findall(r'(?<![\w-])id="([^"]+)"',s);assert len(ids)==len(set(ids)),[x for x in ids if ids.count(x)>1][:6]
scripts=re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>',s,re.S)
for i,script in enumerate(scripts):
 p=subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True)
 assert p.returncode==0,f'JS script {i+1}: {p.stderr}'
print('VERIFY PASS markers',len(markers),'unique IDs',len(ids),'scripts',len(scripts),'sha256',hashlib.sha256(s.encode()).hexdigest())
