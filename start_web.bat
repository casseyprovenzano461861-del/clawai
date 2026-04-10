@echo off
title ClawAI Web
chcp 65001 >nul 2>&1
cd /d "E:\ClawAI"
echo.
echo  Starting ClawAI Web (backend + frontend)...
echo  Backend : http://localhost:8000
echo  Frontend: http://localhost:5173
echo.
"D:\Users\67096\AppData\Local\Programs\Python\Python312\python.exe" start.py --auto-port
if errorlevel 1 pause
