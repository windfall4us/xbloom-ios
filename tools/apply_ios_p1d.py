#!/usr/bin/env python3
"""xBloom iOS v0.1.5 P1D: visual-only extraction/adjustment polish.

Fails closed if the expected iOS v0.1.4 baseline, DOM or native activation is absent.
Never changes business JavaScript, handlers, API URLs, or recipe logic.
"""
from pathlib import Path
import hashlib
import re
import sys

p = Path(__file__).resolve().parents[1] / "web" / "index.html"
if not p.is_file():
    sys.exit('FAIL: web/index.html missing; run at xbloom-ios repo root')
s = p.read_text(encoding='utf-8')
marker = 'XB_IOS_P1D_V015'
if marker in s:
    if s.count(marker) != 1:
        sys.exit('FAIL: duplicate P1D marker')
    print('NOOP SHA256=' + hashlib.sha256(s.encode()).hexdigest())
    sys.exit(0)
prereq = [
    'XB_IOS_P0', 'XB_IOS_P1_V012', 'XB_IOS_P0B_V013', 'XB_IOS_P1C_V014',
    'id="detailExtractionPane"', 'id="detailAdjustPane"',
    'id="extractMetricCards"', 'id="pourCards"', 'id="readyBadge"',
    'id="extractionDripperSelect"', 'id="adaptDripperBtn"',
    'id="latestTastingBox"', 'id="adjustAdviceBox"',
    'id="reason"', 'id="nextRows"', 'id="recordTastingTopBtn"',
    'id="versionManagementDetails"', 'id="tastingHistoryDetails"', 'id="timelineDetails"',
]
missing = [key for key in prereq if key not in s]
if missing: sys.exit('FAIL: missing P1D requirements: ' + repr(missing))
if s.count('</head>') != 1 or s.count('</body>') != 1:
    sys.exit('FAIL: unexpected document boundaries')
if "classList.add('ios-app')" not in s and 'classList.add("ios-app")' not in s:
    sys.exit('FAIL: body.ios-app activation missing (avoid silently inert CSS)')
# Match dynamic class definitions as well as the expected DOM IDs; no blind selectors.
classes = ['extract-metric-grid','extract-metric-card','pour-card-grid',
           'session-dripper','adjust-context','latest-tasting-card',
           'adjust-advice-card','compact-details','detail-section-head']
missing_classes = [c for c in classes if not re.search(r'(?<![\w-])'+re.escape(c)+r'(?![\w-])', s)]
if missing_classes: sys.exit('FAIL: unknown style targets: ' + repr(missing_classes))

