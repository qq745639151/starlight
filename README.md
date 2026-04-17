# Starlight

<img align="right" width="150" height="150" src="https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/120606-Moon-Starlight-Panda.jpg/220px-120606-Moon-Starlight-Panda.jpg">

个人开发环境自动化配置工具。

这是一个收集了各种 Windows 开发环境配置脚本的仓库，用于快速搭建新开发环境，自动配置环境变量、镜像源等。

## 📁 目录结构

```
starlight/
├── bootstrap/          # 一键全自动配置
│   └── bootstrap_all.py    # 一键安装配置所有常用开发工具
├── python/             # Python 相关
│   ├── python_package_clear.py  # 清理全局环境第三方包，保留 pip wheel setuptools
│   └── pip_use_tsinghua_source.py  # 配置 pip 使用清华镜像源
├── npm/                # Node.js/npm 相关
│   └── npm_config.py  # 配置 npm 全局路径到安装目录、淘宝镜像源、添加 PATH
├── java/               # Java JDK 相关
│   ├── config_java_env.py  # 配置 JAVA_HOME 和 PATH，自动移除旧版本
│   └── deduplicate_path.py  # 移除系统 PATH 中的重复条目
├── maven/              # Maven 相关
│   ├── config_maven.py  # 配置 MAVEN_HOME 和 PATH，自动移除旧版本
│   └── settings.xml    # 预置阿里云镜像配置模板
├── go/                 # Go 语言相关
│   ├── config_go_env.py  # 配置 GOROOT 和系统 PATH，自动移除旧版本
│   ├── config_go_paths.py  # 配置 GOPATH/GOMODCACHE/GOCACHE 到 Go 安装目录 + 国内代理
│   └── move_go_data_dirs.py  # 迁移 C盘 数据到 D盘 Go 安装目录
├── mingw/              # MinGW-w64 C/C++ 编译器
│   └── config_mingw_env.py  # 配置 MINGW_HOME 和 PATH
├── uv/                 # uv Python 包管理器
│   └── install_uv.py  # 自动通过 pip 安装 uv
├── tortoisegit/        # TortoiseGit 相关
│   ├── fix_overlay_icons.py  # 自动修复图标覆盖不显示问题
│   └── fix_tortoise_overlay.reg  # 注册表修复文件
├── claude/             # Claude Code 相关
│   └── switch_anthropic_key.py  # 在多组 API 密钥之间快速切换
├── trilium/            # Trilium Notes 相关
│   ├── config_trilium_data_dir.py  # 修改 Trilium 启动脚本更改数据目录位置
│   └── set_trilium_data_dir_env.py  # 通过环境变量指定数据目录
├── windows/            # Windows 系统相关
│   └── move_user_folders.py  # 修改用户默认文件夹（Documents/Downloads 等）位置到其他分区
└── verify_all_configs.py  # 验证所有配置是否生效
```

## 🚀 快速开始

### 一键全自动安装配置（推荐）

```bash
# 需要以管理员身份运行
python bootstrap/bootstrap_all.py

# 指定安装根目录（默认 D:\Softwares）
python bootstrap/bootstrap_all.py --install-dir D:\Tools
```

自动完成：
1. 检测已安装工具，未安装则自动下载
2. 解压/安装
3. 配置系统环境变量
4. 配置镜像源
5. 配置路径（Go会自动将工作区/缓存放到安装目录释放C盘）

默认安装位置：
- `D:\Softwares\Java\jdk1.8` - Java JDK 8
- `D:\Softwares\maven` - Apache Maven
- `D:\Softwares\Go` - Go Language
- `D:\Softwares\mingw64` - MinGW-w64
- `D:\Softwares\nodejs` - Node.js

## 📖 各脚本使用说明

### Python

**清理全局环境** - 当全局包太乱时，清理所有第三方包，只保留基础工具：
```bash
python python/python_package_clear.py
```

**配置清华镜像源**：
```bash
python python/pip_use_tsinghua_source.py
```

### Node.js/npm

**配置 npm** - 将全局模块和缓存放到 nodejs 安装目录，配置淘宝镜像，添加到 PATH：
```bash
python npm/npm_config.py [D:\Softwares\nodejs]
```

