// electron/main.js
// 益禄加油工具 Windows 桌面端主进程。
// 负责：加载 uni-app 的 H5 构建产物 + 主进程每日定时通知 + 登录自启。
//
// 重要：uni-app 的 H5 产物可能以绝对路径（/static/...）引用资源，
// 用 file:// 直接加载会大面积 404。因此这里内置一个本地静态服务器，
// 统一以 http://127.0.0.1:<随机端口>/ 加载，相对路径与绝对路径产物都能正常工作。
const { app, BrowserWindow, Notification, ipcMain } = require('electron')
const path = require('path')
const fs = require('fs')
const http = require('http')
const os = require('os')

// 启动日志：桌面端排障用。Electron 打包后是 GUI 子系统，控制台输出不可见，
// 因此把关键节点与异常写入日志文件（系统临时目录下 memory-app-launch.log）。
const LOG_FILE = path.join(os.tmpdir(), 'memory-app-launch.log')
function log(msg, err) {
  try {
    const line = `[${new Date().toISOString()}] ${msg}` + (err ? ' | ' + (err && err.stack || err.message || String(err)) : '') + '\n'
    fs.appendFileSync(LOG_FILE, line)
  } catch (e) { /* 日志失败不影响主流程 */ }
}
process.on('uncaughtException', (e) => { log('uncaughtException', e) })
process.on('unhandledRejection', (e) => { log('unhandledRejection', e) })
log('=== main.js 已加载 === argv=' + JSON.stringify(process.argv) + ' packaged=' + app.isPackaged)

let win = null

// 每日提醒配置（渲染进程可通过 preload 覆盖）
const reminder = { enabled: true, time: '20:00', title: '益禄加油', body: '该复习啦～' }
let timer = null

// H5 产物候选目录：HBuilderX 发行构建 / dev 编译 / uni-cli 构建
function resolveH5Dir() {
  const candidates = []
  // 打包后：electron-builder 的 extraResources 会把 H5 产物拷到 resources/h5
  if (app.isPackaged && process.resourcesPath) {
    candidates.push(path.join(process.resourcesPath, 'h5'))
  }
  candidates.push(
    // HBuilderX「发行 → Web」实测产物目录（本项目实际产出路径）
    path.join(__dirname, '../unpackage/dist/build/web'),
    // 其它可能的产物目录，按优先级兜底
    path.join(__dirname, '../unpackage/dist/build/h5'),
    path.join(__dirname, '../unpackage/dist/dev/h5'),
    path.join(__dirname, '../dist/build/h5'),
    path.join(__dirname, '../dist/build/web')
  )
  for (const c of candidates) {
    if (fs.existsSync(path.join(c, 'index.html'))) return c
  }
  return null
}

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.htm': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.eot': 'application/vnd.ms-fontobject',
  '.map': 'application/json; charset=utf-8'
}

// 本地静态服务器：端口由系统分配（listen 0），避免端口冲突
function serveDir(root) {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      let p = decodeURIComponent((req.url || '/').split('?')[0])
      if (p === '/' || p === '') p = '/index.html'
      const file = path.join(root, p)
      fs.readFile(file, (err, data) => {
        if (err) {
          // 未知路径兜底回 index.html（兼容 history 路由）
          fs.readFile(path.join(root, 'index.html'), (e2, d2) => {
            if (e2) { res.writeHead(404); res.end('404 Not Found'); return }
            res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' })
            res.end(d2)
          })
          return
        }
        const ext = path.extname(file).toLowerCase()
        res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' })
        res.end(data)
      })
    })
    server.listen(0, '127.0.0.1', () => {
      resolve({ server, port: server.address().port })
    })
  })
}

async function createWindow() {
  win = new BrowserWindow({
    width: 1100,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    title: '益禄加油',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  const dir = resolveH5Dir()
  log('resolveH5Dir 结果=' + dir + ' | resourcesPath=' + process.resourcesPath)
  if (!dir) {
    const html = encodeURIComponent(
      '<h3>未找到 H5 构建产物</h3>' +
      '<p>请在 HBuilderX 中对本项目执行「发行 → 网站-PC Web」，' +
      '生成 <code>unpackage/dist/build/web/index.html</code> 后重启本程序。</p>'
    )
    win.loadURL('data:text/html;charset=utf-8,' + html)
    return
  }

  try {
    const { port } = await serveDir(dir)
    log('静态服务器已启动 port=' + port)
    await win.loadURL('http://127.0.0.1:' + port + '/')
    log('loadURL 完成')
  } catch (err) {
    log('加载 H5 失败', err)
  }

  win.on('closed', () => { log('窗口已 closed'); win = null })
}

function showNotification(title, body) {
  if (Notification.isSupported()) {
    new Notification({ title, body, silent: false }).show()
  }
}

function armReminder() {
  if (timer) clearInterval(timer)
  if (!reminder.enabled) return
  const [h, m] = reminder.time.split(':').map(Number)
  timer = setInterval(() => {
    const now = new Date()
    if (now.getHours() === h && now.getMinutes() === m) {
      showNotification(reminder.title, reminder.body)
    }
  }, 30 * 1000)
}

// 渲染进程（H5）设置提醒参数
ipcMain.on('set-reminder', (e, cfg) => {
  if (cfg && typeof cfg.time === 'string') reminder.time = cfg.time
  if (cfg && typeof cfg.enabled === 'boolean') reminder.enabled = cfg.enabled
  if (cfg && typeof cfg.title === 'string') reminder.title = cfg.title
  if (cfg && typeof cfg.body === 'string') reminder.body = cfg.body
  armReminder()
})

app.whenReady().then(async () => {
  log('app ready 触发')
  await createWindow()
  armReminder()
  // 登录自启：仅在开启提醒时设置，保证每日提醒即便窗口关闭也能触发
  try {
    app.setLoginItemSettings({ openAtLogin: reminder.enabled, path: app.getPath('exe') })
  } catch (e) { /* 某些环境不支持，忽略 */ }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  log('window-all-closed 触发（将退出）')
  // Windows 上默认关闭即退出；如需后台常驻可改为不 quit（配合托盘）
  if (process.platform !== 'darwin') app.quit()
})
