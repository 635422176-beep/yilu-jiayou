# 益禄加油

卡片诵记 App（类「经方诵友」）：多级目录 → 知识点/歌诀卡片 → 翻转背诵 + 诵读(TTS) + SM-2 间隔复习。
一套 uni-app 源码同时产出**微信小程序**与**桌面软件（Electron）**。

## 内容范围
- 吴雄志书目（36 本）
- 中医教材（34 本）
- 西医教材（70 本）
- 共约 8 万张知识点/歌诀卡片

## 目录结构
- `pages/`：书架 / 学习 / 复习 / 我的 四页
- `services/cards.js`：卡片数据层（按书懒加载，支持本地与远程 `CARD_BASE`）
- `utils/review.js`：SM-2 间隔重复算法
- `static/content/`：卡片数据（manifest.json + 每书一个 cards.json，约 127MB）
- `electron/`：桌面端外壳（Electron + 内嵌 H5）

## 构建
- 微信小程序：`HBuilderX → 发行 → 小程序-微信`（卡片走远程加载，见 `services/cards.js` 的 `CARD_BASE`）
- 桌面端：`electron/` 内嵌 H5 构建产物

## 小程序卡片远程托管
微信包体限制无法打包 127MB 卡片，小程序端运行时从 `CARD_BASE`（https）拉取。
将 `static/content/` 整目录托管到任意静态服务（GitHub Pages / OSS / COS 等），
把地址填入 `services/cards.js` 的 `CARD_BASE` 后重新发行即可。
