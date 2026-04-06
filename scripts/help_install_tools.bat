@echo off
echo ====================================================
echo ClawAI 工具安装助手
echo ====================================================
echo.

echo 正在检查系统状态...
echo.

REM 检查当前目录
echo 当前目录: %CD%
echo.

REM 检查常见工具
echo 检查已安装的工具:
echo -------------------------

if exist "C:\Windows\System32\nmap.exe" (
    echo [✅] nmap 已在系统目录
) else (
    echo [❌] nmap 未在系统目录
)

if exist "C:\Windows\System32\masscan.exe" (
    echo [✅] masscan 已在系统目录
) else (
    echo [❌] masscan 未在系统目录
)

if exist "C:\Windows\System32\python.exe" (
    echo [✅] python 已在系统目录
) else (
    echo [❌] python 未在系统目录
)

echo.
echo 检查当前目录中的工具文件:
echo -------------------------

dir *.exe *.zip *.rar *.tar *.gz 2>nul | findstr /v "找不到文件"

echo.
echo ====================================================
echo 安装说明
echo ====================================================
echo.
echo 如果您已经下载了工具文件，请按以下步骤操作:
echo.
echo 1. 找到下载的文件（通常在桌面或下载文件夹）
echo 2. 将文件复制到以下任意位置：
echo    - C:\Windows\System32 （需要管理员权限）
echo    - 当前目录 (%CD%)
echo    - 或添加到PATH的其他目录
echo.
echo 3. 常见工具文件名：
echo    - masscan.exe 或 masscan-windows.exe
echo    - nuclei.exe 或 nuclei-windows.exe
echo    - httpx.exe 或 httpx-windows.exe
echo    - nikto.zip 或 nikto.tar.gz
echo.
echo 4. 如果是压缩文件，请先解压
echo.
echo ====================================================
echo 快速测试
echo ====================================================
echo.
echo 运行以下命令测试工具：
echo.
echo 1. 检查所有工具：python tools\tool_checker.py
echo 2. 测试nmap：python backend\tools\new_nmap.py example.com
echo 3. 测试masscan：python backend\tools\new_masscan.py example.com
echo 4. 测试nikto：python backend\tools\new_nikto.py example.com
echo.
echo ====================================================
echo 常见问题
echo ====================================================
echo.
echo 问题1：找不到工具文件？
echo 解决：检查桌面、下载文件夹、文档文件夹
echo.
echo 问题2：无法复制到C:\Windows\System32？
echo 解决：以管理员身份运行此脚本
echo       或复制到当前目录 (%CD%)
echo.
echo 问题3：下载的是源码不是可执行文件？
echo 解决：需要下载Windows版本(.exe文件)
echo       或使用Docker版本
echo.
echo ====================================================
echo 下一步行动
echo ====================================================
echo.
echo 请告诉我：
echo 1. 您下载了哪些文件？（文件名）
echo 2. 文件在哪个目录？
echo 3. 您遇到了什么具体问题？
echo.
echo 我会帮您解决安装问题！
echo.
pause