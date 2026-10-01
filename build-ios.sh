#!/usr/bin/env bash
# xBloom 咖啡豆仓 iOS 命令行构建（在 Mac 上运行）
set -euo pipefail
cd "$(dirname "$0")"
SCHEME="xBloomCoffeeLibrary"
CONFIG="Release"

echo "== 1/3 cap sync =="
npx cap sync ios

echo "== 2/3 xcodebuild =="
xcodebuild \
  -workspace ios/App/App.xcworkspace \
  -scheme "$SCHEME" \
  -configuration "$CONFIG" \
  -destination 'generic/platform=iOS' \
  -derivedDataPath build/DerivedData \
  build

echo "== 3/3 done =="
echo "App 已构建。用 Xcode Run 到 iPhone（免费侧载）或接云端 CI 出 IPA。"
