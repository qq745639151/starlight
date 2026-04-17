#!/usr/bin/env python3
"""
切换 Claude Code 的 Anthropic API 密钥配置

作用:
读取 Claude Code 的 settings.json 配置文件，只修改与 API 相关的配置项，
保留原有其他配置（如 permissions、plugins、statusLine 等）不变，
提供三组预定义配置供切换选择。

三组预定义配置:
1. 字节火山引擎 ark-code-latest (密钥1)
2. 字节火山引擎 ark-code-latest (密钥2)
3. MiniMax MiniMax-M2.7

用法:
python claude/switch_anthropic_key.py [选项]

选项:
  -h, --help              显示帮助信息
  -l, --list              列出所有可用配置
  -s, --select <index>   直接选择指定索引的配置（0, 1, 2）
  如果不带选项，会交互式提示选择
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional

# 预定义的三组配置
CONFIGURATIONS = [
    {
        "name": "字节火山引擎 - ark-code-latest (密钥1 - 公司)",
        "ANTHROPIC_BASE_URL": "https://ark.cn-beijing.volces.com/api/coding",
        "ANTHROPIC_AUTH_TOKEN": "5290f091-0b95-4f5d-b6b3-2c60c5dbb5c9",
        "ANTHROPIC_MODEL": "ark-code-latest",
        "ANTHROPIC_DEFAULT_SONNET_MODEL": "ark-code-latest",
        "ANTHROPIC_DEFAULT_OPUS_MODEL": "ark-code-latest",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "ark-code-latest",
        "root_model": "ark-code-latest"
    },
    {
        "name": "字节火山引擎 - ark-code-latest (密钥2 - 个人)",
        "ANTHROPIC_BASE_URL": "https://ark.cn-beijing.volces.com/api/coding",
        "ANTHROPIC_AUTH_TOKEN": "881b5add-1784-40b1-bb78-8d4f400addcb",
        "ANTHROPIC_MODEL": "ark-code-latest",
        "ANTHROPIC_DEFAULT_SONNET_MODEL": "ark-code-latest",
        "ANTHROPIC_DEFAULT_OPUS_MODEL": "ark-code-latest",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "ark-code-latest",
        "root_model": "ark-code-latest"
    },
    {
        "name": "MiniMax - MiniMax-M2.7",
        "ANTHROPIC_BASE_URL": "https://api.minimaxi.com/anthropic",
        "ANTHROPIC_AUTH_TOKEN": "sk-cp-aXXPuAoOkhrcndd7tAEflE-hpCTLjGQW-wYSVv0PgVm-t0iXYK0ADdaIQr3zV-fGCHblYcvnkiOFIV0se9ZJdWMmjx_mEyXSmxzRhJoZNI87ZOHpGPJdkAs",
        "ANTHROPIC_MODEL": "MiniMax-M2.7",
        "ANTHROPIC_DEFAULT_SONNET_MODEL": "MiniMax-M2.7",
        "ANTHROPIC_DEFAULT_OPUS_MODEL": "MiniMax-M2.7",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "MiniMax-M2.7",
        "root_model": "MiniMax-M2.7"
    }
]


def get_settings_path() -> Path:
    """获取 Claude Code settings.json 的路径"""
    # 常见的 Windows 路径
    possible_paths = [
        Path.home() / ".claude" / "settings.json",
        Path("C:/Users") / os.getlogin() / ".claude" / "settings.json",
        Path("C:\\Users\\qq745\\.claude\\settings.json"),
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # 如果都找不到，让用户输入
    print("未自动找到 settings.json 文件，请输入完整路径：")
    custom_path = input().strip()
    return Path(custom_path)


def load_settings(settings_path: Path) -> Dict:
    """加载现有 settings.json"""
    with open(settings_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_settings(settings_path: Path, settings: Dict) -> None:
    """保存 settings.json，保持原格式（带缩进）"""
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def apply_config(settings: Dict, config: Dict) -> Dict:
    """应用选定的配置，只修改相关字段，保留其他配置不变"""
    # 修改 env 中的配置
    if "env" not in settings:
        settings["env"] = {}

    settings["env"]["ANTHROPIC_BASE_URL"] = config["ANTHROPIC_BASE_URL"]
    settings["env"]["ANTHROPIC_AUTH_TOKEN"] = config["ANTHROPIC_AUTH_TOKEN"]
    settings["env"]["ANTHROPIC_MODEL"] = config["ANTHROPIC_MODEL"]
    settings["env"]["ANTHROPIC_DEFAULT_SONNET_MODEL"] = config["ANTHROPIC_DEFAULT_SONNET_MODEL"]
    settings["env"]["ANTHROPIC_DEFAULT_OPUS_MODEL"] = config["ANTHROPIC_DEFAULT_OPUS_MODEL"]
    settings["env"]["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = config["ANTHROPIC_DEFAULT_HAIKU_MODEL"]

    # 修改根级别的 model 字段
    settings["model"] = config["root_model"]

    return settings


def list_configs() -> None:
    """列出所有可用配置"""
    print("可用配置：")
    for i, config in enumerate(CONFIGURATIONS):
        print(f"  [{i}] {config['name']}")
        print(f"      URL: {config['ANTHROPIC_BASE_URL']}")
        print(f"      Model: {config['ANTHROPIC_MODEL']}")
        print(f"      Key: {config['ANTHROPIC_AUTH_TOKEN'][:12]}...")
        print()


def interactive_select() -> int:
    """交互式选择配置"""
    list_configs()
    print("请选择要切换到的配置（输入索引 0-2）：")
    while True:
        try:
            choice = int(input().strip())
            if 0 <= choice < len(CONFIGURATIONS):
                return choice
            else:
                print(f"请输入 0 到 {len(CONFIGURATIONS) - 1} 之间的数字：")
        except ValueError:
            print("请输入有效的数字：")


def main():
    # 处理命令行参数
    if len(sys.argv) == 1:
        # 交互式
        selected_index = interactive_select()
    elif sys.argv[1] in ['-h', '--help']:
        print(__doc__)
        sys.exit(0)
    elif sys.argv[1] in ['-l', '--list']:
        list_configs()
        sys.exit(0)
    elif sys.argv[1] in ['-s', '--select'] and len(sys.argv) == 3:
        try:
            selected_index = int(sys.argv[2])
            if not 0 <= selected_index < len(CONFIGURATIONS):
                print(f"错误：索引必须在 0 到 {len(CONFIGURATIONS) - 1} 之间")
                sys.exit(1)
        except ValueError:
            print("错误：索引必须是数字")
            sys.exit(1)
    else:
        print(__doc__)
        sys.exit(1)

    # 获取 settings.json 路径
    settings_path = get_settings_path()
    print(f"\n找到配置文件：{settings_path}")

    # 备份原配置
    settings = load_settings(settings_path)
    backup_path = settings_path.with_suffix('.json.bak')
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    print(f"已备份原配置到：{backup_path}")

    # 显示当前配置
    current_key = settings.get("env", {}).get("ANTHROPIC_AUTH_TOKEN", "Unknown")
    current_model = settings.get("model", "Unknown")
    print(f"\n当前配置：")
    print(f"  模型：{current_model}")
    print(f"  密钥：{current_key[:12]}...")

    # 应用新配置
    selected_config = CONFIGURATIONS[selected_index]
    print(f"\n将要切换到：")
    print(f"  [{selected_index}] {selected_config['name']}")
    print(f"  URL: {selected_config['ANTHROPIC_BASE_URL']}")
    print(f"  模型：{selected_config['root_model']}")
    print(f"  密钥：{selected_config['ANTHROPIC_AUTH_TOKEN'][:12]}...")

    print("\n直接切换中...")
    new_settings = apply_config(settings.copy(), selected_config)
    save_settings(settings_path, new_settings)

    print("\n✓ 切换完成！")
    print("请重启 Claude Code 以使新配置生效。")


if __name__ == "__main__":
    main()
