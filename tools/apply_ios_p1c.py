#!/usr/bin/env python3
"""Apply visual-only iOS P1C navigation/title/status refinements. Abort on unknown baseline."""
from pathlib import Path
import hashlib,sys
p=Path(__file__).resolve().parents[1]/'web'/'index.html'
if not p.exists(): sys.exit('FAIL: expected ios project web/index.html')
s=p.read_text('utf-8')
marker='XB_IOS_P1C_V014'
if marker in s: print('NOOP '+hashlib.sha256(s.encode()).hexdigest());sys.exit(0)
required=['XB_IOS_P0','XB_IOS_P1_V012','XB_IOS_P0B_V013','id="navAddBtn"','id="navWarehouseBtn"','id="navSyncBtn"','id="navSettingsBtn"','id="settingsStatusPane"','id="statusWorkflow"','class="bottom-nav"']
missing=[t for t in required if t not in s]
if missing:sys.exit('FAIL: missing prereq '+repr(missing))
if s.count('</head>')!=1 or s.count('</body>')!=1:sys.exit('FAIL: closing tags unexpected')
if not any(t in s for t in ["classList.add('ios-app')", 'classList.add("ios-app")']):sys.exit('FAIL: body.ios-app activation is missing; CSS would be inert')
css=r'''<style id="XB_IOS_P1C_V014">
/* Only Capacitor app with activated P0 + P1 gates. Preserve all button IDs and handlers. */
@media (max-width:720px) {
  html.xb-ios-p0 body.ios-app .top {margin:0 0 13px;gap:4px;}
  html.xb-ios-p0 body.ios-app .top h1 {font-size:clamp(23px,6vw,30px);line-height:1.2;letter-spacing:-.025em;overflow-wrap:anywhere;}
  html.xb-ios-p0 body.ios-app .settings-back,
  html.xb-ios-p0 body.ios-app .back button {font-size:13px;min-height:39px;padding:8px 11px;}
  /* Icon above unchanged semantic text; existing active class is authoritative. */
  html.xb-ios-p0 body.ios-app .bottom-nav {
    gap:4px;padding:7px max(10px,env(safe-area-inset-right,0px))
      calc(7px + env(safe-area-inset-bottom,0px)) max(10px,env(safe-area-inset-left,0px));
    align-items:stretch;
  }
  html.xb-ios-p0 body.ios-app .bottom-nav button {
    display:flex;flex-direction:column;gap:2px;align-items:center;justify-content:center;
    border-radius:13px;padding:7px 4px;min-width:0;min-height:55px;
    font-size:12px;line-height:1.2;color:var(--muted);font-weight:650;
    -webkit-tap-highlight-color:transparent;
  }
  html.xb-ios-p0 body.ios-app .bottom-nav button::before {
    display:block;height:23px;line-height:23px;font-size:20px;font-weight:500;
  }
  html.xb-ios-p0 body.ios-app #navAddBtn::before{content:"＋"}
  html.xb-ios-p0 body.ios-app #navWarehouseBtn::before{content:"☕";font-size:19px}
  html.xb-ios-p0 body.ios-app #navSyncBtn::before{content:"☁"}
  html.xb-ios-p0 body.ios-app #navSettingsBtn::before{content:"⚙"}
  html.xb-ios-p0 body.ios-app .bottom-nav button.active{
    color:var(--accent);border-color:#dac4b3;background:#efe2d6;
  }
  /* Status: term is compact, long data is allowed to wrap and be selected. */
  html.xb-ios-p0 body.ios-app #settingsStatusPane .validation {padding:11px;border-radius:14px;}
  html.xb-ios-p0 body.ios-app #settingsStatusPane .row {
    display:grid;grid-template-columns:minmax(78px,34%) minmax(0,1fr);
    column-gap:10px;align-items:start;line-height:1.5;padding:9px 0;
  }
  html.xb-ios-p0 body.ios-app #settingsStatusPane .row > :first-child {
    color:var(--muted);font-size:12px;min-width:0;
  }
  html.xb-ios-p0 body.ios-app #settingsStatusPane .row > :last-child {
    font-size:12px;min-width:0;max-width:100%;overflow-wrap:anywhere;
    word-break:break-word;flex:none;text-align:left;
  }
  html.xb-ios-p0 body.ios-app #settingsStatusPane .validation>b{
    display:block;font-size:15px;padding-bottom:5px;
  }
}
@media(max-width:350px){
  html.xb-ios-p0 body.ios-app .bottom-nav button{font-size:11px}
}
@media(prefers-reduced-motion:reduce){
  html.xb-ios-p0 body.ios-app .bottom-nav *{transition:none!important}
}
</style>'''
s=s.replace('</head>',css+'\n</head>',1)
p.write_text(s,'utf-8')
print('APPLIED '+marker)
print('SHA256 '+hashlib.sha256(p.read_bytes()).hexdigest())
