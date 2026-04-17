#!/usr/bin/env python3
r"""
配置 Go 语言环境变量

作用:
在 Windows 系统上配置 Go 语言环境变量，设置 GOROOT 并将 bin 目录添加到系统 PATH。
检查当前环境，如果配置已经符合要求则跳过，避免重复设置。
**单版本配置**，自动移除其他 Go 版本路径，只保留当前配置版本。

默认 Go 安装路径: D:\Softwares\Go

用法:
python go/config_go_env.py [go_path]

参数:
  go_path  可选，指定 Go 安装路径，默认使用 D:\Softwares\Go
"""

import os
import sys
import subprocess
from typing import Optional


# 默认 Go 安装路径
DEFAULT_GO_PATH = r"D:\Softwares\Go"


def get_current_goroot() -> Optional[str]:
    """获取当前系统的 GOROOT 环境变量（从注册表读取，保证获取的是系统配置而非当前进程环境）"""
    result = subprocess.run(
        ['reg', 'query', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', '/v', 'GOROOT'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        # 如果从注册表读取失败，回退到从环境变量获取
        return os.environ.get('GOROOT')

    # 注册表输出格式:
    #     GOROOT    REG_SZ    C:\Go
    # 我们需要找到 REG_SZ 之后的所有内容
    lines = result.stdout.splitlines()
    for line in lines:
        line = line.rstrip('\n')
        # 找出带有 GOROOT 的行，这行以多个空格开头
        if 'GOROOT' in line and 'REG_' in line:
            # 找到 REG_ 的位置，后面就是完整的 GOROOT 值
            reg_index = line.find('REG_')
            # 跳过 REG_xxx 和它前面的空格
            # 找到第三个部分之后都是值（名称 类型 值）
            # 格式是: [空格]名称[空格+]类型[空格+]值
            # 所以从找到 REG_ 后跳过类型
            space_after_reg = line.find(' ', reg_index)
            if space_after_reg != -1:
                # 值从 space_after_reg + 1 开始
                goroot_value = line[space_after_reg + 1:].rstrip().lstrip()
                return goroot_value

    # 如果解析失败，回退到从环境变量获取
    return os.environ.get('GOROOT')


def check_go_exists(go_path: str) -> bool:
    """检查 Go 路径是否存在且包含 bin/go.exe"""
    go_exe = os.path.join(go_path, 'bin', 'go.exe')
    return os.path.exists(go_exe)


def get_system_path() -> str:
    """获取系统 PATH 环境变量"""
    result = subprocess.run(
        ['reg', 'query', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', '/v', 'Path'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        # 如果读取失败，回退到从环境变量获取
        return os.environ.get('PATH', '')

    # 注册表输出格式:
    #     Path    REG_SZ    C:\path1;C:\path 2;C:\path3
    # 我们需要找到 REG_SZ 之后的所有内容
    lines = result.stdout.splitlines()
    for line in lines:
        line = line.rstrip('\n')
        # 找出带有 Path 的行，这行以多个空格开头
        if 'Path' in line and 'REG_' in line:
            # 找到 REG_ 的位置，后面就是完整的 Path 值
            reg_index = line.find('REG_')
            # 跳过 REG_xxx 和它前面的空格
            # 找到第三个部分之后都是值（名称 类型 值）
            # 格式是: [空格]名称[空格+]类型[空格+]值
            # 所以从找到 REG_ 后跳过类型
            space_after_reg = line.find(' ', reg_index)
            if space_after_reg != -1:
                # 值从 space_after_reg + 1 开始
                path_value = line[space_after_reg + 1:].rstrip().lstrip()
                return path_value

    # 如果解析失败，回退到从环境变量获取
    return os.environ.get('PATH', '')


def is_go_in_path(go_bin_path: str) -> bool:
    """检查 Go bin 目录是否已经在 PATH 中"""
    current_path = get_system_path()
    go_bin_path = go_bin_path.replace('/', '\\').lower()
    current_path_lower = current_path.replace('/', '\\').lower()

    return go_bin_path in current_path_lower


def set_goroot(go_path: str) -> bool:
    """设置系统环境变量 GOROOT（需要管理员权限）"""
    # 使用 reg add 而不是 setx，避免 setx 的 1024 字符截断限制
    result = subprocess.run(
        ['reg', 'add', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', '/v', 'GOROOT', '/t', 'REG_SZ', '/d', go_path, '/f'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def find_go_in_path(current_path: str) -> list[str]:
    """在 PATH 中查找已有的 Go bin 路径（任何包含 go.exe 的目录）"""
    entries = current_path.split(';')
    go_entries = []
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        # 识别 Go 路径，包含 go 且 bin 目录存在 go.exe
        entry_lower = entry.lower()
        if 'go' in entry_lower and os.path.exists(os.path.join(entry, 'go.exe')):
            go_entries.append(entry)
    return go_entries


def add_to_system_path(go_bin_path: str) -> bool:
    """将 Go bin 目录添加到系统 PATH（需要管理员权限）
    **单版本配置**，自动移除其他 Go 版本路径，只保留当前版本
    """
    # 获取当前 PATH
    current_path = get_system_path()

    # 查找并移除其他已存在的 Go 版本
    existing_go_entries = find_go_in_path(current_path)
    if existing_go_entries:
        print(f"  发现 {len(existing_go_entries)} 个其他 Go 版本:")
        for entry in existing_go_entries:
            if entry.lower() != go_bin_path.lower():
                print(f"    将移除: {entry}")
                current_path = current_path.replace(entry + ';', '').replace(';' + entry, '').replace(entry, '')

    # 检查是否已经存在当前 Go
    if is_go_in_path(go_bin_path):
        print(f"[OK] {go_bin_path} 已经在 PATH 中，跳过")
        return True

    # 添加当前版本到 PATH
    current_entries = [e.strip() for e in current_path.split(';') if e.strip()]
    current_entries.append(go_bin_path)
    new_path = ';'.join(current_entries)

    # 使用 reg add 而不是 setx，避免 setx 的 1024 字符截断限制
    result = subprocess.run(
        ['reg', 'add', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', '/v', 'Path', '/t', 'REG_SZ', '/d', new_path, '/f'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def check_admin() -> bool:
    """检查是否有管理员权限"""
    try:
        # 尝试读取注册表的系统环境变量键
        subprocess.run(
            ['reg', 'query', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment'],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    # 处理帮助参数
    if len(sys.argv) >= 2 and sys.argv[1] in ['-h', '--help']:
        print(__doc__)
        sys.exit(0)

    # 获取 Go 路径
    if len(sys.argv) >= 2:
        go_path = sys.argv[1].strip()
    else:
        go_path = DEFAULT_GO_PATH

    go_path = os.path.abspath(go_path)
    go_bin_path = os.path.join(go_path, 'bin')

    print(f"Go 安装路径: {go_path}")
    print()

    # 检查 Go 是否存在
    if not check_go_exists(go_path):
        print(f"错误: 在 {go_path} 未找到 Go (缺少 bin/go.exe)")
        print("请确认 Go 安装路径是否正确")
        sys.exit(1)

    # 检查管理员权限
    if not check_admin():
        print("错误: 需要管理员权限才能修改系统环境变量")
        print("请以管理员身份运行此脚本")
        sys.exit(1)

    # 检查当前 GOROOT
    current_goroot = get_current_goroot()
    if current_goroot and os.path.abspath(current_goroot) == os.path.abspath(go_path):
        print(f"[OK] GOROOT 已经是 {go_path}，无需修改")
        goroot_ok = True
    else:
        if current_goroot:
            print(f"  当前 GOROOT: {current_goroot}")
        print(f"  将设置 GOROOT: {go_path}")
        goroot_ok = False

    # 检查 PATH
    if is_go_in_path(go_bin_path):
        print(f"[OK] {go_bin_path} 已经在系统 PATH 中，无需修改")
        path_ok = True
    else:
        print(f"  需要将 {go_bin_path} 添加到系统 PATH")
        path_ok = False

    print()

    if goroot_ok and path_ok:
        print("[OK] 环境配置已经完成，无需修改")
        sys.exit(0)

    # 开始配置
    print("开始配置环境变量...")
    print()

    if not goroot_ok:
        print("设置 GOROOT...")
        success = set_goroot(go_path)
        if not success:
            print("错误: 设置 GOROOT 失败")
            sys.exit(1)
        print("[OK] GOROOT 设置完成")

    print()

    if not path_ok:
        print("添加 bin 目录到 PATH...")
        success = add_to_system_path(go_bin_path)
        if not success:
            print("错误: 添加到 PATH 失败")
            sys.exit(1)
        print("[OK] PATH 添加完成")

    print()
    print("[OK] 配置完成!")

    # 尝试验证 go 版本
    print("\n尝试验证 Go 安装...")
    try:
        result = subprocess.run(
            ['go', 'version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"[OK] Go 验证成功: {result.stdout.strip()}")
        else:
            print("[!] Go 版本命令失败，需要重启终端后生效")
            print("    当前会话环境变量还没更新，这是正常的")
    except FileNotFoundError:
        print("[!] go 命令未找到，需要重启终端后生效")
        print("    当前会话环境变量还没更新，这是正常的")

    print()
    print("请注意:")
    print("  1. 需要重启命令提示符或终端才能看到环境变量变化")
    print("  2. 需要重启已打开的应用程序（如 Claude Code）才能使用新的环境变量")


if __name__ == "__main__":
    main()
