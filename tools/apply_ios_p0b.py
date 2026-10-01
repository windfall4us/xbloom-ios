#!/usr/bin/env python3
"""iOS v0.1.3 targeted viewport shield and server-shortcut bridge.
Does not edit business JS, API endpoints, or Web upstream.
"""
from pathlib import Path
import hashlib,sys
p=Path(__file__).resolve().parents[1]/'web'/'index.html'
if not p.exists():sys.exit('FAIL web/index.html not found')
s=p.read_text('utf8')
marker='XB_IOS_P0B_V013'
if marker in s: print('NOOP',hashlib.sha256(s.encode()).hexdigest());sys.exit(0)
prereq=['XB_IOS_P0','XB_IOS_P1_V012','id="settingsView"','class="bottom-nav"','id="navSettingsBtn"']
missing=[x for x in prereq if x not in s]
if missing:sys.exit('FAIL prerequisite missing: '+repr(missing))
if s.count('</head>') != 1 or s.count('</body>')!=1:sys.exit('FAIL unexpected HTML closing tags')
# Occluding the status region instead of moving scroll container: preserves browser scrollTo, dialogs and scrolling cards.
style=r'''<style id="XB_IOS_P0B_V013">
/* iOS native-only scroll-under-status shield; no scroll container substitution. */
html.xb-ios-p0 { --xb-safe-top:max(54px, env(safe-area-inset-top, 0px)); }
html.xb-ios-p0::before {
  content:""; position:fixed; left:0;right:0;top:0;
  height:var(--xb-safe-top);background:var(--bg);
  z-index:48; pointer-events:none;
}
/* The native settings shortcut is ONLY shown after a working server button is located. */
html.xb-ios-p0 #xbIosServerSettingsShortcut {
  display:none; width:100%; margin:10px 0 14px; box-sizing:border-box;
  background:var(--bg); color:#725039; text-align:left;
  border:1px solid #ded2c4; padding:12px 14px; border-radius:12px;
  font:inherit; font-weight:700; min-height:44px;
}
html.xb-ios-p0.xb-server-bridge-ready #xbIosServerSettingsShortcut { display:block; }
/* Only hide floating controls after verified button bridge; never hide unknown server controls. */
html.xb-ios-p0.xb-server-bridge-ready .xb-p0b-server-float {display:none!important;}
</style>'''
# DOMContentLoaded is safe if JS loaded with defer at end. Observe late-added bridge only in native app.
script=r'''<script id="XB_IOS_P0B_V013_SCRIPT">
(function(){
  if(!document.documentElement.classList.contains('xb-ios-p0')) return;
  function setup(){
    var view=document.getElementById('settingsView');
    if(!view) return;
    var shortcut=document.getElementById('xbIosServerSettingsShortcut');
    if(!shortcut){
      shortcut=document.createElement('button');shortcut.type='button';
      shortcut.id='xbIosServerSettingsShortcut';
      shortcut.textContent='📶 服务器连接设置';
      shortcut.setAttribute('aria-label','打开服务器连接设置');
      var anchor=view.querySelector('.card')||view;
      anchor.insertBefore(shortcut,anchor.firstChild);
    }
    function identify(){
      // Match a *button* only, exact visible label; never guess a server URL field.
      var matches=Array.from(document.querySelectorAll('button'))
        .filter(function(b){return b!==shortcut && /^(?:📶|🛜|🌐|📡)?\s*服务器\s*$/.test((b.textContent||'').trim());});
      if(matches.length!==1) return false; // Ambiguity = preserve original UI.
      var original=matches[0];
      // Require fixed-position floating placement (class or computed style).
      var positioned=getComputedStyle(original).position==='fixed';
      if(!positioned){
        var parent=original.parentElement;
        if(parent) positioned=getComputedStyle(parent).position==='fixed';
      }
      if(!positioned) return false;
      var floatNode=getComputedStyle(original).position==='fixed'?original:original.parentElement;
      if(!floatNode || view.contains(floatNode) || floatNode.classList.contains('bottom-nav'))return false;
      shortcut.onclick=function(){original.click();};
      floatNode.classList.add('xb-p0b-server-float');
      document.documentElement.classList.add('xb-server-bridge-ready');
      return true;
    }
    if(identify())return;
    // Short-lived passive observation for asynchronously injected original shortcut.
    var n=0, mo=new MutationObserver(function(){
      if(identify() || ++n>80)mo.disconnect();
    });
    mo.observe(document.body,{childList:true,subtree:true});
    setTimeout(function(){mo.disconnect();},10000);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',setup,{once:true});
  else setup();
})();
</script>'''
s=s.replace('</head>',style+'\n</head>',1).replace('</body>',script+'\n</body>',1)
p.write_text(s,'utf8')
print('APPLIED '+str(p));print('SHA256 '+hashlib.sha256(p.read_bytes()).hexdigest())
