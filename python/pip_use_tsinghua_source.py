# -*- coding: utf-8 -*-
# =============================================================================
# 脚本名称: pip_use_tsinghua_source.py
# 作用: 配置 pip 使用清华镜像源
# 适用场景: 国内网络访问 PyPI 下载慢，配置国内镜像加速
# 使用方法: python pip_use_tsinghua_source.py
# 效果: pip install xxx 会从清华镜像下载，速度更快
# 幂等性: 支持重复运行，已配置时会跳过
# =============================================================================
import os
import platform
import subprocess

# 清华 pip 镜像源
TSINGHUA_MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"

# 配置文件路径
if platform.system() == "Windows":
    pip_config_dir = os.path.join(os.environ["APPDATA"], "pip")
    pip_config_file = os.path.join(pip_config_dir, "pip.ini")
else:
    pip_config_dir = os.path.expanduser("~/.pip")
    pip_config_file = os.path.join(pip_config_dir, "pip.conf")

# 检查是否已配置
result = subprocess.run(["pip", "config", "list"], capture_output=True, text=True)
if TSINGHUA_MIRROR in result.stdout:
    print(f"pip 已配置清华镜像源: {TSINGHUA_MIRROR}")
else:
    # 确保目录存在
    os.makedirs(pip_config_dir, exist_ok=True)

    # 写入配置
    config_content = f"""[global]
index-url = {TSINGHUA_MIRROR}
"""
    with open(pip_config_file, "w", encoding="utf-8") as f:
        f.write(config_content)

    print(f"pip 镜像源已配置为清华源: {TSINGHUA_MIRROR}")
    print(f"配置文件路径: {pip_config_file}")

# 验证配置
result = subprocess.run(["pip", "config", "list"], capture_output=True, text=True)
print(f"\n验证结果:\n{result.stdout}")
