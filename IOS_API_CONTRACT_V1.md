# xBloom Coffee Library — iOS API Contract v1

> 版本：v1 · 冻结日：2026-10-01 · 基线：**v2.3.7**（ux-polish-pinn-release-hardening）
> 后端 live SHA：main `9e2f180e…` / index `804d010d…` / baseline tar `76948a85…`
> 本契约面向 iOS v0.1（Capacitor 封装），**只读约束**：iOS 客户端只消费现有 API，后端零改动。

---

## 0. 派生架构（核心规则）

```
iPhone App (Capacitor)
  └── web/index.html = v2.3.7 派生副本（+35/-7 行 iOS shim，见 §5）
        │ window.fetch → CapacitorHttp（原生网络层，绕过 WKWebView CORS）
        ▼
   http://192.168.50.22:8088  (FastAPI v2.3.7, 可配置 API_BASE)
```

- **后端不新增 /api/v1 命名空间**（单用户单服务器，收益不足）。
- **契约保护手段**：本文件 + `API_CHANGELOG.md`；已被 iOS 使用的字段不得无迁移说明直接删除/改语义。
- 可选：health 响应后续加 `"api_contract": "1"`（v2.3.8 起）。

---

## 1. v0.1 接口面（53 路由中的子集）

### 豆仓 / 列表
| Method | Path | 用途 |
|---|---|---|
| GET | `/api/beans` | 豆仓列表（在喝/养豆/归档/全部/搜索） |
| GET | `/api/beans/{bean_id}` | 豆详情（含 current/latest_candidate/_summary） |
| GET | `/api/beans/duplicates?threshold=0.62` | 重复整理 |

### 萃取
| Method | Path | 用途 |
|---|---|---|
| GET | `/api/beans/{bean_id}/validate-current` | Current 校验（XBLOOM_READY 徽章） |
| GET | `/api/drippers` | 滤杯列表（7 个，含 origami_pinn preset） |
| POST | `/api/beans/{bean_id}/recipes/{version}/adapt-dripper` | 更换滤杯 → 生成适配 Candidate |
| GET | `/api/beans/{bean_id}/history` | 版本时间线 |

### 调整 / Tasting
| Method | Path | 用途 |
|---|---|---|
| GET | `/api/beans/{bean_id}/tasting/latest` | 最近冲煮反馈 |
| GET | `/api/beans/{bean_id}/tasting/history` | 冲煮历史（A/B 对比） |
| POST | `/api/tasting/detailed` | 保存反馈（8 组合症状 + 本次滤杯） |
| POST | `/api/beans/{bean_id}/tasting/recommend-latest` | 保存并生成调整方案 |
| GET | `/api/beans/{bean_id}/candidates` | 候选列表 |
| POST | `/api/beans/{bean_id}/recipes/{version}/promote-preview` | Promote 预览 |
| POST | `/api/beans/{bean_id}/recipes/{version}/promote` | Promote 到 Current |

### 新增豆（v2.3.7 两步流）
| Method | Path | 用途 |
|---|---|---|
| GET | `/api/intake/capabilities` | 新增页前置能力（**P0 已纳入**） |
| POST | `/api/beans/recognize-label` | 拍照/上传 → OCR 识别（multipart `image`） |
| POST | `/api/beans` | 保存豆 profile |
| POST | `/api/beans/{bean_id}/image` | 上传包装图（multipart `image`） |
| POST | `/api/beans/{bean_id}/generate-initial` | 规则生成首版配方 |
| POST | `/api/beans/{bean_id}/generate-initial-ai` | AI 生成首版配方 |

### 同步中心
| Method | Path | 用途 |
|---|---|---|
| GET | `/api/sync-center` | 快照（云状态 + A/B/C 槽位 + 结果） |
| POST | `/api/sync-center/apply` | 应用同步 |

### 设置
| Method | Path | 用途 |
|---|---|---|
| GET | `/api/settings` | 全局设置 |
| GET | `/api/settings/resting` | 养豆规则 |
| GET | `/api/settings/drippers` | 滤杯注册表 |
| GET | `/api/cloud/status` | 云连接状态 |

