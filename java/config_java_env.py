#!/usr/bin/env python3
r"""
配置 Java JDK 环境变量

作用:
在 Windows 系统上配置 JDK 的环境变量，设置 JAVA_HOME 并将 bin 目录添加到系统 PATH。
检查当前环境，如果配置已经符合要求则跳过，避免重复设置。

默认 JDK 路径: D:\Softwares\Java\jdk1.8

用法:
python java/config_java_env.py [jdk_path]

参数:
  jdk_path  可选，指定 JDK 安装路径，默认使用 D:\Softwares\Java\jdk1.8
"""

import os
import sys
import subprocess
from typing import Optional, Tuple


# 默认 JDK 路径
DEFAULT_JDK_PATH = r"D:\Softwares\Java\jdk1.8"


def get_current_java_home() -> Optional[str]:
    """获取当前系统的 JAVA_HOME 环境变量"""
    return os.environ.get('JAVA_HOME')


def check_jdk_exists(jdk_path: str) -> bool:
    """检查 JDK 路径是否存在且包含 bin/java.exe"""
    java_exe = os.path.join(jdk_path, 'bin', 'java.exe')
    return os.path.exists(java_exe)


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


def find_jdk_in_path(current_path: str) -> list[str]:
    """在 PATH 中查找已有的 JDK bin 路径（任何包含 java.exe 的目录）"""
    entries = current_path.split(';')
    jdk_entries = []
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        # 识别可能的 JDK bin 路径
        entry_lower = entry.lower()
        if 'jdk' in entry_lower and 'bin' in entry_lower and os.path.exists(os.path.join(entry, 'java.exe')):
            jdk_entries.append(entry)
    return jdk_entries


def is_jdk_in_path(jdk_bin_path: str) -> bool:
    """检查 JDK bin 目录是否已经在 PATH 中"""
    current_path = get_system_path()
    jdk_bin_path = jdk_bin_path.replace('/', '\\').lower()
    current_path_lower = current_path.replace('/', '\\').lower()

    return jdk_bin_path in current_path_lower


def remove_jdk_from_path(current_path: str, jdk_bin_to_remove: str) -> str:
    """从 PATH 中移除指定的 JDK bin 路径"""
    entries = current_path.split(';')
    result = []
    jdk_bin_to_remove_lower = jdk_bin_to_remove.replace('/', '\\').lower()
    for entry in entries:
        entry_stripped = entry.strip()
        entry_lower = entry_stripped.replace('/', '\\').lower()
        if entry_lower != jdk_bin_to_remove_lower:
            result.append(entry_stripped)
    return ';'.join(result)


def set_java_home(jdk_path: str) -> bool:
    """设置系统环境变量 JAVA_HOME（需要管理员权限）"""
    result = subprocess.run(
        ['setx', '/M', 'JAVA_HOME', jdk_path],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def set_classpath(jdk_path: str) -> bool:
    r"""设置系统环境变量 CLASSPATH（需要管理员权限）
    配置: .;%JAVA_HOME%\lib\dt.jar;%JAVA_HOME%\lib\tools.jar
    """
    classpath = r".;%JAVA_HOME%\lib\dt.jar;%JAVA_HOME%\lib\tools.jar"
    result = subprocess.run(
        ['setx', '/M', 'CLASSPATH', classpath],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def get_current_classpath() -> Optional[str]:
    """获取当前 CLASSPATH 环境变量"""
    return os.environ.get('CLASSPATH')


def add_to_system_path(jdk_bin_path: str) -> bool:
    """将 JDK bin 目录添加到系统 PATH（需要管理员权限）
    支持多版本 JDK 并存，只检查当前路径是否已存在，不存在才追加，保留其他版本
    """
    # 获取当前 PATH
    current_path = get_system_path()

    # 检查是否已经存在当前 JDK
    if is_jdk_in_path(jdk_bin_path):
        print(f"[OK] {jdk_bin_path} 已经在 PATH 中，跳过")
        return True

    # 不存在就追加，保留其他所有路径（支持多版本并存）
    new_path = f"{current_path};{jdk_bin_path}"
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

    # 获取 JDK 路径
    if len(sys.argv) >= 2:
        jdk_path = sys.argv[1].strip()
    else:
        jdk_path = DEFAULT_JDK_PATH

    jdk_path = os.path.abspath(jdk_path)
    jdk_bin_path = os.path.join(jdk_path, 'bin')

    print(f"JDK 路径: {jdk_path}")
    print()

    # 检查 JDK 是否存在
    if not check_jdk_exists(jdk_path):
        print(f"错误: 在 {jdk_path} 未找到 JDK (缺少 bin/java.exe)")
        print("请确认 JDK 安装路径是否正确")
        sys.exit(1)

    # 检查管理员权限
    if not check_admin():
        print("错误: 需要管理员权限才能修改系统环境变量")
        print("请以管理员身份运行此脚本")
        sys.exit(1)

    # 检查当前 JAVA_HOME
    current_java_home = get_current_java_home()
    if current_java_home and os.path.abspath(current_java_home) == os.path.abspath(jdk_path):
        print(f"[OK] JAVA_HOME 已经是 {jdk_path}，无需修改")
        java_home_ok = True
    else:
        if current_java_home:
            print(f"  当前 JAVA_HOME: {current_java_home}")
        print(f"  将设置 JAVA_HOME: {jdk_path}")
        java_home_ok = False

    # 检查 PATH
    if is_jdk_in_path(jdk_bin_path):
        print(f"[OK] {jdk_bin_path} 已经在系统 PATH 中，无需修改")
        path_ok = True
    else:
        print(f"  需要将 {jdk_bin_path} 添加到系统 PATH")
        path_ok = False

    # 检查 CLASSPATH
    # 对于 JDK 1.8 需要配置 CLASSPATH 包含 dt.jar 和 tools.jar
    expected_classpath = ".;%JAVA_HOME%\\lib\\dt.jar;%JAVA_HOME%\\lib\\tools.jar"
    current_classpath = get_current_classpath()
    if current_classpath is not None and current_classpath.strip() != "":
        # 只要 CLASSPATH 已经存在就认为配置好了
        print(f"[OK] CLASSPATH 已经配置，无需修改")
        classpath_ok = True
    else:
        print(f"  将设置 CLASSPATH: {expected_classpath}")
        classpath_ok = False

    print()

    if java_home_ok and path_ok and classpath_ok:
        print("[OK] 环境配置已经完成，无需修改")
        sys.exit(0)

    # 开始配置
    print("开始配置环境变量...")
    print()

    if not java_home_ok:
        print("设置 JAVA_HOME...")
        success = set_java_home(jdk_path)
        if not success:
            print("错误: 设置 JAVA_HOME 失败")
            sys.exit(1)
        print("[OK] JAVA_HOME 设置完成")

    print()

    if not path_ok:
        print("添加 bin 目录到 PATH...")
        success = add_to_system_path(jdk_bin_path)
        if not success:
            print("错误: 添加到 PATH 失败")
            sys.exit(1)
        print("[OK] PATH 添加完成")

    print()

    if not classpath_ok:
        print("设置 CLASSPATH...")
        success = set_classpath(jdk_path)
        if not success:
            print("错误: 设置 CLASSPATH 失败")
            sys.exit(1)
        print("[OK] CLASSPATH 设置完成")

    print()
    print("[OK] 配置完成!")
    print("请注意:")
    print("  1. 需要重启命令提示符或终端才能看到环境变量变化")
    print("  2. 需要重启已打开的应用程序（如 Claude Code）才能使用新的环境变量")


if __name__ == "__main__":
    main()
