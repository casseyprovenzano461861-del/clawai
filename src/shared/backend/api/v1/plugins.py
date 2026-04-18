# -*- coding: utf-8 -*-
"""
插件管理API端点
提供插件的查询、安装、启用/禁用、更新和配置管理
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import Field
import logging

from backend.auth.fastapi_permissions import require_authentication
from backend.schemas.base import BaseSchema
from backend.schemas.error import APIError, ErrorCode

router = APIRouter(prefix="/api/v1/plugins", tags=["插件管理"])

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 内存存储（生产环境应使用数据库）
# ──────────────────────────────────────────────
_NOW = datetime.now().isoformat()
_INSTALLED_AT = "2026-04-01T00:00:00"


def _tool(id_, name, version, desc, author, category, icon, tags,
          downloads, rating, size, installed=False, enabled=False, settings=None):
    return {
        "id": id_, "name": name, "version": version, "description": desc,
        "author": author, "category": category, "type": category, "icon": icon,
        "tags": tags, "downloads": downloads, "rating": rating, "size": size,
        "installed": installed, "enabled": enabled,
        "status": "active" if installed else "available",
        "installed_at": _INSTALLED_AT if installed else None,
        "updated_at": _NOW,
        "settings": settings or {},
    }


_PLUGINS: Dict[str, Dict[str, Any]] = {p["id"]: p for p in [
    # ── 端口扫描 / 网络探测 ──────────────────────────────
    _tool("nmap", "Nmap 网络扫描器", "7.94.0",
          "业界标准的网络探测与安全审计工具，支持端口扫描、服务识别、OS检测、NSE脚本",
          "Gordon Lyon", "scanner", "🔍",
          ["network", "port-scan", "os-detection", "nse"],
          125000, 4.9, "8.2 MB", installed=True, enabled=True,
          settings={"timeout": 30, "max_retries": 3, "default_flags": "-sV -O"}),

    _tool("masscan", "Masscan 高速扫描", "1.3.2",
          "互联网级别的高速端口扫描器，速度可达每秒千万数据包",
          "Robert Graham", "scanner", "⚡",
          ["network", "port-scan", "fast"],
          52000, 4.6, "1.8 MB", installed=True, enabled=True,
          settings={"rate": 10000, "timeout": 5}),

    _tool("rustscan", "RustScan 快速扫描", "2.2.2",
          "用Rust编写的超快端口扫描器，可与Nmap无缝集成",
          "RustScan Team", "scanner", "🦀",
          ["network", "port-scan", "rust", "fast"],
          38000, 4.7, "5.4 MB", installed=True, enabled=True,
          settings={"batch_size": 4500, "timeout": 1500}),

    _tool("httpx", "HTTPX HTTP探测", "1.6.5",
          "快速多功能HTTP工具包，支持批量探测HTTP/HTTPS服务状态、技术指纹",
          "ProjectDiscovery", "scanner", "🌐",
          ["http", "web", "fingerprint"],
          61000, 4.8, "12.3 MB", installed=True, enabled=True),

    # ── Web 扫描 ─────────────────────────────────────────
    _tool("nuclei", "Nuclei 漏洞扫描", "3.2.1",
          "基于模板的漏洞扫描器，拥有7000+个CVE/漏洞模板库",
          "ProjectDiscovery", "scanner", "☢️",
          ["vulnerability", "cve", "template", "web"],
          67000, 4.8, "45 MB", installed=True, enabled=True,
          settings={"concurrency": 25, "rate_limit": 150, "timeout": 5}),

    _tool("nikto", "Nikto Web扫描", "2.1.6",
          "开源Web服务器扫描器，可检测6700+危险文件/CGI、过时软件和配置问题",
          "CIRT.net", "scanner", "🕵️",
          ["web", "server", "misconfiguration"],
          78000, 4.4, "2.1 MB", installed=True, enabled=True),

    _tool("whatweb", "WhatWeb 指纹识别", "0.5.5",
          "Web应用指纹识别工具，可识别CMS、博客平台、JS库、Web服务器等1800+插件",
          "Andrew Horton", "recon", "🏷️",
          ["fingerprint", "web", "cms"],
          41000, 4.5, "4.2 MB", installed=True, enabled=True),

    _tool("wafw00f", "WAFW00F WAF检测", "2.2.0",
          "自动检测目标Web应用是否部署了WAF以及WAF类型，支持170+种WAF指纹",
          "Enablesecurity", "recon", "🛡️",
          ["waf", "fingerprint", "web"],
          33000, 4.4, "1.5 MB", installed=True, enabled=True),

    # ── 目录/路径枚举 ────────────────────────────────────
    _tool("gobuster", "Gobuster 目录枚举", "3.6.0",
          "用Go编写的目录/文件/DNS/VHost暴力破解工具，支持多种枚举模式",
          "OJ Reeves", "scanner", "📂",
          ["directory", "fuzzing", "dns", "web"],
          58000, 4.6, "7.8 MB", installed=True, enabled=True,
          settings={"threads": 10, "timeout": 10}),

    _tool("dirsearch", "Dirsearch 目录扫描", "0.4.3",
          "高速Web路径暴力破解和目录枚举工具，内置庞大字典库",
          "maurosoria", "scanner", "📁",
          ["directory", "fuzzing", "web"],
          45000, 4.4, "3.8 MB", installed=True, enabled=True),

    _tool("ffuf", "FFUF 模糊测试", "2.1.0",
          "用Go编写的高速Web模糊测试工具，支持URL/Header/POST数据模糊",
          "joohoi", "scanner", "🎯",
          ["fuzzing", "web", "wordlist"],
          49000, 4.7, "9.1 MB", installed=True, enabled=True,
          settings={"threads": 40, "rate": 0, "timeout": 10}),

    _tool("feroxbuster", "Feroxbuster 递归枚举", "2.10.4",
          "用Rust编写的快速、简单且递归的内容发现工具",
          "epi052", "scanner", "🔄",
          ["directory", "recursive", "web", "rust"],
          29000, 4.6, "11.2 MB", installed=True, enabled=True),

    # ── SQL 注入 / Web 攻击 ──────────────────────────────
    _tool("sqlmap", "SQLMap 注入检测", "1.8.3",
          "自动化SQL注入漏洞检测与利用工具，支持MySQL/PostgreSQL/Oracle/MSSQL等",
          "sqlmapproject", "exploit", "💉",
          ["sql-injection", "database", "web"],
          89000, 4.7, "5.1 MB", installed=True, enabled=True,
          settings={"level": 1, "risk": 1, "threads": 4}),

    _tool("xsstrike", "XSStrike XSS检测", "3.1.5",
          "高级XSS检测套件，内置爬虫、模糊测试引擎和手工Payload生成器",
          "s0md3v", "exploit", "🎭",
          ["xss", "web", "injection"],
          31000, 4.5, "2.3 MB", installed=True, enabled=True),

    _tool("commix", "Commix 命令注入", "3.9",
          "自动化命令注入漏洞检测和利用工具，支持时间盲注、半盲注等",
          "commixproject", "exploit", "💻",
          ["command-injection", "web", "rce"],
          22000, 4.3, "4.7 MB", installed=True, enabled=True),

    _tool("tplmap", "Tplmap SSTI检测", "0.5",
          "服务器端模板注入（SSTI）漏洞自动检测与利用工具",
          "epinna", "exploit", "🧪",
          ["ssti", "template-injection", "web"],
          18000, 4.3, "3.1 MB"),

    # ── 信息收集 / 子域名 ────────────────────────────────
    _tool("amass", "Amass 资产枚举", "4.2.0",
          "深度攻击面映射与资产发现工具，整合50+数据源进行子域名枚举",
          "OWASP", "recon", "🗺️",
          ["subdomain", "recon", "osint"],
          54000, 4.7, "18.6 MB", installed=True, enabled=True),

    _tool("subfinder", "Subfinder 子域名发现", "2.6.6",
          "被动子域名发现工具，聚合47+数据源，速度快且准确率高",
          "ProjectDiscovery", "recon", "🔭",
          ["subdomain", "passive", "recon"],
          48000, 4.8, "8.9 MB", installed=True, enabled=True),

    _tool("sublist3r", "Sublist3r 子域名枚举", "1.1",
          "使用OSINT技术的子域名枚举工具，整合Google/Bing/Yahoo等搜索引擎",
          "aboul3la", "recon", "📡",
          ["subdomain", "osint", "recon"],
          36000, 4.2, "1.4 MB"),

    _tool("theharvester", "theHarvester 信息收集", "4.4.0",
          "通过搜索引擎、数据库收集邮件地址、子域名、IP、员工姓名等信息",
          "laramies", "recon", "🌾",
          ["email", "subdomain", "osint", "recon"],
          42000, 4.4, "3.2 MB", installed=True, enabled=True),

    _tool("dnsrecon", "DNSRecon DNS侦察", "1.1.4",
          "全面的DNS枚举工具，支持区域传送、暴力枚举、反向查询等",
          "darkoperator", "recon", "🔎",
          ["dns", "recon", "enumeration"],
          29000, 4.3, "2.8 MB", installed=True, enabled=True),

    _tool("whois-tool", "WHOIS 查询工具", "5.5.22",
          "查询域名/IP注册信息、注册人、注册时间、到期时间等WHOIS数据",
          "IANA", "recon", "📋",
          ["whois", "domain", "recon"],
          65000, 4.1, "0.5 MB", installed=True, enabled=True),

    # ── SSL/TLS 检测 ─────────────────────────────────────
    _tool("sslscan", "SSLScan SSL扫描", "2.1.3",
          "快速SSL/TLS扫描工具，检测弱密码套件、协议版本、心脏滴血等漏洞",
          "rbsec", "scanner", "🔒",
          ["ssl", "tls", "certificate"],
          27000, 4.5, "1.9 MB", installed=True, enabled=True),

    _tool("testssl", "TestSSL.sh TLS测试", "3.2",
          "全面的SSL/TLS测试工具，检测配置错误、协议弱点、证书问题",
          "testssl.sh", "scanner", "🧩",
          ["ssl", "tls", "security-audit"],
          21000, 4.4, "2.7 MB"),

    # ── CMS 扫描 ─────────────────────────────────────────
    _tool("wpscan", "WPScan WordPress扫描", "3.8.25",
          "WordPress安全扫描器，枚举用户/插件/主题并检测已知漏洞",
          "WPScan Team", "scanner", "📰",
          ["wordpress", "cms", "web"],
          56000, 4.6, "4.3 MB", installed=True, enabled=True,
          settings={"enumerate": "u,p,t,vp,vt", "api_token": ""}),

    _tool("enhanced-wpscan", "增强版 WPScan", "3.8.25+",
          "集成AI分析的WordPress扫描器，自动关联CVE并生成攻击建议",
          "ClawAI Team", "scanner", "🚀",
          ["wordpress", "cms", "ai", "enhanced"],
          8000, 4.8, "4.5 MB", installed=True, enabled=True),

    _tool("joomscan", "JoomScan Joomla扫描", "0.0.7",
          "OWASP维护的Joomla CMS漏洞扫描器",
          "OWASP", "scanner", "🔩",
          ["joomla", "cms", "web"],
          18000, 4.1, "1.1 MB"),

    _tool("droopescan", "Droopescan CMS扫描", "1.45.1",
          "支持Drupal/SilverStripe/WordPress/Joomla/Moodle等多CMS插件扫描",
          "droope", "scanner", "🕸️",
          ["drupal", "cms", "multi"],
          14000, 4.0, "1.3 MB"),

    _tool("cmsmap", "CMSMap CMS漏洞扫描", "1.0",
          "自动检测主流CMS漏洞，支持WordPress/Joomla/Drupal/Moodle",
          "Dionach", "scanner", "🗂️",
          ["cms", "wordpress", "joomla", "drupal"],
          11000, 4.0, "0.9 MB"),

    # ── 密码破解 ─────────────────────────────────────────
    _tool("hydra", "Hydra 在线爆破", "9.5",
          "支持50+协议的快速在线密码破解工具（FTP/SSH/HTTP/SMB等）",
          "vanhauser-thc", "brute-force", "🔓",
          ["brute-force", "login", "protocol"],
          78000, 4.3, "1.2 MB", installed=True, enabled=True,
          settings={"threads": 16, "timeout": 30}),

    _tool("medusa", "Medusa 并行爆破", "2.2",
          "高速并行网络登录密码破解工具，支持多种认证协议",
          "foofus.net", "brute-force", "🐍",
          ["brute-force", "parallel", "login"],
          25000, 4.1, "0.8 MB"),

    _tool("hashcat", "Hashcat GPU破解", "6.2.6",
          "世界最快的GPU密码恢复工具，支持350+哈希算法",
          "hashcat.net", "brute-force", "⚙️",
          ["hash", "gpu", "password-cracking"],
          92000, 4.9, "22 MB", installed=True, enabled=True,
          settings={"workload": 3, "opencl_device_types": "1,2"}),

    _tool("john", "John the Ripper", "1.9.0",
          "经典密码破解工具，支持多种加密格式的字典和暴力破解",
          "openwall", "brute-force", "🔑",
          ["hash", "password-cracking", "dictionary"],
          105000, 4.5, "3.1 MB", installed=True, enabled=True),

    # ── 后渗透 / 横向移动 ────────────────────────────────
    _tool("metasploit", "Metasploit 框架", "6.4.0",
          "世界最广泛使用的渗透测试框架，提供2000+漏洞利用模块",
          "Rapid7", "exploit", "💀",
          ["exploit", "post-exploitation", "payloads"],
          234000, 4.9, "512 MB",
          settings={}),

    _tool("impacket", "Impacket 网络协议", "0.12.0",
          "Python网络协议工具集，支持SMB/MSRPC/NTLM/Kerberos等Windows协议",
          "SecureAuth", "post-exploit", "🧰",
          ["windows", "smb", "kerberos", "lateral-movement"],
          47000, 4.7, "8.4 MB", installed=True, enabled=True),

    _tool("evil-winrm", "Evil-WinRM 远程管理", "3.5",
          "专为渗透测试设计的WinRM Shell，支持文件传输、PowerShell加载等",
          "Hackplayers", "post-exploit", "😈",
          ["windows", "winrm", "shell"],
          32000, 4.6, "2.1 MB", installed=True, enabled=True),

    _tool("crackmapexec", "CrackMapExec 内网渗透", "5.4.0",
          "内网评估瑞士军刀，支持SMB/WMI/MSSQL/LDAP等协议的批量认证和命令执行",
          "byt3bl33d3r", "post-exploit", "🗡️",
          ["windows", "smb", "active-directory", "lateral-movement"],
          38000, 4.7, "15.6 MB", installed=True, enabled=True),

    _tool("searchsploit", "SearchSploit 漏洞库", "4.6.0",
          "Exploit-DB离线搜索工具，本地查询40000+个公开漏洞利用代码",
          "Offensive Security", "exploit", "🔬",
          ["exploit-db", "cve", "offline"],
          61000, 4.8, "1.1 GB", installed=True, enabled=True),

    # ── AI / 报告 ─────────────────────────────────────────
    _tool("ai-report-gen", "AI 智能报告生成器", "1.2.0",
          "基于AI的渗透测试报告自动生成，支持HTML/PDF/JSON多种格式导出",
          "ClawAI Team", "reporting", "📊",
          ["ai", "report", "automation"],
          15000, 4.5, "2.3 MB", installed=True, enabled=True,
          settings={"language": "zh-CN", "template": "standard", "include_charts": True}),

    _tool("burpsuite-integration", "Burp Suite 集成", "2024.1",
          "Web应用安全测试平台集成，支持代理拦截、主动/被动扫描",
          "PortSwigger", "proxy", "🕷️",
          ["web", "proxy", "scanner", "intercept"],
          98000, 4.6, "156 MB",
          settings={}),

    # ── Demo 插件（来自 ClawAI 插件市场 Demo）──────────────
    {
        "id": "jwt_scanner",
        "name": "JWT 安全检测器",
        "version": "1.0.0",
        "description": "自动检测 JSON Web Token 安全漏洞：alg:none 混淆攻击、弱签名密钥（内置500+字典）、敏感信息泄露、过期校验缺失",
        "author": "ClawAI Demo Team",
        "author_url": "https://github.com/clawai-demo/jwt_scanner",
        "category": "exploit",
        "type": "exploit",
        "icon": "🔐",
        "tags": ["jwt", "authentication", "token", "web"],
        "downloads": 3200,
        "rating": 4.7,
        "size": "0.3 MB",
        "installed": True,
        "enabled": True,
        "status": "active",
        "installed_at": "2026-04-11T00:00:00",
        "updated_at": _NOW,
        "license": "MIT",
        "source": "demo",
        "plugin_path": "plugins/demo/jwt_scanner",
        "settings": {
            "check_alg_none": True,
            "check_weak_secret": True,
            "wordlist": "builtin",
            "timeout": 10,
        },
        "permissions": ["http:request", "finding:report"],
    },
    {
        "id": "log4shell_scanner",
        "name": "Log4Shell 漏洞检测",
        "version": "1.2.0",
        "description": "专项检测 CVE-2021-44228 (Log4Shell) 及变体。通过 JNDI payload 注入与内置 HTTP 回调验证，无需外部 DNSLOG 服务",
        "author": "ClawAI Demo Team",
        "author_url": "https://github.com/clawai-demo/log4shell_scanner",
        "category": "exploit",
        "type": "exploit",
        "icon": "🔥",
        "tags": ["log4j", "log4shell", "rce", "cve-2021-44228", "jndi"],
        "downloads": 5800,
        "rating": 4.9,
        "size": "0.5 MB",
        "installed": True,
        "enabled": True,
        "status": "active",
        "installed_at": "2026-04-11T00:00:00",
        "updated_at": _NOW,
        "license": "MIT",
        "source": "demo",
        "plugin_path": "plugins/demo/log4shell_scanner",
        "cve_references": ["CVE-2021-44228", "CVE-2021-45046", "CVE-2021-45105"],
        "settings": {
            "callback_server": "",
            "inject_headers": ["User-Agent", "X-Forwarded-For", "Referer", "X-Api-Version"],
            "check_variants": True,
            "timeout": 15,
        },
        "permissions": ["http:request", "dns:listen", "finding:report", "network:callback"],
    },
    {
        "id": "ai_payload_gen",
        "name": "AI 辅助 Payload 生成器",
        "version": "2.0.0",
        "description": "基于 LLM 的智能 Payload 生成器，根据目标技术栈和 WAF 类型生成绕过变体，支持 SQLi/XSS/SSTI/SSRF/RCE/LFI/XXE 等10+ 漏洞类型",
        "author": "ClawAI Demo Team",
        "author_url": "https://github.com/clawai-demo/ai_payload_gen",
        "category": "ai_enhanced",
        "type": "ai_enhanced",
        "icon": "🤖",
        "tags": ["ai", "payload", "waf-bypass", "sqli", "xss", "llm"],
        "downloads": 4100,
        "rating": 4.8,
        "size": "0.4 MB",
        "installed": True,
        "enabled": True,
        "status": "active",
        "installed_at": "2026-04-11T00:00:00",
        "updated_at": _NOW,
        "license": "MIT",
        "source": "demo",
        "plugin_path": "plugins/demo/ai_payload_gen",
        "settings": {
            "model": "auto",
            "vuln_types": ["sqli", "xss", "ssti", "ssrf", "rce", "lfi", "xxe"],
            "variants_count": 5,
            "waf_aware": True,
            "context_aware": True,
        },
        "permissions": ["llm:call", "finding:read", "finding:update", "skill:register"],
    },
]}

_MARKETPLACE_EXTRA: List[Dict[str, Any]] = []  # 所有工具已在 _PLUGINS 中，市场展示全集


# ──────────────────────────────────────────────
# Pydantic 模型
# ──────────────────────────────────────────────
class PluginSettingsUpdate(BaseSchema):
    settings: Dict[str, Any] = Field(..., description="插件配置项")


# ──────────────────────────────────────────────
# 路由
# ──────────────────────────────────────────────
@router.get("")
async def list_plugins(
    category: Optional[str] = Query(None, description="按分类过滤"),
    installed: Optional[bool] = Query(None, description="只显示已安装"),
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取插件列表"""
    try:
        plugins = list(_PLUGINS.values())
        if category:
            plugins = [p for p in plugins if p.get("category") == category]
        if installed is not None:
            plugins = [p for p in plugins if p.get("installed") == installed]

        return {
            "success": True,
            "data": plugins,
            "total": len(plugins)
        }
    except Exception as e:
        logger.error(f"获取插件列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(code=ErrorCode.UNKNOWN_ERROR, message="获取插件列表失败", severity="high").model_dump()
        )


