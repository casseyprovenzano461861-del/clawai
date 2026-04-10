@echo off
chcp 65001 >nul 2>&1
"D:\Users\67096\AppData\Local\Programs\Python\Python312\python.exe" "E:\ClawAI\clawai.py" %*
if errorlevel 1 pause
