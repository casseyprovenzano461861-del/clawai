@echo off
REM ClawAI 核心工具下载安装脚本
REM 从GitHub下载Windows可执行文件，提升真实执行比例

echo ========================================
echo ClawAI 核心工具下载安装助手
echo 目标: 安装核心工具，提升真实执行比例
echo ========================================
echo.

REM 设置目录
set TOOLS_DIR=e:\ClawAI\tools_bin
if not exist "%TOOLS_DIR%" mkdir "%TOOLS_DIR%"

echo 创建工具目录: %TOOLS_DIR%
echo.

REM 1. 下载 HTTPX
echo [1/5] 下载 HTTPX...
echo 从 GitHub 下载 HTTPX Windows 版本...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/projectdiscovery/httpx/releases/download/v1.6.1/httpx_1.6.1_windows_amd64.zip' -OutFile '%TOOLS_DIR%\httpx.zip'"
if exist "%TOOLS_DIR%\httpx.zip" (
    powershell -Command "Expand-Archive -Path '%TOOLS_DIR%\httpx.zip' -DestinationPath '%TOOLS_DIR%\httpx' -Force"
    copy "%TOOLS_DIR%\httpx\httpx.exe" "%TOOLS_DIR%\"
    echo ✓ HTTPX 下载完成
) else (
    echo ✗ HTTPX 下载失败，请手动下载
    echo   下载地址: https://github.com/projectdiscovery/httpx/releases
)

REM 2. 下载 Nuclei
echo.
echo [2/5] 下载 Nuclei...
echo 从 GitHub 下载 Nuclei Windows 版本...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/projectdiscovery/nuclei/releases/download/v3.3.1/nuclei_3.3.1_windows_amd64.zip' -OutFile '%TOOLS_DIR%\nuclei.zip'"
if exist "%TOOLS_DIR%\nuclei.zip" (
    powershell -Command "Expand-Archive -Path '%TOOLS_DIR%\nuclei.zip' -DestinationPath '%TOOLS_DIR%\nuclei' -Force"
    copy "%TOOLS_DIR%\nuclei\nuclei.exe" "%TOOLS_DIR%\"
    echo ✓ Nuclei 下载完成
) else (
    echo ✗ Nuclei 下载失败，请手动下载
    echo   下载地址: https://github.com/projectdiscovery/nuclei/releases
)

REM 3. 下载 WhatWeb
echo.
echo [3/5] 下载 WhatWeb...
echo 注意: WhatWeb 需要 Ruby 环境，先下载可执行文件...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/urbanadventurer/WhatWeb/archive/refs/heads/master.zip' -OutFile '%TOOLS_DIR%\whatweb.zip'"
if exist "%TOOLS_DIR%\whatweb.zip" (
    powershell -Command "Expand-Archive -Path '%TOOLS_DIR%\whatweb.zip' -DestinationPath '%TOOLS_DIR%\whatweb' -Force"
    echo ✓ WhatWeb 源码下载完成
    echo   注意: WhatWeb 需要 Ruby 环境
    echo   安装 Ruby: https://rubyinstaller.org/
) else (
    echo ✗ WhatWeb 下载失败，请手动下载
    echo   下载地址: https://github.com/urbanadventurer/WhatWeb
)

REM 4. 下载 SQLMap
echo.
echo [4/5] 下载 SQLMap...
echo 下载 SQLMap 源码...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/sqlmapproject/sqlmap/archive/refs/heads/master.zip' -OutFile '%TOOLS_DIR%\sqlmap.zip'"
if exist "%TOOLS_DIR%\sqlmap.zip" (
    powershell -Command "Expand-Archive -Path '%TOOLS_DIR%\sqlmap.zip' -DestinationPath '%TOOLS_DIR%\sqlmap' -Force"
    echo ✓ SQLMap 源码下载完成
    echo   注意: SQLMap 需要 Python 环境
    echo   安装 Python: https://www.python.org/downloads/
) else (
    echo ✗ SQLMap 下载失败，请手动下载
    echo   下载地址: https://github.com/sqlmapproject/sqlmap
)

REM 5. 下载 Nikto
echo.
echo [5/5] 下载 Nikto...
echo 下载 Nikto 源码...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/sullo/nikto/archive/refs/heads/master.zip' -OutFile '%TOOLS_DIR%\nikto.zip'"
if exist "%TOOLS_DIR%\nikto.zip" (
    powershell -Command "Expand-Archive -Path '%TOOLS_DIR%\nikto.zip' -DestinationPath '%TOOLS_DIR%\nikto' -Force"
    echo ✓ Nikto 源码下载完成
    echo   注意: Nikto 需要 Perl 环境
    echo   安装 Strawberry Perl: https://strawberryperl.com/
) else (
    echo ✗ Nikto 下载失败，请手动下载
    echo   下载地址: https://github.com/sullo/nikto
)

echo.
echo ========================================
echo 下载完成汇总
echo ========================================
echo.
echo 已下载工具位置: %TOOLS_DIR%
echo.
echo 文件列表:
dir "%TOOLS_DIR%" /b
echo.
echo [重要] 下一步操作:
echo 1. 将工具目录添加到系统 PATH 环境变量
echo   在命令提示符中运行:
echo   setx PATH "%%PATH%%;%TOOLS_DIR%"
echo.
echo 2. 或者将工具复制到已有 PATH 路径中
echo   如: C:\Windows 或 C:\Program Files
echo.
echo 3. 安装必要的运行环境:
echo   - Python (SQLMap, dirsearch)
echo   - Ruby (WhatWeb)
echo   - Perl (Nikto)
echo.
echo 4. 运行测试验证工具安装:
echo   python tools\tool_checker.py
echo   python test_real_execution_ratio_final.py
echo.
echo ========================================
echo 提示: 如果工具无法运行，请确保安装了必要的运行环境
echo ========================================
pause