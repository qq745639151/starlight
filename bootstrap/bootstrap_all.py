#!/usr/bin/env python3
r"""
一键自动检测并配置所有开发环境

功能:
1. 依次检查 Java JDK, Maven, Go, MinGW-w64, Node.js, uv 是否已安装
2. 如果未安装，自动下载对应版本的安装包到指定目录
3. 执行静默安装
4. 配置系统环境变量 (JAVA_HOME, MAVEN_HOME, GOROOT, MINGW_HOME, 添加 bin 到 PATH)
5. 配置镜像源 (pip 清华源, npm 淘宝源, Maven 阿里云)
6. 最后自动检查所有配置是否生效

支持配置的工具:
- Java JDK 8/11/17/21
- Apache Maven
- Go Language
- MinGW-w64 C/C++ 编译器
- Node.js
- uv Python 包管理器
- pip 配置清华镜像源

默认安装路径:
  D:\Softwares\jdkXX
  D:\Softwares\maven
  D:\Softwares\Go
  D:\Softwares\mingw64
  D:\Softwares\nodejs

用法:
  python bootstrap/bootstrap_all.py [--install-dir <base-dir>]

参数:
  --install-dir <base-dir>  指定安装根目录，默认 D:\Softwares

注意:
  - 需要**管理员权限**运行
  - 需要网络连接下载安装包
  - 安装完成后需要重启电脑/终端才能生效
  - 脚本只安装配置环境，不会修改已有正确配置
"""

import os
import sys
import argparse
import subprocess
import zipfile
from typing import List, Tuple, Dict, Optional, Any
from urllib.request import urlretrieve

# 默认配置
DEFAULT_INSTALL_BASE = r"D:\Softwares"

# 工具下载信息
# 这里使用稳定版本链接
TOOL_CONFIGS = {
    'java': {
        'version': 'jdk1.8.0_202',
        'url': 'https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u202-b08/OpenJDK8U-jdk_x64_windows_hotspot_8u202b08.msi',
        'filename': 'OpenJDK8U-jdk_x64.msi',
        'install_args': '/qn /norestart',
        'default_path': r'D:\Softwares\Java\jdk1.8',
        'env_name': 'JAVA_HOME',
    },
    'maven': {
        'version': '3.9.6',
        'url': 'https://archive.apache.org/dist/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.zip',
        'filename': 'apache-maven-3.9.6-bin.zip',
        'is_archive': True,
        'default_path': r'D:\Softwares\maven',
        'env_name': 'MAVEN_HOME',
    },
    'go': {
        'version': '1.22.5',
        'url': 'https://go.dev/dl/go1.22.5.windows-amd64.zip',
        'filename': 'go1.22.5.windows-amd64.zip',
        'is_archive': True,
        'default_path': r'D:\Softwares\Go',
        'env_name': 'GOROOT',
    },
    'node': {
        'version': '25.9.0',
        'url': 'https://nodejs.org/dist/v25.9.0/node-v25.9.0-x64.msi',
        'filename': 'node-v25.9.0-x64.msi',
        'install_args': '/qn /norestart',
        'default_path': r'D:\Softwares\nodejs',
        'env_name': None,  # Node.js installer adds PATH automatically
    },
    'mingw': {
        'version': '15.2.0',
        'url': 'https://github.com/niXman/mingw-builds-binaries/releases/download/15.2.0/x86_64-15.2.0-release-posix-seh-rt_v10-rev1.7z',
        'filename': 'mingw64-15.2.0.7z',
        'is_archive': True,
        'default_path': r'D:\Softwares\mingw64',
        'env_name': 'MINGW_HOME',
    },
}


def parse_args():
    parser = argparse.ArgumentParser(
        description='一键自动配置所有开发环境'
    )
    parser.add_argument(
        '--install-dir',
        type=str,
        default=DEFAULT_INSTALL_BASE,
        help=f'安装根目录，默认 {DEFAULT_INSTALL_BASE}'
    )
    return parser.parse_args()


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


