# xBloom App v0.3.0 — 基线前移到生产 UI 2.6.0

已发布：v0.2.1（基线 = 生产 UI v1.9.2，`2721ce75…`）
本版：**v0.3.0**（基线 = 生产 UI **2.6.0**，`c4356839…`）

## 为什么现在出包

生产已经跑到 App 2.6.0，萃取页和调整页都换了结构，而 App 里的页面还停在 v1.9.2 的样子。v0.3.0 只做一件事：把 App 的页面基线前移到 2.6.0，让手机和浏览器看到同一个界面。

## 前移后 App 立刻有了

| 页面 | 新能力 |
|---|---|
| 萃取 | 「当前配方 / AI 建议」双页签；状态行绿点（已校验 / 已同步）；AI 四参数一行四列；注水白卡 + 前段/中段/尾段 + 占 X%；折叠白卡带右侧摘要 |
| 调整 | 首屏只留「记录冲煮反馈」；版本管理默认展开；当前版一行摘要（版本 · 来源 · 参数 · 注水）；候选只写差异；归档候选池（早于当前版本）；回退弹窗明确写出「会从 v1.7 退回 v1.1」 |

## 相对 v0.2.1 改了什么

| 文件 | 改动 |
|---|---|
| `v260_base.html` | 新增，= 生产 `app/static/index.html`（`c4356839…`），只读快照 |
| `tools/upgrade_ios_v030.py` | 新增，v0.2.1 脚本的 2.6.0 版（BASE_SHA 前移，其余流程不变） |
| `tools/verify_ios_v030.py` | 新增，**53 PASS / 0 FAIL**（v0.2.1 是 45 项，新增 8 项 2.6.0 能力检查） |
| `tools/apply_ios_p1d.py` | **兼容修复**：2.6.0 把 `#readyBadge` 换成 `#extractStatusRow`、版本管理不再是 `<details id="versionManagementDetails">`，P1D 的锚点断言因此失败。改成「两种 id 二选一，两个都没有就 fail」，CSS 同时覆盖新 id。fail-closed 语义未变 |
| `web/index.html` | 重新生成，`4259c86c…` → **`1e5770b1…`**（317,645 B） |
| `project.pbxproj` / `package.json` | `MARKETING_VERSION 2.2.0` / `CURRENT_PROJECT_VERSION 22` / `package.json 0.3.0` |

## 保持不变（逐条复核）

- 7 个 iOS 补丁（P0/P1/P0B/P1C/P1D/P2A/P2B）全部按序应用，marker 计数与 v0.2.1 一致
- **无内网地址**：`xbReadServer()` 未配置返回空串，首次启动弹面板要求填写（F-03）
- 全部 API 走 `api() → absURL()`，`fetch(` 只有 1 处，`location.origin` 0 处，`prompt(` 0 处
- 仍只有 7 个字号 token，文本规则 0 处字面 px，字形图标 2 处（20px / 19px），无 clamp/em/vw/rem，无 800/900
- iOS CSS 全部 `html.xb-ios-p0` 门禁，普通浏览器不会激活

## 三视口实测（Capacitor mock + 只读代理，390 / 375 / 430）

| 视口 | 萃取 | 调整 |
|---|---|---|
| 375 | 溢出 0，参数列 `99px×3` | 溢出 0，首屏卡1 261px |
| 390 | 溢出 0，参数列 `104px×3`，双页签、状态行、三折叠齐全 | 溢出 0，首屏卡1 261px，`原生 4 · 候选 4`，归档 `4 个` |
| 430 | 溢出 0，参数列 `117px×3` | 溢出 0，首屏卡1 241px |

服务器按钮仍在 `right 12 / bottom 110`，不压底部导航。

## 已知（不是本版引入）

- 打开**没有 AI 缓存**的豆子时，萃取页会自动 `POST /api/beans/{id}/ai-first-auto` 生成首版 AI 配方。这是 v2.3.x 起的设计。
- 真机测试仍未做（`DEVICE_TEST_PENDING`）。

## 复现

```bash
python3 tools/upgrade_ios_v030.py   # 以 v260_base.html 为基线重新生成 web/index.html
python3 tools/verify_ios_v030.py    # 53 项结构校验
```
