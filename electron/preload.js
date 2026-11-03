// electron/preload.js
// 在渲染进程（uni-app H5）与 Electron 主进程之间建立安全桥。
const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('memDesktop', {
  isElectron: true,
  // 通知主进程更新每日提醒配置（由 utils/notify.js 的 H5 分支调用）
  setReminder: (cfg) => ipcRenderer.send('set-reminder', cfg)
})
