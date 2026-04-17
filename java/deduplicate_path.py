#!/usr/bin/env python3
"""
去重系统 PATH 环境变量

移除重复的 PATH 条目，保留第一个出现的顺序，清理空条目。
"""

import os
import subprocess
import sys
sys.path.insert(0, os.path.dirname(__file__))

from config_java_env import get_system_path


def main():
    # 获取当前系统 PATH
    current_path = get_system_path()

    # 分割并去重
    entries = [p.strip() for p in current_path.split(';') if p.strip()]
    seen = set()
    unique_entries = []
    duplicates = []

    for p in entries:
        p_lower = p.lower()
        if p_lower in seen:
            duplicates.append(p)
        else:
            seen.add(p_lower)
            unique_entries.append(p)

    print(f"原始 PATH: {len(entries)} 个条目")
    print(f"去重后: {len(unique_entries)} 个条目")
    print(f"发现重复: {len(duplicates)} 个")
    print()

    if duplicates:
        print("重复条目:")
        for d in duplicates:
            print(f"  - {d}")
        print()

    new_path = ";".join(unique_entries)

    print("新 PATH 将包含以下条目:")
    for i, entry in enumerate(unique_entries, 1):
        print(f"  [{i:2d}] {entry}")

    print()
    print("WARNING: 这将覆盖系统 PATH 环境变量，请确认以上列表正确！")
    print("输入 'YES' 继续，其他任意键取消：")

    try:
        confirm = input().strip()
    except (EOFError, KeyboardInterrupt):
        print("\n已取消")
        sys.exit(1)

    if confirm != 'YES':
        print("已取消")
        sys.exit(0)

    # 写入系统 PATH
    print("\n写入中...")
    result = subprocess.run(
        ['setx', '/M', 'Path', new_path],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("\n[OK] 成功去重并写入系统 PATH!")
        print("请重启电脑或重启终端以使更改生效。")
    else:
        print(f"\n错误: 写入失败")
        print(f"返回码: {result.returncode}")
        print(f"输出: {result.stderr}")
        sys.exit(1)


if __name__ == "__main__":
    main()
