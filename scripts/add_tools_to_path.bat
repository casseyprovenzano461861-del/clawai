@echo off
echo ====================================================
echo ClawAI 工具路径配置助手
echo ====================================================
echo.

echo 检测到工具安装在 C:\Tools 目录
echo.

echo 检查工具文件:
echo -------------------------
if exist "C:\Tools\httpx\httpx.exe" (
    echo [✅] httpx.exe 存在
) else (
    echo [❌] httpx.exe 不存在
)

if exist "C:\Tools\nuclei\nuclei.exe" (
    echo [✅] nuclei.exe 存在
) else (
    echo [❌] nuclei.exe 不存在
)

REM 检查masscan可执行文件
if exist "C:\Tools\masscan-master\bin\masscan.exe" (
    echo [✅] masscan.exe 存在 (在bin目录)
) else if exist "C:\Tools\masscan-master\masscan.exe" (
    echo [✅] masscan.exe 存在
) else (
    echo [⚠️] masscan.exe 不存在，需要编译或下载预编译版本
)

echo.
echo ====================================================
echo 解决方案
echo ====================================================
echo.

echo 方案1：复制到系统PATH目录（推荐）
echo.
echo 将以下文件复制到 C:\Windows\System32:
echo   1. C:\Tools\httpx\httpx.exe
echo   2. C:\Tools\nuclei\nuclei.exe
echo.
echo 如果是管理员权限，运行：
echo   copy "C:\Tools\httpx\httpx.exe" "C:\Windows\System32\"
echo   copy "C:\Tools\nuclei\nuclei.exe" "C:\Windows\System32\"
echo.

echo 方案2：添加C:\Tools到PATH环境变量
echo.
echo 1. 右键点击"此电脑" -> "属性" -> "高级系统设置"
echo 2. 点击"环境变量"
echo 3. 在"系统变量"或"用户变量"中找到"Path"
echo 4. 点击"编辑" -> "新建"
echo 5. 添加以下路径：
echo    - C:\Tools\httpx
echo    - C:\Tools\nuclei
echo    - C:\Tools\WhatWeb
echo    - C:\Tools\nikto-main\program
echo.

echo 方案3：使用临时PATH
echo.
echo 在当前命令行中运行：
echo   set PATH=C:\Tools\httpx;%PATH%
echo   set PATH=C:\Tools\nuclei;%PATH%
echo   set PATH=C:\Tools\WhatWeb;%PATH%
echo.

echo ====================================================
echo 对于masscan的特殊处理
echo ====================================================
echo.
echo masscan是源码，需要编译或下载预编译版本：
echo.
echo 1. 下载预编译版本：
echo    访问：https://github.com/robertdavidgraham/masscan/releases
echo    下载 masscan-windows.exe
echo    重命名为 masscan.exe
echo    复制到 C:\Tools\ 或 C:\Windows\System32\
echo.
echo 2. 或编译源码：
echo    需要Visual Studio和make工具
echo    打开开发者命令提示符，运行：
echo      cd C:\Tools\masscan-master
echo      nmake /f Makefile.win
echo.

echo ====================================================
echo 对于nikto的特殊处理
echo ====================================================
echo.
echo nikto需要Perl环境：
echo.
echo 1. 安装Perl: https://www.perl.org/get.html
echo 2. 安装必要模块：
echo      ppm install LWP::Protocol::https
echo      ppm install Net::SSLeay
echo 3. 运行：perl C:\Tools\nikto-main\program\nikto.pl -h http://example.com
echo.
echo 或使用Docker：
echo   docker pull sullo/nikto
echo   docker run --rm sullo/nikto -h http://example.com
echo.

echo ====================================================
echo 测试命令
echo ====================================================
echo.
echo 测试httpx：
echo   C:\Tools\httpx\httpx.exe -version
echo.
echo 测试nuclei：
echo   C:\Tools\nuclei\nuclei.exe -version
echo.
echo 测试ClawAI集成：
echo   python backend\tools\new_nmap.py example.com
echo   （先确保工具在PATH中）
echo.
echo ====================================================
echo 快速修复脚本
echo ====================================================
echo.
echo 创建临时修复（仅当前会话有效）：
echo   set PATH=C:\Tools\httpx;C:\Tools\nuclei;%PATH%
echo   echo 已添加httpx和nuclei到PATH
echo.
echo 然后测试：
echo   httpx -version
echo   nuclei -version
echo.
pause