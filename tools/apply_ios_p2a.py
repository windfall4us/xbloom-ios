#!/usr/bin/env python3
"""Fail-closed v0.1.6 iOS-only P2A patch. No server, API schema, or production Web changes."""
from pathlib import Path
import hashlib, re, sys
root = Path(__file__).resolve().parents[1]
p = root / 'web' / 'index.html'
jsfile = Path(__file__).with_name('ios_p2a.js')
if not p.is_file() or not jsfile.is_file(): sys.exit('FAIL missing web/index.html or tools/ios_p2a.js')
s = p.read_text(encoding='utf-8')
marker = 'XB_IOS_P2A_V016'
if marker in s:
    if s.count(marker) != 2: sys.exit('FAIL damaged or duplicated P2A markers')
    print('NOOP ' + hashlib.sha256(p.read_bytes()).hexdigest()); sys.exit(0)
required = ['XB_IOS_P0', 'XB_IOS_P1_V012', 'XB_IOS_P0B_V013',
            'XB_IOS_P1C_V014', 'XB_IOS_P1D_V015',
            'id="navAddBtn"', 'id="navSettingsBtn"',
            'id="recordTastingTopBtn"', 'id="adaptDripperBtn"',
            'id="settingsView"', 'id="newBeanView"']
missing = [x for x in required if x not in s]
if missing: sys.exit('FAIL baseline prerequisites missing: ' + repr(missing))
if s.count('</head>') != 1 or s.count('</body>') != 1:
    sys.exit('FAIL unexpected document boundaries')
if not re.search(r'\basync\s+function\s+api\s*\(', s):
    sys.exit('FAIL expected async function api unavailable; refusing to modify shim')
if not any(x in s for x in ["classList.add('ios-app')", 'classList.add("ios-app")']):
    sys.exit('FAIL body.ios-app activation not present')
if not ('absURL(' in s):
    sys.exit('FAIL iOS API base shim absURL missing')
css = r'''<style id="XB_IOS_P2A_V016">
html.xb-ios-p0 body.ios-app #xbP2AToast {
  position:fixed;left:16px;right:16px;
  bottom:calc(102px + env(safe-area-inset-bottom,0px));
  z-index:120;padding:12px 15px;border-radius:13px;
  background:#4b342b;color:white;font-size:13px;line-height:1.45;
  opacity:0;transform:translateY(12px);pointer-events:none;
  transition:opacity .2s,transform .2s;box-shadow:0 5px 20px #0002;
}
html.xb-ios-p0 body.ios-app #xbP2AToast.visible {opacity:1;transform:translateY(0)}
html.xb-ios-p0 body.ios-app #xbP2AToast[data-kind="error"] {background:#8d3830}
html.xb-ios-p0 body.ios-app #xbP2ANetwork[hidden] {display:none!important}
html.xb-ios-p0 body.ios-app #xbP2ANetwork {
  position:fixed;top:calc(max(54px,env(safe-area-inset-top,0px)) + 4px);
  left:10px;right:10px;z-index:100;display:flex;align-items:center;gap:9px;
  padding:10px 12px;border-radius:13px;background:#fff4e9;color:#663b27;
  border:1px solid #e2ba92;box-shadow:0 6px 20px #0002;
  font-size:12px;line-height:1.4;
}
html.xb-ios-p0 body.ios-app #xbP2ANetworkText {flex:1;min-width:0}
html.xb-ios-p0 body.ios-app #xbP2ARetry {
  flex:0 0 auto;padding:8px 10px;border:1px solid #b48a68;
  border-radius:9px;background:white;color:#663b27;font-size:12px;
}
html.xb-ios-p0 body.ios-app button.xb-p2a-busy {
  opacity:.62!important;cursor:wait;pointer-events:none;
}
@media(prefers-reduced-motion:reduce){
  html.xb-ios-p0 body.ios-app #xbP2AToast{transition:none}
}
</style>'''
script = '<script>\n' + jsfile.read_text(encoding='utf-8') + '\n</script>'
if script.count(marker) != 1: sys.exit('FAIL unexpected P2A script marker count')
out = s.replace('</head>', css + '\n</head>', 1).replace('</body>', script + '\n</body>', 1)
if out.count(marker) != 2:
    # One marker in CSS tag, one in JS comment. Both are intentionally paired.
    sys.exit('FAIL inserted P2A marker count')
# Deliberately check before writing to avoid partial corruption.
if len(out) <= len(s) or out.count('</body>') != 1:
    sys.exit('FAIL output sanity')
p.write_text(out, encoding='utf-8')
print('APPLIED P2A; sha256=' + hashlib.sha256(p.read_bytes()).hexdigest())
