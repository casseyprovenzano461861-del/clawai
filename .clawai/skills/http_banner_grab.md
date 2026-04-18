---
name: http_banner_grab
display_name: HTTP Banner 抓取
description: 抓取目标 Web 服务器的响应头信息（Server、X-Powered-By 等），辅助指纹识别
category: recon
type: scanner
severity: info
target_type: url
parameters:
  - name: target
    type: string
    required: true
    description: 目标 URL，如 http://192.168.1.1
  - name: timeout
    type: integer
    required: false
    default: 10
    description: 请求超时秒数
tags:
  - custom
  - recon
  - banner
author: user
---

import urllib.request
import urllib.error
import ssl

target = "{{target}}"
timeout = {{timeout}}

# 忽略证书验证（内网/靶场环境）
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    req = urllib.request.Request(target, headers={"User-Agent": "ClawAI-Scanner/1.0"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        print(f"[+] Status: {resp.status} {resp.reason}")
        interesting = ["Server", "X-Powered-By", "X-AspNet-Version", "X-Generator", "Via"]
        found_any = False
        for h in interesting:
            v = resp.headers.get(h)
            if v:
                print(f"[+] {h}: {v}")
                found_any = True
        if not found_any:
            print("[-] 未发现敏感头信息")
        # 读取部分响应体，检查框架特征
        body = resp.read(512).decode('utf-8', errors='ignore')
        for kw in ["WordPress", "Drupal", "Joomla", "Laravel", "Django", "Flask", "phpMyAdmin"]:
            if kw.lower() in body.lower():
                print(f"[+] 检测到框架特征: {kw}")
except urllib.error.HTTPError as e:
    print(f"[!] HTTP Error {e.code}: {e.reason}")
except Exception as e:
    print(f"[!] 连接失败: {e}")
