// electron-builder 自定义签名脚本（no-op）。
// 本项目无代码签名证书，不签名即可（Windows 仅会弹 SmartScreen 提示，功能不受影响）。
// 配置后 electron-builder 走自定义签名路径，不再下载内置 winCodeSign（其 macOS 符号链接在非管理员 Windows 上无法解压）。
// 调用方式：node sign-noop.js <file.exe> [--certificateFile ...] [...]
process.exit(0)
