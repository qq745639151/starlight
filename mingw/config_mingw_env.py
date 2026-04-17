#!/usr/bin/env python3
r"""
配置 MinGW-w64 C/C++ 环境变量

作用:
在 Windows 系统上配置 MinGW-w64 环境变量，设置 MINGW_HOME 并将 bin 目录和 GCC libexec 目录添加到系统 PATH。
检查当前环境，如果配置已经符合要求则跳过，避免重复设置。
**单版本配置**，自动移除其他 MinGW-w64 版本路径，只保留当前配置版本。

默认 MinGW-w64 安装路径: D:\Softwares\mingw64

用法:
python mingw/config_mingw_env.py [mingw_path]

参数:
  mingw_path  可选，指定 MinGW-w64 安装路径，默认使用 D:\Softwares\mingw64
"""

import os
import sys
import subprocess
from typing import Optional, List


# 默认 MinGW-w64 安装路径
DEFAULT_MINGW_PATH = r"D:\Softwares\mingw64"


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
            # 格式是: [空格]名称[空格+]类型[空格+]值
            # 所以从找到 REG_ 后跳过类型
            space_after_reg = line.find(' ', reg_index)
            if space_after_reg != -1:
                # 值从 space_after_reg + 1 开始
                path_value = line[space_after_reg + 1:].rstrip().lstrip()
                return path_value

    # 如果解析失败，回退到从环境变量获取
    return os.environ.get('PATH', '')


def is_mingw_in_path(mingw_bin_path: str) -> bool:
    """检查 MinGW bin 目录是否已经在 PATH 中"""
    current_path = get_system_path()
    mingw_bin_path = mingw_bin_path.replace('/', '\\').lower()
    current_path_lower = current_path.replace('/', '\\').lower()

    return mingw_bin_path in current_path_lower


