import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.windfall.xbloomlibrary',
  appName: 'xBloom 咖啡豆仓',
  webDir: 'web',
  // CapacitorHttp: 让 window.fetch 走原生网络层，绕过 WKWebView CORS 限制
  // （后端 FastAPI 无 CORS 中间件，必须开此选项，后端零改动）
  plugins: {
    CapacitorHttp: {
      enabled: true
    }
  },
  ios: {
    scheme: 'xBloomCoffeeLibrary',
    // iOS ATS 见 ios/App/App/Info.plist（NSAllowsArbitraryLoads + NSLocalNetworkUsageDescription）
    contentInset: 'never'
  }
};

export default config;
