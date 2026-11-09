# v0.2.0 — 生产 UI-v1.9.2（7 级排版）rebase

iOS 壳：Capacitor，`web/index.html` = 生产页面 + 7 个 iOS 补丁。

## 基线

| | |
|---|---|
| 生产页面 | `app/static/index.html` = `2721ce75…`（UI-v1.9.2，7 级字号） |
| 基线副本 | `v192_base.html`（同 SHA，逐字节一致） |
| 产出 bundle | `web/index.html` = `1d561846…` |

## 这一版为什么不能直接复用 v0.1.9 的补丁

v1.9.2 把网页里 114 处写死字号收敛成 7 个 token（32/24/22/18/16/14/12）。
而 iOS 的 7 个补丁（P0…P2B）是围绕旧页面手调的，里面还留着 31 条写死字号：

- `.top h1` 用 `clamp(23px,6vw,30px)` —— 网页是 32
- `#warehouse .intro` / `.muted` 11px —— 网页是 14
- `#detailExtractionPane h3` 15px —— 网页是 18
- `.extract-metric-card b` 15px —— 网页是 22

直接套上去，App 会变成「第二套字号体系」，正是 1.9.2 要消掉的东西。

## 这一版做了什么

1. `tools/upgrade_ios_v020.py`：以 `v192_base.html` 为基线做 fail-closed rebase（基线 SHA 锁、
   `web/index.html` 必须是 v0.1.9 的 `e0ef9e17`、Info.plist 权限/ATS 不得回退、失败自动回滚）。
2. 新增 `ALIGN` 表：把 31 条 iOS 专属字号规则逐条对齐到网页的同一角色——
   5 条直接删掉（继承基线：页面标题 32、区块标题 18、卡片标题 18、正文 14 ×2），
   24 条钉到对应 token（卡片标题 16、参数数值 22、次要说明 14、徽章/单位 12、按钮 16）。
   出现表里没有的 iOS 字号规则时脚本直接失败，不允许悄悄新开一套尺度。
3. 补丁里剩余的 `clamp()` 全部换成 token；`font-weight:650/800` 统一到 700。
4. 只有 2 处保留像素字号：底部导航 `::before` 的图标字形（20px / 19px）——那是图形不是文字。
5. V020 的 iOS 专属 CSS 不含任何 `font-size`，字号一律由网页 token 决定。

## 验证

```
python3 tools/verify_ios_v020.py     → 41 PASS / 0 FAIL
node tools/test_p2a.cjs              → 4/4 PASS
```

41 项覆盖：基线 SHA、9 个标记计数、368 个 DOM id 无丢失、`fetch(` 仅 1 处、无 `location.origin`、
无 `prompt()`、iOS CSS 全部带 `html.xb-ios-p0`、V020 不含 font-size、7 个 token 取值、文本规则 0 处字面 px、
≤3 处图标字形、无 clamp/em/vw 字号、无 800/900 字重、`h3` 显式声明、7 段 `<script>` 语法。

真数据 E2E（`tools/ios_e2e_harness.py`：静态 + GET-only 反代到生产，注入 Capacitor mock）：

| 页面 | 网页 | iOS 包 |
|---|---|---|
| 豆仓 375/390/430 | 12/14/16/18/32 | 12/14/16/18/32（8 张卡全在） |
| 萃取 | 12/14/16/18/22/32 | 完全相同；`h3` 全为 18；下拉框 44 高、白底、12 圆角、16px |
| 调整 | 12/14/16/18/24/32 | 完全相同；5 个区块（合并后的记录入口在） |
| 设置 | 12/14/16/18/32 | 相同 |

三视口横向溢出 0、文字裁切 0。

## 版本

`MARKETING_VERSION 2.0.0` / `CURRENT_PROJECT_VERSION 20` / `package.json 0.2.0`。

## 回滚

`git checkout v0.1.9 -- web/index.html` 并 `npx cap sync ios`；或 `cp web-backups/index.html.pre-v020.bak web/index.html`。
