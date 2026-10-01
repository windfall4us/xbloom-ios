#!/usr/bin/env python3
"""Idempotent, iOS-only P0 layout patch for xbloom-ios/web/index.html.
Run from repository root: python3 tools/apply_ios_p0.py
"""
from pathlib import Path
import sys, re, hashlib
root=Path(__file__).resolve().parent.parent
html=root/'web'/'index.html'
if not html.is_file(): sys.exit('FAIL: Missing web/index.html; run from cloned xbloom-ios repository')
s=html.read_text(encoding='utf-8')
markers=['class="bottom-nav"','class="intake-steps"','id="stepPhoto"','id="stepProfile"','id="navWarehouseBtn"']
miss=[m for m in markers if m not in s]
if miss: sys.exit('FAIL: HTML mismatch: '+', '.join(miss))
if 'XB_IOS_P0_BEGIN' in s:
    print('NOOP: existing XB_IOS_P0_BEGIN; sha256='+hashlib.sha256(html.read_bytes()).hexdigest()); sys.exit(0)
if s.count('</head>')!=1 or s.count('<meta name="viewport"')!=1:
    sys.exit('FAIL: unexpected document structure (head/viewport)')
# Important: no modifications to JS functions or existing bound buttons.
# viewport-fit=cover allows WebKit to compute safe area insets.
s=s.replace('content="width=device-width,initial-scale=1"', 'content="width=device-width,initial-scale=1,viewport-fit=cover"',1)
style="""
<!-- XB_IOS_P0_BEGIN: iOS Capacitor-specific safe area & no-clipping; leave Web styling intact -->
<script>
(function () {
  var cap = window.Capacitor;
  var ios = /iPhone|iPad|iPod/.test(navigator.userAgent);
  var native = !!(cap && (typeof cap.isNativePlatform === 'function' ? cap.isNativePlatform() : true));
  if (ios && (native || location.protocol === 'capacitor:')) {
    document.documentElement.classList.add('xb-ios-p0');
  }
})();
</script>
<style>
/* Capacitor/iOS only: never change browser Web UI. */
html.xb-ios-p0 { width:100%; max-width:100%; overflow-x:clip; }
html.xb-ios-p0 body {
  width:100%; max-width:100%; min-width:0; overflow-x:clip;
  /* Existing WKWebView overlays iOS status bar: explicitly reserve top inset.
     min fallback is needed on WebViews reporting env(safe-area-inset-top)=0. */
  padding-top:max(54px, env(safe-area-inset-top, 0px));
  padding-bottom:0;
}
html.xb-ios-p0 .wrap {
  box-sizing:border-box; width:100%; min-width:0; max-width:100%;
  padding-left:max(12px, env(safe-area-inset-left, 0px));
  padding-right:max(12px, env(safe-area-inset-right, 0px));
  /* Reserve space for fixed nav including home indicator. */
  padding-bottom:calc(88px + env(safe-area-inset-bottom, 0px));
}
html.xb-ios-p0 .bottom-nav {
  box-sizing:border-box; width:100%; max-width:100%;
  padding-left:max(12px, env(safe-area-inset-left, 0px));
  padding-right:max(12px, env(safe-area-inset-right, 0px));
  padding-bottom:calc(10px + env(safe-area-inset-bottom, 0px));
}
html.xb-ios-p0 .bottom-nav button {min-width:0; padding-left:5px; padding-right:5px;}
/* Replace 4 * min-width:118px with four responsive steps. No DOM removal. */
html.xb-ios-p0 .intake-steps {
  display:grid; grid-template-columns:repeat(4,minmax(0,1fr));
  overflow-x:visible; width:100%; min-width:0; max-width:100%; gap:5px;
}
html.xb-ios-p0 .intake-step {
  min-width:0!important; width:100%; max-width:100%;
  white-space:normal; overflow-wrap:anywhere; word-break:normal;
  padding:8px 2px; font-size:clamp(9px,2.5vw,11px); line-height:1.25;
  touch-action:manipulation;
}
html.xb-ios-p0 .card,
html.xb-ios-p0 .detail,
html.xb-ios-p0 .detail-pane,
html.xb-ios-p0 .form-grid,
html.xb-ios-p0 .sync-slot-grid,
html.xb-ios-p0 .capture-panel {min-width:0; max-width:100%;}
html.xb-ios-p0 img {max-width:100%;}
/* Keep existing intentional horizontal scroll: tabs and pour cards. */
html.xb-ios-p0 .settings-tabs,
html.xb-ios-p0 .pour-card-grid {max-width:100%;}
@media (max-width:375px){html.xb-ios-p0 .intake-step{font-size:9px;padding:7px 1px;}}
</style>
<!-- XB_IOS_P0_END -->
"""
s=s.replace('</head>',style+'</head>',1)
html.write_text(s,encoding='utf-8')
print('PATCH PASS: '+str(html))
print('SHA256: '+hashlib.sha256(html.read_bytes()).hexdigest())
print('P0 DOM unchanged: stepPhoto, stepProfile, bottom-nav still exist')