@router.get("/marketplace")
async def get_marketplace(
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取插件市场（包含未安装插件）"""
    try:
        all_plugins = list(_PLUGINS.values()) + _MARKETPLACE_EXTRA
        return {
            "success": True,
            "data": all_plugins,
            "total": len(all_plugins),
            "categories": ["scanner", "exploit", "recon", "post-exploit", "brute-force", "proxy", "reporting"]
        }
    except Exception as e:
        logger.error(f"获取插件市场失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(code=ErrorCode.UNKNOWN_ERROR, message="获取插件市场失败", severity="high").model_dump()
        )


@router.get("/{plugin_id}")
async def get_plugin(
    plugin_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取插件详情"""
    plugin = _PLUGINS.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"插件 {plugin_id} 不存在", severity="low").model_dump()
        )
    return {"success": True, "data": plugin}


@router.post("/{plugin_id}/install")
async def install_plugin(
    plugin_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """安装插件"""
    try:
        # 先在已知插件中查找
        plugin = _PLUGINS.get(plugin_id)
        if not plugin:
            # 从市场列表查找
            market_plugin = next((p for p in _MARKETPLACE_EXTRA if p["id"] == plugin_id), None)
            if not market_plugin:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"插件 {plugin_id} 不存在", severity="low").model_dump()
                )
            # 加入已知插件
            _PLUGINS[plugin_id] = {**market_plugin, "settings": {}, "installed_at": None}
            plugin = _PLUGINS[plugin_id]

        if plugin.get("installed"):
            return {"success": True, "message": f"插件 {plugin_id} 已安装", "data": plugin}

        # 模拟安装
        plugin["installed"] = True
        plugin["enabled"] = True
        plugin["status"] = "active"
        plugin["installed_at"] = datetime.now().isoformat()
        plugin["updated_at"] = datetime.now().isoformat()

        logger.info(f"插件安装成功: {plugin_id} by {current_user.get('username')}")
        return {
            "success": True,
            "message": f"插件 {plugin['name']} 安装成功",
            "data": plugin
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"安装插件失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(code=ErrorCode.UNKNOWN_ERROR, message="安装插件失败", severity="high").model_dump()
        )


