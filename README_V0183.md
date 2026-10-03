# xBloom iOS v0.1.8.3 — Detail Workflow Fix（基于 Web v2.3.10 导航精简版）

## 锁定输入
- Web v2.3.10 verified tar SHA256: `93d083550994e49f4d40a4079be64a24f929050c67e510666be9c9119e97f6a4`
- 生产 HTML 基线 SHA256: `87ce29b558b6e93073f9ffda944fc120597e2cb036bb59e134457125e3613858`
- 当前 iOS v0.1.8.2 网页 SHA256: `7b42bbb807f9794503bdb9136e4752d4920a94d2dde89f247ff84cd998ed9c0e`
- 派生新 HTML SHA256: `2177503790346d81b1952ea41dd8b9d7490e6037c04e44799cbbb55994ce4d6d`

## 套用方式 A（推荐：在现有 iOS 仓库原地迁移）
解压迁移工具包到当前 `xbloom-ios` 仓库**根目录**，仅覆盖 `tools/` 的相应脚本并新增 `v2310_base.html`、本 README；**不要覆盖 `web/index.html` 和原生 `ios/` 目录**。

```bash
cp web/index.html /tmp/xbloom-ios-0182-safe-backup.html
python3 tools/upgrade_ios_v0183.py
python3 tools/verify_ios_v0183.py
python3 tools/upgrade_ios_v0183.py   # 预期 NOOP
node tools/test_p2a.cjs
npm install
npx cap sync ios
# 然后推送到 feature/ios-v0183-v2310 分支，触发 build-ipa.yml
```

前置不匹配则拒绝执行。迁移失败自动用 `web/index.html.pre-v0183.bak` 恢复；成功也保留备份。勿把 `.bak` 提交至 Git。

## 套用方式 B（完整可打开源码）
另提供 `xbloom-ios-v0.1.8.3-complete-source.zip`，已生成新网页和原生配置。解压后：`npm install && npx cap sync ios && npx cap open ios`。
它不包含签名凭据或 `node_modules`，不带生产数据。不要将未验证的工程覆盖当前 iOS Git 主分支。

## 新版范围
- 继承 Web v2.3.10 `XB_V2310_DETAIL_WORKFLOW_FIX` 与 `XB_V2310_NAV_COMPACT_R1`。
- 五个豆仓入口单行，整理按钮保留人工确认；新增/设置/详情顶部返回隐藏（原 ID 和绑定保留）。
- 有 Candidate 无 Current：仍可按独立滤杯基准生成新候选，且候选版本可独立重新校验。
- 调整页仅有一个反馈入口；已有配方时首版生成按钮按规则隐藏。
- iOS API Base、P0～P2B 全量恢复；保留相机/相册权限；保留 v0.1.8.2 **先进入详情后等待 AI** 和简化完成文案。
- 服务器快捷按钮背景使用 `var(--bg)` 以避免色差。

## 本地测试与真实边界
本地迁移、二次 NOOP、JavaScript 语法、287 个唯一 DOM ID、原生权限四项、P2A 4/4 运行模拟均通过。
**尚未在最新 GitHub 分支执行 CI，尚未使用 iPhone 验收。** 不能将静态 PASS 当作真机 PASS。

## 建议真机核查
新豆：保存后立即跳转，等待约 1 分钟仍能浏览详情；配方出来后弹窗只有简洁文案。
详情：三标签及底栏显示，顶部无多余返回；无 Current 可以生成 V60 候选，Current 不变。
萃取：校验行唯一，按钮可验证 Candidate/Current；调整仅一处反馈入口。
豆仓：五列一行整理，禁自动删除；相机权限弹窗；照片预览、断网提示、Cloud Sync 继续正常。

## 重要约束
未修改 Web 后端、Docker、Native、Candidate、Current、settings.yaml；未替用户部署和签名。
