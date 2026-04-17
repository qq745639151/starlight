# -*- coding: utf-8 -*-
# =============================================================================
# 脚本名称: npm_config.py
# 作用: 配置 npm 全局安装路径、缓存目录、淘宝镜像源，并设置 PATH 环境变量
# 适用场景: 全新安装 Node.js 后，默认全局包安装在 C:\Program Files 下，
#          且使用官方源下载慢。配置后全局包会安装在 npm prefix 目录下，
#          并可通过淘宝镜像加速下载
# 使用方法: python npm_config.py
# 效果:
#   1. 创建 node_cache 和 node_global 目录
#   2. 配置 npm 全局安装路径 (prefix)
#   3. 配置 npm 缓存路径 (cache)
#   4. 配置 npm 使用淘宝镜像源 (registry)
#   5. 将 node_global/bin 添加到用户 PATH 环境变量（永久生效）
#   6. 移除默认的 C:\Users\<user>\AppData\Roaming\npm（已迁移到新路径）
# 幂等性: 支持重复运行，已配置时会跳过，只修改未达标项
# =============================================================================
import subprocess
import os
import winreg

# 淘宝 npm 镜像源
TAOBAO_MIRROR = "https://registry.npmmirror.com"

# 检查现有配置
def get_npm_config(key):
    result = subprocess.run(
        ["npm", "config", "get", key],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

current_prefix = get_npm_config("prefix")
current_cache = get_npm_config("cache")
current_registry = get_npm_config("registry")

# 检查 PATH 中是否包含指定路径
def is_in_path(path):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ)
        current_path, _ = winreg.QueryValueEx(key, "Path")
        winreg.CloseKey(key)
        return path in current_path
    except FileNotFoundError:
        return False

# 从 PATH 中移除指定路径
def remove_from_path(path_to_remove):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE)
        current_path, _ = winreg.QueryValueEx(key, "Path")
        if path_to_remove not in current_path:
            winreg.CloseKey(key)
            return False  # 已经不存在了

        # 分割路径，过滤掉要移除的，再重新拼接
        entries = current_path.split(';')
        entries = [e.strip() for e in entries if e.strip() and e.strip() != path_to_remove]
        new_path = ';'.join(entries)

        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
        winreg.CloseKey(key)
        return True
    except PermissionError:
        print("警告: 移除旧路径失败，可能需要管理员权限")
        return False
    except FileNotFoundError:
        return False

# 获取 npm 全局路径并设置目录
npm_prefix = current_prefix if current_prefix else subprocess.run(
    ["npm", "config", "get", "prefix"],
    capture_output=True,
    text=True,
    check=True
).stdout.strip()

npm_cache = os.path.join(npm_prefix, "node_cache")
npm_global = os.path.join(npm_prefix, "node_global")
npm_global_bin = os.path.join(npm_global, "bin")

# 默认的旧用户 npm 路径
default_old_npm_path = os.path.join(os.environ.get('USERPROFILE', 'C:\\Users\\qq745'), 'AppData', 'Roaming', 'npm')

# 检查是否已全部配置完成
all_configured = (
    current_prefix == npm_global and
    current_cache == npm_cache and
    current_registry == TAOBAO_MIRROR and
    is_in_path(npm_global_bin) and
    not is_in_path(default_old_npm_path)
)

if all_configured:
    print("npm 已配置完成，无需重复设置")
    print(f"  prefix: {npm_global}")
    print(f"  cache: {npm_cache}")
    print(f"  registry: {TAOBAO_MIRROR}")
    print(f"  PATH: {npm_global_bin}")
else:
    # 创建目录
    os.makedirs(npm_cache, exist_ok=True)
    os.makedirs(npm_global, exist_ok=True)

    # 配置 npm
    if current_prefix != npm_global:
        subprocess.run(["npm", "config", "set", "prefix", npm_global], check=True)
        print(f"已设置 prefix: {npm_global}")
    else:
        print(f"prefix 已配置: {npm_global}")

    if current_cache != npm_cache:
        subprocess.run(["npm", "config", "set", "cache", npm_cache], check=True)
        print(f"已设置 cache: {npm_cache}")
    else:
        print(f"cache 已配置: {npm_cache}")

    if current_registry != TAOBAO_MIRROR:
        subprocess.run(["npm", "config", "set", "registry", TAOBAO_MIRROR], check=True)
        print(f"已设置 registry: {TAOBAO_MIRROR}")
    else:
        print(f"registry 已配置: {TAOBAO_MIRROR}")

    # 移除旧的默认 npm 路径（用户目录下的 AppData\Roaming\npm）
    if is_in_path(default_old_npm_path):
        print(f"正在移除旧的默认 npm 路径: {default_old_npm_path}")
        success = remove_from_path(default_old_npm_path)
        if success:
            print(f"已移除 {default_old_npm_path}")
        else:
            print(f"移除 {default_old_npm_path} 失败")
    else:
        print(f"旧路径 {default_old_npm_path} 不在 PATH 中，跳过")

    # 将 node_global/bin 添加到 PATH
    if not is_in_path(npm_global_bin):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE)
            try:
                current_path, _ = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current_path = ""
            new_path = current_path + (";" if current_path else "") + npm_global_bin
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            print(f"已添加 {npm_global_bin} 到 PATH")
            winreg.CloseKey(key)
        except PermissionError:
            print("警告: 修改 PATH 失败，可能需要管理员权限")
    else:
        print(f"PATH 已配置: {npm_global_bin}")

# 验证配置
result = subprocess.run(["npm", "config", "list"], capture_output=True, text=True)
print(f"\n验证结果:\n{result.stdout}")
