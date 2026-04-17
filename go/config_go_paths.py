#!/usr/bin/env python3
r"""
配置 Go 路径环境变量（通过 go env -w）

作用:
在 Windows 系统上配置 Go 的工作路径和缓存路径到 Go 安装目录下，
避免占用 C 盘空间，并配置国内代理加速模块下载。

所有可配置路径都通过 go env -w 写入 Go 的配置文件，
无需修改系统环境变量。

Go 默认路径都在 C:\Users\<user>\go 下，会占用 C 盘空间，
这个脚本将它们全部迁移到 Go 安装目录下。

用法:
python go/config_go_paths.py [go_path]

参数:
  go_path  可选，指定 Go 安装路径，默认使用 D:\Softwares\Go
"""

import os
import sys
import subprocess
from typing import Dict, Optional


# 默认 Go 安装路径
DEFAULT_GO_PATH = r"D:\Softwares\Go"


def get_go_env() -> Dict[str, str]:
    """获取当前所有 go env 配置"""
    result = subprocess.run(
        ['go', 'env'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return {}

    env_map = {}
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or '=' not in line:
            continue
        # 格式: set GOROOT=D:\Softwares\Go
        if line.startswith('set '):
            line = line[4:]
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"')
        env_map[key] = value

    return env_map


def set_go_env(key: str, value: str) -> bool:
    """使用 go env -w 设置环境变量"""
    result = subprocess.run(
        ['go', 'env', '-w', f'{key}={value}'],
        capture_output=True,
        text=True
    )
    success = result.returncode == 0
    if success:
        print(f"[OK] {key} = {value}")
    else:
        print(f"[FAIL] {key} = {value}")
        if result.stderr:
            print(f"      {result.stderr.strip()}")
    return success


def check_go_exists(go_path: str) -> bool:
    """检查 Go 路径是否存在且包含 bin/go.exe"""
    go_exe = os.path.join(go_path, 'bin', 'go.exe')
    return os.path.exists(go_exe)


def main():
    # 处理帮助参数
    if len(sys.argv) >= 2 and sys.argv[1] in ['-h', '--help']:
        print(__doc__)
        sys.exit(0)

    # 获取 Go 路径
    if len(sys.argv) >= 2:
        go_base_path = sys.argv[1].strip()
    else:
        go_base_path = DEFAULT_GO_PATH

    go_base_path = os.path.abspath(go_base_path)

    print(f"Go 安装根目录: {go_base_path}")
    print()

    # 检查 Go 是否存在
    if not check_go_exists(go_base_path):
        print(f"错误: 在 {go_base_path} 未找到 Go (缺少 bin/go.exe)")
        print("请确认 Go 安装路径是否正确")
        sys.exit(1)

    # 检查 go 命令是否可用
    try:
        result = subprocess.run(['go', 'version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("错误: go 命令不可用")
            print("请确保 Go 的 bin 目录已经添加到系统 PATH")
            print("先运行 config_go_env.py 配置系统环境变量")
            sys.exit(1)
        else:
            print(f"[OK] Go 可用: {result.stdout.strip()}")
    except FileNotFoundError:
        print("错误: go 命令未找到")
        print("请确保 Go 的 bin 目录已经添加到系统 PATH")
        print("先运行 config_go_env.py 配置系统环境变量")
        sys.exit(1)

    print()

    # 定义要配置的路径
    # 所有路径都放在 Go 安装根目录下
    paths = {
        'GOPATH': os.path.join(go_base_path, 'work'),
        'GOMODCACHE': os.path.join(go_base_path, 'pkg', 'mod'),
        'GOCACHE': os.path.join(go_base_path, 'cache', 'go-build'),
        'GOPROXY': 'https://goproxy.cn,direct',
    }

    # 获取当前配置
    current_env = get_go_env()
    changes_needed = False

    print("当前配置检查:")
    print("-" * 60)
    for key, expected_value in paths.items():
        current_value = current_env.get(key, '(not set)')
        if current_value == expected_value:
            print(f"[OK] {key:<15} = {current_value} (already correct)")
        else:
            print(f"[CHANGE] {key:<15} = {current_value} → {expected_value}")
            changes_needed = True
    print("-" * 60)
    print()

    if not changes_needed:
        print("[OK] 所有配置已经正确，无需修改")
        sys.exit(0)

    # 开始配置
    print("开始应用配置...")
    print()

    # 创建所需目录
    print("创建目录结构...")
    for key, expected_value in paths.items():
        if key != 'GOPROXY':  # GOPROXY 是 URL，不是路径
            # 确保目录存在
            os.makedirs(expected_value, exist_ok=True)
    print("[OK] 目录创建完成")
    print()

    # 设置环境变量
    print("应用配置:")
    all_ok = True
    for key, expected_value in paths.items():
        # 转换为 Windows 风格路径
        expected_value = expected_value.replace('/', '\\')
        if not set_go_env(key, expected_value):
            all_ok = False

    print()

    if all_ok:
        print("[OK] 所有配置完成!")
        print()
        print("配置已通过 go env -w 写入 Go 的配置文件")
        print("不需要修改系统环境变量，立即在新终端生效")
    else:
        print("[WARN] 部分配置失败，请检查输出")
        sys.exit(1)


if __name__ == "__main__":
    main()