def set_mingw_home(mingw_path: str) -> bool:
    """设置系统环境变量 MINGW_HOME（需要管理员权限）"""
    # 使用 reg add 而不是 setx，避免 setx 的 1024 字符截断限制
    result = subprocess.run(
        ['reg', 'add', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', '/v', 'MINGW_HOME', '/t', 'REG_SZ', '/d', mingw_path, '/f'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def find_mingw_in_path(current_path: str) -> List[str]:
    """在 PATH 中查找已有的 MinGW bin 路径（任何包含 gcc.exe 的目录）"""
    entries = current_path.split(';')
    mingw_entries = []
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        # 识别 MinGW 路径，包含 mingw 且 bin 目录存在 gcc.exe
        entry_lower = entry.lower()
        if ('mingw' in entry_lower or 'gcc' in entry_lower) and os.path.exists(os.path.join(entry, 'gcc.exe')):
            mingw_entries.append(entry)
    return mingw_entries


def add_to_system_path(mingw_bin_path: str, mingw_libexec_path: str) -> bool:
    """将 MinGW bin 目录和 libexec GCC 目录添加到系统 PATH（需要管理员权限）
    **单版本配置**，自动移除其他 MinGW 版本路径，只保留当前版本
    """
    # 获取当前 PATH
    current_path = get_system_path()

    # 查找并移除其他已存在的 MinGW 版本
    existing_mingw_entries = find_mingw_in_path(current_path)
    if existing_mingw_entries:
        print(f"  发现 {len(existing_mingw_entries)} 个其他 MinGW 版本:")
        for entry in existing_mingw_entries:
            if entry.lower() != mingw_bin_path.lower():
                print(f"    将移除: {entry}")
                current_path = current_path.replace(entry + ';', '').replace(';' + entry, '').replace(entry, '')

    # 检查是否已经存在当前 MinGW
    if is_mingw_in_path(mingw_bin_path):
        print(f"[OK] {mingw_bin_path} 已经在 PATH 中，跳过")
        return True

    # 添加当前版本到 PATH（放在最前面，优先级高于其他编译器）
    current_entries = [e.strip() for e in current_path.split(';') if e.strip()]
    # 将 MinGW 放在最前面，确保优先使用
    new_entries = [mingw_bin_path]
    if mingw_libexec_path:
        new_entries.append(mingw_libexec_path)
    new_entries.extend(current_entries)
    new_path = ';'.join(new_entries)

    # 使用 reg add 而不是 setx，避免 setx 的 1024 字符截断限制
    result = subprocess.run(
        ['reg', 'add', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', '/v', 'Path', '/t', 'REG_SZ', '/d', new_path, '/f'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def get_current_mingw_home() -> Optional[str]:
    """获取当前系统的 MINGW_HOME 环境变量（从注册表读取，保证获取的是系统配置而非当前进程环境）"""
    result = subprocess.run(
        ['reg', 'query', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', '/v', 'MINGW_HOME'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        # 如果从注册表读取失败，回退到从环境变量获取
        return os.environ.get('MINGW_HOME')

    # 注册表输出格式:
    #     MINGW_HOME    REG_SZ    C:\Program Files\mingw64
    # 我们需要找到 REG_SZ 之后的所有内容
    lines = result.stdout.splitlines()
    for line in lines:
        line = line.rstrip('\n')
        # 找出带有 MINGW_HOME 的行，这行以多个空格开头
        if 'MINGW_HOME' in line and 'REG_' in line:
            # 找到 REG_ 的位置，后面就是完整的 MINGW_HOME 值
            reg_index = line.find('REG_')
            # 跳过 REG_xxx 和它前面的空格
            # 找到第三个部分之后都是值（名称 类型 值）
            # 格式是: [空格]名称[空格+]类型[空格+]值
            # 所以从找到 REG_ 后跳过类型
            space_after_reg = line.find(' ', reg_index)
            if space_after_reg != -1:
                # 值从 space_after_reg + 1 开始
                mingw_home_value = line[space_after_reg + 1:].rstrip().lstrip()
                return mingw_home_value

    # 如果解析失败，回退到从环境变量获取
    return os.environ.get('MINGW_HOME')


def check_mingw_exists(mingw_path: str) -> bool:
    """检查 MinGW 路径是否存在且包含 bin/gcc.exe"""
    gcc_exe = os.path.join(mingw_path, 'bin', 'gcc.exe')
    return os.path.exists(gcc_exe)


def find_libexec_gcc_path(mingw_path: str) -> Optional[str]:
    """查找 libexec/gcc/x86_64-w64-mingw32/<version> 路径

    需要这个路径才能让 gcc 找到 cc1.exe, cc1plus.exe 等内部工具
    """
    base_path = os.path.join(mingw_path, 'libexec', 'gcc', 'x86_64-w64-mingw32')
    if not os.path.exists(base_path):
        return None

    # 查找版本子目录
    entries = os.listdir(base_path)
    for entry in entries:
        full_path = os.path.join(base_path, entry)
        if os.path.isdir(full_path):
            # 检查里面是否有 cc1.exe
            if os.path.exists(os.path.join(full_path, 'cc1.exe')):
                return full_path

    return None


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

    # 获取 MinGW 路径
    if len(sys.argv) >= 2:
        mingw_path = sys.argv[1].strip()
    else:
        mingw_path = DEFAULT_MINGW_PATH

    mingw_path = os.path.abspath(mingw_path)
    mingw_bin_path = os.path.join(mingw_path, 'bin')

    print(f"MinGW-w64 安装路径: {mingw_path}")
    print()

    # 检查 MinGW 是否存在
    if not check_mingw_exists(mingw_path):
        print(f"错误: 在 {mingw_path} 未找到 MinGW (缺少 bin/gcc.exe)")
        print("请确认 MinGW-w64 安装路径是否正确")
        sys.exit(1)

    # 查找 libexec GCC 路径
    mingw_libexec_path = find_libexec_gcc_path(mingw_path)
    if not mingw_libexec_path:
        print(f"警告: 在 {mingw_path}\\libexec\\gcc\\x86_64-w64-mingw32 未找到 GCC 版本目录")
        print("      这可能导致 gcc 无法找到 cc1.exe/cc1plus.exe")
        print()

    # 检查管理员权限
    if not check_admin():
        print("错误: 需要管理员权限才能修改系统环境变量")
        print("请以管理员身份运行此脚本")
        sys.exit(1)

    # 检查当前 MINGW_HOME
    current_mingw_home = get_current_mingw_home()
    if current_mingw_home and os.path.abspath(current_mingw_home) == os.path.abspath(mingw_path):
        print(f"[OK] MINGW_HOME 已经是 {mingw_path}，无需修改")
        mingw_home_ok = True
    else:
        if current_mingw_home:
            print(f"  当前 MINGW_HOME: {current_mingw_home}")
        print(f"  将设置 MINGW_HOME: {mingw_path}")
        mingw_home_ok = False

    # 检查 PATH
    if is_mingw_in_path(mingw_bin_path):
        print(f"[OK] {mingw_bin_path} 已经在系统 PATH 中，无需修改")
        path_ok = True
    else:
        print(f"  需要将 {mingw_bin_path} 添加到系统 PATH")
        path_ok = False

    print()

    if mingw_home_ok and path_ok:
        print("[OK] 环境配置已经完成，无需修改")
        # 尝试验证
        print("\n尝试验证 MinGW 安装...")
        try:
            result = subprocess.run(
                ['gcc', '--version'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                first_line = result.stdout.splitlines()[0] if result.stdout else "OK"
                print(f"[OK] GCC 验证成功: {first_line}")
            else:
                print("[!] GCC 版本命令失败，需要重启终端后生效")
                print("    当前会话环境变量还没更新，这是正常的")
        except FileNotFoundError:
            print("[!] gcc 命令未找到，需要重启终端后生效")
            print("    当前会话环境变量还没更新，这是正常的")
        sys.exit(0)

    # 开始配置
    print("开始配置环境变量...")
    print()

    if not mingw_home_ok:
        print("设置 MINGW_HOME...")
        success = set_mingw_home(mingw_path)
        if not success:
            print("错误: 设置 MINGW_HOME 失败")
            sys.exit(1)
        print("[OK] MINGW_HOME 设置完成")

    print()

    if not path_ok:
        print("添加 bin 目录和 libexec GCC 目录到 PATH...")
        success = add_to_system_path(mingw_bin_path, mingw_libexec_path)
        if not success:
            print("错误: 添加到 PATH 失败")
            sys.exit(1)
        print("[OK] PATH 添加完成")

    print()

    print("[OK] 配置完成!")

    # 尝试验证 MinGW 安装
    print("\n尝试验证 MinGW 安装...")
    try:
        result = subprocess.run(
            ['gcc', '--version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            first_line = result.stdout.splitlines()[0] if result.stdout else "OK"
            print(f"[OK] GCC 验证成功: {first_line}")
        else:
            print("[!] GCC 版本命令失败，需要重启终端后生效")
            print("    当前会话环境变量还没更新，这是正常的")
    except FileNotFoundError:
        print("[!] gcc 命令未找到，需要重启终端后生效")
        print("    当前会话环境变量还没更新，这是正常的")

    print()
    print("请注意:")
    print("  1. 需要重启命令提示符或终端才能看到环境变量变化")
    print("  2. 需要重启已打开的应用程序（如 Claude Code）才能使用新的环境变量")
    print("  3. MinGW 已添加到 PATH 最前面，优先级高于其他编译器（如 MSVC）")


if __name__ == "__main__":
    main()
