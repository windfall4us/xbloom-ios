# xBloom 咖啡豆仓 iOS v0.1.9 —— 生产 UI-v1.9 rebase

**基线**：生产 `app/static/index.html` = `e134640984d17bf1639a882c2fbff138cd76dfacf3c031de51595389e1fd4d7d`（UI-v1.9，3172 行 / 257,509 B）
**派生包**：`web/index.html` = `e0ef9e171979f3cf727f8c3ec735733583b847b4a75bc4cfe1a675b4f4ef2edd`（3761 行 / 292,762 B）
**上一版**：v0.1.8.3，基于 v2.3.10 基线（`87ce29b5`），派生 SHA `21775037…`

---

## 1. 这次跨了多远

v0.1.8.3 停在服务端 v2.3.10；这一版直接接到当前生产 UI-v1.9，中间跨过 v1.4–v1.9 六个前端批次：

| 批次 | 前端变化 |
|---|---|
| v1.4 | 参数面板改成 3 列 `.param-grid`；注水柱视觉规格 |
| v1.5 | AI 卡片新增 P1 结构解读（三段水量占比 + 三条单变量路线） |
| v1.6 | 注水柱第三行改 `停 N 秒`；`manual_adjustment` 来源标注 |
| v1.7 | 注水柱列宽改由容器驱动（修 600–885 px 视口偏移） |
| v1.8 | 萃取页去重（标题统一为 `AI`）；硬件 chip 可跳申报 |
| v1.9 | 调整页 6→5 卡合并；「保存并生成候选配方」；修 `tasteBrewTime` 选择器 |

上一版是 v2.3.10 的页面，**根本看不到这些**。

## 2. 垫片重放（7 个补丁 + 1 个新 shim）

`tools/upgrade_ios_v019.py` 是 fail-closed 的：基线 SHA、上一版 SHA、Info.plist 五项权限、7 个补丁门禁任一不符就整体回滚。

| 补丁 | 作用 | 本次结果 |
|---|---|---|
| P0 | `viewport-fit=cover` + 安全区 + 禁页面横向滚动 | APPLIED |
| P1 | 设置 5 tab、状态行长值折行、豆仓紧凑卡 | APPLIED |
| P0B | 顶部滚动遮罩 + 设置页服务器入口代理 | APPLIED |
| P1C | 顶部标题紧凑、底部导航图标+文字 | APPLIED |
| P1D | 萃取/调整面板 3 列网格与动作优先 | APPLIED |
| P2A | 写请求防重 + Toast + 网络失败不当成功 | APPLIED |
| P2B | 图片全屏查看器 + 键盘避让 + Haptics | APPLIED |
| **V019 shim** | API base 适配器 + **iOS 安全服务器编辑器** | NEW |

## 3. 与上一版相比的实质改动

### 3.1 URL 重定向目标变了（v1.9 重构）

v1.9 把配方工具改成 `recipeToolTarget()` 间接层（`target.beanId` / `target.version`），旧垫片匹配的字符串已经不存在。本版按新形式重接：

| 功能 | v1.9 原样 | iOS 派生 |
|---|---|---|
| 下载配方 | `location.href=\`/api/.../download\`` | `absURL(...)` |
| 二维码 | `image.src=\`/api/.../qr?base_url=${location.origin}\`` | `absURL(...)`，`base_url` 用配置的服务器 |
| 原始 YAML | `location.origin+\`/raw/recipes/...\`` | `xbReadServer()+\`...\`` |

`location.origin` 残留 **0 处**：在 Capacitor 里 origin 是 `capacitor://localhost`，用它拼出来的二维码和链接都是废的。

### 3.2 服务器编辑器：prompt() → 内联面板

WKWebView **不实现 `prompt()`**，所以 v0.1.8.3 起「🛜 服务器」按钮在真机上是死的（点了没反应）。本版改成内联面板：底部弹出输入框（16px 字号防 iOS 聚焦缩放）+ 保存/取消，保存后写 `localStorage` 并 reload。仍保留 fixed 定位的触发按钮，所以 P0B 的设置页代理继续有效。

### 3.3 去掉旧的 `preserve_async()` 移植

v0.1.8.2 曾把「保存豆子后先跳详情、再等 AI」的代码硬塞进老页面，因为它当时同步阻塞 60 秒。**v1.9 的服务端流程本身已经是异步的**（`createIntakeRequestId` → `pollIntake` 每 1.5 s → `finishIntakeNavigation` → `openBean` + 切到萃取页）。

所以这次**不移植**旧代码——强行塞回去会让页面去调已经不匹配的提交路径。`upgrade_ios_v019.py` 里 `assert_capabilities()` 反转成了正向锁：这五个能力必须存在，且旧标记 `首版配方生成中…` 必须为 0。

