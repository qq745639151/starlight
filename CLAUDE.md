# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a personal utility repository for automating development environment setup.

## Directory Structure

### python/
Python 环境配置脚本

- `python_package_clear.py` — 清理 Python 全局环境中的第三方包，保留 pip, wheel, setuptools
- `pip_use_tsinghua_source.py` — 配置 pip 使用清华镜像源加速下载

### npm/
npm 配置脚本

- `npm_config.py` — 配置 npm 全局路径、缓存目录、淘宝镜像源，并将 node_global/bin 添加到用户 PATH

### tortoise/
TortoiseGit 配置

- `fix_tortoise_overlay.reg` — 解决 TortoiseGit 图标覆盖不显示的问题

### claude/
Claude Code API 配置切换

- `switch_anthropic_key.py` — 在三组预定义 API 密钥之间切换，只修改相关配置项，保留其他原有设置不变

### java/
Java JDK 环境配置

- `config_java_env.py` — 配置 JDK 系统环境变量，设置 JAVA_HOME 并将 bin 目录添加到系统 PATH，自动检查已存在的配置避免重复设置，支持多版本 JDK 并存
- `deduplicate_path.py` — 移除系统 PATH 中的重复条目，保留原始顺序

### uv/
uv Python 包管理器安装

- `install_uv.py` — 通过 pip 自动安装 uv，检测是否已安装，已安装就跳过

## Scripts

```bash
# 清理 Python 第三方包
python python/python_package_clear.py

# 配置 pip 镜像源
python python/pip_use_tsinghua_source.py

# 配置 npm（创建全局目录 + 淘宝镜像源 + PATH）
python npm/npm_config.py

# 修复 TortoiseGit 图标覆盖
reg import tortoise/fix_tortoise_overlay.reg
```

## Development Notes

- No test framework configured
- No build system
- No CI/CD
- Python files follow PEP 8 with type annotations
