#!/usr/bin/env python3
r"""
配置 Trilium Notes 数据存储目录

作用:
修改 Trilium 启动脚本，将默认数据存储目录从 `./trilium-data` 修改为用户 Documents 目录下的 `Trilium-data`。
这样数据会保存在文档目录，即使重装系统 Trilium 数据也不会丢失。

默认 Trilium 安装路径: D:\Softwares\Trilium
默认目标数据目录: %USERPROFILE%\Documents\Trilium-data

用法:
python trilium/config_trilium_data_dir.py [trilium_path]

参数:
  trilium_path  可选，指定 Trilium 安装路径，默认使用 D:\Softwares\Trilium
"""

import os
import sys
import subprocess
from typing import Optional


# 默认 Trilium 安装路径
DEFAULT_TRILIUM_PATH = r"D:\Softwares\Trilium"


def get_documents_trilium_path() -> str:
    """获取 Documents 目录下的 Trilium-data 路径"""
    user_profile = os.environ.get('USERPROFILE', r'C:\Users\%USERNAME%')
    return os.path.join(user_profile, 'Documents', 'Trilium-data')


def check_trilium_exists(trilium_path: str) -> bool:
    """检查 Trilium 安装路径是否存在并且包含 trilium.exe"""
    trilium_exe = os.path.join(trilium_path, 'trilium.exe')
    return os.path.exists(trilium_exe)


def backup_file(file_path: str) -> bool:
    """备份文件，添加 .bak 后缀"""
    if os.path.exists(file_path) and not os.path.exists(file_path + '.bak'):
        try:
            with open(file_path, 'rb') as src:
                with open(file_path + '.bak', 'wb') as dst:
                    dst.write(src.read())
            print(f"[OK] 已备份: {file_path}.bak")
            return True
        except Exception as e:
            print(f"[!] 备份失败: {e}")
            return False
    return True


def modify_portable_bat(trilium_path: str, target_data_dir: str) -> bool:
    """修改 trilium-portable.bat，更改数据目录"""
    bat_path = os.path.join(trilium_path, 'trilium-portable.bat')

    if not os.path.exists(bat_path):
        print(f"错误: 未找到 {bat_path}")
        return False

    # 读取原始内容
    with open(bat_path, 'r', encoding='gbk') as f:
        content = f.read()

    # 检查是否已经修改
    if 'Trilium-data' in content and 'Documents' in content:
        print("[OK] trilium-portable.bat 已经配置为 Documents/Trilium-data，跳过")
        return True

    # 备份
    backup_file(bat_path)

    # 修改：将 ./trilium-data 改为目标路径
    # powershell 行
    content = content.replace(
        "powershell -ExecutionPolicy Bypass -NonInteractive -NoLogo -Command \"Set-Item -Path Env:TRILIUM_DATA_DIR -Value './trilium-data'; ./trilium.exe\"",
        f"powershell -ExecutionPolicy Bypass -NonInteractive -NoLogo -Command \"Set-Item -Path Env:TRILIUM_DATA_DIR -Value '{target_data_dir}'; ./trilium.exe\""
    )

    # batch 行
    content = content.replace(
        "SET TRILIUM_DATA_DIR=%DIR%\\trilium-data",
        f"SET TRILIUM_DATA_DIR={target_data_dir}"
    )

    # 写入修改后的内容
    with open(bat_path, 'w', encoding='gbk') as f:
        f.write(content)

    print(f"[OK] trilium-portable.bat 已修改，数据目录 -> {target_data_dir}")
    return True


def create_custom_bat(trilium_path: str, target_data_dir: str) -> bool:
    """创建一个自定义启动脚本 trilium-documents.bat"""
    custom_bat_path = os.path.join(trilium_path, 'trilium-documents.bat')

    if os.path.exists(custom_bat_path):
        print("[OK] trilium-documents.bat 已存在，跳过")
        return True

    bat_content = f'''@echo off
:: 启动 Trilium，数据存储在 Documents\\Trilium-data

:: Try to get powershell to launch Trilium since it deals with UTF-8 characters in current path
:: If there's no powershell available, fallback to unicode enabled command interpreter

WHERE powershell.exe > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 GOTO BATCH ELSE GOTO POWERSHELL

:POWERSHELL
powershell -ExecutionPolicy Bypass -NonInteractive -NoLogo -Command "Set-Item -Path Env:TRILIUM_DATA_DIR -Value '{target_data_dir}'; ./trilium.exe"
GOTO END

:BATCH
:: Make sure we support UTF-8 characters
chcp 65001

:: 设置数据目录到 Documents\\Trilium-data
SET TRILIUM_DATA_DIR={target_data_dir}
cd "%~dp0"
start trilium.exe
GOTO END

:END
'''

    with open(custom_bat_path, 'w', encoding='gbk') as f:
        f.write(bat_content)

    print(f"[OK] 已创建自定义启动脚本: {custom_bat_path}")
    return True


def ensure_data_dir_exists(target_data_dir: str) -> bool:
    """确保数据目录存在，如果不存在则创建"""
    if not os.path.exists(target_data_dir):
        try:
            os.makedirs(target_data_dir, exist_ok=True)
            print(f"[OK] 已创建数据目录: {target_data_dir}")
        except Exception as e:
            print(f"错误: 创建数据目录失败: {e}")
            return False
    else:
        print(f"[OK] 数据目录已存在: {target_data_dir}")
    return True


def main():
    # 处理帮助参数
    if len(sys.argv) >= 2 and sys.argv[1] in ['-h', '--help']:
        print(__doc__)
        sys.exit(0)

    # 获取 Trilium 路径
    if len(sys.argv) >= 2:
        trilium_path = sys.argv[1].strip()
    else:
        trilium_path = DEFAULT_TRILIUM_PATH

    trilium_path = os.path.abspath(trilium_path)
    target_data_dir = get_documents_trilium_path()

    print(f"Trilium 安装路径: {trilium_path}")
    print(f"目标数据目录: {target_data_dir}")
    print()

    # 检查 Trilium 是否存在
    if not check_trilium_exists(trilium_path):
        print(f"错误: 在 {trilium_path} 未找到 Trilium (缺少 trilium.exe)")
        print("请确认 Trilium 安装路径是否正确")
        sys.exit(1)

    # 确保数据目录存在
    if not ensure_data_dir_exists(target_data_dir):
        sys.exit(1)

    print()

    # 修改 trilium-portable.bat
    if not modify_portable_bat(trilium_path, target_data_dir):
        print("警告: 修改 trilium-portable.bat 失败")

    print()

    # 创建自定义启动脚本
    if not create_custom_bat(trilium_path, target_data_dir):
        print("错误: 创建自定义启动脚本失败")
        sys.exit(1)

    print()
    print("[OK] 配置完成!")
    print()
    print("现在你可以通过两种方式启动 Trilium:")
    print(f"  1. 使用修改后的: {trilium_path}\\trilium-portable.bat")
    print(f"  2. 使用新建的:   {trilium_path}\\trilium-documents.bat (推荐，专门用于 Documents 数据目录启动)")
    print()
    print(f"所有数据都会存储到: {target_data_dir}")
    print("即使重装系统，只要 Documents 分区不格式化，数据都会保留")


if __name__ == "__main__":
    main()