作用：
- 默认 `%APPDATA%\npm` 在 C 盘，会占用 C 盘空间，脚本移动到安装目录
- 配置淘宝镜像加速

### Java JDK

**配置环境变量**：
```bash
python java/config_java_env.py [D:\Softwares\Java\jdk1.8.0_xxx]
```

特点：
- 自动设置 `JAVA_HOME`
- 自动添加 `bin` 到系统 PATH
- 自动移除 PATH 中其他版本的 JDK，只保留当前版本
- 使用 `reg add` 而不是 `setx`，避免 1024 字符截断问题

**去重 PATH** - 移除系统 PATH 中的重复条目：
```bash
python java/deduplicate_path.py
```

### Maven

**配置环境变量**：
```bash
python maven/config_maven.py [D:\Softwares\maven]
```

自动配置阿里云镜像，加速依赖下载。

### Go

**配置系统环境变量**：
```bash
python go/config_go_env.py [D:\Softwares\Go]
```

**配置工作路径和代理** - 将 `GOPATH/GOMODCACHE/GOCACHE` 全部放到 Go 安装目录（释放 C 盘），配置国内代理：
```bash
python go/config_go_paths.py [D:\Softwares\Go]
```

配置后的路径：
- `GOROOT` → `D:\Softwares\Go` (系统环境变量)
- `GOPATH` → `D:\Softwares\Go\work`
- `GOMODCACHE` → `D:\Softwares\Go\pkg\mod`
- `GOCACHE` → `D:\Softwares\Go\cache\go-build`
- `GOPROXY` → `https://goproxy.cn,direct`

> 所有路径配置通过 `go env -w` 写入 Go 配置，**不需要修改系统环境变量**

### MinGW-w64

**配置环境变量**：
```bash
python mingw/config_mingw_env.py [D:\Softwares\mingw64]
```

### TortoiseGit

**修复图标覆盖不显示问题**（需要管理员权限）：
```bash
python tortoisegit/fix_overlay_icons.py
```

会自动导入注册表并重启 Windows 资源管理器。解决 TortoiseGit 安装后图标覆盖不显示的问题。

### Claude Code

**切换 Anthropic API 密钥** - 在多组密钥之间快速切换：

编辑脚本末尾的 `CONFIGS` 列表添加你的密钥配置，然后：
```bash
python claude/switch_anthropic_key.py 1
```

参数是配置序号（从 0 开始）。只会修改 API 密钥，保留其他 Claude Code 配置。

### Trilium Notes

**通过环境变量指定数据目录**：
```bash
python trilium/set_trilium_data_dir_env.py D:\Data\Trilium-data
```

设置系统环境变量 `TRILIUM_DATA_DIR`，Trilium 会将数据存储到指定位置。

**修改启动脚本指定数据目录**（旧方法）：
```bash
python trilium/config_trilium_data_dir.py D:\Data\Trilium-data
```

### Windows 用户文件夹

**移动用户默认文件夹到其他分区**：
```bash
python windows/move_user_folders.py
```

支持移动：Documents、Downloads、Pictures、Music、Videos、Desktop、Favorites。通过修改注册表完成，**需要重启电脑生效**。

### uv

**自动安装 uv**：
```bash
python uv/install_uv.py
```

检测是否已安装，如果没有则通过 pip 安装。

### 验证所有配置

验证所有工具是否配置成功：
```bash
python verify_all_configs.py
```

输出每个工具的版本信息，确认是否配置生效。

## ⚠️ 注意事项

1. **需要管理员权限** - 大部分脚本修改系统环境变量需要管理员权限
2. **需要重启生效** - 系统环境变量更改后需要重启终端/电脑才能看到新配置
3. **默认安装路径** - 大多数脚本默认安装路径是 `D:\Softwares\XXX`，可通过参数修改
4. **单版本配置** - `config_*.py` 脚本会自动移除 PATH 中其他版本的同工具路径，只保留当前配置版本，适合单版本开发环境

## 🎯 适用场景

- 新电脑/新系统快速搭建开发环境
- 重新安装系统后一键恢复配置
- 统一团队开发环境配置
- 释放 C 盘空间，将开发工具数据移动到其他分区

## 🔧 要求

- Windows 10/11
- Python 3.8+
- 管理员权限

## 📝 License

MIT
