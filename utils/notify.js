// utils/notify.js
// 跨端「每日复习提醒」调度封装。
//
// 目标平台与对应实现：
//   - Android / iOS（APP-PLUS）  → plus.localNotification，离线生效
//   - 鸿蒙（APP-HARMONY）        → 需接入 @ohos/notificationManager（uni 插件 / ArkTS 模块）；
//                                   本 JS 构建无 plus，这里做能力探测 + 优雅降级
//   - 微信小程序（MP-WEIXIN）     → 无本地通知，改用订阅消息：
//                                   wx.requestSubscribeMessage 申请授权，实际每日推送由服务端完成
//   - H5 / Electron / Web         → Web Notifications API（页面存活时生效）；
//                                   Electron 内优先交给主进程 Electron.Notification 兜底（见 electron/main.js）
//
// 所有分支均做能力探测，任何一端不可用都降级为 no-op，绝不抛错中断 App.onLaunch。

function nextFireDate(h, m) {
  const d = new Date()
  d.setHours(h, m, 0, 0)
  if (d <= new Date()) d.setDate(d.getDate() + 1) // 今天已过的时刻 → 排到明天
  return d
}

let webTimer = null

/* ============ Android / iOS ============ */
// #ifdef APP-PLUS
function scheduleAppPlus({ time, title, body }) {
  if (typeof plus === 'undefined' || !plus.localNotification) {
    console.warn('[notify] 本地通知 API 不可用，跳过调度')
    return
  }
  try {
    try { plus.localNotification.clear() } catch (e) { /* ignore */ }
    const [h, m] = time.split(':').map(Number)
    plus.localNotification.notify({
      title,
      body,
      date: nextFireDate(h, m),
      sound: 'system',
      vibrate: true
    })
  } catch (e) {
    console.error('[notify] 调度失败', e)
  }
}
// #endif

/* ============ 鸿蒙 ============ */
// #ifdef APP-HARMONY
function scheduleHarmony() {
  // uni-app 鸿蒙构建无 plus；通知须走 @ohos/notificationManager（原生模块 / uni 通知插件）。
  // 此处仅做能力探测，缺依赖时安全降级，由原生侧补齐或后续接入 uni 通知插件。
  console.info('[notify] 鸿蒙端每日提醒需接入 ohos notificationManager，当前降级跳过')
}
// #endif

/* ============ 微信小程序 ============ */
// #ifdef MP-WEIXIN
function scheduleWeixin() {
  // 小程序不支持本地通知。每日提醒应改用「订阅消息」：
  //   1) 微信公众平台申请一次性订阅消息模板（如「复习提醒」）
  //   2) 在用户点击场景下调用 wx.requestSubscribeMessage 申请授权
  //   3) 服务端（云函数 + 定时触发器）每日到点调用 subscribeMessage 下发
  // 由于需服务端配合，这里仅打印引导，不在 onLaunch 自动弹窗申请（避免骚扰）。
  console.info('[notify] 小程序端请改用订阅消息（wx.requestSubscribeMessage + 服务端定时下发）')
}
// #endif

/* ============ H5 / Electron / Web ============ */
// #ifdef H5
function scheduleWeb({ time, title, body }) {
  // Electron 桌面：交给主进程定时弹通知（窗口最小化也能触发）
  if (typeof window !== 'undefined' && window.memDesktop && window.memDesktop.setReminder) {
    try { window.memDesktop.setReminder({ time, title, body }); return } catch (e) { /* fallthrough */ }
  }
  // 普通浏览器：Web Notifications（页面存活时生效）
  if (typeof Notification === 'undefined') return
  try {
    if (Notification.permission === 'granted') {
      armWebTimer(time, title, body)
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then(p => {
        if (p === 'granted') armWebTimer(time, title, body)
      })
    }
  } catch (e) {
    console.warn('[notify] Web 通知降级', e)
  }
}
function armWebTimer(time, title, body) {
  const [h, m] = time.split(':').map(Number)
  if (webTimer) clearInterval(webTimer)
  webTimer = setInterval(() => {
    const now = new Date()
    if (now.getHours() === h && now.getMinutes() === m) {
      try { new Notification(title, { body }) } catch (e) { /* ignore */ }
    }
  }, 30 * 1000)
}
// #endif

/* ============ 统一入口 ============ */
export function scheduleDailyReminder({ time = '20:00', title = '记忆背诵', body = '该复习啦～' } = {}) {
  // #ifdef APP-PLUS
  scheduleAppPlus({ time, title, body }); return
  // #endif
  // #ifdef APP-HARMONY
  scheduleHarmony(); return
  // #endif
  // #ifdef MP-WEIXIN
  scheduleWeixin(); return
  // #endif
  // #ifdef H5
  scheduleWeb({ time, title, body }); return
  // #endif
  // 其余（如 SSR / 未知平台）降级
  console.info('[notify] 当前平台不支持本地提醒，跳过')
}

export function cancelReminder() {
  if (webTimer) { clearInterval(webTimer); webTimer = null }
  // #ifdef APP-PLUS
  if (typeof plus !== 'undefined' && plus.localNotification) {
    try { plus.localNotification.clear() } catch (e) { /* ignore */ }
  }
  // #endif
}
