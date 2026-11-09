#!/usr/bin/env python3
"""Structural verification for the v0.1.9 iOS web bundle (no server access).

Checks:
  1. baseline file is still the locked UI-v1.9 page
  2. every iOS marker is present, with the exact expected count
  3. the derived bundle loses no DOM id from the baseline
  4. all API traffic goes through api()->absURL()  (no absolute /api in fetch)
  5. no leftover location.origin / prompt()-based server editing
  6. every inline <script> block parses under `node --check`
  7. iOS-only CSS cannot activate in a plain browser
"""
from pathlib import Path
import hashlib, re, subprocess, sys, tempfile

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web/index.html'
BASE = ROOT / 'v19_base.html'
BASE_SHA = 'e134640984d17bf1639a882c2fbff138cd76dfacf3c031de51595389e1fd4d7d'

MARKERS = {
    'XB_IOS_V019_SHIM': 1,
    'XB_IOS_V019_REBASE': 2,
    'XB_IOS_P0_BEGIN': 1,
    'XB_IOS_P1_V012': 2,
    'XB_IOS_P0B_V013': 2,
    'XB_IOS_P1C_V014': 1,
    'XB_IOS_P1D_V015': 1,
    'XB_IOS_P2A_V016': 2,
    'XB_IOS_P2B_V017': 1,
}

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
    """Yield inline <script> bodies, ignoring tags that carry src=."""
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


def main():
    print('== 基线 ==')
    ok('v19_base.html 仍是 UI-v1.9', sha(BASE) == BASE_SHA, sha(BASE)[:16])
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
    # Count real calls only: strip /* */ blocks and // line comments first, otherwise the
    # explanatory comments ("no prompt()") would be counted as a call.
    code = re.sub(r'/\*.*?\*/', '', new, flags=re.S)
    code = re.sub(r'//[^\n]*', '', code)
    calls = len(re.findall(r'(?<![\w.$])prompt\s*\(', code))
    ok('无 prompt( 调用', calls == 0, f'实际 {calls}')
    ok('内联面板存在', new.count("id='xbIosServerPanel'") == 1)
    ok('输入框 16px（防 iOS 聚焦缩放）', "font-size:16px;padding:10px" in new)
    ok('保存按钮存在', new.count("'xbIosServerSave'") == 1)

    print('== iOS CSS 门禁 ==')
    css_start = new.find('<style id="XB_IOS_V019_REBASE">')
    css_end = new.find('</style>', css_start)
    block = new[css_start:css_end]
    rules = [l.strip() for l in block.splitlines() if l.strip().startswith('html.xb-ios-p0') or l.strip().startswith('@media')]
    ungated = [l for l in block.splitlines()
               if '{' in l and 'xb-ios-p0' not in l and not l.strip().startswith(('@media', '</style', '<style'))]
    ok('V019 规则全部带 html.xb-ios-p0', not ungated, f'未门禁 {ungated[:2]}' if ungated else f'{len(rules)} 条')
    ok('基线不含 iOS 标记', 'XB_IOS_P0_BEGIN' not in base)

    print('== 脚本语法 ==')
    blocks = script_blocks(new)
    with tempfile.TemporaryDirectory() as td:
        for i, (line, body) in enumerate(blocks):
            p = Path(td) / f'b{i}.js'
            p.write_text(body, 'utf8')
            r = subprocess.run(['node', '--check', str(p)], capture_output=True, text=True)
            ok(f'<script> #{i + 1} (行 {line}) 语法', r.returncode == 0, (r.stderr or '').strip().splitlines()[0][:90] if r.returncode else '')

    print()
    print(f'结果: {len(passes)} PASS / {len(fails)} FAIL')
    if fails:
        print('失败项: ' + ', '.join(fails))
        sys.exit(1)


if __name__ == '__main__':
    main()
