#!/usr/bin/env python3
"""Structural verification for the v0.3.1 iOS web bundle (no server access).

Checks:
  1. baseline file is still the locked UI-2.6.1 page
  2. every iOS marker is present, with the exact expected count
  3. the derived bundle loses no DOM id from the baseline
  4. all API traffic goes through api()->absURL()
  5. no leftover location.origin / prompt()-based server editing
  6. every inline <script> block parses under `node --check`
  7. iOS-only CSS cannot activate in a plain browser
  8. the whole bundle stays on the 7-step type scale (v1.9.2 rule): no literal
     text font-size, no clamp()/vw/em sizing, no 800/900 weights; only icon
     glyphs (::before/::after) may keep a pictograph size
"""
from pathlib import Path
import hashlib, re, subprocess, sys, tempfile

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web/index.html'
BASE = ROOT / 'v261_base.html'
BASE_SHA = '0088f57a47b81b6389578d3b7b74676375406cc2cee9fbbb0e22c58b7ed743dc'

MARKERS = {
    'XB_IOS_V031_SHIM': 1,
    'XB_IOS_V031_REBASE': 2,
    'XB_IOS_P0_BEGIN': 1,
    'XB_IOS_P1_V012': 2,
    'XB_IOS_P0B_V013': 2,
    'XB_IOS_P1C_V014': 1,
    'XB_IOS_P1D_V015': 1,
    'XB_IOS_P2A_V016': 2,
    'XB_IOS_P2B_V017': 1,
}
TOKENS = {'display': 32, 'hero': 24, 'value': 22, 'section': 18,
          'body-lg': 16, 'body': 14, 'caption': 12}
GLYPH_RULES = 3          # #navWarehouseBtn::before, bottom-nav icons, … pictographs only

fails, passes = [], []


def ok(label, cond, detail=''):
    if cond:
        passes.append(label)
        print(f'  PASS  {label}' + (f'  {detail}' if detail else ''))
    else:
        fails.append(label)
        print(f'  FAIL  {label}' + (f'  {detail}' if detail else ''))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def script_blocks(html):
    out = []
    for m in re.finditer(r'<script\b([^>]*)>', html):
        attrs, start = m.group(1), m.end()
        if 'src=' in attrs:
            continue
        end = html.find('</script>', start)
        if end == -1:
            continue
        out.append((html[:start].count('\n') + 1, html[start:end]))
    return out


def rules(html):
    for m in re.finditer(r'(?P<sel>(?:(?!@)[^{}])+)\{(?P<body>[^{}]*)\}', html):
        yield m.group('sel').strip(), m.group('body')


