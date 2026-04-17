#!/usr/bin/env python3
r"""
Move Go data directories to D:\Softwares\Go

This script sets system environment variables for GOENV and GOTELEMETRYDIR
to move them from system drive to D:\Softwares\Go.

Go already handles the following via `go env -w`:
- GOPATH → D:\Softwares\Go\workspace
- GOCACHE → D:\Softwares\Go\cache
- GOMODCACHE → D:\Softwares\Go\pkg\mod

GOENV and GOTELEMETRYDIR must be set via system environment variables.
"""

import os
import sys
import subprocess
from typing import Optional


def get_system_env_var(name: str) -> Optional[str]:
    """Get a system environment variable from registry"""
    result = subprocess.run(
        ['reg', 'query', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', '/v', name],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return None

    lines = result.stdout.splitlines()
    for line in lines:
        line = line.rstrip('\n')
        if name in line and 'REG_' in line:
            reg_index = line.find('REG_')
            space_after_reg = line.find(' ', reg_index)
            if space_after_reg != -1:
                value = line[space_after_reg + 1:].rstrip().lstrip()
                return value

    return None


def set_system_env_var(name: str, value: str) -> bool:
    """Set a system environment variable in registry (requires admin)"""
    result = subprocess.run(
        ['reg', 'add', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', '/v', name, '/t', 'REG_SZ', '/d', value, '/f'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def check_admin() -> bool:
    """Check if we have admin permissions"""
    try:
        subprocess.run(
            ['reg', 'query', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment'],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ['-h', '--help']:
        print(__doc__)
        sys.exit(0)

    # Check admin
    if not check_admin():
        print("Error: Need administrator privileges to modify system environment variables")
        print("Please run this script as administrator")
        sys.exit(1)

    # Target locations
    targets = [
        ("GOENV", r"D:\Softwares\Go\env\go.env"),
        ("GOTELEMETRYDIR", r"D:\Softwares\Go\telemetry"),
    ]

    print("Moving Go data directories to D:\\Softwares\\Go")
    print()

    changed = False

    for name, target in targets:
        current = get_system_env_var(name)
        if current == target:
            print(f"[OK] {name} already set to {target}, no change needed")
            continue

        if current:
            print(f"  Current {name}: {current}")
        print(f"  Setting {name} to: {target}")

        success = set_system_env_var(name, target)
        if not success:
            print(f"Error: Failed to set {name}")
            sys.exit(1)

        print(f"[OK] {name} set successfully")
        changed = True
        print()

    if not changed:
        print("[OK] All configurations are already correct, no changes needed")
        sys.exit(0)

    print()
    print("[OK] Configuration complete!")
    print()
    print("Notes:")
    print("  1. Changes are stored in system registry")
    print("  2. You need to restart your terminal/command prompt for changes to take effect")
    print("  3. You may need to restart Claude Code/IDE for the new paths to be picked up")


if __name__ == "__main__":
    main()
