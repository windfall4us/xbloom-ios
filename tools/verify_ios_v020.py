#!/usr/bin/env python3
"""Structural verification for the v0.2.0 iOS web bundle (no server access).

Checks:
  1. baseline file is still the locked UI-v1.9.2 page
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
BASE = ROOT / 'v192_base.html'
BASE_SHA = '2721ce754acea460759d86f3f57dca7feaad34785719979925eb4ad83397d053'

MARKERS = {
    'XB_IOS_V020_SHIM': 1,
    'XB_IOS_V020_REBASE': 2,
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
    ok('v192_base.html 仍是 UI-v1.9.2', sha(BASE) == BASE_SHA, sha(BASE)[:16])
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
    css_start = new.find('<style id="XB_IOS_V020_REBASE">')
    css_end = new.find('</style>', css_start)
    block = new[css_start:css_end]
    ungated = [l for l in block.splitlines()
               if '{' in l and 'xb-ios-p0' not in l
               and not l.strip().startswith(('@media', '</style', '<style'))]
    ok('V020 规则全部带 html.xb-ios-p0', not ungated, f'未门禁 {ungated[:2]}' if ungated else 'ok')
    decl = re.findall(r'font-size\s*:', block)
    ok('V020 不覆盖任何字号 token', not decl,
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