@router.post("/{plugin_id}/enable")
async def enable_plugin(
    plugin_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """启用插件"""
    plugin = _PLUGINS.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"插件 {plugin_id} 不存在", severity="low").model_dump()
        )
    if not plugin.get("installed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIError(code=ErrorCode.VALIDATION_ERROR, message="请先安装插件", severity="medium").model_dump()
        )

    plugin["enabled"] = True
    plugin["status"] = "active"
    plugin["updated_at"] = datetime.now().isoformat()

    return {"success": True, "message": f"插件 {plugin['name']} 已启用", "data": plugin}


@router.post("/{plugin_id}/disable")
async def disable_plugin(
    plugin_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """禁用插件"""
    plugin = _PLUGINS.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"插件 {plugin_id} 不存在", severity="low").model_dump()
        )

    plugin["enabled"] = False
    plugin["status"] = "disabled"
    plugin["updated_at"] = datetime.now().isoformat()

    return {"success": True, "message": f"插件 {plugin['name']} 已禁用", "data": plugin}


@router.post("/{plugin_id}/update")
async def update_plugin(
    plugin_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """更新插件到最新版本"""
    plugin = _PLUGINS.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"插件 {plugin_id} 不存在", severity="low").model_dump()
        )
    if not plugin.get("installed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIError(code=ErrorCode.VALIDATION_ERROR, message="插件未安装，无法更新", severity="medium").model_dump()
        )

    # 模拟更新（实际应触发包管理器）
    plugin["status"] = "active"
    plugin["updated_at"] = datetime.now().isoformat()

    logger.info(f"插件更新成功: {plugin_id}")
    return {
        "success": True,
        "message": f"插件 {plugin['name']} 更新成功",
        "data": plugin
    }


