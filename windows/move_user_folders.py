#!/usr/bin/env python3
r"""
修改 Windows 用户默认文件夹位置 - 移动到其他分区

作用:
修改 Windows 系统用户文件夹（Documents, Downloads, Pictures, Music, Videos）
的存储位置到指定路径，比如从 C 盘移动到 D/E 盘，节省系统盘空间。

修改通过注册表完成，需要重启电脑或注销后生效。

支持的系统文件夹:
  - Documents 文档
  - Downloads 下载
  - Pictures 图片
  - Music 音乐
  - Videos 视频
  - Desktop 桌面

用法:
  python windows/move_user_folders.py <folder-name> <new-path>
  python windows/move_user_folders.py --list
  python windows/move_user_folders.py --all <base-path>

参数:
  folder-name  要移动的文件夹名称 (documents|downloads|pictures|music|videos|desktop
  new-path    新的位置（完整路径，比如 E:\Documents
  --list      列出当前所有文件夹的位置
  --all <path 将所有文件夹移动到指定基础路径下 <base-path\<folder-name>

示例:
  python windows/move_user_folders.py --list
  python windows/move_user_folders.py documents E:\Documents
  python windows/move_user_folders.py --all E:\User\fanlei

注意:
  - 需要**管理员权限**运行
  - 修改后需要注销重新登录或重启电脑才能生效
  - 建议先备份重要数据再操作
  - 脚本会自动创建目标路径，如果路径包含用户名
"""

import os
import sys
import subprocess
from typing import Dict, Optional, List
import winreg

# 系统文件夹名称映射
# 支持两种方式：CLSID (Known Folder) 和传统名称
# 来源: HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders
FOLDER_MAPPING = {
    'documents': [
        '{F7D421B-529B-41A2-A757-285D560E07B9}',  # Known Folder CLSID
        'Personal',  # Legacy name
    ],
    'downloads': [
        '{374DE290-123F-4565-9164-39C4925E467B}',  # Known Folder CLSID
        '{7D83EE9B-2244-4E70-B1F5-5393042AF1E4}',  # Alternative CLSID
        'Downloads',  # Legacy name
    ],
    'pictures': [
        '{DD34571F-9076-411C-A520-AA6DC4397B10}',  # Known Folder CLSID
        'My Pictures',  # Legacy name
    ],
    'music': [
        '{1CF1260C-4DF3-5CDB-988B-9F50413504B}',  # Known Folder CLSID
        'My Music',  # Legacy name
    ],
    'videos': [
        '{48D507F1-3116-4AC3-9F08-A7E27B504107}',  # Known Folder CLSID
        'My Video',  # Legacy name
    ],
    'desktop': [
        '{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}',  # Known Folder CLSID
        'Desktop',  # Legacy name
    ],
    'favorites': [
        '{1777F761-68AD-4D8A-87BD-30B759FA33DD}',  # Known Folder CLSID
        'Favorites',  # Legacy name
    ],
}

FOLDER_DISPLAY = {
    'documents': 'Documents',
    'downloads': 'Downloads',
    'pictures': 'Pictures',
    'music': 'Music',
    'videos': 'Videos',
    'desktop': 'Desktop',
    'favorites': 'Favorites',
}


def check_admin() -> bool:
    """检查是否有管理员权限"""
    try:
        # 尝试读取注册表系统项
        subprocess.run(
            ['reg', 'query', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment'],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_current_folder_location(folder_name: str) -> Optional[str]:
    """获取当前文件夹位置从注册表
    尝试多个键名（CLSID 和传统名称）
    """
    keys = FOLDER_MAPPING.get(folder_name.lower())
    if not keys:
        return None

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'
        )
        for name in keys:
            try:
                value, _ = winreg.QueryValueEx(key, name)
                winreg.CloseKey(key)
                return value
            except Exception:
                continue
        winreg.CloseKey(key)
        return None
    except Exception:
        return None


def set_folder_location(folder_name: str, new_path: str) -> bool:
    """设置新位置到注册表
    尝试多个键名（CLSID 和传统名称）
    """
    keys = FOLDER_MAPPING.get(folder_name.lower())
    if not keys:
        return False

    # 确保路径是绝对路径
    new_path = os.path.abspath(new_path)

    # 创建目标目录
    try:
        os.makedirs(new_path, exist_ok=True)
        print(f"[OK] 确保目标目录已创建/存在: {new_path}")
    except Exception as e:
        print(f"[!] 创建目标目录失败: {e}")
        return False

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders',
            0,
            winreg.KEY_SET_VALUE
        )
        # 对每个存在的键设置值
        success_count = 0
        for name in keys:
            try:
                winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, new_path)
                print(f"[OK] 注册表已更新: {name} -> {new_path}")
                success_count += 1
            except Exception:
                continue
        winreg.CloseKey(key)
        return success_count > 0
    except Exception as e:
        print(f"[!] 修改注册表失败: {e}")
        return False


