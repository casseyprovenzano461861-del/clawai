@echo off
REM Test script to verify menu options
chcp 65001 >nul 2>nul

echo ============================================
echo   Testing ClawAI Menu Options
echo ============================================

REM Test option 7 (System Info)
echo.
echo Testing Option 7 - System Information:
echo 7 | scripts\start.bat

timeout /t 5 >nul

REM Test option 8 (Exit)
echo.
echo Testing Option 8 - Exit:
echo 8 | scripts\start.bat

echo.
echo Menu testing completed!
pause