### 3.4 新 V019 样式块

```css
html.xb-ios-p0 body.ios-app #aiAdvancedRecord > summary{min-height:44px;...}   /* iOS 触达下限 */
html.xb-ios-p0 body.ios-app .param-grid{max-width:100%}
html.xb-ios-p0 body.ios-app .param-cell{padding:12px 6px}
html.xb-ios-p0 body.ios-app .param-cell .param-v{font-size:20px}
@media(max-width:520px){ .ai-band-grid{grid-template-columns:1fr} .ai-route{padding:8px} }
```

全部挂在 `html.xb-ios-p0 body.ios-app` 上——普通浏览器里这条链永远不成立，Web 端零影响。

## 4. 验证（全部实跑）

```
python3 tools/verify_ios_v019.py     → 31 PASS / 0 FAIL
node tools/test_p2a.cjs              → 4/4 PASS
```

| 组 | 检查 |
|---|---|
| 基线 | `v19_base.html` 仍是 `e1346409…` |
| 标记 | 9 个标记计数全对（V019 shim ×1、V019 rebase ×2、P0/P1/P0B/…） |
| DOM | 基线 368 个 id **零丢失**（新增 11 个都是 iOS 自己的） |
| API 出口 | `fetch(` 仅 1 处；无 `fetch("/api`；`api()` 首行 `url=absURL(url)` |
| 服务器编辑器 | 真实调用 `prompt(` = 0；内联面板 + 输入框 16px + 保存按钮 |
| CSS 门禁 | V019 的 8 条规则全部带 `html.xb-ios-p0` |
| 语法 | 7 个 `<script>` 块全部 `node --check` 通过 |

浏览器冒烟（iPhone UA + Capacitor 模拟 + 只读代理到生产）：

| 场景 | 结果 |
|---|---|
| 纯浏览器（无 Capacitor） | `html`/`body` 无 iOS 类、无服务器按钮 → iOS 样式完全惰性 |
| iPhone 模拟 | `html.xb-ios-p0`、`body.ios-app`、body padding-top 54px、无横向溢出 |
| 8 颗豆加载 | 8 张卡，图片 src 全部 `http://<base>/media/...`（absURL 生效） |
| 详情 · 参数 | 6 项：粉量 16g / 研磨 57.5 / 转速 100rpm / 水温 93℃ / 1:15.5 / 248mL |
| 详情 · 注水柱 | 3 柱，列宽 111/112/112（等分），柱高 56/121/132 |
| 调整页 | **5 张卡**，高级区默认折叠，summary 高 46px（≥44 触达下限） |
| 下载配方 | `absURL('/api/beans/shii-2026/recipes/1.7/download')` |
| 二维码 | `absURL('/api/.../qr?base_url=http%3A%2F%2F127.0.0.1%3A8099')` ← 用配置服务器，不是 origin |
| 原始链接 | `http://127.0.0.1:8099/raw/recipes/shii-2026/1.7.yaml` |
| 服务器编辑器 | 点击 → 面板（input type=url, 16px）→ 保存 → localStorage 写入 → reload 后 `absURL` 用新地址 |
| 设置页入口 | `📶 服务器连接设置` 存在，原浮动按钮被隐藏（P0B 代理生效） |
| 图片查看器 | 点 heroimg → `#xbP2BViewer` flex / z-index 10050 → 关闭后移除 |
| 三视口 375/390/430 | 横向溢出 0 |

测试代理是 **GET-only**（非 GET 返回 405），全程没有向生产写入任何数据。

## 5. 版本与构建

| 项 | 值 |
|---|---|
| App 版本 | `MARKETING_VERSION 1.9.0` / `CURRENT_PROJECT_VERSION 19` |
| package.json | `0.1.9` |
| 同步 | `npx cap sync ios` → `ios/App/App/public/index.html` SHA 与 `web/index.html` 一致 |
| 清理 | 把 9 个 `web/*.bak` 移到 `web-backups/`，不再打进 app bundle |

## 6. 仍待真机验收

以下只能在实机确认，本次未做：

1. 新豆保存后 60 秒 AI 等待期间仍可浏览详情（v1.9 服务端异步 + 轮询）
2. Dynamic Island 区域滚动不露内容（P0 遮罩）
3. 底部导航在 home indicator 上不遮挡（`calc(7px + env(safe-area-inset-bottom))`）
4. 服务器地址编辑器在真机可输入、保存后重启仍生效
5. 图片双指缩放与拖动
6. 慢网连点不产生两次同路径 POST
7. 相机权限弹窗（Info.plist 四个描述键 + ATS）
