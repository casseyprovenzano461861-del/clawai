#!/usr/bin/env python3
import subprocess
import sys

def main():
    """Nmap包装器"""
    cmd = ['C:\Program Files (x86)\Nmap\nmap.exe'] + sys.argv[1:]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
