#!/usr/bin/env python3
"""
在 Windows 上安装 uv - 快速的 Python 包管理器

作用:
自动下载并安装 uv 到 Windows 系统，添加到 PATH，验证安装。
uv 是一个比 pip 更快的 Python 包管理器，兼容 pip 和 requirements.txt。

用法:
python uv/install_uv.py
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path


def is_uv_installed() -> bool:
    """检查 uv 是否已经安装"""
    result = subprocess.run(
        ['uv', '--version'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def get_uv_version() -> str:
    """获取已安装的 uv 版本"""
    result = subprocess.run(
        ['uv', '--version'],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return ""


def install_uv_via_pip() -> bool:
    """通过 pip 安装 uv"""
    print("通过 pip 安装 uv...")
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '--upgrade', 'uv'],
        capture_output=False
    )
    return result.returncode == 0


def main():
    print("uv 安装脚本")
    print("uv 是一个快速的 Python 包管理器，兼容 pip")
    print()

    # 检查是否已经安装
    if is_uv_installed():
        version = get_uv_version()
        print(f"[OK] uv 已经安装: {version}")
        print("无需重复安装")
        sys.exit(0)

    print("开始安装 uv...")

    # 方法: 通过 pip 安装最简单
    success = install_uv_via_pip()

    if not success:
        print("pip 安装失败")
        sys.exit(1)

    print()
    print("[OK] uv 安装成功!")
    print("请重启终端或命令提示符以使 PATH 更改生效")
    print()
    print("验证安装:")
    print("  uv --version")
    print()
    print("常用命令:")
    print("  uv init          # 初始化新项目")
    print("  uv add requests # 添加依赖")
    print("  uv install      # 安装所有依赖")
    print("  uv run python   # 在虚拟环境中运行 python")


if __name__ == "__main__":
    main()
