---
name: dir_scan
display_name: Web 目录扫描
description: 扫描 Web 目标的常见敏感目录/文件，发现暴露资产（admin、backup、config 等），无需外部工具
category: recon
type: scanner
severity: medium
target_type: url
parameters:
  - name: target
    type: string
    required: true
    description: 目标 URL，如 http://192.168.1.1
  - name: threads
    type: integer
    required: false
    default: 10
    description: 并发线程数（1-20）
  - name: timeout
    type: integer
    required: false
    default: 5
    description: 单请求超时秒数
tags:
  - custom
  - recon
  - dirscan
author: user
---

import urllib.request
import urllib.error
import ssl
import threading
from queue import Queue

target = "{{target}}".rstrip("/")
threads = min(max(int({{threads}}), 1), 20)
timeout = int({{timeout}})

# 常见敏感路径字典
WORDLIST = [
    # 管理后台
    "admin", "admin/", "administrator", "manage", "manager", "backend",
    "panel", "dashboard", "control", "cp",
    # 常见文件
    "robots.txt", "sitemap.xml", ".htaccess", ".env", "web.config",
    "config.php", "config.json", "config.yml", "settings.py",
    # 备份
    "backup", "backup.zip", "backup.tar.gz", "db.sql", "dump.sql",
    "site.zip", "www.zip", "backup.sql",
    # 信息泄露
    "phpinfo.php", "info.php", "test.php", "shell.php",
    "readme.md", "README.md", "CHANGELOG.md", "LICENSE",
    # 版本控制
    ".git/", ".git/config", ".svn/", ".DS_Store",
    # API
    "api/", "api/v1/", "api/docs", "swagger.json", "openapi.json",
    # 日志
    "logs/", "log/", "error.log", "access.log", "debug.log",
    # 上传目录
    "upload/", "uploads/", "files/", "static/", "assets/",
    # 其他
    "install/", "setup/", "login", "logout", "register",
    "phpmyadmin/", "wp-admin/", "wp-login.php",
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

found = []
lock = threading.Lock()
queue = Queue()

for path in WORDLIST:
    queue.put(path)

def worker():
    while not queue.empty():
        try:
            path = queue.get_nowait()
        except Exception:
            break
        url = f"{target}/{path}"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (ClawAI DirScan)"},
            )
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                status = resp.status
                size = len(resp.read())
                with lock:
                    found.append((status, size, url))
        except urllib.error.HTTPError as e:
            if e.code not in (404, 410):
                # 403/401/500 等也值得记录
                with lock:
                    found.append((e.code, 0, url))
        except Exception:
            pass
        finally:
            queue.task_done()

thread_list = [threading.Thread(target=worker, daemon=True) for _ in range(threads)]
for t in thread_list:
    t.start()
for t in thread_list:
    t.join()

# 输出结果
STATUS_LABEL = {
    200: "[200 OK]      ",
    301: "[301 Redirect] ",
    302: "[302 Redirect] ",
    401: "[401 AuthReq]  ",
    403: "[403 Forbidden]",
    500: "[500 Error]    ",
}

found.sort(key=lambda x: (x[0], x[2]))

if found:
    print(f"[+] 目标: {target}")
    print(f"[+] 发现 {len(found)} 个路径：\n")
    for status, size, url in found:
        label = STATUS_LABEL.get(status, f"[{status}]         ")
        size_str = f"{size}B" if size else ""
        print(f"  {label}  {url}  {size_str}")
else:
    print(f"[-] 未发现敏感路径: {target}")