css = r'''<style id="XB_IOS_P1D_V015">
/* v0.1.5 P1D: native-only visual hierarchy; all existing elements/handlers intact. */
@media(max-width:720px){
  html.xb-ios-p0 body.ios-app #detailExtractionPane,
  html.xb-ios-p0 body.ios-app #detailAdjustPane{min-width:0;max-width:100%;}
  html.xb-ios-p0 body.ios-app #detailExtractionPane main,
  html.xb-ios-p0 body.ios-app #detailAdjustPane main{min-width:0;max-width:100%;}
  html.xb-ios-p0 body.ios-app #detailExtractionPane main > .card,
  html.xb-ios-p0 body.ios-app #detailAdjustPane main > .card{
    padding:14px 13px;border-radius:15px;min-width:0;
  }
  html.xb-ios-p0 body.ios-app #detailExtractionPane h3,
  html.xb-ios-p0 body.ios-app #detailAdjustPane h3{
    font-size:16px;line-height:1.35;margin:0 0 4px;
  }
  html.xb-ios-p0 body.ios-app #detailExtractionPane .detail-section-head,
  html.xb-ios-p0 body.ios-app #detailAdjustPane .detail-section-head{
    gap:8px;align-items:flex-start;
  }
  html.xb-ios-p0 body.ios-app #extractionSourceHint,
  html.xb-ios-p0 body.ios-app #detailAdjustPane .detail-section-head .muted{
    font-size:12px;line-height:1.4;overflow-wrap:anywhere;
  }
  /* Current version, dripper and Ready stay visible: no data is hidden. */
  html.xb-ios-p0 body.ios-app #readyBadge{flex-shrink:0;max-width:100%;}
  html.xb-ios-p0 body.ios-app #detailExtractionPane .session-dripper{
    display:grid;grid-template-columns:minmax(0,1fr);gap:7px;margin-top:11px;
  }
  html.xb-ios-p0 body.ios-app #detailExtractionPane .session-dripper b{font-size:12px;}
  html.xb-ios-p0 body.ios-app #extractionDripperSelect{
    min-width:0;width:100%;max-width:100%;min-height:42px;
  }
  html.xb-ios-p0 body.ios-app #adaptDripperBtn{width:100%;min-height:42px;}
  /* Compact core parameters without reducing label legibility. */
  html.xb-ios-p0 body.ios-app #extractMetricCards{
    grid-template-columns:repeat(3,minmax(0,1fr));gap:0;
    padding:6px 3px;margin-top:11px;border-radius:13px;
  }
  html.xb-ios-p0 body.ios-app #extractMetricCards .extract-metric-card{
    padding:10px 3px;min-width:0;
  }
  html.xb-ios-p0 body.ios-app #extractMetricCards .extract-metric-card:nth-child(3n){border-right:0;}
  html.xb-ios-p0 body.ios-app #extractMetricCards .extract-metric-card span{
    font-size:11px;line-height:1.35;overflow-wrap:anywhere;
  }
  html.xb-ios-p0 body.ios-app #extractMetricCards .extract-metric-card b{
    font-size:clamp(15px,4.8vw,21px);line-height:1.25;
    display:block;overflow-wrap:anywhere;
  }
  /* Pour cards remain horizontal and scrollable within the pour region. */
  html.xb-ios-p0 body.ios-app #pourCards{
    max-width:100%;min-width:0;overscroll-behavior-x:contain;
    -webkit-overflow-scrolling:touch;scroll-snap-type:x proximity;
  }
  html.xb-ios-p0 body.ios-app #detailExtractionPane .recipe-tool-details>summary{
    min-height:44px;padding:12px 14px;
  }
  /* Adjustment: action first; historical details retain original folded semantics. */
  html.xb-ios-p0 body.ios-app #detailAdjustPane .adjust-context{
    margin-top:9px;gap:6px;
  }
  html.xb-ios-p0 body.ios-app #detailAdjustPane .adjust-context .status{
    font-size:12px;max-width:100%;overflow-wrap:anywhere;
  }
  html.xb-ios-p0 body.ios-app #latestTastingBox,
  html.xb-ios-p0 body.ios-app #adjustAdviceBox{
    border-radius:12px;padding:11px 12px;line-height:1.55;
    overflow-wrap:anywhere;
  }
  html.xb-ios-p0 body.ios-app #detailAdjustPane #recordTastingTopBtn{
    width:100%;min-height:44px;
  }
  html.xb-ios-p0 body.ios-app #detailAdjustPane .box.next{
    min-width:0;max-width:100%;overflow-wrap:anywhere;
  }
  html.xb-ios-p0 body.ios-app #reason{font-size:12px;line-height:1.5;overflow-wrap:anywhere;}
  html.xb-ios-p0 body.ios-app #detailAdjustPane .compact-details>summary{
    min-height:44px;padding:11px 2px;display:block;line-height:1.5;
  }
  html.xb-ios-p0 body.ios-app #detailAdjustPane .history-pick-card{
    min-width:0;max-width:100%;overflow-wrap:anywhere;
  }
}
@media(max-width:350px){
  html.xb-ios-p0 body.ios-app #extractMetricCards .extract-metric-card b{font-size:15px;}
  html.xb-ios-p0 body.ios-app #extractMetricCards .extract-metric-card span{font-size:10px;}
}
</style>'''
s = s.replace('</head>', css + '\n</head>', 1)
p.write_text(s, encoding='utf-8')
print('APPLIED ' + marker)
print('SHA256 ' + hashlib.sha256(s.encode()).hexdigest())
