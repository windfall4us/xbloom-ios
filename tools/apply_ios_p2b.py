#!/usr/bin/env python3
"""iOS-only P2B UX adapter. Runs fail-closed, no Web/backend change."""
from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parent.parent
p=ROOT/'web'/'index.html'
s=p.read_text(encoding='utf-8')
style_id='XB_IOS_P2B_V017'
script_id='XB_IOS_P2B_RUNTIME_V017'
if s.count(style_id)==1 and s.count(script_id)==1:
    print('NOOP: P2B already installed');sys.exit(0)
if style_id in s or script_id in s: raise SystemExit('FAIL: partial P2B marker')
required=['XB_IOS_P2A_V016','XB_IOS_P1D','XB_IOS_P1C','XB_IOS_P0B','xb-ios-p0','ios-app','class="bean-img"','class="heroimg"','xbP2AToast','<head>','</head>','</body>']
missing=[x for x in required if x not in s]
if missing:raise SystemExit('FAIL: missing '+repr(missing))
if s.count('</head>') != 1 or s.count('</body>') != 1:raise SystemExit('FAIL: invalid DOM boundaries')
if 'function initP2A' not in s:raise SystemExit('FAIL: P2A hook missing')
css='''
<style id="XB_IOS_P2B_V017">
/* Activated only by ios-app marker, inherited from v0.1.2 fix. */
html.xb-ios-p0 body.ios-app img.bean-img,
html.xb-ios-p0 body.ios-app img.heroimg{cursor:zoom-in;touch-action:manipulation}
html.xb-ios-p0 body.ios-app #xbP2BViewer[hidden]{display:none!important}
html.xb-ios-p0 body.ios-app #xbP2BViewer{position:fixed;inset:0;z-index:10050;background:rgba(19,17,16,.96);display:flex;flex-direction:column;align-items:center;justify-content:center;overscroll-behavior:contain;color:#fff}
html.xb-ios-p0 body.ios-app #xbP2BViewer .xb-p2b-close{position:absolute;right:16px;top:max(58px,env(safe-area-inset-top));z-index:2;width:46px;height:46px;border:1px solid #8c817b;border-radius:24px;background:#302925;color:#fff;font-size:26px;display:grid;place-items:center}
html.xb-ios-p0 body.ios-app #xbP2BViewer .xb-p2b-stage{width:100%;height:100%;touch-action:none;display:flex;align-items:center;justify-content:center;overflow:hidden}
html.xb-ios-p0 body.ios-app #xbP2BViewer img{display:block;max-width:96vw;max-height:80dvh;object-fit:contain;transform-origin:center center;will-change:transform;user-select:none;-webkit-user-drag:none;touch-action:none}
html.xb-ios-p0 body.ios-app #xbP2BViewer .xb-p2b-hint{position:absolute;bottom:max(30px,env(safe-area-inset-bottom));text-align:center;font-size:12px;color:#d7ccc2;pointer-events:none}
@media(prefers-reduced-motion:reduce){html.xb-ios-p0 body.ios-app #xbP2BViewer *{transition:none!important}}
</style>
'''
js=r'''
<script id="XB_IOS_P2B_RUNTIME_V017">
(function(){
  'use strict';
  function init(){
    if(!window.Capacitor || !document.documentElement.classList.contains('xb-ios-p0') || !document.body.classList.contains('ios-app')) return;
    if(document.getElementById('xbP2BViewer')) return;
    var viewer=document.createElement('div');
    viewer.id='xbP2BViewer';viewer.hidden=true;
    viewer.setAttribute('role','dialog');viewer.setAttribute('aria-modal','true');viewer.setAttribute('aria-label','包装图片预览');
    viewer.innerHTML='<button class="xb-p2b-close" type="button" aria-label="关闭图片预览">×</button><div class="xb-p2b-stage"><img alt="包装图片放大预览" draggable="false"></div><div class="xb-p2b-hint">双指缩放 · 双击复位</div>';
    document.body.appendChild(viewer);
    var stage=viewer.querySelector('.xb-p2b-stage'),photo=stage.querySelector('img'),close=viewer.querySelector('button');
    var previousFocus=null,priorOverflow='',scale=1,dx=0,dy=0,touches=new Map(),startDist=0,startScale=1,startDx=0,startDy=0,startPoint=null,lastTap=0;
    function paint(){photo.style.transform='translate('+dx+'px,'+dy+'px) scale('+scale+')'}
    function reset(){scale=1;dx=0;dy=0;paint()}
    function hide(){if(viewer.hidden)return;viewer.hidden=true;photo.removeAttribute('src');document.body.style.overflow=priorOverflow;touches.clear();reset();if(previousFocus&&previousFocus.isConnected)previousFocus.focus({preventScroll:true})}
    function show(src,alt){if(!src)return;previousFocus=document.activeElement;priorOverflow=document.body.style.overflow;document.body.style.overflow='hidden';photo.src=src;photo.alt=(alt||'咖啡包装')+'放大预览';viewer.hidden=false;reset();close.focus({preventScroll:true})}
    document.addEventListener('click',function(e){var img=e.target.closest&&e.target.closest('img.bean-img,img.heroimg');if(!img || !img.closest('#warehouse,#detailView') || !img.currentSrc && !img.src)return;e.preventDefault();e.stopPropagation();show(img.currentSrc||img.src,img.alt)},true);
    close.addEventListener('click',hide);
    viewer.addEventListener('click',function(e){if(e.target===viewer || e.target===stage)hide()});
    document.addEventListener('keydown',function(e){if(!viewer.hidden&&e.key==='Escape'){e.preventDefault();hide()}});
    function dist(){var v=Array.from(touches.values());return Math.hypot(v[0].x-v[1].x,v[0].y-v[1].y)}
    stage.addEventListener('pointerdown',function(e){if(viewer.hidden)return;stage.setPointerCapture(e.pointerId);touches.set(e.pointerId,{x:e.clientX,y:e.clientY});if(touches.size===2){startDist=dist();startScale=scale;startPoint=null}else if(touches.size===1){startPoint={x:e.clientX,y:e.clientY};startDx=dx;startDy=dy}});
    stage.addEventListener('pointermove',function(e){if(!touches.has(e.pointerId))return;touches.set(e.pointerId,{x:e.clientX,y:e.clientY});if(touches.size===2 && startDist>0){scale=Math.max(1,Math.min(5,startScale*dist()/startDist));if(scale===1){dx=dy=0}paint()}else if(touches.size===1&&scale>1&&startPoint){dx=startDx+e.clientX-startPoint.x;dy=startDy+e.clientY-startPoint.y;paint()}});
    function end(e){touches.delete(e.pointerId);startPoint=null;if(touches.size<2)startDist=0}
    stage.addEventListener('pointerup',end);stage.addEventListener('pointercancel',end);
    stage.addEventListener('dblclick',function(e){e.preventDefault();reset()});
    // Keyboard avoidance: use visual viewport, keep existing scroll root and inputs unchanged.
    var viewport=window.visualViewport,keyboardPending=0;
    function activeEditor(){var el=document.activeElement;return el && el.matches && el.matches('input:not([type=checkbox]):not([type=radio]),textarea,select,[contenteditable="true"]')?el:null}
    function adjust(){if(!viewer.hidden)return;var el=activeEditor();if(!el)return;var vv=window.visualViewport;var visibleBottom=vv?vv.offsetTop+vv.height:window.innerHeight;var obstruction=window.innerHeight-visibleBottom;if(obstruction<110)return;var r=el.getBoundingClientRect();if(r.bottom>visibleBottom-18 || r.top<Math.max(0,vv.offsetTop)+12)el.scrollIntoView({block:'center',behavior:'instant'})}
    function schedule(){clearTimeout(keyboardPending);keyboardPending=setTimeout(adjust,140)}
    if(viewport){viewport.addEventListener('resize',schedule);viewport.addEventListener('scroll',schedule)}
    document.addEventListener('focusin',function(e){if(e.target&&e.target.matches&&e.target.matches('input,textarea,select,[contenteditable="true"]'))schedule()});
    // Haptics: only on explicitly recognized P2A success text, when native plugin exists.
    var toast=document.getElementById('xbP2AToast'),lastHapticText='';
    if(toast && window.MutationObserver){var obs=new MutationObserver(function(){var label=toast.textContent.trim();if(!toast.classList.contains('visible')||toast.dataset.kind!=='success'||!['咖啡豆已创建','已生成滤杯适配候选'].includes(label)){lastHapticText='';return}if(label===lastHapticText)return;lastHapticText=label;var p=window.Capacitor&&window.Capacitor.Plugins&&window.Capacitor.Plugins.Haptics;if(p&&typeof p.impact==='function')Promise.resolve(p.impact({style:'LIGHT'})).catch(function(){});});obs.observe(toast,{childList:true,characterData:true,attributes:true,subtree:true,attributeFilter:['class','data-kind']})}
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
</script>
'''
assert '</head>' in s and '</body>' in s
s=s.replace('</head>',css+'</head>',1).replace('</body>',js+'</body>',1)
p.write_text(s,encoding='utf-8')
print('APPLIED: iOS P2B preview, keyboard, optional Haptics')
