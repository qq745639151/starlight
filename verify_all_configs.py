#!/usr/bin/env python3
r"""
验证所有开发环境配置是否生效

验证以下环境变量和配置:
- JAVA_HOME - Java JDK
- MAVEN_HOME - Maven
- GOROOT - Go
- MINGW_HOME - MinGW-w64 C/C++
- NPM 配置 - 镜像源和全局路径
- PIP 配置 - 清华镜像源
- UV - Python 包管理器
- TRILIUM_DATA_DIR - Trilium Notes 数据目录
"""

import os
import sys
import subprocess
from typing import List, Tuple, Optional

def check_environment_var(var_name: str) -> Tuple[bool, Optional[str]]:
    """检查环境变量是否存在且路径存在"""
    value = os.environ.get(var_name)
    if not value:
        # 尝试从注册表读取系统环境变量
        try:
            result = subprocess.run(
                ['reg', 'query', r'HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment', '/v', var_name],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                for line in lines:
                    if var_name in line and 'REG_' in line:
                        reg_index = line.find('REG_')
                        space_after_reg = line.find(' ', reg_index)
                        if space_after_reg != -1:
                            value = line[space_after_reg + 1:].rstrip().lstrip()
                            break
        except Exception:
            pass
    if not value:
        return False, None
    # 检查路径是否存在
    if os.path.exists(value):
        return True, value
    else:
        return False, value

def check_command_exists(cmd: str) -> bool:
    """检查命令是否存在"""
    try:
        result = subprocess.run([cmd, '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        try:
            result = subprocess.run([cmd, '-version'], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

def check_pip_source() -> Tuple[bool, str]:
    """检查 pip 镜像源配置"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'config', 'get', 'global.index-url'], capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout.strip()
            if 'tsinghua' in output or 'mirror' in output:
                return True, output
        return False, result.stdout.strip()
    except Exception as e:
        return False, str(e)

def check_npm_config() -> Tuple[bool, List[str]]:
    """检查 npm 配置"""
    issues = []
    # 先检查 where npm
    try:
        result = subprocess.run(['where', 'npm'], capture_output=True, text=True)
        if result.returncode != 0:
            issues.append("npm 不在当前 PATH 中（系统环境变量已更新可能需要重启终端）")
            return len(issues) == 0, issues
    except Exception:
        pass

    try:
        # 检查 registry
        result = subprocess.run(['npm', 'config', 'get', 'registry'], capture_output=True, text=True)
        if result.returncode == 0:
            registry = result.stdout.strip()
            if 'taobao' not in registry and 'npmmirror' not in registry:
                issues.append(f"npm registry 不是淘宝镜像: {registry}")
        else:
            issues.append(f"npm config 命令失败 (code {result.returncode})")
    except Exception:
        # 如果调用失败，说明 PATH 没更新，但这不代表配置不对
        # 系统环境变量已经改了，只是当前会话看不到
        issues.append("无法在当前会话读取 npm 配置，系统环境变量可能已更新（需要重启终端）")
    return len(issues) == 0, issues

def get_java_version() -> Optional[str]:
    """获取 Java 版本"""
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        # java -version 输出到 stderr
        output = result.stderr.strip() or result.stdout.strip()
        if output:
            lines = output.splitlines()
            if lines:
                return lines[0]
    except Exception:
        pass
    return None

def get_maven_version() -> Optional[str]:
    """获取 Maven 版本"""
    try:
        result = subprocess.run(['mvn', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            first_line = result.stdout.strip().splitlines()[0]
            return first_line
    except Exception:
        pass
    return None

def get_go_version() -> Optional[str]:
    """获取 Go 版本"""
    try:
        result = subprocess.run(['go', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None

def get_gcc_version() -> Optional[str]:
    """获取 GCC 版本"""
    try:
        result = subprocess.run(['gcc', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            first_line = result.stdout.strip().splitlines()[0]
            return first_line
    except Exception:
        pass
    return None

def get_uv_version() -> Optional[str]:
    """获取 uv 版本"""
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None

def get_node_version() -> Optional[str]:
    """获取 Node.js 版本"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None

def main():
    print("=" * 60)
    print("开发环境配置验证")
    print("=" * 60)
    print()

    all_ok = True
    results: List[Tuple[str, bool, str]] = []

    # 1. Java JDK
    print("1. Java JDK 配置:")
    ok, value = check_environment_var('JAVA_HOME')
    if ok:
        print(f"   [OK] JAVA_HOME = {value}")
        version = get_java_version()
        if version:
            print(f"   [OK] java 命令可用: {version}")
        else:
            print(f"   [FAIL] java 命令不可用")
            all_ok = False
    else:
        if value:
            print(f"   [FAIL] JAVA_HOME = {value} (路径不存在)")
            all_ok = False
        else:
            print(f"   [FAIL] JAVA_HOME 未设置")
            all_ok = False
    results.append(("Java JDK", ok, "JAVA_HOME 环境变量"))
    print()

    # 2. Maven
    print("2. Maven 配置:")
    ok, value = check_environment_var('MAVEN_HOME')
    if ok:
        print(f"   [OK] MAVEN_HOME = {value}")
        version = get_maven_version()
        if version:
            print(f"   [OK] mvn 命令可用: {version}")
        else:
            print(f"   [FAIL] mvn 命令不可用")
            all_ok = False
    else:
        if value:
            print(f"   [FAIL] MAVEN_HOME = {value} (路径不存在)")
            all_ok = False
        else:
            print(f"   [FAIL] MAVEN_HOME 未设置")
            all_ok = False
    results.append(("Maven", ok, "MAVEN_HOME 环境变量"))
    print()

    # 3. Go
    print("3. Go 语言配置:")
    ok, value = check_environment_var('GOROOT')
    if ok:
        print(f"   [OK] GOROOT = {value}")
        version = get_go_version()
        if version:
            print(f"   [OK] go 命令可用: {version}")
        else:
            print(f"   [FAIL] go 命令不可用")
            all_ok = False
    else:
        if value:
            print(f"   [FAIL] GOROOT = {value} (路径不存在)")
            all_ok = False
        else:
            print(f"   [FAIL] GOROOT 未设置")
            all_ok = False
    results.append(("Go 语言", ok, "GOROOT 环境变量"))
    print()

    # 4. MinGW-w64
    print("4. MinGW-w64 C/C++ 配置:")
    ok, value = check_environment_var('MINGW_HOME')
    if ok:
        print(f"   [OK] MINGW_HOME = {value}")
        version = get_gcc_version()
        if version:
            print(f"   [OK] gcc 命令可用: {version}")
        else:
            print(f"   [FAIL] gcc 命令不可用")
            all_ok = False
    else:
        if value:
            print(f"   [FAIL] MINGW_HOME = {value} (路径不存在)")
            all_ok = False
        else:
            print(f"   [FAIL] MINGW_HOME 未设置")
            all_ok = False
    results.append(("MinGW-w64", ok, "MINGW_HOME 环境变量"))
    print()

    # 5. pip 清华镜像源
    print("5. pip 清华镜像源:")
    ok, output = check_pip_source()
    if ok:
        print(f"   [OK] pip 镜像源已配置: {output}")
    else:
        print(f"   [FAIL] pip 镜像源未配置为清华源: {output}")
        all_ok = False
    results.append(("pip 清华镜像", ok, "pip 全局 index-url"))
    print()

    # 6. npm 淘宝镜像源
    print("6. npm 配置:")
    ok, issues = check_npm_config()
    if ok:
        print(f"   [OK] npm 配置正确 (淘宝镜像源)")
        version = get_node_version()
        if version:
            print(f"   [OK] node 命令可用: {version}")
    else:
        for issue in issues:
            print(f"   [FAIL] {issue}")
        all_ok = False
    results.append(("npm 配置", ok, "npm 淘宝镜像和路径"))
    print()

    # 7. uv Python 包管理器
    print("7. uv Python 包管理器:")
    version = get_uv_version()
    if version:
        print(f"   [OK] uv 已安装: {version}")
        ok = True
    else:
        print(f"   [FAIL] uv 未安装或不在 PATH 中")
        ok = False
        all_ok = False
    results.append(("uv", ok, "uv 命令可执行"))
    print()

    # 8. Trilium Notes
    print("8. Trilium Notes 数据目录:")
    ok, value = check_environment_var('TRILIUM_DATA_DIR')
    if ok:
        print(f"   [OK] TRILIUM_DATA_DIR = {value}")
    else:
        if value:
            print(f"   [FAIL] TRILIUM_DATA_DIR = {value} (路径不存在)")
            all_ok = False
        else:
            print(f"   [FAIL] TRILIUM_DATA_DIR 未设置")
            all_ok = False
    results.append(("Trilium Notes", ok, "TRILIUM_DATA_DIR 环境变量"))
    print()

    # 总结
    print("=" * 60)
    print("验证总结:")
    print("=" * 60)
    print()

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)

    for name, ok, desc in results:
        status = "[OK] 通过" if ok else "[FAIL] 失败"
        print(f"  {name:<15} {status} - {desc}")

    print()
    print(f"结果: {passed}/{total} 项配置通过验证")

    if all_ok:
        print()
        print("[OK] 所有配置都已正确生效!")
        return 0
    else:
        print()
        print("[FAIL] 部分配置未生效，请检查上述失败项")
        return 1

if __name__ == "__main__":
    sys.exit(main())