> 明确**不进 v0.1 UI**：`/api/backup`（运维）、`/api/system/validator`（P1 后置）、`/api/ai/recommendation-observability`（P1 后置）、`/raw/recipes/{bean}/{v}.yaml`（P1，分享/导出用）、cloud 写接口（settings 写留 Web）。

---

## 2. 关键响应形状（iOS 直接消费）

### Bean 卡片（/api/beans 列表项）
```
{ bean_id, sample_no, name, roaster, roast_level, flavor_notes[],
  image_url(相对 /media/…, 客户端需 absURL), status, _summary{...} }
```

### 豆详情（/api/beans/{id}）
```
{ bean_id, name, ..., current_version, current_recipe{dose_g,grind,ratio,temp_c,pours[]},
  latest_candidate{version,...} | null, _summary{...}, history[] }
```

### 适配响应（POST adapt-dripper）
```
{ ok, created, version, source_version, source_dripper, target_dripper,
  changes[{field,label,before,after,unit}], readiness{state,ready,internal,external} }
```

### 通用
- 成功：HTTP 2xx，多数含 `"ok": true`。
- 失败：FastAPI `{"detail": "…"}`（中文）。iOS 端 `api()` 已解析 `detail` 为可读 message。
- **v2.3.8 计划**：统一错误信封 `{ok:false, code, message, details}`（届时 Web 与 iOS 同步升级）。

---

## 3. 幂等（v2.3.8 后端增强，非 v0.1 阻塞）

手机网络重试是真实风险（用户曾出现重复"晴川"）。**首版只做 `POST /api/beans`**：
- 请求头 `Idempotency-Key: <UUID>`；服务端缓存 key→(bean_id, response) 24h；同 key 重试返回首次结果。
- Candidate / Tasting / Promote 幂等随后做（v0.2）。

---

## 4. 认证 / 网络演进

- v0.1：LAN 直连 `http://192.168.50.22:8088`，**无认证**（个人局域网）。
- 外网（Tailscale / HTTPS + Bearer Token）：v0.2+。Token 存 iOS Keychain（原生插件）。
- `API_BASE` 已支持 localStorage 配置（App 内「🛜 服务器」按钮），换网络不需要重打包。

---

## 5. iOS shim（v2.3.7 派生包改动清单，+35/-7 行）

| 位置 | 改动 |
|---|---|
| `<script>` 首部 | `API_BASE`（localStorage `xbloom_api_base`，默认 `http://192.168.50.22:8088`）+ `absURL()` |
| `api()` | `fetch(absURL(url), opt)` —— 53 个 API 调用唯一出口 |
| 豆卡/详情图片 | `image_url` → `absURL(image_url)`（2 处） |
| 配方下载/打包 | `location.href` → `absURL(...)`（2 处） |
| 配方二维码 | `base_url` 改用 `API_BASE`；`qrImg.src` → `absURL(...)` |
| 底部新增 | 「🛜 服务器」编辑器（iOS 无 `prompt()`，用内联输入框） |

验证：`node --check` PASS；裸 `/api` 引用 0；与 v2.3.7 基线 diff = +35/-7 行。
派生副本路径：`ios/web/index.html`（勿回写基线）。

---

## 6. 验收标准（iOS v0.1）

- [ ] 连接 `192.168.50.22:8088`，health 正常
- [ ] 豆仓列表与 Web 数据一致（4 款豆）
- [ ] 萃取参数与 Web 一致（Current/滤杯/注水段/Ready 徽章）
- [ ] 无 Current / 有 Candidate 情形正常
- [ ] 拍照上传包装 → OCR 识别 → 表单确认 → 保存
- [ ] Tasting 保存 + 调整方案生成 + Promote
- [ ] 断网有明确错误提示（api() throw message）
- [ ] 390×844 无横向溢出（继承 Web 移动验收）
- [ ] 服务器地址可配置（🛜 按钮），切换后重载生效
