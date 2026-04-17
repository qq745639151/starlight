#!/usr/bin/env python3
r"""
配置 Maven 环境变量

作用:
在 Windows 系统上配置 Maven 环境变量，设置 MAVEN_HOME 并将 bin 目录添加到系统 PATH。
检查当前环境，如果配置已经符合要求则跳过，避免重复设置。
支持多版本 Maven 并存，只添加当前版本，不删除其他版本。

默认 Maven 安装路径: D:\Softwares\maven

用法:
python maven/config_maven.py [maven_path]

参数:
  maven_path  可选，指定 Maven 安装路径，默认使用 D:\Softwares\maven
"""

import os
import sys
import subprocess
from typing import Optional


# 默认 Maven 安装路径
DEFAULT_MAVEN_PATH = r"D:\Softwares\maven"


def get_current_maven_home() -> Optional[str]:
    """获取当前系统的 MAVEN_HOME 环境变量"""
    return os.environ.get('MAVEN_HOME')


def check_maven_exists(maven_path: str) -> bool:
    """检查 Maven 路径是否存在且包含 bin/mvn.cmd"""
    mvn_cmd = os.path.join(maven_path, 'bin', 'mvn.cmd')
    return os.path.exists(mvn_cmd)


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


def is_maven_in_path(maven_bin_path: str) -> bool:
    """检查 Maven bin 目录是否已经在 PATH 中"""
    current_path = get_system_path()
    maven_bin_path = maven_bin_path.replace('/', '\\').lower()
    current_path_lower = current_path.replace('/', '\\').lower()

    return maven_bin_path in current_path_lower


def set_maven_home(maven_path: str) -> bool:
    """设置系统环境变量 MAVEN_HOME（需要管理员权限）"""
    result = subprocess.run(
        ['setx', '/M', 'MAVEN_HOME', maven_path],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def add_to_system_path(maven_bin_path: str) -> bool:
    """将 Maven bin 目录添加到系统 PATH（需要管理员权限）
    支持多版本 Maven 并存，只检查当前路径是否已存在，不存在才追加，保留其他版本
    """
    # 获取当前 PATH
    current_path = get_system_path()

    # 检查是否已经存在当前 Maven
    if is_maven_in_path(maven_bin_path):
        print(f"[OK] {maven_bin_path} 已经在 PATH 中，跳过")
        return True

    # 不存在就追加，保留其他所有路径（支持多版本并存）
    new_path = f"{current_path};{maven_bin_path}"
    result = subprocess.run(
        ['setx', '/M', 'Path', new_path],
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

    # 获取 Maven 路径
    if len(sys.argv) >= 2:
        maven_path = sys.argv[1].strip()
    else:
        maven_path = DEFAULT_MAVEN_PATH

    maven_path = os.path.abspath(maven_path)
    maven_bin_path = os.path.join(maven_path, 'bin')

    print(f"Maven 安装路径: {maven_path}")
    print()

    # 检查 Maven 是否存在
    if not check_maven_exists(maven_path):
        print(f"错误: 在 {maven_path} 未找到 Maven (缺少 bin/mvn.cmd)")
        print("请确认 Maven 安装路径是否正确")
        sys.exit(1)

    # 检查管理员权限
    if not check_admin():
        print("错误: 需要管理员权限才能修改系统环境变量")
        print("请以管理员身份运行此脚本")
        sys.exit(1)

    # 检查当前 MAVEN_HOME
    current_maven_home = get_current_maven_home()
    if current_maven_home and os.path.abspath(current_maven_home) == os.path.abspath(maven_path):
        print(f"[OK] MAVEN_HOME 已经是 {maven_path}，无需修改")
        maven_home_ok = True
    else:
        if current_maven_home:
            print(f"  当前 MAVEN_HOME: {current_maven_home}")
        print(f"  将设置 MAVEN_HOME: {maven_path}")
        maven_home_ok = False

    # 检查 PATH
    if is_maven_in_path(maven_bin_path):
        print(f"[OK] {maven_bin_path} 已经在系统 PATH 中，无需修改")
        path_ok = True
    else:
        print(f"  需要将 {maven_bin_path} 添加到系统 PATH")
        path_ok = False

    print()

    if maven_home_ok and path_ok:
        print("[OK] 环境配置已经完成，无需修改")
        # 尝试验证
        print("\n尝试验证 Maven 安装...")
        try:
            result = subprocess.run(
                ['mvn', '-version'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                first_line = result.stdout.splitlines()[0] if result.stdout else "OK"
                print(f"[OK] Maven 验证成功: {first_line}")
            else:
                print("[!] Maven 版本命令失败，需要重启终端后生效")
                print("    当前会话环境变量还没更新，这是正常的")
        except FileNotFoundError:
            print("[!] mvn 命令未找到，需要重启终端后生效")
            print("    当前会话环境变量还没更新，这是正常的")
        sys.exit(0)

    # 开始配置
    print("开始配置环境变量...")
    print()

    if not maven_home_ok:
        print("设置 MAVEN_HOME...")
        success = set_maven_home(maven_path)
        if not success:
            print("错误: 设置 MAVEN_HOME 失败")
            sys.exit(1)
        print("[OK] MAVEN_HOME 设置完成")

    print()

    if not path_ok:
        print("添加 bin 目录到 PATH...")
        success = add_to_system_path(maven_bin_path)
        if not success:
            print("错误: 添加到 PATH 失败")
            sys.exit(1)
        print("[OK] PATH 添加完成")

    print()
    print("[OK] 配置完成!")

    # 尝试验证 Maven 安装
    print("\n尝试验证 Maven 安装...")
    try:
        result = subprocess.run(
            ['mvn', '-version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            first_line = result.stdout.splitlines()[0] if result.stdout else "OK"
            print(f"[OK] Maven 验证成功: {first_line}")
        else:
            print("[!] Maven 版本命令失败，需要重启终端后生效")
            print("    当前会话环境变量还没更新，这是正常的")
    except FileNotFoundError:
        print("[!] mvn 命令未找到，需要重启终端后生效")
        print("    当前会话环境变量还没更新，这是正常的")

    print()
    print("请注意:")
    print("  1. 需要重启命令提示符或终端才能看到环境变量变化")
    print("  2. 需要重启已打开的应用程序（如 Claude Code）才能使用新的环境变量")


if __name__ == "__main__":
    main()
