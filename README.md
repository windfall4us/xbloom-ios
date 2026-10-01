# xBloom 咖啡豆仓 — iOS 客户端（Capacitor）

v2.3.7 后端 web 前端的 **派生副本**（iOS 专属垫片：`API_BASE` 可配置 + `absURL()`），后端零改动。
接口契约见 `IOS_API_CONTRACT_V1.md`。

## CI 打包（未签名，免费 macOS Runner）

每次 **手动触发**（Actions → Run workflow）或推送 `v*` tag 时自动构建，产出两个 artifact：

| Artifact | 内容 | 用途 |
|---|---|---|
| `xbloom-ios-unsigned.ipa` | `Payload/App.app` 未签名 | Apple Configurator / 本地重签名 |
| `xbloom-ios-unsigned.app.zip` | 未签名 .app | Mac 本地 `codesign` 后安装 |

CI **不签名**（CODE_SIGNING_ALLOWED=NO）——签名始终在你 Mac 本地做（免费 Personal Team profile 7 天过期，本地 Xcode 自动再生）。

## 本地签名安装测试（Mac）

### A. 命令行（下载 CI artifact 后）
```bash
# 解压 .app.zip
codesign -f -s "Apple Development: 你的名字 (TEAMID)" --entitlements App.entitlements App.app
xcrun devicectl device install app --device <UDID> App.app
# 或 Apple Configurator 2：把 .app 拖进设备图标
```

### B. 最省事（Xcode 全自动）
```bash
git clone https://github.com/windfall4us/xbloom-ios.git
cd xbloom-ios && npm install && npx cap sync ios && npx cap open ios
```
Xcode → App target → Signing 选 Personal Team → 选 iPhone → ⌘R（7 天过期后重 Run 刷新）。

> 首次启动 App 弹「本地网络」权限 → 允许。服务器地址：App 内 🛜 按钮改（默认 `http://192.168.50.22:8088`）。

## 成本
公开仓库 → GitHub macOS Runner **免费无限次**。升级签名后（$99 开发者账号）：workflow 加
`-allowProvisioningUpdates` + 签名 Secrets 即自动出正式 IPA / TestFlight。
