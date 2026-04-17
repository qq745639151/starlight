#!/usr/bin/env python3
r"""
设置系统环境变量 TRILIUM_DATA_DIR - 系统环境变量方式

作用:
在 Windows 系统上设置永久的系统环境变量 TRILIUM_DATA_DIR，
指定 Trilium Notes 数据存储目录。设置后，Trilium 启动时会
自动读取这个环境变量并使用指定目录存储数据，**无需修改任何启动脚本**。

这是**系统环境变量方式**，另一种方式是修改 Trilium 启动脚本设置环境变量，
请参见 `config_trilium_data_dir.py`。

默认数据目录: 系统默认 Documents\Trilium-data (自动检测，支持 Documents 移动到其他分区)

用法:
python trilium/set_trilium_data_dir_env.py [data_directory]

参数:
  data_directory  可选，指定数据目录路径，默认使用系统 Documents\Trilium-data

另见:
  config_trilium_data_dir.py - 修改 Trilium 启动脚本方式，不需要设置系统环境变量
"""

import os
import sys
import subprocess
from typing import Optional


def get_documents_trilium_path() -> str:
    """获取系统默认 Documents 目录下的 Trilium-data 路径
    使用 Windows Shell API 获取正确的 Documents 位置，即使它被移动到其他分区
    """
    try:
        # 使用 powershell 获取系统真实的 Documents 目录位置
        # 这能正确处理用户将 Documents 移动到其他分区的情况
        result = subprocess.run(
            ['powershell', '-Command', '[Environment]::GetFolderPath(\"MyDocuments\")'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            docs_path = result.stdout.strip()
            if docs_path:
                return os.path.join(docs_path, 'Trilium-data')
    except Exception:
        pass

    # 回退方案：从 USERPROFILE 拼接
    user_profile = os.environ.get('USERPROFILE', r'C:\Users\%USERNAME%')
    return os.path.join(user_profile, 'Documents', 'Trilium-data')


def get_current_trilium_data_dir() -> Optional[str]:
    """获取当前系统的 TRILIUM_DATA_DIR 环境变量"""
    # 尝试从注册表读取系统环境变量
    result = subprocess.run(
        ['reg', 'query', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', '/v', 'TRILIUM_DATA_DIR'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        # 从当前环境读取
        return os.environ.get('TRILIUM_DATA_DIR')

    # 解析注册表输出
    lines = result.stdout.splitlines()
    for line in lines:
        line = line.rstrip('\n')
        if 'TRILIUM_DATA_DIR' in line and 'REG_' in line:
            reg_index = line.find('REG_')
            space_after_reg = line.find(' ', reg_index)
            if space_after_reg != -1:
                value = line[space_after_reg + 1:].rstrip().lstrip()
                return value

    return os.environ.get('TRILIUM_DATA_DIR')


def set_trilium_data_dir(data_dir: str) -> bool:
    """设置系统环境变量 TRILIUM_DATA_DIR（需要管理员权限）"""
    data_dir_abs = os.path.abspath(data_dir)
    # 使用 reg add 而不是 setx，避免 setx 的 1024 字符截断限制
    result = subprocess.run(
        ['reg', 'add', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', '/v', 'TRILIUM_DATA_DIR', '/t', 'REG_SZ', '/d', data_dir_abs, '/f'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def ensure_data_dir_exists(data_dir: str) -> bool:
    """确保数据目录存在，如果不存在则创建"""
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir, exist_ok=True)
            print(f"[OK] 已创建数据目录: {data_dir}")
        except Exception as e:
            print(f"错误: 创建数据目录失败: {e}")
            return False
    else:
        print(f"[OK] 数据目录已存在: {data_dir}")
    return True


def check_admin() -> bool:
    """检查是否有管理员权限"""
    try:
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

    # 获取数据目录路径
    if len(sys.argv) >= 2:
        data_dir = sys.argv[1].strip()
    else:
        data_dir = get_documents_trilium_path()

    data_dir = os.path.abspath(data_dir)

    print(f"TRILIUM_DATA_DIR 将设置为: {data_dir}")
    print()

    # 检查管理员权限
    if not check_admin():
        print("错误: 需要管理员权限才能修改系统环境变量")
        print("请以管理员身份运行此脚本")
        sys.exit(1)

    # 检查当前 TRILIUM_DATA_DIR
    current_value = get_current_trilium_data_dir()
    if current_value and os.path.abspath(current_value) == data_dir:
        print(f"[OK] TRILIUM_DATA_DIR 已经是 {data_dir}，无需修改")
        print()
        print("请注意:")
        print("  1. 需要重启命令提示符或终端才能看到环境变量变化")
        print("  2. 需要重启已打开的应用程序（如 Trilium、Claude Code）才能使用新的环境变量")
        sys.exit(0)

    # 显示当前值
    if current_value:
        print(f"  当前 TRILIUM_DATA_DIR: {current_value}")
    print(f"  将设置为: {data_dir}")
    print()

    # 确保数据目录存在
    if not ensure_data_dir_exists(data_dir):
        sys.exit(1)

    print()

    # 设置环境变量
    print("正在设置 TRILIUM_DATA_DIR...")
    success = set_trilium_data_dir(data_dir)
    if not success:
        print("错误: 设置 TRILIUM_DATA_DIR 失败")
        sys.exit(1)

    print("[OK] 配置完成!")
    print()
    print("请注意:")
    print("  1. 需要重启命令提示符或终端才能看到环境变量变化")
    print("  2. 需要重启已打开的应用程序（如 Trilium、Claude Code）才能使用新的环境变量")
    print(f"  3. 之后 Trilium 会自动使用 {data_dir} 作为数据存储目录")


if __name__ == "__main__":
    main()
