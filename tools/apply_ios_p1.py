#!/usr/bin/env python3
"""Idempotent iOS-only UI patch; apply on top of v0.1.1 P0 ios/web/index.html."""
from pathlib import Path
import sys
p=Path(__file__).resolve().parents[1]/'web'/'index.html'
if not p.exists():
    p=Path.cwd()/'web'/'index.html'
if not p.exists(): sys.exit('FAIL: web/index.html not found (run from xbloom-ios repo root)')
s=p.read_text('utf-8')
if 'XB_IOS_P1_V012' in s:
    print('NOOP: XB_IOS_P1_V012 already applied');sys.exit(0)
required=['XB_IOS_P0','id="settingsAiTab"','id="settingsStatusTab"','id="dripperRegistryList"','class="bean-card"','id="warehouse"','class="bottom-nav"']
missing=[x for x in required if x not in s]
if missing:sys.exit('FAIL missing prerequisite markers: '+', '.join(missing))
css='''
/* XB_IOS_P1_V012 — appearance-only overrides for Capacitor iPhone. */
@media(max-width:720px){
 body.ios-app #settingsView .tabs{width:100%;max-width:100%;margin:10px 0 12px!important;padding:3px 4px 8px!important;overflow-x:auto!important;overflow-y:hidden;scroll-snap-type:x proximity;overscroll-behavior-inline:contain;-webkit-overflow-scrolling:touch;scrollbar-width:none;justify-content:flex-start!important;}
 body.ios-app #settingsView .tabs::-webkit-scrollbar{display:none}
 body.ios-app #settingsView .tabs .tab{scroll-snap-align:start;min-height:40px;max-width:none;flex:0 0 auto!important;white-space:nowrap;padding:8px 12px;overflow:visible!important;text-overflow:clip!important;color:#5d5047!important;background:#fffaf5!important;border:1px solid #ddd0c2!important}
 body.ios-app #settingsView .tabs .tab.active{background:var(--accent)!important;border-color:var(--accent)!important;color:#fff!important}
 body.ios-app #settingsView .card,body.ios-app #settingsView .settings-row{min-width:0;max-width:100%}
 body.ios-app #settingsStatusPane .row{display:flex;flex-wrap:wrap;align-items:flex-start;gap:6px 12px}
 body.ios-app #settingsStatusPane .row>span,body.ios-app #settingsStatusPane .row>div{min-width:0;max-width:100%;overflow-wrap:anywhere;word-break:break-word}
 body.ios-app #settingsStatusPane .row>span:last-child{flex:1 1 54%;text-align:left}
 body.ios-app .dripper-registry-list{gap:8px}
 body.ios-app .dripper-registry-item{padding:12px 13px;border-radius:14px}
 body.ios-app .dripper-registry-head{gap:8px;align-items:flex-start}
 body.ios-app .dripper-registry-head>div{min-width:0;flex:1}
 body.ios-app .dripper-registry-head b{font-size:15px;overflow-wrap:anywhere}
 body.ios-app .dripper-registry-meta{font-size:11px;line-height:1.4}
 body.ios-app .dripper-registry-item .actions{margin-top:7px!important}
 body.ios-app .dripper-registry-item .action{min-height:38px;padding:7px 12px}
 /* Bean list becomes scan-friendly without removing information or changing card click targets. */
 body.ios-app #warehouse.warehouse{grid-template-columns:minmax(0,1fr);gap:10px}
 body.ios-app #warehouse .bean-card{display:grid;grid-template-columns:112px minmax(0,1fr);align-items:stretch;min-height:144px}
 body.ios-app #warehouse .bean-img,body.ios-app #warehouse .img-placeholder{width:112px;height:100%;min-height:144px;aspect-ratio:auto;object-fit:cover;border-radius:0}
 body.ios-app #warehouse .bean-body{min-width:0;padding:11px 12px}
 body.ios-app #warehouse .bean-title{gap:5px;flex-wrap:wrap}
 body.ios-app #warehouse .bean-title b{font-size:15px;line-height:1.3;overflow-wrap:anywhere}
 body.ios-app #warehouse .tags{margin:6px 0;gap:4px}
 body.ios-app #warehouse .tag{font-size:10px;padding:3px 6px}
 body.ios-app #warehouse .intro{-webkit-line-clamp:2;font-size:11px}
 body.ios-app #warehouse .muted{font-size:11px;line-height:1.35}
 body.ios-app #detailView .heroimg{max-height:230px;object-fit:contain;background:#eee7de}
}
@media(max-width:350px){body.ios-app #warehouse .bean-card{grid-template-columns:96px minmax(0,1fr)}body.ios-app #warehouse .bean-img,body.ios-app #warehouse .img-placeholder{width:96px}}
'''
# Append as last stylesheet so prior P0 selectors are preserved. All style applied only in iOS.
needle='</style>'
if needle not in s:sys.exit('FAIL: style closing tag missing')
s=s.replace(needle,css+'\n'+needle,1)
# Do not change JS application functions. Click-only passive scroll handler prevents selected tab appearing clipped.
js='''
<script id="XB_IOS_P1_V012">
(function(){
  if(!(window.Capacitor && document.body)) return;
  function alignSelected(){
    var bar=document.querySelector('#settingsView .tabs');
    if(!bar || !bar.clientWidth) return;
    var tab=bar.querySelector('.tab.active');
    if(!tab) return;
    var target=tab.offsetLeft-bar.offsetLeft-(bar.clientWidth-tab.offsetWidth)/2;
    bar.scrollLeft=Math.max(0,target);
  }
  document.querySelectorAll('#settingsView .tabs .tab').forEach(function(tab){
    tab.addEventListener('click',function(){requestAnimationFrame(alignSelected);});
  });
  var nav=document.getElementById('navSettingsBtn');
  if(nav) nav.addEventListener('click',function(){requestAnimationFrame(alignSelected);});
  // Show first tab when settings is initially displayed; no mutation observers, polling, or API changes.
})();
</script>
'''
if '</body>' not in s:sys.exit('FAIL: body closing tag missing')
s=s.replace('</body>',js+'</body>',1)
p.write_text(s,'utf-8')
print('APPLIED XB_IOS_P1_V012: '+str(p))