def main():
    print('== 基线 ==')
    ok('v261_base.html 仍是 UI-2.6.1', sha(BASE) == BASE_SHA, sha(BASE)[:16])
    base = BASE.read_text('utf8')
    new = WEB.read_text('utf8')

    print('== 标记 ==')
    for k, n in MARKERS.items():
        ok(f'{k} = {n}', new.count(k) == n, f'实际 {new.count(k)}')

    print('== DOM 完整性 ==')
    idsb = set(re.findall(r'id="([^"]+)"', base))
    idsn = set(re.findall(r'id="([^"]+)"', new))
    lost = sorted(idsb - idsn)
    ok('baseline id 无丢失', not lost, f'丢失 {lost}' if lost else f'{len(idsb)} 个全在')

    print('== API 出口 ==')
    ok('fetch( 只有 1 处（api() 内）', new.count('fetch(') == 1, f'实际 {new.count("fetch(")}')
    ok('无 fetch("/api', new.count('fetch("/api') == 0)
    ok('无 fetch(`/api', new.count('fetch(`/api') == 0)
    ok('api() 首行走 absURL', 'async function api(url,opt){\n url=absURL(url);' in new)
    ok('无 location.origin 残留', new.count('location.origin') == 0, f'实际 {new.count("location.origin")}')
    ok('QR base_url 用 xbReadServer', 'encodeURIComponent(xbReadServer())' in new)
    ok('raw 链接用 xbReadServer', new.count('xbReadServer(') >= 4, f'实际 {new.count("xbReadServer(")}')

    print('== 服务器编辑器 ==')
    code = re.sub(r'/\*.*?\*/', '', new, flags=re.S)
    code = re.sub(r'//[^\n]*', '', code)
    calls = len(re.findall(r'(?<![\w.$])prompt\s*\(', code))
    ok('无 prompt( 调用', calls == 0, f'实际 {calls}')
    ok('内联面板存在', new.count("id='xbIosServerPanel'") == 1)
    ok('输入框用 --fs-body-lg（16px，防 iOS 聚焦缩放）',
       'font-size:var(--fs-body-lg);padding:10px' in new)
    ok('保存按钮存在', new.count("'xbIosServerSave'") == 1)

    print('== iOS CSS 门禁 ==')
    css_start = new.find('<style id="XB_IOS_V031_REBASE">')
    css_end = new.find('</style>', css_start)
    block = new[css_start:css_end]
    ungated = [l for l in block.splitlines()
               if '{' in l and 'xb-ios-p0' not in l
               and not l.strip().startswith(('@media', '</style', '<style'))]
    ok('V031 规则全部带 html.xb-ios-p0', not ungated, f'未门禁 {ungated[:2]}' if ungated else 'ok')
    decl = re.findall(r'font-size\s*:', block)
    ok('V031 不覆盖任何字号 token', not decl,
       f'block 内 {len(decl)} 条 font-size 声明' if decl else '无 font-size 声明')
    ok('基线不含 iOS 标记', 'XB_IOS_P0_BEGIN' not in base)

    print('== 排版规范（v1.9.2）==')
    ok('基线是 type-scale 页面', '--fs-display:32px' in base)
    tok_used = set(re.findall(r'--fs-([a-z-]+):', new))
    ok('仅 7 个字号 token', tok_used == set(TOKENS), f'{sorted(tok_used)}')
    ok('token 取值与规范一致',
       all(f'--fs-{k}:{v}px' in new for k, v in TOKENS.items()))

    literal_text, glyph_literals = [], []
    for sel, body in rules(new):
        if 'font-size' not in body:
            continue
        hits = re.findall(r'font-size:\s*[\d.]+px', body)
        if not hits:
            continue
        if '::before' in sel or '::after' in sel or re.search(r'content:\s*["\']', body):
            glyph_literals += hits
        else:
            literal_text += [f'{sel} -> {h}' for h in hits]
    ok('文本规则无字面 px 字号', not literal_text, f'{literal_text[:3]}' if literal_text else '0 处')
    ok(f'图标字形像素 ≤ {GLYPH_RULES} 处', len(glyph_literals) <= GLYPH_RULES,
       f'实际 {len(glyph_literals)}: {glyph_literals}')

    clamp_css = [l for l in new.splitlines() if 'font-size' in l and 'clamp(' in l]
    ok('CSS 无 clamp() 字号', not clamp_css, f'{clamp_css[:2]}' if clamp_css else '0 处')
    rel = [l for l in new.splitlines() if 'font-size' in l and re.search(r'font-size:[^;}]*\d(em|vw|rem|%)', l)]
    ok('CSS 无 em/vw/rem/% 字号', not rel, f'{rel[:2]}' if rel else '0 处')
    heavy = re.findall(r'font-weight:\s*(?:800|900|650|750)', new)
    ok('无 800/900/650 字重', not heavy, f'{heavy[:3]}' if heavy else '0 处')
    ok('h3 显式声明 section',
       bool(re.search(r'h3\{font-size:var\(--fs-section\)', new)))

    print('== F-03：不写死内网地址 ==')
    private = re.findall(r'(?:192\.168|10|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}', new)
    ok('bundle 内不含内网地址', not private,
       f'出现 {len(private)} 次: {private[:2]}' if private else '0 处')
    ok('默认服务器地址为空串', "localStorage.getItem(XB_SERVER_KEY)||''" in new)
    ok('未配置时 absURL 不拼主机', 'const base=xbReadServer();if(!base)return path;' in new)
    ok('首次启动自动弹出配置面板', "if(!xbReadServer()){" in new and "xbIosServerHint" in new)

    print('== 2.6.0 能力保留 ==')
    ok('萃取页双页签存在', new.count('xb-tabbar') >= 1 and new.count('xbExtractTab') >= 2,
       f"tabbar={new.count('xb-tabbar')} tab={new.count('xbExtractTab')}")
    ok('调整页版本管理仍存在', new.count('versionManagerSummary') >= 1)
    ok('归档池仍存在', new.count('archivePoolDetails') >= 1)
    ok('候选差异端点仍在用', new.count('candidates/diff') >= 1)
    ok('回退弹窗语义保留', 'is_rollback' in new)
    ok('AI 参数四列规则保留', 'cols-4' in new or 'ai-param-grid' in new)
    ok('版本标签只有一个函数', new.count('function xbMachineVersion(') == 1)

    print('== 2.6.1 页面结构（底部导航/设置/同步不能被嵌进 detailView）==')
    from html.parser import HTMLParser as _HP
    class _D(_HP):
        def __init__(self):
            super().__init__(convert_charrefs=True); self.stack=[]; self.depth={}
        def handle_starttag(self, tag, attrs):
            a=dict(attrs); i=a.get('id')
            if i in ('warehouseView','syncView','detailView','newBeanView','settingsView') and i not in self.depth:
                self.depth[i]=len(self.stack)
            if a.get('class')=='bottom-nav' and 'bottom-nav' not in self.depth:
                self.depth['bottom-nav']=len(self.stack)
            if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):
                self.stack.append(tag)
        def handle_endtag(self, tag):
            if tag in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'): return
            for idx in range(len(self.stack)-1,-1,-1):
                if self.stack[idx]==tag:
                    del self.stack[idx:]; return
    d=_D(); d.feed(new)
    views=[d.depth.get(k) for k in ('warehouseView','syncView','detailView','newBeanView','settingsView','bottom-nav')]
    ok('五个视图 + 底部导航同级', len(set(views))==1 and None not in views, str(views))
    ok('底部导航不在 detailView 内', d.depth.get('bottom-nav')==d.depth.get('detailView'))
    ok('列表空状态存在', 'warehouse-empty' in new)

    print('== 脚本语法 ==')
    blocks = script_blocks(new)
    with tempfile.TemporaryDirectory() as td:
        for i, (line, body) in enumerate(blocks):
            p = Path(td) / f'b{i}.js'
            p.write_text(body, 'utf8')
            r = subprocess.run(['node', '--check', str(p)], capture_output=True, text=True)
            ok(f'<script> #{i + 1} (行 {line}) 语法', r.returncode == 0,
               (r.stderr or '').strip().splitlines()[0][:90] if r.returncode else '')

    print()
    print(f'结果: {len(passes)} PASS / {len(fails)} FAIL')
    if fails:
        print('失败项: ' + ', '.join(fails))
        sys.exit(1)


if __name__ == '__main__':
    main()
