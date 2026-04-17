# -*- coding: utf-8 -*-
# =============================================================================
# 脚本名称: python_package_clear.py
# 作用: 清理 Python 全局环境中的第三方包
# 适用场景: 全新安装 Python 后，默认环境可能预装了一些不需要的第三方包
#          运行本脚本可清理这些包，只保留 pip, wheel, setuptools 基础包
# 使用方法: python python_package_clear.py
# =============================================================================
import subprocess

# 保留的基础包
KEEP_PACKAGES = {"pip", "wheel", "setuptools", "uv"}

# 获取所有已安装的包
result = subprocess.run(
    ["pip", "freeze", "--user"],
    capture_output=True,
    text=True,
    check=True
)

# 解析包名（格式: package==version）
packages_to_remove = []
for line in result.stdout.splitlines():
    if line.strip():
        pkg_name = line.split("==")[0].split("@")[0].strip()
        if pkg_name and pkg_name.lower() not in KEEP_PACKAGES:
            packages_to_remove.append(pkg_name)

# 批量卸载
if packages_to_remove:
    subprocess.run(
        ["pip", "uninstall", "-y"] + packages_to_remove,
        check=True
    )
    print(f"已卸载 {len(packages_to_remove)} 个第三方包")
else:
    print("没有需要卸载的第三方包")