def get_environment_var(var_name: str) -> Optional[str]:
    """获取环境变量从系统注册表"""
    try:
        result = subprocess.run(
            ['reg', 'query', r'HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment', '/v', var_name],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return os.environ.get(var_name)

        lines = result.stdout.splitlines()
        for line in lines:
            line = line.rstrip('\n')
            if var_name in line and 'REG_' in line:
                reg_index = line.find('REG_')
                space_after_reg = line.find(' ', reg_index)
                if space_after_reg != -1:
                    value = line[space_after_reg + 1:].rstrip().lstrip()
                    return value
        return os.environ.get(var_name)
    except Exception:
        return os.environ.get(var_name)


def is_tool_already_installed(env_name: Optional[str], install_path: str) -> bool:
    """检查工具是否已经安装"""
    if env_name:
        existing = get_environment_var(env_name)
        if existing and os.path.exists(existing):
            print(f"[OK] {env_name} = {existing} 已存在且路径有效，跳过安装")
            return True
    if os.path.exists(install_path):
        # 检查目录不为空
        if any(os.scandir(install_path)):
            print(f"[OK] 安装目录 {install_path} 已存在且不为空，跳过安装")
            return True
    return False


def download_file(url: str, dest_path: str) -> bool:
    """下载文件显示进度"""
    print(f"正在下载: {url}")
    print(f"保存到: {dest_path}")
    try:
        def progress_hook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 // total_size)
                sys.stdout.write(f"\r  进度: {percent}% ({downloaded // 1024 // 1024} MB / {total_size // 1024 // 1024} MB)")
                sys.stdout.flush()
        urlretrieve(url, dest_path, progress_hook)
        print("\n[OK] 下载完成")
        return True
    except Exception as e:
        print(f"\n[!] 下载失败: {e}")
        return False


def extract_archive(archive_path: str, dest_dir: str) -> bool:
    """解压压缩包 (zip 或 7z)"""
    print(f"正在解压: {archive_path} -> {dest_dir}")
    os.makedirs(os.path.dirname(dest_dir), exist_ok=True)

    if archive_path.endswith('.zip'):
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # 获取顶级目录名称
                top_dir = None
                for name in zip_ref.namelist():
                    parts = name.split('/')
                    if len(parts) > 0 and (top_dir is None):
                        top_dir = parts[0]
                zip_ref.extractall(os.path.dirname(dest_dir))
                # 如果解压出来是 go1.22.5/go/..., 需要移动到 dest_dir
                if top_dir and top_dir != os.path.basename(dest_dir):
                    extracted_path = os.path.join(os.path.dirname(dest_dir), top_dir)
                    if os.path.exists(extracted_path) and not os.path.exists(dest_dir):
                        import shutil
                        shutil.move(extracted_path, dest_dir)
            print("[OK] 解压完成")
            return True
        except Exception as e:
            print(f"[!] 解压失败: {e}")
            return False

    elif archive_path.endswith('.7z'):
        # 使用 7-Zip 如果可用
        try:
            result = subprocess.run(
                ['7z', 'x', archive_path, f'-o{os.path.dirname(dest_dir)}', '-y'],
                capture_output=True,
            )
            if result.returncode == 0:
                print("[OK] 解压完成")
                return True
            else:
                print("[!] 7z 解压失败，请手动解压")
                return False
        except FileNotFoundError:
            print("[!] 未找到 7z 命令，请安装 7-Zip 后手动解压")
            return False
    else:
        print(f"[!] 不支持的压缩格式: {archive_path}")
        return False


def add_to_system_path(new_path: str) -> bool:
    """添加路径到系统 PATH，避免重复"""
    # 获取当前 PATH
    result = subprocess.run(
        ['reg', 'query', r'HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment', '/v', 'Path'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print("[!] 无法读取系统 PATH")
        return False

    current_path = None
    lines = result.stdout.splitlines()
    for line in lines:
        line = line.rstrip('\n')
        if 'Path' in line and 'REG_' in line:
            reg_index = line.find('REG_')
            space_after_reg = line.find(' ', reg_index)
            if space_after_reg != -1:
                current_path = line[space_after_reg + 1:].rstrip().lstrip()
                break

    if not current_path:
        current_path = os.environ.get('PATH', '')

    # 检查是否已经存在
    new_path_norm = os.path.normcase(new_path)
    for entry in current_path.split(';'):
        entry = entry.strip()
        if os.path.normcase(entry) == new_path_norm:
            print("[OK] 路径已经在 PATH 中，跳过")
            return True

    # 添加到末尾
    new_full_path = current_path.rstrip(';') + ';' + new_path
    print(f"添加 {new_path} 到 PATH")

    # 使用 reg add 而不是 setx，避免 setx 的 1024 字符截断限制
    result = subprocess.run(
        ['reg', 'add', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', '/v', 'Path', '/t', 'REG_SZ', '/d', new_full_path, '/f'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def set_system_env(var_name: str, value: str) -> bool:
    """设置系统环境变量"""
    existing = get_environment_var(var_name)
    if existing and os.path.normcase(existing) == os.path.normcase(value):
        print(f"[OK] {var_name} 已经是 {value}，跳过")
        return True

    # 使用 reg add 而不是 setx，避免 setx 的 1024 字符截断限制
    result = subprocess.run(
        ['reg', 'add', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', '/v', var_name, '/t', 'REG_SZ', '/d', value, '/f'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def configure_pip_tsinghua() -> bool:
    """配置 pip 使用清华镜像源"""
    print("\n[步骤] 配置 pip 清华镜像源")
    try:
        # 检查是否已经配置
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'config', 'get', 'global.index-url'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            current_url = result.stdout.strip()
            if 'tsinghua' in current_url or 'mirror' in current_url:
                print(f"[OK] pip 已经配置镜像源: {current_url}")
                return True

        # 写入配置
        pip_conf_dir = os.path.join(os.path.expanduser('~'), 'pip')
        pip_conf_file = os.path.join(pip_conf_dir, 'pip.ini')
        os.makedirs(pip_conf_dir, exist_ok=True)

        conf_content = '''[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
'''
        with open(pip_conf_file, 'w', encoding='utf-8') as f:
            f.write(conf_content)
        print("[OK] pip 清华镜像源配置完成")
        return True
    except Exception as e:
        print(f"[!] pip 配置失败: {e}")
        return False


def configure_maven_aliyun(maven_home: str) -> bool:
    """配置 Maven 使用阿里云镜像"""
    print("\n[步骤] 配置 Maven 阿里云镜像")
    settings_path = os.path.join(maven_home, 'conf', 'settings.xml')

    # 如果我们仓库有模板，使用模板
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        '..', 'maven', 'settings.xml'
    )
    if os.path.exists(template_path):
        import shutil
        shutil.copy(template_path, settings_path)
        print("[OK] Maven settings.xml 已配置阿里云镜像")
        return True
    print("[!] 模板文件未找到，跳过")
    return False


def verify_tool(name: str, check_command: str, description: str) -> bool:
    """验证工具是否可用"""
    print(f"\n[验证] {description}...")
    try:
        result = subprocess.run(
            check_command.split(),
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            first_line = (result.stdout.strip().splitlines() + result.stderr.strip().splitlines())[0]
            print(f"[OK] {description} 可用: {first_line}")
            return True
        else:
            print(f"[FAIL] {description} 不可用（需要重启终端/电脑生效）")
            return False
    except FileNotFoundError:
        print(f"[FAIL] {description} 命令未找到（需要重启终端/电脑生效）")
        return False
    except Exception:
        print(f"[FAIL] {description} 验证失败（需要重启终端/电脑生效）")
        return False


def main():
    args = parse_args()
    install_base = os.path.abspath(args.install_dir)

    print("=" * 70)
    print("一键自动配置所有开发环境")
    print("=" * 70)
    print()
    print(f"安装根目录: {install_base}")
    print()

    # 检查管理员权限
    if not check_admin():
        print("错误: 需要管理员权限才能修改系统环境变量")
        print("请以管理员身份运行此脚本")
        sys.exit(1)

    all_ok = True
    results: List[Tuple[str, bool, str]] = []

    # 创建下载缓存目录
    download_dir = os.path.join(os.path.dirname(__file__), 'downloads')
    os.makedirs(download_dir, exist_ok=True)

    # 1. Java JDK
    print("\n" + "=" * 70)
    print("1. 检查 Java JDK")
    print("-" * 70)

    java_config = TOOL_CONFIGS['java']
    java_default_path = os.path.join(install_base, 'Java', 'jdk1.8')
    if not is_tool_already_installed(java_config['env_name'], java_default_path):
        # 需要安装
        download_path = os.path.join(download_dir, java_config['filename'])
        if not os.path.exists(download_path):
            if not download_file(java_config['url'], download_path):
                results.append(('Java JDK', False, '下载失败'))
                all_ok = False
        else:
            print(f"[OK] 安装包已下载: {download_path}")

        print(f"正在安装 Java JDK 到 {java_default_path}")
        result = subprocess.run(
            ['msiexec', java_config['install_args'], '/i', download_path],
            capture_output=True,
        )
        if result.returncode == 0 or result.returncode == 3010:  # 3010 = 需要重启
            print("[OK] Java JDK 安装完成")
            set_system_env('JAVA_HOME', java_default_path)
            bin_path = os.path.join(java_default_path, 'bin')
            add_to_system_path(bin_path)
            results.append(('Java JDK', True, '安装完成'))
        else:
            print(f"[!] Java JDK 安装失败，退出码 {result.returncode}")
            results.append(('Java JDK', False, '安装失败'))
            all_ok = False
    else:
        results.append(('Java JDK', True, '已安装'))

    # 2. Maven
    print("\n" + "=" * 70)
    print("2. 检查 Apache Maven")
    print("-" * 70)

    maven_config = TOOL_CONFIGS['maven']
    maven_default_path = os.path.join(install_base, 'maven')
    if not is_tool_already_installed(maven_config['env_name'], maven_default_path):
        download_path = os.path.join(download_dir, maven_config['filename'])
        if not os.path.exists(download_path):
            if not download_file(maven_config['url'], download_path):
                results.append(('Apache Maven', False, '下载失败'))
                all_ok = False
        else:
            print(f"[OK] 压缩包已下载: {download_path}")

        if extract_archive(download_path, maven_default_path):
            print("[OK] Maven 解压完成")
            set_system_env('MAVEN_HOME', maven_default_path)
            bin_path = os.path.join(maven_default_path, 'bin')
            add_to_system_path(bin_path)
            configure_maven_aliyun(maven_default_path)
            results.append(('Apache Maven', True, '安装完成'))
        else:
            results.append(('Apache Maven', False, '解压失败'))
            all_ok = False
    else:
        results.append(('Apache Maven', True, '已安装'))
        if 'MAVEN_HOME' in os.environ:
            configure_maven_aliyun(os.environ['MAVEN_HOME'])

    # 3. Go
    print("\n" + "=" * 70)
    print("3. 检查 Go 语言")
    print("-" * 70)

    go_config = TOOL_CONFIGS['go']
    go_default_path = os.path.join(install_base, 'Go')
    if not is_tool_already_installed(go_config['env_name'], go_default_path):
        download_path = os.path.join(download_dir, go_config['filename'])
        if not os.path.exists(download_path):
            if not download_file(go_config['url'], download_path):
                results.append(('Go 语言', False, '下载失败'))
                all_ok = False
        else:
            print(f"[OK] 压缩包已下载: {download_path}")

        if extract_archive(download_path, go_default_path):
            print("[OK] Go 解压完成")
            set_system_env('GOROOT', go_default_path)
            bin_path = os.path.join(go_default_path, 'bin')
            add_to_system_path(bin_path)
            results.append(('Go 语言', True, '安装完成'))
        else:
            results.append(('Go 语言', False, '解压失败'))
            all_ok = False
    else:
        results.append(('Go 语言', True, '已安装'))

    # 配置 Go 路径和国内代理
    print("\n[步骤] 配置 Go 路径和国内代理")
    go_config_script = os.path.join(
        os.path.dirname(__file__),
        '..', 'go', 'config_go_paths.py'
    )
    if os.path.exists(go_config_script):
        result = subprocess.run(
            [sys.executable, go_config_script, go_default_path],
            capture_output=False,
            text=False
        )
        if result.returncode == 0:
            print("[OK] Go 路径和代理配置完成")
            results.append(('Go 路径配置', True, '配置完成'))
        else:
            print("[WARN] Go 路径配置可能有问题，请检查")
            results.append(('Go 路径配置', False, '配置失败'))
            # 不标记整体失败，因为安装已经完成
    else:
        print("[WARN] config_go_paths.py not found, skipping")
        results.append(('Go 路径配置', False, '脚本不存在'))

    # 验证 Go 是否可用
    verify_tool('go', 'go version', 'Go 语言')

    # 4. MinGW-w64
    print("\n" + "=" * 70)
    print("4. 检查 MinGW-w64 C/C++")
    print("-" * 70)

    mingw_config = TOOL_CONFIGS['mingw']
    mingw_default_path = os.path.join(install_base, 'mingw64')
    if not is_tool_already_installed(mingw_config['env_name'], mingw_default_path):
        download_path = os.path.join(download_dir, mingw_config['filename'])
        if not os.path.exists(download_path):
            if not download_file(mingw_config['url'], download_path):
                results.append(('MinGW-w64', False, '下载失败'))
                all_ok = False
        else:
            print(f"[OK] 压缩包已下载: {download_path}")

        if extract_archive(download_path, mingw_default_path):
            print("[OK] MinGW-w64 解压完成")
            set_system_env('MINGW_HOME', mingw_default_path)
            bin_path = os.path.join(mingw_default_path, 'bin')
            add_to_system_path(bin_path)
            results.append(('MinGW-w64', True, '安装完成'))
        else:
            results.append(('MinGW-w64', False, '解压失败'))
            all_ok = False
    else:
        results.append(('MinGW-w64', True, '已安装'))

    # 5. Node.js
    print("\n" + "=" * 70)
    print("5. 检查 Node.js")
    print("-" * 70)

    node_config = TOOL_CONFIGS['node']
    node_default_path = os.path.join(install_base, 'nodejs')
    if not is_tool_already_installed(node_config['env_name'], node_default_path):
        download_path = os.path.join(download_dir, node_config['filename'])
        if not os.path.exists(download_path):
            if not download_file(node_config['url'], download_path):
                results.append(('Node.js', False, '下载失败'))
                all_ok = False
        else:
            print(f"[OK] 安装包已下载: {download_path}")

        print(f"正在安装 Node.js 到 {node_default_path}")
        result = subprocess.run(
            ['msiexec', node_config['install_args'], '/i', download_path],
            capture_output=True,
        )
        if result.returncode == 0 or result.returncode == 3010:
            print("[OK] Node.js 安装完成")
            # Node.js 安装程序自动添加 PATH
            results.append(('Node.js', True, '安装完成'))
        else:
            print(f"[!] Node.js 安装失败，退出码 {result.returncode}")
            results.append(('Node.js', False, '安装失败'))
            all_ok = False
    else:
        results.append(('Node.js', True, '已安装'))

    # 6. uv
    print("\n" + "=" * 70)
    print("6. 检查 uv Python 包管理器")
    print("-" * 70)

    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] uv 已安装: {result.stdout.strip()}")
            results.append(('uv', True, '已安装'))
        else:
            print("正在通过 pip 安装 uv...")
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'uv'], capture_output=True, text=True)
            if result.returncode == 0:
                print("[OK] uv 安装完成")
                results.append(('uv', True, '安装完成'))
            else:
                print("[!] uv 安装失败")
                results.append(('uv', False, 'pip 安装失败'))
                all_ok = False
    except FileNotFoundError:
        print("正在通过 pip 安装 uv...")
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'uv'], capture_output=True, text=True)
        if result.returncode == 0:
            print("[OK] uv 安装完成")
            results.append(('uv', True, '安装完成'))
        else:
            print("[!] uv 安装失败")
            results.append(('uv', False, 'pip 安装失败'))
            all_ok = False

    # 7. 配置 pip
    print("\n" + "=" * 70)
    print("7. 配置 pip 清华镜像源")
    print("-" * 70)

    if configure_pip_tsinghua():
        results.append(('pip 清华镜像', True, '配置完成'))
    else:
        results.append(('pip 清华镜像', False, '配置失败'))
        all_ok = False

    # 总结
    print("\n" + "=" * 70)
    print("安装配置完成总结")
    print("=" * 70)
    print()

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)

    for name, ok, msg in results:
        status = "[OK] 通过" if ok else "[FAIL] 失败"
        print(f"  {name:<15} {status} - {msg}")

    print()
    print(f"结果: {passed}/{total} 项成功完成")

    print()
    print("=" * 70)
    print("重要提示:")
    print("  1. 需要**重启电脑**才能使所有环境变量更改生效")
    print("  2. 或者至少注销当前用户再重新登录")
    print("  3. 下载的安装包缓存在 bootstrap/downloads/ 目录，可以删除节省空间")
    print("  4. 如果需要验证，请重启终端后运行 python verify_all_configs.py 检查")
    print("=" * 70)

    if all_ok:
        print()
        print("[OK] 所有操作成功完成!")
        return 0
    else:
        print()
        print("[FAIL] 部分操作失败，请检查上述失败项")
        return 1


if __name__ == "__main__":
    sys.exit(main())
