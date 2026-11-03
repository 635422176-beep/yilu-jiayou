#!/usr/bin/env python3
# 7za.exe 包装器
# 背景：electron-builder 在 Windows 上解压 winCodeSign 缓存时会遇到两个 macOS
# 符号链接(darwin/10.12/lib/libcrypto.dylib, libssl.dylib)，非管理员无法创建，
# 导致整个解压失败、NSIS 安装包构建卡死。
# 本包装在检测到解压 winCodeSign 归档时，自动排除这两个符号链接
# (Windows 代码签名用不到它们)，从而让解压成功。
import sys
import os
import subprocess

# 打包后的 exe 与 7za_real.exe 同目录，按 exe 自身位置定位真实 7za
REAL_7ZA = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "7za_real.exe")


def main():
    args = sys.argv[1:]
    new_args = list(args)
    joined = " ".join(args).lower()
    # 仅当解压 winCodeSign 归档时注入排除参数，避免影响其它正常解压
    if "x" in args and "wincodesign" in joined:
        new_args.append("-x!darwin/10.12/lib/libcrypto.dylib")
        new_args.append("-x!darwin/10.12/lib/libssl.dylib")
    return subprocess.call([REAL_7ZA] + new_args)


if __name__ == "__main__":
    sys.exit(main())
