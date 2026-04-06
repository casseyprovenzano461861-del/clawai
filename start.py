#!/usr/bin/env python3
"""
Simple startup script for ClawAI
"""
import os
import sys
import socket
import subprocess
import time

def check_port(port):
    """Check if port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(('localhost', port)) != 0
    except:
        return False

def find_available_port(start=8000, end=8010):
    """Find an available port in range"""
    for port in range(start, end + 1):
        if check_port(port):
            return port
    return None

def main():
    print("=" * 40)
    print("ClawAI Startup Script")
    print("=" * 40)

    # Check Python version
    if sys.version_info < (3, 11):
        print(f"ERROR: Python 3.11+ required, found {sys.version_info.major}.{sys.version_info.minor}")
        return 1

    # Check virtual environment
    venv_dir = ".venv"
    if not os.path.exists(venv_dir):
        print(f"Creating virtual environment at {venv_dir}...")
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)

    # Activate virtual environment (in current process)
    # Note: This script should be run from outside the venv

    # Find available port
    port = find_available_port()
    if port is None:
        print("ERROR: No available ports in range 8000-8010")
        print("Please close applications using these ports or modify port range")
        return 1

    print(f"\nStarting ClawAI on port {port}")
    print(f"API Documentation: http://localhost:{port}/docs")
    print(f"Health Check: http://localhost:{port}/health")
    print("\nPress Ctrl+C to stop\n")

    # Start the application
    try:
        # Use the virtual environment's python
        if os.name == 'nt':  # Windows
            python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
        else:  # Unix/Linux
            python_exe = os.path.join(venv_dir, "bin", "python")

        if not os.path.exists(python_exe):
            python_exe = sys.executable

        cmd = [python_exe, "run.py", "--port", str(port)]
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())