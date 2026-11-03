# 益禄加油 · 微信小程序（远程卡片方案）

## 为什么这样设计
桌面端把 127MB 卡片直接打进安装包；但微信小程序主包 + 分包合计上限约 20MB，
无法内嵌全部卡片。因此小程序端改为「运行时远程加载」：安装包仅含界面与逻辑，
卡片 JSON（manifest.json + cards/）托管在你的静态服务器 / CDN 上，按需按本书读取。

## 你必须提供两样东西（只有你能给）
1. **卡片托管地址**：把项目根目录 `public/static/content/` 整个文件夹上传到任意静态托管
   （对象存储 OSS / COS、GitHub Pages、Vercel、你自己的服务器等），拿到一个 https 基础地址，
   例如 `https://your-cdn.com/cards/`。
2. **小程序 appid**：在微信公众平台注册 / 获取，填到 `manifest.json` 的 `mp-weixin.appid`；
   并在「开发管理 → 开发设置 → 服务器域名」把你的卡片域名加入 request 合法域名。

## 三步让小程序跑起来
1. 改 `services/cards.js` 顶部的 `CARD_BASE` 为你的托管地址（留空 = 本地，仅桌面端用）。
2. 用 HBuilderX「发行 → 小程序-微信」，或本机 uni 工具链构建：
   `npx uni build -p mp-weixin`（产物在 `unpackage/dist/build/mp-weixin`）。
3. 微信开发者工具导入该目录，填 appid，预览 / 上传发布。

## 说明
- 小程序端本项目当前未在此环境产出（无 HBuilderX / 无可用 uni 构建链，
  所用 alpha 依赖版本互相矛盾）。上述为在你本机一键完成的步骤；
  界面与卡片逻辑已就绪，桌面端与小程序端复用同一套代码（cards.js 的 CARD_BASE 切换数据源）。
- 桌面端不受影响：`CARD_BASE` 留空时走本地 `/static/content/`，与原来一致。
