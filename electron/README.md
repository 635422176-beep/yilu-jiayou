# 记忆背诵工具 · Windows 桌面端（Electron 包裹）

uni-app 本身没有原生 Windows 桌面目标，这里用 **Electron 包裹 H5 构建产物** 交付一个可安装的 `.exe`。

## 构建步骤（需用户自备 Node 环境）

1. **先构建 uni-app 的 H5 产物**（二选一）：
   - HBuilderX：发行 → 网站(H5)，输出到 `memory-app/dist/build/h5/`
   - 或 uni-cli：`cd memory-app && npm run build:h5`（同样输出到 `dist/build/h5/`）
   - 请确保 `manifest.json` 的 `h5` 已设为 `hash` 路由 + 相对 `publicPath: "./"`（已配好），否则 `file://` 下资源 404。

2. **安装并启动 Electron**（在本 `electron/` 目录）：
   ```bash
   cd memory-app/electron
   npm install
   npm start
   ```
   启动后窗口加载 `../dist/build/h5/index.html`。

3. **打包成安装包**（可选，需联网下载 Electron 二进制）：
   ```bash
   npm run pack        # 产出 Windows NSIS 安装包
   ```

## 通知说明
- H5 渲染层（`utils/notify.js` 的 H5 分支）检测到 `window.memDesktop` 时，会把提醒时间/文案转发给主进程。
- 主进程（`main.js`）用 `Electron.Notification` 按设定时间每日弹提醒，并默认**登录自启**，即使窗口最小化也能触发（窗口完全关闭则不弹，属预期）。
- 纯浏览器打开 H5（非 Electron）时，退化为 Web Notifications API（仅页面存活时生效）。

## 安全
- 已开启 `contextIsolation: true` 与 `nodeIntegration: false`，preload 仅通过 `contextBridge` 暴露最小接口 `memDesktop`。
