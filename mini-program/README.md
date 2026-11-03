# 益禄加油 · 微信小程序发布指南

> 本工程是标准 uni-app 项目，用 HBuilderX 即可一套源码同时出「微信小程序」与「桌面端」。
> 本文档说明小程序端的构建产物、发布流程，以及 127MB 卡片的远程托管方案。

---

## 一、构建产物（已生成，可直接用）

- **小程序源码产物**：`unpackage/dist/dev/mp-weixin`（约 287KB）
  - 已**排除** 127MB 本地卡片，体积合规，可直接导入微信开发者工具上传。
  - 四个页面（书架/学习/复习/我的）、SM-2 复习逻辑、TTS 诵读均已编译进去。

### 重新构建命令（需本机有 HBuilderX）

```bat
D:/.appdata/HBuilderX/cli.exe launch mp-weixin --project "C:/Users/HUAWEI/WorkBuddy/2026-10-31-07-42-15/memory-app" --compile true
```

⚠️ **重要**：构建前请保证项目根目录的 `static/` 整体移走（例如 `mv static static_local`）。
否则 HBuilderX 会把 127MB 卡片原样打进小程序包，超过微信 20MB 上限，无法上传。
构建完成恢复：`mv static_local static`。

---

## 二、导入微信开发者工具并发布（需你操作）

本机未安装微信开发者工具，且上传必须用你本人登录微信账号的开发者工具，此步需你完成：

1. 安装并打开「微信开发者工具」。
2. 「导入项目」→ 目录选择 `unpackage/dist/dev/mp-weixin`。
3. **AppID**：将 `touristappid` 换成你的小程序 AppID。
   - 方式 A：直接改 `manifest.json` 的 `mp-weixin.appid` 后重新执行上面的构建命令；
   - 方式 B：在开发者工具导入时填写，或改 `project.config.json` 的 `appid`。
4. 点击「上传」→ 填版本号与备注 → 提交。
5. 登录 [mp.weixin.qq.com](https://mp.weixin.qq.com) → 版本管理 → 提交审核 → 发布。

---

## 三、卡片远程托管（小程序端必做）

微信主包+分包上限约 20MB，127MB 卡片**无法打包进小程序**，必须运行时从 https 远程拉取。

`services/cards.js` 顶部已预留开关：

```js
// 填入远程 https 基址即让小程序端加载卡片，
// 例如 'https://your-user.github.io/your-repo/static/content/'
export const CARD_BASE = ''
const LOCAL_BASE = '/static/content/'
const BASE = CARD_BASE || LOCAL_BASE
```

操作步骤：
1. 将仓库里的 `static/content/` 整目录上传到任意 https 静态托管
   （推荐 GitHub Pages / 阿里云 OSS / 腾讯云 COS）。
2. 拿到基址（末尾带 `/static/content/`），填入上面的 `CARD_BASE`。
3. 重新执行「一、重新构建命令」。
4. 在公众平台 **开发管理 → 开发设置 → 服务器域名**，把该域名加入 `request` 合法域名。

### GitHub Pages 托管（需你提供 token 让我推送）

- 本仓库已 `git init` 并提交，包含 `static/content/`（卡片数据，单文件最大 4MB，满足 GitHub 限制）。
- 你提供 **GitHub Personal Access Token** 后，我执行：
  - `git remote add origin <你的仓库 URL>`
  - `git push -u origin main`
  - 仓库 Settings → Pages → 选 `main` 分支根目录 → 得到 `https://<user>.github.io/<repo>/`
  - 把 `https://<user>.github.io/<repo>/static/content/` 填入 `CARD_BASE` → 重新构建小程序。

---

## 四、桌面端（已完成，无需此步）

- 桌面软件已打包：`益禄加油.exe`（直接运行）、`益禄加油 Setup 1.0.0.exe`（安装包）、便携版 7z。
- 卡片随包**本地加载**，离线可用，不依赖远程托管。

---

## 五、待你提供的三项（仅你可提供）

1. **小程序 AppID**：替换 `manifest.json` 的 `mp-weixin.appid`（或在开发者工具填写）。
2. **GitHub Token（可选）**：用于把卡片推到 GitHub Pages 做远程托管；不提供则卡片需你用其他 https 托管。
3. **微信开发者工具 + 你的微信账号**：用于最终「上传 / 发布」（本机未安装开发者工具）。