@router.delete("/{plugin_id}")
async def uninstall_plugin(
    plugin_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """卸载插件"""
    plugin = _PLUGINS.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"插件 {plugin_id} 不存在", severity="low").model_dump()
        )

    plugin["installed"] = False
    plugin["enabled"] = False
    plugin["status"] = "available"
    plugin["installed_at"] = None
    plugin["settings"] = {}
    plugin["updated_at"] = datetime.now().isoformat()

    logger.info(f"插件卸载成功: {plugin_id} by {current_user.get('username')}")
    return {"success": True, "message": f"插件 {plugin['name']} 已卸载"}


@router.get("/{plugin_id}/settings")
async def get_plugin_settings(
    plugin_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取插件配置"""
    plugin = _PLUGINS.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"插件 {plugin_id} 不存在", severity="low").model_dump()
        )
    return {"success": True, "data": plugin.get("settings", {})}


@router.put("/{plugin_id}/settings")
async def update_plugin_settings(
    plugin_id: str,
    settings_data: PluginSettingsUpdate,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """更新插件配置"""
    plugin = _PLUGINS.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"插件 {plugin_id} 不存在", severity="low").model_dump()
        )

    plugin["settings"] = {**plugin.get("settings", {}), **settings_data.settings}
    plugin["updated_at"] = datetime.now().isoformat()

    return {"success": True, "message": "配置更新成功", "data": plugin["settings"]}


__all__ = ["router"]
