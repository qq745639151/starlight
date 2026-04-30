#!/usr/bin/env python3
"""Check Go environment variables in the registry and compare to current go env output"""

import subprocess
import os

def get_reg_value(key: str, value_name: str) -> str | None:
    """Read a value from Windows registry"""
    result = subprocess.run(
        ['reg', 'query', key, '/v', value_name],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return None

    lines = result.stdout.splitlines()
    for line in lines:
        line = line.rstrip('\n')
        if value_name in line and 'REG_' in line:
            reg_index = line.find('REG_')
            space_after_reg = line.find(' ', reg_index)
            if space_after_reg != -1:
                return line[space_after_reg + 1:].rstrip().lstrip()
    return None

# Check system registry
print("=== Registry Check (System Environment - HKLM) ===")
goroot_reg = get_reg_value(r'HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'GOROOT')
print(f"GOROOT: {goroot_reg}")

path_reg = get_reg_value(r'HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path')
print(f"\nGo entries in system PATH:")
if path_reg:
    entries = path_reg.split(';')
    go_entries = [e for e in entries if 'go' in e.lower()]
    for entry in go_entries:
        print(f"  {entry}")
    # Check for C: entries
    c_go_entries = [e for e in entries if 'go' in e.lower() and e.lower().startswith('c:')]
    print(f"\nC: drive Go entries found in system PATH: {len(c_go_entries)}")
    for entry in c_go_entries:
        print(f"  {entry}")
else:
    print("  Could not read system PATH")

print("\n=== User Environment (HKCU) ===")
goroot_user = get_reg_value(r'HKCU\Environment', 'GOROOT')
print(f"GOROOT: {goroot_user}")

path_user = get_reg_value(r'HKCU\Environment', 'Path')
if path_user:
    entries = path_user.split(';')
    c_go_entries_user = [e for e in entries if 'go' in e.lower() and e.lower().startswith('c:')]
    print(f"C: drive Go entries found in user PATH: {len(c_go_entries_user)}")
    for entry in c_go_entries_user:
        print(f"  {entry}")

print("\n=== Current Process Environment ===")
print(f"GOROOT: {os.environ.get('GOROOT')}")
path = os.environ.get('PATH', '')
# In bash it's colon-separated, in Windows it's semicolon-separated
if ';' in path:
    entries = path.split(';')
else:
    entries = path.split(':')
go_entries_path = [e for e in entries if 'go' in e.lower()]
print(f"\nGo entries in current process PATH: {len(go_entries_path)}")
for entry in go_entries_path:
    print(f"  {entry}")

c_go_entries_proc = [e for e in entries if 'go' in e.lower() and e.lower().startswith('c:')]
print(f"\nC: drive Go entries in current process PATH: {len(c_go_entries_proc)}")
for entry in c_go_entries_proc:
    print(f"  {entry}")

print("\n=== go env Output (filtered) ===")
result = subprocess.run(['go', 'env'], capture_output=True, text=True)
if result.returncode == 0:
    go_env_lines = result.stdout.splitlines()
    key_words = ['GOROOT', 'GOTOOLDIR', 'GOCACHE', 'GOMODCACHE', 'GOPATH', 'GOENV', 'GOTELEMETRYDIR']
    for line in go_env_lines:
        if any(key in line for key in key_words):
            print(line)
else:
    print("go command failed to run")
