#!/usr/bin/env python3
r"""
修复 TortoiseGit 图标覆盖不显示问题

作用:
自动导入注册表修复 TortoiseGit 图标覆盖，解决图标覆盖不显示的问题。
这是 Windows 上 TortoiseGit 的常见问题。

用法:
  python tortoisegit/fix_overlay_icons.py

注意:
  - 需要**管理员权限**运行
  - 脚本会自动重启 Windows 资源管理器让修改立即生效
  - 只需要运行一次，修复后永久生效
"""

import os
import sys
import subprocess


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


def import_reg() -> bool:
    """导入注册表文件"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    reg_file = os.path.join(script_dir, 'fix_tortoise_overlay.reg')

    if not os.path.exists(reg_file):
        print(f"错误: 注册表文件不存在: {reg_file}")
        return False

    print(f"正在导入注册表: {reg_file}")
    result = subprocess.run(
        ['reg', 'import', reg_file],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("[OK] 注册表导入成功")
        return True
    else:
        print(f"[!] 注册表导入失败: {result.stderr}")
        return False


def restart_explorer() -> None:
    """重启 Windows 资源管理器让修改生效"""
    print("\n正在重启 Windows 资源管理器...")
    try:
        # 关闭 explorer
        subprocess.run(['taskkill', '/F', '/IM', 'explorer.exe'], capture_output=True)
        # 重新启动 explorer
        subprocess.Popen(['explorer.exe'])
        print("[OK] Windows 资源管理器已重启")
        print("现在应该能看到 TortoiseGit 图标覆盖了")
    except Exception as e:
        print(f"[!] 重启 Windows 资源管理器失败: {e}")
        print("请手动重启电脑或重启资源管理器")


def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ['-h', '--help']:
        print(__doc__)
        sys.exit(0)

    # 检查管理员权限
    if not check_admin():
        print("错误: 需要管理员权限才能修改注册表")
        print("请以管理员身份运行此脚本")
        sys.exit(1)

    # 导入注册表
    if not import_reg():
        sys.exit(1)

    # 重启 explorer
    restart_explorer()

    print()
    print("[OK] 修复完成!")


if __name__ == "__main__":
    main()
