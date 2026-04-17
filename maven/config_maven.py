#!/usr/bin/env python3
r"""
配置 Maven 环境变量

作用:
在 Windows 系统上配置 Maven 环境变量，设置 MAVEN_HOME 并将 bin 目录添加到系统 PATH。
检查当前环境，如果配置已经符合要求则跳过，避免重复设置。
**单版本配置**，自动移除其他 Maven 版本路径，只保留当前配置版本。
同时配置阿里云镜像加速下载，设置本地仓库路径到 maven/repository。

默认 Maven 安装路径: D:\Softwares\maven

用法:
python maven/config_maven.py [maven_path]

参数:
  maven_path  可选，指定 Maven 安装路径，默认使用 D:\Softwares\maven
"""

import os
import sys
import subprocess
from typing import Optional


# 默认 Maven 安装路径
DEFAULT_MAVEN_PATH = r"D:\Softwares\maven"

# 阿里云 Maven 镜像配置
ALIBABA_MIRROR_CONFIG = '''
  <mirror>
    <id>aliyunmaven</id>
    <mirrorOf>*</mirrorOf>
    <name>阿里云公共仓库</name>
    <url>https://maven.aliyun.com/repository/public</url>
  </mirror>
'''




def get_system_path() -> str:
    """获取系统 PATH 环境变量"""
    result = subprocess.run(
        ['reg', 'query', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', '/v', 'Path'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        # 如果读取失败，回退到从环境变量获取
        return os.environ.get('PATH', '')

    # 注册表输出格式:
    #     Path    REG_SZ    C:\path1;C:\path 2;C:\path3
    # 我们需要找到 REG_SZ 之后的所有内容
    lines = result.stdout.splitlines()
    for line in lines:
        line = line.rstrip('\n')
        # 找出带有 Path 的行，这行以多个空格开头
        if 'Path' in line and 'REG_' in line:
            # 找到 REG_ 的位置，后面就是完整的 Path 值
            reg_index = line.find('REG_')
            # 跳过 REG_xxx 和它前面的空格
            # 格式是: [空格]名称[空格+]类型[空格+]值
            # 所以从找到 REG_ 后跳过类型
            space_after_reg = line.find(' ', reg_index)
            if space_after_reg != -1:
                # 值从 space_after_reg + 1 开始
                path_value = line[space_after_reg + 1:].rstrip().lstrip()
                return path_value

    # 如果解析失败，回退到从环境变量获取
    return os.environ.get('PATH', '')


def is_maven_in_path(maven_bin_path: str) -> bool:
    """检查 Maven bin 目录是否已经在 PATH 中"""
    current_path = get_system_path()
    maven_bin_path = maven_bin_path.replace('/', '\\').lower()
    current_path_lower = current_path.replace('/', '\\').lower()

    return maven_bin_path in current_path_lower


def set_maven_home(maven_path: str) -> bool:
    """设置系统环境变量 MAVEN_HOME（需要管理员权限）"""
    result = subprocess.run(
        ['setx', '/M', 'MAVEN_HOME', maven_path],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def find_maven_in_path(current_path: str) -> list[str]:
    """在 PATH 中查找已有的 Maven bin 路径（任何包含 mvn.cmd 的目录）"""
    entries = current_path.split(';')
    maven_entries = []
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        # 识别 Maven 路径，包含 maven 且 bin 目录存在 mvn.cmd
        entry_lower = entry.lower()
        if ('maven' in entry_lower or 'mvn' in entry_lower) and os.path.exists(os.path.join(entry, 'mvn.cmd')):
            maven_entries.append(entry)
    return maven_entries


def add_to_system_path(maven_bin_path: str) -> bool:
    """将 Maven bin 目录添加到系统 PATH（需要管理员权限）
    **单版本配置**，自动移除其他 Maven 版本路径，只保留当前版本
    """
    # 获取当前 PATH
    current_path = get_system_path()

    # 查找并移除其他已存在的 Maven 版本
    existing_maven_entries = find_maven_in_path(current_path)
    if existing_maven_entries:
        print(f"  发现 {len(existing_maven_entries)} 个其他 Maven 版本:")
        for entry in existing_maven_entries:
            if entry.lower() != maven_bin_path.lower():
                print(f"    将移除: {entry}")
                current_path = current_path.replace(entry + ';', '').replace(';' + entry, '').replace(entry, '')

    # 检查是否已经存在当前 Maven
    if is_maven_in_path(maven_bin_path):
        print(f"[OK] {maven_bin_path} 已经在 PATH 中，跳过")
        return True

    # 添加当前版本到 PATH
    current_entries = [e.strip() for e in current_path.split(';') if e.strip()]
    current_entries.append(maven_bin_path)
    new_path = ';'.join(current_entries)

    result = subprocess.run(
        ['setx', '/M', 'Path', new_path],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def get_current_maven_home() -> Optional[str]:
    """获取当前系统的 MAVEN_HOME 环境变量"""
    return os.environ.get('MAVEN_HOME')


def check_maven_exists(maven_path: str) -> bool:
    """检查 Maven 路径是否存在且包含 bin/mvn.cmd"""
    mvn_cmd = os.path.join(maven_path, 'bin', 'mvn.cmd')
    return os.path.exists(mvn_cmd)


def check_admin() -> bool:
    """检查是否有管理员权限"""
    try:
        # 尝试读取注册表的系统环境变量键
        subprocess.run(
            ['reg', 'query', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment'],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def configure_maven_settings(maven_path: str) -> bool:
    """配置 Maven settings.xml：阿里云镜像 + 本地仓库路径

    本地仓库: {maven_path}/repository
    镜像: 阿里云公共仓库，加速下载
    """
    import xml.etree.ElementTree as ET

    # settings.xml 路径
    settings_path = os.path.join(maven_path, 'conf', 'settings.xml')
    local_repo_path = os.path.join(maven_path, 'repository')

    # 创建 repository 目录
    os.makedirs(local_repo_path, exist_ok=True)

    # 如果文件不存在，创建根元素
    if not os.path.exists(settings_path):
        # 创建新的 settings.xml
        settings = ET.Element('settings')
        settings.set('xmlns', 'http://maven.apache.org/SETTINGS/1.0.0')
        settings.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        settings.set('xsi:schemaLocation', 'http://maven.apache.org/SETTINGS/1.0.0 http://maven.apache.org/xsd/settings-1.0.0.xsd')
        tree = ET.ElementTree(settings)
        root = settings
        # 默认命名空间为空
        ET.register_namespace('', 'http://maven.apache.org/SETTINGS/1.0.0')
    else:
        # 检查是否已经配置了阿里云镜像
        with open(settings_path, 'r', encoding='utf-8') as f:
            content_check = f.read()
        if 'maven.aliyun.com' in content_check and local_repo_path in content_check:
            print("[OK] settings.xml 已经配置好阿里云镜像和本地仓库，跳过")
            return True
        # 解析现有 XML
        tree = ET.parse(settings_path)
        root = tree.getroot()
        # 获取命名空间 URI
        namespace = root.tag.split('}')[0].strip('{') if '}' in root.tag else ''
        if namespace:
            ns = {'maven': namespace}
            ET.register_namespace('', namespace)

    # 根据是否有命名空间查找元素
    def find_element(parent, tag):
        # 先尝试不带命名空间
        elem = parent.find(tag)
        if elem is not None:
            return elem
        # 尝试带命名空间
        if 'namespace' in locals() and namespace:
            elem = parent.find(f'./{tag}', ns)
        return elem

    def find_elements(parent, tag):
        # 先尝试不带命名空间
        elems = parent.findall(tag)
        if elems:
            return elems
        # 尝试带命名空间
        if 'namespace' in locals() and namespace:
            elems = parent.findall(f'./{tag}', ns)
        return elems

    # 设置本地仓库
    localRepository = find_element(root, 'localRepository')
    if localRepository is None:
        localRepository = ET.SubElement(root, 'localRepository')
    localRepository.text = local_repo_path

    # 找到或创建 mirrors 节点
    mirrors = find_element(root, 'mirrors')
    if mirrors is None:
        mirrors = ET.SubElement(root, 'mirrors')

    # 检查是否已有 aliyunmaven mirror，没有就添加
    has_aliyun = False
    for mirror in find_elements(mirrors, 'mirror'):
        id_elem = find_element(mirror, 'id')
        if id_elem is not None and id_elem.text == 'aliyunmaven':
            has_aliyun = True
            break

    if not has_aliyun:
        # 添加阿里云镜像
        mirror = ET.SubElement(mirrors, 'mirror')
        id_elem = ET.SubElement(mirror, 'id')
        id_elem.text = 'aliyunmaven'
        mirrorOf = ET.SubElement(mirror, 'mirrorOf')
        mirrorOf.text = '*'
        name = ET.SubElement(mirror, 'name')
        name.text = '阿里云公共仓库'
        url = ET.SubElement(mirror, 'url')
        url.text = 'https://maven.aliyun.com/repository/public'

    # 写入格式化的 XML
    try:
        # 使用 indent 格式化（Python 3.9+）
        try:
            ET.indent(tree, space='  ', level=0)
        except AttributeError:
            # 如果旧版本 Python 没有 indent，跳过格式化
            pass

        tree.write(settings_path, encoding='utf-8', xml_declaration=True)
        print(f"[OK] settings.xml 配置完成:")
        print(f"  本地仓库: {local_repo_path}")
        print(f"  镜像: 阿里云公共仓库 https://maven.aliyun.com/repository/public")
        return True
    except PermissionError:
        print("错误: 没有权限写入 settings.xml")
        return False


def main():
    # 处理帮助参数
    if len(sys.argv) >= 2 and sys.argv[1] in ['-h', '--help']:
        print(__doc__)
        sys.exit(0)

    # 获取 Maven 路径
    if len(sys.argv) >= 2:
        maven_path = sys.argv[1].strip()
    else:
        maven_path = DEFAULT_MAVEN_PATH

    maven_path = os.path.abspath(maven_path)
    maven_bin_path = os.path.join(maven_path, 'bin')

    print(f"Maven 安装路径: {maven_path}")
    print()

    # 检查 Maven 是否存在
    if not check_maven_exists(maven_path):
        print(f"错误: 在 {maven_path} 未找到 Maven (缺少 bin/mvn.cmd)")
        print("请确认 Maven 安装路径是否正确")
        sys.exit(1)

    # 检查管理员权限
    if not check_admin():
        print("错误: 需要管理员权限才能修改系统环境变量")
        print("请以管理员身份运行此脚本")
        sys.exit(1)

    # 检查当前 MAVEN_HOME
    current_maven_home = get_current_maven_home()
    if current_maven_home and os.path.abspath(current_maven_home) == os.path.abspath(maven_path):
        print(f"[OK] MAVEN_HOME 已经是 {maven_path}，无需修改")
        maven_home_ok = True
    else:
        if current_maven_home:
            print(f"  当前 MAVEN_HOME: {current_maven_home}")
        print(f"  将设置 MAVEN_HOME: {maven_path}")
        maven_home_ok = False

    # 检查 PATH
    if is_maven_in_path(maven_bin_path):
        print(f"[OK] {maven_bin_path} 已经在系统 PATH 中，无需修改")
        path_ok = True
    else:
        print(f"  需要将 {maven_bin_path} 添加到系统 PATH")
        path_ok = False

    print()

    if maven_home_ok and path_ok:
        print("[OK] 环境配置已经完成，无需修改")
        # 尝试验证
        print("\n尝试验证 Maven 安装...")
        try:
            result = subprocess.run(
                ['mvn', '-version'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                first_line = result.stdout.splitlines()[0] if result.stdout else "OK"
                print(f"[OK] Maven 验证成功: {first_line}")
            else:
                print("[!] Maven 版本命令失败，需要重启终端后生效")
                print("    当前会话环境变量还没更新，这是正常的")
        except FileNotFoundError:
            print("[!] mvn 命令未找到，需要重启终端后生效")
            print("    当前会话环境变量还没更新，这是正常的")
        sys.exit(0)

    # 开始配置
    print("开始配置环境变量...")
    print()

    if not maven_home_ok:
        print("设置 MAVEN_HOME...")
        success = set_maven_home(maven_path)
        if not success:
            print("错误: 设置 MAVEN_HOME 失败")
            sys.exit(1)
        print("[OK] MAVEN_HOME 设置完成")

    print()

    if not path_ok:
        print("添加 bin 目录到 PATH...")
        success = add_to_system_path(maven_bin_path)
        if not success:
            print("错误: 添加到 PATH 失败")
            sys.exit(1)
        print("[OK] PATH 添加完成")

    print()

    # 配置 settings.xml (阿里云镜像 + 本地仓库)
    print("配置 settings.xml...")
    settings_success = configure_maven_settings(maven_path)
    if not settings_success:
        print("警告: settings.xml 配置失败")

    print()
    print("[OK] 配置完成!")

    # 尝试验证 Maven 安装
    print("\n尝试验证 Maven 安装...")
    try:
        result = subprocess.run(
            ['mvn', '-version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            first_line = result.stdout.splitlines()[0] if result.stdout else "OK"
            print(f"[OK] Maven 验证成功: {first_line}")
        else:
            print("[!] Maven 版本命令失败，需要重启终端后生效")
            print("    当前会话环境变量还没更新，这是正常的")
    except FileNotFoundError:
        print("[!] mvn 命令未找到，需要重启终端后生效")
        print("    当前会话环境变量还没更新，这是正常的")

    print()
    print("请注意:")
    print("  1. 需要重启命令提示符或终端才能看到环境变量变化")
    print("  2. 需要重启已打开的应用程序（如 Claude Code）才能使用新的环境变量")


if __name__ == "__main__":
    main()
