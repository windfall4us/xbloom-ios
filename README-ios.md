# xBloom 咖啡豆仓 iOS — 构建指南（Mac）

项目已在本机（Linux 开发机）完整生成：**Capacitor 7.6.9 + 派生 web bundle + ios/ 原生工程**。
你只需要在 Mac 上：打开 → 选签名 → Run。

## 目录结构

```
ios/
├── web/index.html          # v2.3.7 派生副本（+35/-7 行 iOS shim，勿改基线）
├── ios/App/App.xcworkspace # 已生成的 Xcode 工程（可打开）
├── ios/App/App/public/     # cap sync 打包进去的 web bundle
├── capacitor.config.ts     # appId / CapacitorHttp / scheme
├── IOS_API_CONTRACT_V1.md  # 冻结的 API 契约
├── build-ios.sh            # 命令行构建脚本
└── package.json
```

## 第一步：Mac 上打开工程（免费侧载）

```bash
# 0) 前提：Xcode（含 Command Line Tools）
xcode-select --install

# 1) 首次装 CocoaPods（Capacitor iOS 依赖管理）
sudo gem install cocoapods

# 2) 把项目拷到 Mac（git 或 U 盘均可），然后：
cd ios
npm install          # 恢复 node_modules（全局 ~/.npmrc 若 omit=dev 也没关系，依赖全在 dependencies）
npx cap sync ios     # 同步 web bundle + pod install（自动执行）

# 3) 打开 Xcode
npx cap open ios     # 或 open ios/App/App.xcworkspace
```

## Xcode 内操作（一次性）

1. `App.xcworkspace` → 左侧选择 **App** target
2. **Signing & Capabilities** → Team 选你的 **Personal Team**（免费）
   - Bundle ID 自动为 `com.windfall.xbloomlibrary`
3. 顶部选择你的 **iPhone**（先 USB 连接，或无线调试）
4. **Run**（⌘R）

> ⚠️ 免费账号签名 **7 天过期**：过期后在 Xcode 里重新 Run 一次即可续期。
> ⚠️ 首次打开 App 会弹「本地网络」权限 → 允许（否则连不上 192.168.50.22）。
> ⚠️ iPhone 与盒子需同一局域网。

## 命令行构建（可选，替代 Xcode Run）

```bash
./build-ios.sh        # = xcodebuild -workspace ... -scheme xBloomCoffeeLibrary build
```

## 日常更新流程（后续 Web 版本升级后）

```bash
# 1. 把新版 v2.3.x index.html 重新派生（垫片步骤见 IOS_API_CONTRACT_V1.md §5）
cp <新基线>/app/static/index.html web/index.html
# 2. 重打 7 处 shim 补丁
# 3. 验证：node --check + 裸引用扫描（validate_bundle.py）
npx cap sync ios
# 4. Xcode Run
```

## 云端 IPA（付费账号才值得）

- 免费 Personal Team：云端签名 7 天失效 + 设备绑定 → 无意义。
- **$99 Apple Developer Program**：导出 Distribution 证书(p12) + profile → Codemagic / GitHub Actions macOS runner 自动构建 + TestFlight（90 天）。
- 触发条件：不想每 7 天重签 / 要多台设备 / 上架。

## 已知 v0.1 限制（v0.2 计划）

- 下载配方/打包：`location.href` 在 WKWebView 行为受限 → v0.2 换 Capacitor Share Sheet / Files。
- 相机：`<input type="file" capture>` 可用但体验一般 → v0.2 换 @capacitor/camera。
- alert：WKWebView 原生 alert 可用；prompt 不可用（已用内联输入替代）。