def list_all_locations() -> None:
    """列出所有文件夹当前位置"""
    print("当前系统文件夹位置:")
    print("=" * 60)
    for name, display in FOLDER_DISPLAY.items():
        current = get_current_folder_location(name)
        if current:
            # 展开环境变量比如 %USERPROFILE%
            current = os.path.expandvars(current)
            print(f"  {display:<12} : {current}")
        else:
            print(f"  {display:<12} : 无法读取")
    print("=" * 60)


def move_all_folders(base_path: str) -> bool:
    """将所有文件夹移动到基础路径下"""
    base_path = os.path.abspath(base_path)
    print(f"将所有文件夹移动到基础路径: {base_path}")
    print()

    all_ok = True

    for name, display in FOLDER_DISPLAY.items():
        target = os.path.join(base_path, display)
        print(f"正在移动 {display} -> {target}")
        if not set_folder_location(name, target):
            all_ok = False
        print()

    return all_ok


def move_single_folder(folder_name: str, new_path: str) -> bool:
    """移动单个文件夹到新位置"""
    folder_name = folder_name.lower()
    if folder_name not in FOLDER_MAPPING:
        print(f"错误: 不支持的文件夹名称 {folder_name}")
        print(f"支持的文件夹: {', '.join(FOLDER_DISPLAY.keys())}")
        return False

    current = get_current_folder_location(folder_name)
    if current:
        current_expanded = os.path.expandvars(current)
        print(f"当前位置: {FOLDER_DISPLAY[folder_name]} = {current_expanded}")
    else:
        print(f"警告: 无法读取当前位置，继续操作...")

    new_path = os.path.abspath(new_path)
    print(f"新位置: {FOLDER_DISPLAY[folder_name]} = {new_path}")
    print()

    return set_folder_location(folder_name, new_path)


def main():
    # 处理帮助参数
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
        print(__doc__)
        sys.exit(0)

    # 检查管理员权限
    if not check_admin():
        print("错误: 需要管理员权限才能修改注册表")
        print("请以管理员身份运行此脚本")
        sys.exit(1)

    # 列出当前位置
    if sys.argv[1] == '--list':
        list_all_locations()
        sys.exit(0)

    # 移动所有文件夹
    if sys.argv[1] == '--all':
        if len(sys.argv) < 3:
            print("错误: --all 需要指定基础路径参数")
            print("示例: python move_user_folders.py --all E:\\User\\username")
            sys.exit(1)
        base_path = sys.argv[2]
        success = move_all_folders(base_path)
        if success:
            print()
            print("[OK] 所有文件夹移动完成!")
        else:
            print()
            print("[!] 部分文件夹移动失败")
            sys.exit(1)
    else:
        # 移动单个文件夹
        if len(sys.argv) < 3:
            print("错误: 需要指定文件夹名称和新路径")
            print("示例: python move_user_folders.py documents E:\\Documents")
            sys.exit(1)
        folder_name = sys.argv[1]
        new_path = sys.argv[2]
        success = move_single_folder(folder_name, new_path)
        if success:
            print()
            print("[OK] 移动完成!")
        else:
            print()
            print("[!] 移动失败")
            sys.exit(1)

    print()
    print("请注意:")
    print("  1. 需要注销当前用户并重新登录才能生效")
    print("  2. 或者重启电脑后生效")
    print("  3. 原文件夹中的文件需要手动复制到新位置")


if __name__ == "__main__":
    main()
