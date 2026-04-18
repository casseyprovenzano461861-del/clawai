# -*- coding: utf-8 -*-
"""
渗透测试报告生成器
支持 HTML / Markdown / JSON 格式，包含 CVSS v3 评分、修复建议、执行摘要
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


# ─── CVSS v3 基础评分映射 ────────────────────────────────────────────────────

_CVSS_BASE: Dict[str, Dict[str, Any]] = {
    # 漏洞类型 → {score, vector, severity_label}
    "sql_injection":        {"score": 9.8, "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "label": "Critical"},
    "sqli":                 {"score": 9.8, "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "label": "Critical"},
    "rce":                  {"score": 9.8, "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "label": "Critical"},
    "command_injection":    {"score": 9.8, "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "label": "Critical"},
    "deserialization":      {"score": 9.0, "vector": "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:C/C:H/I:H/A:H", "label": "Critical"},
    "xxe":                  {"score": 8.8, "vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H", "label": "High"},
    "ssrf":                 {"score": 8.6, "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:N", "label": "High"},
    "ssti":                 {"score": 8.1, "vector": "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H", "label": "High"},
    "file_upload":          {"score": 8.8, "vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H", "label": "High"},
    "auth_bypass":          {"score": 8.1, "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N", "label": "High"},
    "broken_auth":          {"score": 8.1, "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N", "label": "High"},
    "xss":                  {"score": 6.1, "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N", "label": "Medium"},
    "xss_reflected":        {"score": 6.1, "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N", "label": "Medium"},
    "xss_stored":           {"score": 6.8, "vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:L/I:L/A:N", "label": "Medium"},
    "idor":                 {"score": 7.5, "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N", "label": "High"},
    "lfi":                  {"score": 7.5, "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N", "label": "High"},
    "csrf":                 {"score": 4.3, "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N", "label": "Medium"},
    "info_disclosure":      {"score": 5.3, "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N", "label": "Medium"},
    "nosql_injection":      {"score": 8.8, "vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H", "label": "High"},
    "open_redirect":        {"score": 4.7, "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:N/A:N", "label": "Medium"},
}

_SEVERITY_FROM_SCORE = [
    (9.0, "critical"),
    (7.0, "high"),
    (4.0, "medium"),
    (0.1, "low"),
    (0.0, "info"),
]

# ─── 运行时 finding type → 漏洞类型 key（用于查 CVSS/修复建议） ─────────────
#
# 覆盖 session.findings 中所有可能出现的 type 值
_RUNTIME_TYPE_MAP: Dict[str, str] = {
    # CVE/技能结果 → 按 skill_id 进一步细化（见下方 _SKILL_ID_MAP）
    "cve_skill":     "rce",             # 默认映射 RCE，skill_id 会覆盖
    "attack_chain":  "rce",             # 完整攻击链
    # 凭据 & 访问
    "credential":    "broken_auth",
    "ssh_access":    "broken_auth",
    # 扫描类
    "port_scan":     "info_disclosure",
    "http_probe":    "info_disclosure",
    "dir_scan":      "info_disclosure",
    "dir_enum":      "info_disclosure",
    # 漏洞类型直接命名
    "sqli":          "sqli",
    "sql_injection": "sql_injection",
    "xss":           "xss",
    "xss_reflected": "xss_reflected",
    "xss_stored":    "xss_stored",
    "rce":           "rce",
    "lfi":           "lfi",
    "ssrf":          "ssrf",
    "xxe":           "xxe",
    "ssti":          "ssti",
    "csrf":          "csrf",
    "idor":          "idor",
    "file_upload":   "file_upload",
    "deserialization": "deserialization",
    "nosql_injection": "nosql_injection",
    "auth_bypass":   "auth_bypass",
    "flag":          "info_disclosure",
    "simulated_scan": "info_disclosure",
}

# skill_id 前缀/关键词 → 漏洞类型 key（精细化 cve_skill 映射）
_SKILL_ID_MAP: Dict[str, str] = {
    "sqli":            "sql_injection",
    "dvwa_sqli":       "sql_injection",
    "sql":             "sql_injection",
    "xss":             "xss",
    "dvwa_xss":        "xss",
    "lfi":             "lfi",
    "rce":             "rce",
    "fuel_cms":        "rce",
    "flask_pickle":    "deserialization",
    "earth_django":    "rce",
    "cve_s2":          "rce",
    "cve_struts":      "rce",
    "cve_tomcat":      "rce",
    "cve_weblogic":    "rce",
    "cve_thinkphp":    "rce",
    "cve_activemq":    "rce",
    "cve_fastjson":    "deserialization",
    "cve_jboss":       "deserialization",
    "cve_shiro":       "deserialization",
    "cve_geoserver":   "rce",
    "cve_django":      "sql_injection",
    "cve_php_fpm":     "rce",
    "flask_ssti":      "ssti",
    "ssrf":            "ssrf",
    "xxe":             "xxe",
    "file_upload":     "file_upload",
    "idor":            "idor",
    "csrf":            "csrf",
    "nosql":           "nosql_injection",
    "auth_bruteforce": "broken_auth",
    "auth_bypass":     "auth_bypass",
    "dvwa_bruteforce": "broken_auth",
    "openssh_user":    "info_disclosure",
    "privesc":         "rce",           # 提权 = 本地 RCE 升级
    "waf":             "info_disclosure",
    "flag_detector":   "info_disclosure",
}

# ─── 运行时 finding → 人类可读标题映射 ───────────────────────────────────────
_RUNTIME_TITLE_MAP: Dict[str, str] = {
    "cve_skill":     "{skill_id} — CVE 漏洞利用",
    "credential":    "敏感凭据泄露",
    "ssh_access":    "SSH 未授权/弱口令访问",
    "port_scan":     "开放端口信息泄露",
    "http_probe":    "Web 服务信息暴露",
    "dir_scan":      "敏感目录/文件暴露",
    "dir_enum":      "目录枚举发现",
    "attack_chain":  "完整攻击链（Critical）",
    "flag":          "CTF Flag 已获取",
}

# ─── 运行时 finding → 影响描述 ───────────────────────────────────────────────
_RUNTIME_IMPACT_MAP: Dict[str, str] = {
    "cve_skill":    "攻击者可利用该漏洞在目标服务器上执行任意命令，完全控制系统。",
    "credential":   "攻击者获取系统账号凭据，可直接登录系统或横向移动至内网其他主机。",
    "ssh_access":   "攻击者已通过 SSH 取得系统 Shell 访问权限，可读取敏感文件、植入后门或横向移动。",
    "port_scan":    "暴露的端口和服务版本信息可被攻击者用于有针对性的漏洞利用。",
    "http_probe":   "Web 服务版本、框架信息暴露，增加被针对性攻击的风险。",
    "dir_scan":     "敏感目录或备份文件暴露，可能泄露源代码、配置文件或管理入口。",
    "dir_enum":     "枚举发现隐藏路径，可能暴露管理接口或未授权访问点。",
    "attack_chain": "攻击者已完成从初始访问到系统控制的完整攻击链，目标系统已被完全攻陷。",
    "flag":         "目标系统中的关键数据（Flag）已被获取，证明攻击者具备完整的系统访问权限。",
}

# ─── 修复建议库 ──────────────────────────────────────────────────────────────

_REMEDIATION: Dict[str, Dict[str, str]] = {
    "sql_injection": {
        "short": "使用参数化查询/预编译语句",
        "detail": (
            "1. 使用参数化查询（PreparedStatement）或 ORM 框架，彻底避免字符串拼接 SQL。\n"
            "2. 启用数据库最小权限原则，Web 账号不应拥有 DROP/ALTER 权限。\n"
            "3. 部署 WAF 规则过滤常见 SQL 注入 Payload。\n"
            "4. 对所有用户输入进行白名单校验，拒绝包含 SQL 关键字的非预期输入。"
        ),
        "refs": ["https://owasp.org/www-community/attacks/SQL_Injection",
                 "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html"],
    },
    "sqli": {
        "short": "使用参数化查询/预编译语句",
        "detail": (
            "1. 使用参数化查询（PreparedStatement）或 ORM 框架，彻底避免字符串拼接 SQL。\n"
            "2. 启用数据库最小权限原则，Web 账号不应拥有 DROP/ALTER 权限。\n"
            "3. 部署 WAF 规则过滤常见 SQL 注入 Payload。\n"
            "4. 对所有用户输入进行白名单校验，拒绝包含 SQL 关键字的非预期输入。"
        ),
        "refs": ["https://owasp.org/www-community/attacks/SQL_Injection"],
    },
    "xss": {
        "short": "对输出进行 HTML 编码，启用 CSP",
        "detail": (
            "1. 对所有动态内容在输出时进行 HTML 实体编码（htmlspecialchars 等）。\n"
            "2. 配置 Content-Security-Policy（CSP）响应头，限制脚本来源。\n"
            "3. 设置 HttpOnly 和 Secure Cookie 标志，防止脚本读取会话 Cookie。\n"
            "4. 使用现代前端框架（React/Vue）的自动转义功能，避免 dangerouslySetInnerHTML。"
        ),
        "refs": ["https://owasp.org/www-community/attacks/xss/",
                 "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html"],
    },
    "rce": {
        "short": "禁止将用户输入传递给系统命令",
        "detail": (
            "1. 严禁将用户输入直接拼接到 shell 命令中，使用语言内置 API 替代。\n"
            "2. 若必须执行外部命令，使用参数列表（非字符串）调用方式，并严格白名单校验参数。\n"
            "3. 在独立的沙箱/容器中运行用户触发的命令，限制系统调用权限。\n"
            "4. 启用应用层防火墙，监控异常进程创建行为。"
        ),
        "refs": ["https://owasp.org/www-community/attacks/Command_Injection"],
    },
    "ssrf": {
        "short": "校验并限制服务器端请求的目标地址",
        "detail": (
            "1. 使用白名单限制允许请求的域名/IP 范围，拒绝内网地址（10.x、172.x、192.168.x、127.x）。\n"
            "2. 禁用非必要协议（file://、gopher://、dict://）。\n"
            "3. 对 URL 进行解析后再校验，防止 DNS 重绑定绕过（在发起请求前再次验证解析后 IP）。\n"
            "4. 响应内容不应直接返回给用户，避免内网信息泄露。"
        ),
        "refs": ["https://owasp.org/www-community/attacks/Server_Side_Request_Forgery"],
    },
    "xxe": {
        "short": "禁用 XML 外部实体解析",
        "detail": (
            "1. 在 XML 解析器中明确禁用 DTD 和外部实体（FEATURE_EXTERNAL_GENERAL_ENTITIES=false）。\n"
            "2. 升级 XML 解析库到最新版本。\n"
            "3. 考虑使用 JSON 替代 XML 作为数据交换格式。\n"
            "4. 对上传的 XML 文件进行严格的内容类型和大小校验。"
        ),
        "refs": ["https://owasp.org/www-community/vulnerabilities/XML_External_Entity_(XXE)_Processing"],
    },
    "lfi": {
        "short": "避免将用户输入用于文件路径",
        "detail": (
            "1. 绝不将用户输入直接用于文件路径，使用白名单映射替代。\n"
            "2. 使用 realpath() 解析路径后校验是否在允许目录内。\n"
            "3. 禁用 PHP allow_url_include 和 allow_url_fopen（若使用 PHP）。\n"
            "4. 部署 chroot/容器隔离敏感文件。"
        ),
        "refs": ["https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/11.1-Testing_for_Local_File_Inclusion"],
    },
    "auth_bypass": {
        "short": "加强身份验证逻辑，修复授权绕过",
        "detail": (
            "1. 审查所有身份验证入口，确保每个受保护端点都经过认证中间件。\n"
            "2. 使用成熟的认证框架（OAuth2/OIDC），避免自行实现认证逻辑。\n"
            "3. 实施多因素认证（MFA）提升关键功能安全性。\n"
            "4. 对认证失败进行速率限制和账号锁定策略。"
        ),
        "refs": ["https://owasp.org/www-project-top-ten/2021/A07_2021-Identification_and_Authentication_Failures"],
    },
    "csrf": {
        "short": "实施 CSRF Token 和 SameSite Cookie",
        "detail": (
            "1. 为所有状态变更操作实施 CSRF Token 验证。\n"
            "2. 设置 Cookie 的 SameSite=Strict 或 SameSite=Lax 属性。\n"
            "3. 验证 Origin/Referer 请求头（作为纵深防御）。\n"
            "4. 敏感操作要求用户重新输入密码或完成二次验证。"
        ),
        "refs": ["https://owasp.org/www-community/attacks/csrf"],
    },
    "idor": {
        "short": "实施对象级授权验证",
        "detail": (
            "1. 对每个资源访问请求验证当前用户是否有权访问该对象。\n"
            "2. 使用不可预测的 UUID 替代自增 ID。\n"
            "3. 在服务端而非客户端实施访问控制检查。\n"
            "4. 记录并监控异常的资源访问模式。"
        ),
        "refs": ["https://owasp.org/www-project-top-ten/2021/A01_2021-Broken_Access_Control"],
    },
    "info_disclosure": {
        "short": "收敛错误信息，移除敏感数据暴露",
        "detail": (
            "1. 生产环境禁用详细错误信息和堆栈跟踪。\n"
            "2. 删除或保护包含敏感信息的备份文件（.bak、.old、~）。\n"
            "3. 审查 HTTP 响应头，移除 Server、X-Powered-By 等版本信息。\n"
            "4. 扫描并清理 .git、.svn、.env 等敏感目录的公开访问。"
        ),
        "refs": ["https://owasp.org/www-project-top-ten/2021/A05_2021-Security_Misconfiguration"],
    },
    "deserialization": {
        "short": "避免反序列化不可信数据",
        "detail": (
            "1. 避免反序列化来自不可信来源的数据，优先使用 JSON 等简单数据格式。\n"
            "2. 使用白名单限制可反序列化的类。\n"
            "3. 对序列化数据进行签名验证，防止篡改。\n"
            "4. 在沙箱环境中执行反序列化操作，限制其权限。"
        ),
        "refs": ["https://owasp.org/www-community/vulnerabilities/Deserialization_of_untrusted_data"],
    },
    "nosql_injection": {
        "short": "校验并净化 NoSQL 查询参数",
        "detail": (
            "1. 对所有用户输入进行类型校验，禁止传入对象类型到查询条件。\n"
            "2. 使用 ORM 或查询构建器替代原始查询字符串。\n"
            "3. 启用 MongoDB 的 $where 禁用选项，限制 JavaScript 执行。\n"
            "4. 部署 WAF 规则过滤常见 NoSQL 注入 Payload。"
        ),
        "refs": ["https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05.6-Testing_for_NoSQL_Injection"],
    },
    "file_upload": {
        "short": "严格校验上传文件类型和内容",
        "detail": (
            "1. 验证文件 MIME 类型（使用 magic bytes，而非文件扩展名）。\n"
            "2. 将上传文件存储在 Web 根目录之外，通过代理提供访问。\n"
            "3. 重命名上传文件，防止文件名注入。\n"
            "4. 限制上传文件大小，对图片等文件进行二次渲染（消除 Payload）。"
        ),
        "refs": ["https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload"],
    },
    "ssti": {
        "short": "禁止将用户输入传递给模板引擎",
        "detail": (
            "1. 绝不将用户输入作为模板字符串渲染，使用数据绑定方式传递变量。\n"
            "2. 升级模板引擎版本，启用沙箱模式（如 Jinja2 SandboxedEnvironment）。\n"
            "3. 对渲染输出进行转义，防止二次注入。\n"
            "4. 使用静态代码分析工具检测模板注入风险点。"
        ),
        "refs": ["https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/18-Testing_for_Server-side_Template_Injection"],
    },
    "open_redirect": {
        "short": "校验重定向目标 URL 使用白名单",
        "detail": (
            "1. 使用白名单限制允许重定向的目标域名。\n"
            "2. 避免将用户输入直接用于重定向 URL，使用路径标识符替代。\n"
            "3. 对重定向 URL 进行严格解析，防止 // 或 \\\\\\\\、unicode 编码绕过。"
        ),
        "refs": ["https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/11-Client-side_Testing/04-Testing_for_Client-side_URL_Redirect"],
    },
    "broken_auth": {
        "short": "加固认证机制，禁用弱口令，启用 MFA",
        "detail": (
            "1. 强制使用强密码策略（12 位以上，含大小写/数字/符号），定期轮换。\n"
            "2. 启用多因素认证（MFA/2FA），防止凭据泄露后被直接利用。\n"
            "3. 对登录接口实施速率限制和账号锁定策略，防止暴力破解。\n"
            "4. 禁用默认账号（admin/root）或修改默认密码，删除测试账号。\n"
            "5. 使用 SSH Key 认证替代密码认证，禁用 root 远程登录。"
        ),
        "refs": [
            "https://owasp.org/www-project-top-ten/2021/A07_2021-Identification_and_Authentication_Failures",
            "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html",
        ],
    },
    "info_disclosure": {
        "short": "隐藏服务版本信息，限制目录浏览",
        "detail": (
            "1. 配置 Web 服务器隐藏版本号（如 Apache ServerTokens Prod，Nginx server_tokens off）。\n"
            "2. 禁用目录列表（Apache Options -Indexes，Nginx autoindex off）。\n"
            "3. 删除或保护备份文件（.bak/.zip/.sql）、配置文件、.git 目录。\n"
            "4. 配置 robots.txt 不暴露敏感路径，并配合访问控制限制实际访问。\n"
            "5. 定期使用目录扫描工具自查暴露资产。"
        ),
        "refs": [
            "https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/01-Information_Gathering/",
        ],
    },
}

_DEFAULT_REMEDIATION = {
    "short": "修复该安全漏洞，参考相关 OWASP 指南",
    "detail": "请参考 OWASP Top 10 和相关安全最佳实践修复此漏洞。",
    "refs": ["https://owasp.org/www-project-top-ten/"],
}

# ─── HTML 模板 ───────────────────────────────────────────────────────────────

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  :root {{
    --critical: #dc2626; --high: #ea580c; --medium: #d97706;
    --low: #2563eb; --info: #6b7280;
    --bg: #0f172a; --surface: #1e293b; --border: #334155;
    --text: #e2e8f0; --text-muted: #94a3b8; --accent: #06b6d4;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: var(--bg); color: var(--text);
         line-height: 1.6; padding: 2rem; }}
  .container {{ max-width: 1100px; margin: 0 auto; }}
  /* Header */
  .report-header {{ background: linear-gradient(135deg, #0c1a2e 0%, #162032 100%);
    border: 1px solid var(--accent); border-radius: 12px; padding: 2rem 2.5rem;
    margin-bottom: 2rem; position: relative; overflow: hidden; }}
  .report-header::before {{ content: ''; position: absolute; inset: 0;
    background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(6,182,212,.03) 2px, rgba(6,182,212,.03) 4px);
    pointer-events: none; }}
  .report-title {{ font-size: 1.8rem; font-weight: 700; color: var(--accent); margin-bottom: .5rem; }}
  .report-meta {{ display: flex; gap: 2rem; flex-wrap: wrap; font-size: .85rem; color: var(--text-muted); margin-top: 1rem; }}
  .report-meta span {{ display: flex; align-items: center; gap: .4rem; }}
  /* Risk banner */
  .risk-banner {{ display: flex; align-items: center; gap: 1rem; padding: 1rem 1.5rem;
    border-radius: 8px; margin-bottom: 1.5rem; border-left: 4px solid; }}
  .risk-critical {{ background: rgba(220,38,38,.12); border-color: var(--critical); color: #fca5a5; }}
  .risk-high     {{ background: rgba(234,88,12,.12);  border-color: var(--high);     color: #fdba74; }}
  .risk-medium   {{ background: rgba(217,119,6,.12);  border-color: var(--medium);   color: #fcd34d; }}
  .risk-low      {{ background: rgba(37,99,235,.12);  border-color: var(--low);      color: #93c5fd; }}
  .risk-banner .risk-label {{ font-size: 1.1rem; font-weight: 700; }}
  /* Stats */
  .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem; margin-bottom: 2rem; }}
  .stat-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
    padding: 1rem 1.2rem; text-align: center; }}
  .stat-num {{ font-size: 2rem; font-weight: 700; line-height: 1; }}
  .stat-label {{ font-size: .75rem; color: var(--text-muted); margin-top: .3rem; text-transform: uppercase; letter-spacing: .05em; }}
  .num-critical {{ color: var(--critical); }}
  .num-high     {{ color: var(--high); }}
  .num-medium   {{ color: var(--medium); }}
  .num-low      {{ color: var(--low); }}
  .num-info     {{ color: var(--info); }}
  /* Section */
  .section {{ margin-bottom: 2rem; }}
  .section-title {{ font-size: 1.1rem; font-weight: 600; color: var(--accent);
    border-bottom: 1px solid var(--border); padding-bottom: .5rem; margin-bottom: 1rem; }}
  /* Executive summary */
  .exec-summary {{ background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 1.5rem; line-height: 1.8; color: var(--text-muted); }}
  /* Finding card */
  .finding {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
    margin-bottom: 1rem; overflow: hidden; }}
  .finding-header {{ display: flex; align-items: center; gap: .8rem; padding: .9rem 1.2rem;
    border-bottom: 1px solid var(--border); }}
  .sev-badge {{ font-size: .7rem; font-weight: 700; padding: .2rem .6rem; border-radius: 4px;
    text-transform: uppercase; letter-spacing: .05em; }}
  .sev-critical {{ background: rgba(220,38,38,.2); color: #fca5a5; }}
  .sev-high     {{ background: rgba(234,88,12,.2);  color: #fdba74; }}
  .sev-medium   {{ background: rgba(217,119,6,.2);  color: #fcd34d; }}
  .sev-low      {{ background: rgba(37,99,235,.2);  color: #93c5fd; }}
  .sev-info     {{ background: rgba(107,114,128,.2);color: #d1d5db; }}
  .finding-title {{ font-weight: 600; flex: 1; }}
  .cvss-score {{ font-size: .8rem; color: var(--text-muted); margin-left: auto; white-space: nowrap; }}
  .finding-body {{ padding: 1.2rem; display: grid; gap: 1rem; }}
  .finding-body table {{ width: 100%; border-collapse: collapse; font-size: .85rem; }}
  .finding-body td {{ padding: .4rem .6rem; border-bottom: 1px solid var(--border); vertical-align: top; }}
  .finding-body td:first-child {{ color: var(--text-muted); width: 6rem; white-space: nowrap; }}
  .remediation {{ background: rgba(6,182,212,.06); border: 1px solid rgba(6,182,212,.2);
    border-radius: 6px; padding: 1rem; }}
  .remediation-title {{ font-size: .8rem; color: var(--accent); font-weight: 600; margin-bottom: .5rem; }}
  .remediation-steps {{ font-size: .83rem; color: var(--text-muted); white-space: pre-wrap; }}
  .refs {{ margin-top: .6rem; }}
  .refs a {{ font-size: .78rem; color: var(--accent); text-decoration: none; display: block; }}
  .refs a:hover {{ text-decoration: underline; }}
  /* Methodology */
  .methodology ol {{ padding-left: 1.5rem; color: var(--text-muted); font-size: .9rem; }}
  .methodology li {{ margin-bottom: .4rem; }}
  /* Footer */
  .report-footer {{ text-align: center; color: var(--text-muted); font-size: .78rem;
    border-top: 1px solid var(--border); padding-top: 1rem; margin-top: 2rem; }}
</style>
</head>
<body>
<div class="container">

<!-- Header -->
<div class="report-header">
  <div class="report-title">{title}</div>
  <div class="report-meta">
    <span>&#x1F3AF; 目标：<strong>{target}</strong></span>
    <span>&#x1F4C5; 生成时间：{generated_at}</span>
    <span>&#x1F527; 扫描类型：{scan_type}</span>
    <span>&#x231B; 扫描时长：{duration}</span>
  </div>
  <div class="report-meta" style="margin-top:6px;border-top:1px solid rgba(0,212,255,0.1);padding-top:8px">
    <span>&#x1F464; 测试人员：{tester_name}</span>
    <span>&#x1F3E2; 委托方：{client_name}</span>
    <span>&#x1F4CB; 测试周期：{test_start_date} ~ {test_end_date}</span>
    {project_id_span}
  </div>
</div>

<!-- Risk Banner -->
<div class="risk-banner risk-{overall_risk_class}">
  <div>
    <div class="risk-label">&#x26A0; 整体风险等级：{overall_risk_label}</div>
    <div style="font-size:.85rem;margin-top:.3rem;">{risk_summary}</div>
  </div>
</div>

<!-- Stats -->
<div class="stats">
  <div class="stat-card"><div class="stat-num num-critical">{cnt_critical}</div><div class="stat-label">Critical</div></div>
  <div class="stat-card"><div class="stat-num num-high">{cnt_high}</div><div class="stat-label">High</div></div>
  <div class="stat-card"><div class="stat-num num-medium">{cnt_medium}</div><div class="stat-label">Medium</div></div>
  <div class="stat-card"><div class="stat-num num-low">{cnt_low}</div><div class="stat-label">Low</div></div>
  <div class="stat-card"><div class="stat-num num-info">{cnt_info}</div><div class="stat-label">Info</div></div>
  <div class="stat-card"><div class="stat-num" style="color:var(--accent)">{cnt_total}</div><div class="stat-label">总计</div></div>
</div>

<!-- Executive Summary -->
<div class="section">
  <div class="section-title">&#x1F4CB; 执行摘要</div>
  <div class="exec-summary">{executive_summary}</div>
</div>

<!-- Findings -->
<div class="section">
  <div class="section-title">&#x1F50D; 漏洞详情</div>
  {findings_html}
</div>

<!-- Methodology -->
<div class="section methodology">
  <div class="section-title">&#x1F9EA; 测试方法</div>
  <ol>
    <li>信息收集：目标侦察、端口扫描、服务指纹识别</li>
    <li>漏洞扫描：自动化工具扫描（Nuclei、Nikto、SQLMap 等）</li>
    <li>手工验证：对自动化发现的漏洞进行手工确认和 PoC 复现</li>
    <li>漏洞利用：在授权范围内验证漏洞可利用性</li>
    <li>风险评估：基于 CVSS v3 评分和业务影响综合评级</li>
    <li>报告输出：整理发现、提供修复建议</li>
  </ol>
</div>

<div class="report-footer">
  本报告由 ClawAI 自动生成 · 仅供授权安全评估使用 · {generated_at}
</div>

{disclaimer}

</div>
</body>
</html>
"""

_FINDING_HTML = """\
<div class="finding">
  <div class="finding-header">
    <span class="sev-badge sev-{sev_class}">{severity}</span>
    <span class="finding-title">{title}</span>
    <span class="cvss-score">CVSS {cvss_score} &nbsp;|&nbsp; {cvss_vector_short}</span>
  </div>
  <div class="finding-body">
    <table>
      <tr><td>位置</td><td><code>{location}</code></td></tr>
      <tr><td>描述</td><td>{description}</td></tr>
      {evidence_row}
      <tr><td>影响</td><td>{impact}</td></tr>
      {cve_row}
    </table>
    <div class="remediation">
      <div class="remediation-title">&#x1F527; 修复建议</div>
      <div class="remediation-steps">{remediation_detail}</div>
      {refs_html}
    </div>
  </div>
</div>
"""

# ─── 工具函数 ────────────────────────────────────────────────────────────────

def _get_cvss(vuln_type: str, provided_score: Optional[float] = None) -> Dict[str, Any]:
    """查找 CVSS 信息，优先使用已提供的分数"""
    key = (vuln_type or "").lower().replace(" ", "_").replace("-", "_")
    base = _CVSS_BASE.get(key, {})
    score = provided_score if provided_score is not None else base.get("score", 5.0)
    # 根据分数确定严重程度
    severity = "info"
    for threshold, sev in _SEVERITY_FROM_SCORE:
        if score >= threshold:
            severity = sev
            break
    return {
        "score": score,
        "vector": base.get("vector", "N/A"),
        "severity": severity,
        "label": base.get("label", severity.capitalize()),
    }


def _get_remediation(vuln_type: str) -> Dict[str, Any]:
    key = (vuln_type or "").lower().replace(" ", "_").replace("-", "_")
    return _REMEDIATION.get(key, _DEFAULT_REMEDIATION)


# 严重性等级数字比较映射
_SEV_ORDER: Dict[str, int] = {
    "critical": 4,
    "high":     3,
    "medium":   2,
    "low":      1,
    "info":     0,
}


def _extract_from_preview(f: Dict[str, Any], pattern: str) -> str:
    """从 finding 的输出预览或证据字段中提取匹配内容（group 1）。"""
    import re
    text = f.get("output_preview", "") or f.get("evidence", "") or f.get("output", "") or ""
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            return ""
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1) if m else ""


def _severity_from_str(s: str) -> str:
    s = (s or "").lower()
    if s in ("critical", "high", "medium", "low", "info"):
        return s
    if "critical" in s:
        return "critical"
    if "high" in s or "严重" in s or "高" in s:
        return "high"
    if "medium" in s or "中" in s:
        return "medium"
    if "low" in s or "低" in s:
        return "low"
    return "info"


def _count_sev(findings: List[Dict]) -> Dict[str, int]:
    cnt = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        sev = f.get("_severity_normalized", "info")
        cnt[sev] = cnt.get(sev, 0) + 1
    return cnt


def _overall_risk(cnt: Dict[str, int]) -> tuple:
    if cnt.get("critical", 0):
        return "critical", "Critical（严重）"
    if cnt.get("high", 0):
        return "high", "High（高危）"
    if cnt.get("medium", 0):
        return "medium", "Medium（中危）"
    if cnt.get("low", 0):
        return "low", "Low（低危）"
    return "info", "Info（信息）"


def _build_executive_summary(target: str, cnt: Dict[str, int], findings: List[Dict]) -> str:
    total = sum(cnt.values())
    if total == 0:
        return f"本次对目标 {target} 的安全评估未发现明显漏洞，整体安全状况良好。建议持续监控并定期进行安全复查。"

    lines = [
        f"本次对目标 {target} 的安全评估共发现 {total} 个安全问题，"
        f"其中严重漏洞 {cnt['critical']} 个、高危漏洞 {cnt['high']} 个、"
        f"中危漏洞 {cnt['medium']} 个、低危漏洞 {cnt['low']} 个、信息类 {cnt['info']} 个。"
    ]

    if cnt["critical"] or cnt["high"]:
        criticals = [f for f in findings if f.get("_severity_normalized") in ("critical", "high")]
        top = criticals[:3]
        names = "、".join(f.get("title") or f.get("name") or f.get("type", "未知漏洞") for f in top)
        lines.append(f"\n高危及以上漏洞包括：{names}等，建议立即修复。")

    lines.append(
        "\n评估团队建议优先修复严重和高危漏洞，防止攻击者利用这些漏洞获取系统权限或敏感数据，"
        "并在修复完成后进行复测确认。"
    )
    return "".join(lines)


# ─── 主类 ────────────────────────────────────────────────────────────────────

class PenetrationReportGenerator:
    """渗透测试报告生成器"""

    # ── 核心入口 ──────────────────────────────────────────────────────────────

    def generate_report(
        self,
        target: str,
        findings: List[Dict[str, Any]],
        report_format: str = "html",
        template: str = "standard",
        include_executive_summary: bool = True,
        include_technical_details: bool = True,
        include_recommendations: bool = True,
        scan_type: str = "standard",
        duration: Optional[float] = None,
        # 增补字段
        project_id: Optional[str] = None,
        tester_name: Optional[str] = None,
        client_name: Optional[str] = None,
        test_start_date: Optional[str] = None,
        test_end_date: Optional[str] = None,
        disclaimer: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """生成报告数据字典"""
        now = datetime.now()

        # 规范化每个 finding
        enriched = []
        for f in findings:
            enriched.append(self._enrich_finding(f))

        cnt = _count_sev(enriched)
        risk_class, risk_label = _overall_risk(cnt)

        report = {
            "id": f"report_{int(now.timestamp())}",
            "title": f"渗透测试安全评估报告 - {target}",
            "target": target,
            "generated_at": now.isoformat(),
            "scan_type": scan_type,
            "duration": f"{duration:.0f}s" if duration else "N/A",
            "format": report_format,
            "template": template,
            # 增补字段：项目关联 + 报告元信息
            "project_id": project_id or "",
            "tester_name": tester_name or "ClawAI 自动化渗透测试系统",
            "client_name": client_name or "",
            "test_start_date": test_start_date or now.strftime("%Y-%m-%d"),
            "test_end_date": test_end_date or now.strftime("%Y-%m-%d"),
            "disclaimer": disclaimer or (
                "本报告仅供授权范围内的安全评估参考使用。报告内容、截图及漏洞细节属机密信息，"
                "未经书面授权，不得向第三方披露或用于任何商业目的。"
                "本次评估结果反映特定时间点的安全状况，不构成对目标系统安全性的完整保证。"
            ),
            "supported_export_formats": {
                "html": "网页格式（推荐，支持所有浏览器直接查看）",
                "pdf": "PDF 格式（需安装 weasyprint：pip install weasyprint）",
                "markdown": "Markdown 文本格式",
                "json": "JSON 原始数据格式（适合二次处理）",
            },
            "findings": enriched,
            "statistics": cnt,
            "overall_risk": risk_class,
            "overall_risk_label": risk_label,
            "executive_summary": _build_executive_summary(target, cnt, enriched) if include_executive_summary else "",
        }
        return report

    def generate_html_report(self, report_dict: Dict[str, Any]) -> str:
        """将报告字典渲染为 HTML 字符串"""
        findings = report_dict.get("findings", [])
        cnt = report_dict.get("statistics", _count_sev(findings))
        risk_class = report_dict.get("overall_risk", "info")
        risk_label = report_dict.get("overall_risk_label", "Info")

        risk_summary = (
            f"共发现 {sum(cnt.values())} 个安全问题，"
            f"其中 {cnt.get('critical',0)} Critical / {cnt.get('high',0)} High / "
            f"{cnt.get('medium',0)} Medium / {cnt.get('low',0)} Low。"
        )

        findings_html = self._render_findings_html(findings) if findings else "<p style='color:#6b7280'>本次扫描未发现漏洞。</p>"

        pid = report_dict.get("project_id", "")
        project_id_span = f"<span>&#x1F4C1; 项目ID：{pid}</span>" if pid else ""

        disclaimer_text = report_dict.get("disclaimer", "")
        disclaimer_html = (
            f"<section style='margin-top:32px;padding:16px;background:rgba(255,255,255,0.03);"
            f"border:1px solid rgba(255,255,255,0.08);border-radius:8px'>"
            f"<h3 style='color:#6b7280;font-size:12px;margin:0 0 8px;text-transform:uppercase;letter-spacing:1px'>免责声明</h3>"
            f"<p style='color:#6b7280;font-size:12px;line-height:1.6;margin:0'>{disclaimer_text}</p>"
            f"</section>"
        ) if disclaimer_text else ""

        html = _HTML_TEMPLATE.format(
            title=report_dict.get("title", "渗透测试报告"),
            target=report_dict.get("target", "N/A"),
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            scan_type=report_dict.get("scan_type", "standard"),
            duration=report_dict.get("duration", "N/A"),
            overall_risk_class=risk_class,
            overall_risk_label=risk_label,
            risk_summary=risk_summary,
            cnt_critical=cnt.get("critical", 0),
            cnt_high=cnt.get("high", 0),
            cnt_medium=cnt.get("medium", 0),
            cnt_low=cnt.get("low", 0),
            cnt_info=cnt.get("info", 0),
            cnt_total=sum(cnt.values()),
            executive_summary=report_dict.get("executive_summary", "").replace("\n", "<br>"),
            findings_html=findings_html,
            tester_name=report_dict.get("tester_name", "ClawAI 自动化渗透测试系统"),
            client_name=report_dict.get("client_name", "—"),
            test_start_date=report_dict.get("test_start_date", ""),
            test_end_date=report_dict.get("test_end_date", ""),
            project_id=pid,
            project_id_span=project_id_span,
            disclaimer=disclaimer_html,
        )
        return html

    def generate_markdown_report(self, report_dict: Dict[str, Any]) -> str:
        """将报告字典渲染为 Markdown 字符串"""
        findings = report_dict.get("findings", [])
        cnt = report_dict.get("statistics", _count_sev(findings))
        lines = [
            f"# {report_dict.get('title', '渗透测试报告')}",
            "",
            f"| 字段 | 值 |",
            f"|------|---|",
            f"| 目标 | `{report_dict.get('target', 'N/A')}` |",
            f"| 生成时间 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |",
            f"| 扫描类型 | {report_dict.get('scan_type', 'standard')} |",
            f"| 整体风险 | **{report_dict.get('overall_risk_label', 'N/A')}** |",
            f"| 测试人员 | {report_dict.get('tester_name', 'N/A')} |",
            f"| 委托方 | {report_dict.get('client_name', '—')} |",
            f"| 测试周期 | {report_dict.get('test_start_date', '')} ~ {report_dict.get('test_end_date', '')} |",
            "",
            "## 统计",
            "",
            f"| Critical | High | Medium | Low | Info | 总计 |",
            f"|----------|------|--------|-----|------|------|",
            f"| {cnt.get('critical',0)} | {cnt.get('high',0)} | {cnt.get('medium',0)} | {cnt.get('low',0)} | {cnt.get('info',0)} | {sum(cnt.values())} |",
            "",
            "## 执行摘要",
            "",
            report_dict.get("executive_summary", ""),
            "",
            "## 漏洞详情",
            "",
        ]

        for i, f in enumerate(findings, 1):
            sev = f.get("_severity_normalized", "info").upper()
            cvss = f.get("_cvss", {})
            rem = f.get("_remediation", {})
            lines += [
                f"### {i}. {f.get('title') or f.get('name') or f.get('type', '未知漏洞')} `[{sev}]`",
                "",
                f"- **位置**: `{f.get('location', 'N/A')}`",
                f"- **描述**: {f.get('description', 'N/A')}",
                f"- **CVSS 评分**: {cvss.get('score', 'N/A')} ({cvss.get('vector', 'N/A')})",
                f"- **影响**: {f.get('impact', 'N/A')}",
            ]
            if f.get("evidence"):
                lines.append(f"- **证据**: `{f['evidence']}`")
            if f.get("cve_id"):
                lines.append(f"- **CVE**: {f['cve_id']}")
            lines += [
                "",
                f"**修复建议**: {rem.get('short', '')}",
                "",
                rem.get("detail", ""),
                "",
            ]

        lines += ["---", "", "*本报告由 ClawAI 自动生成，仅供授权安全评估使用。*"]
        return "\n".join(lines)

    def generate_pdf_report(self, report_dict: Dict[str, Any]) -> bytes:
        """
        生成 PDF 字节流（需要 weasyprint）。
        若 weasyprint 未安装，返回 None。
        """
        try:
            from weasyprint import HTML as WPHtml
            html_str = self.generate_html_report(report_dict)
            return WPHtml(string=html_str).write_pdf()
        except ImportError:
            return None

    # ── 内部方法 ──────────────────────────────────────────────────────────────

    def _enrich_finding(self, f: Dict[str, Any]) -> Dict[str, Any]:
        """规范化并丰富单个 finding。

        核心改进：对运行时 type（cve_skill / credential / ssh_access 等）
        做语义映射，精确推断漏洞类型 key，从而获得正确的 CVSS 评分、
        严重性等级和有针对性的修复建议。
        """
        f = dict(f)  # 浅拷贝避免修改原始数据
        ftype = (f.get("type") or "").lower()
        skill_id = (f.get("skill_id") or "").lower()

        # ── Step 1: 推断漏洞类型 key ────────────────────────────────────────
        # 优先用 category/vuln_type（如已明确指定）
        vuln_type = (
            f.get("category") or f.get("vuln_type") or ""
        ).lower().replace(" ", "_").replace("-", "_")

        if not vuln_type:
            # cve_skill：先按 skill_id 关键词细化，再 fallback 到 type 映射
            if ftype == "cve_skill" and skill_id:
                for prefix, vtype in _SKILL_ID_MAP.items():
                    if skill_id.startswith(prefix) or prefix in skill_id:
                        vuln_type = vtype
                        break
            if not vuln_type:
                vuln_type = _RUNTIME_TYPE_MAP.get(ftype, "")

        if not vuln_type:
            # 最后 fallback：从 title/type 原始字符串推断
            vuln_type = (
                f.get("type") or f.get("title") or ""
            ).lower().replace(" ", "_").replace("-", "_")

        # ── Step 2: 补充 title ───────────────────────────────────────────────
        if not f.get("title"):
            tpl = _RUNTIME_TITLE_MAP.get(ftype, "")
            if tpl:
                f["title"] = tpl.format(
                    skill_id=f.get("skill_id", ftype),
                    type=ftype,
                )
            elif f.get("description"):
                f["title"] = str(f["description"])[:60]
            else:
                f["title"] = f.get("name") or ftype or "未知问题"

        # ── Step 3: 严重性 ───────────────────────────────────────────────────
        raw_sev = f.get("severity", "")
        cvss_info = _get_cvss(vuln_type, f.get("cvss_score"))

        # cve_skill 且 vulnerable=True → 至少 High
        if ftype == "cve_skill" and f.get("vulnerable"):
            cvss_info = _get_cvss(vuln_type or "rce", f.get("cvss_score"))
            if cvss_info["severity"] not in ("critical", "high"):
                cvss_info["severity"] = "high"
                cvss_info["score"] = max(cvss_info["score"], 7.5)

        # credential / ssh_access → High
        if ftype in ("credential", "ssh_access"):
            if cvss_info["severity"] not in ("critical", "high"):
                cvss_info["severity"] = "high"
                cvss_info["score"] = max(cvss_info["score"], 7.5)

        # attack_chain → 强制 Critical（不受 raw_sev 影响）
        if ftype == "attack_chain":
            cvss_info["severity"] = "critical"
            cvss_info["score"] = 9.8

        # 强制类型：不受原始 severity 字段影响，直接用 cvss_info
        _force_sev_types = {"attack_chain", "credential", "ssh_access"}
        if ftype in _force_sev_types:
            normalized_sev = cvss_info["severity"]
        elif raw_sev:
            normalized_sev = _severity_from_str(raw_sev)
            # 已确认漏洞 / cve_skill 不降级
            if (f.get("vulnerable") or ftype == "cve_skill") and \
               _SEV_ORDER.get(normalized_sev, 0) < _SEV_ORDER.get(cvss_info["severity"], 0):
                normalized_sev = cvss_info["severity"]
        else:
            normalized_sev = cvss_info["severity"]

        f["_severity_normalized"] = normalized_sev
        f["_cvss"] = cvss_info

        # ── Step 4: 修复建议 ─────────────────────────────────────────────────
        f["_remediation"] = _get_remediation(vuln_type)

        # ── Step 5: 补充描述、影响、位置、证据 ──────────────────────────────
        if not f.get("description"):
            # cve_skill 用 match description 或 skill_id
            if ftype == "cve_skill":
                f["description"] = (
                    f.get("evidence", "")[:200]
                    or f.get("output_preview", "")[:200]
                    or f.get("skill_id", "")
                )
            elif ftype == "credential":
                uname = f.get("username") or _extract_from_preview(f, r"username.*?[：:]\s*(\S+)")
                pwd   = f.get("password") or _extract_from_preview(f, r"password.*?[：:]\s*(\S+)")
                f["description"] = f"发现明文凭据：用户名 {uname or '未知'}，密码 {pwd or '未知'}"
            elif ftype == "ssh_access":
                host  = f.get("host") or f.get("target") or "目标主机"
                uname = f.get("username") or _extract_from_preview(f, r"(\w+)@")
                f["description"] = f"SSH 成功登录 {uname or ''}@{host}，已获得系统 Shell"
            elif ftype == "port_scan":
                ports = f.get("open_ports") or f.get("output_preview", "")
                f["description"] = f"开放端口及服务：{str(ports)[:200]}"
            elif ftype == "dir_scan":
                paths = f.get("paths", [])
                f["description"] = (
                    f"发现 {len(paths)} 个敏感路径：{', '.join(paths[:5])}"
                    if paths else "目录扫描完成"
                )
            elif ftype == "http_probe":
                f["description"] = f.get("output_preview", "")[:200]

        if not f.get("impact"):
            f["impact"] = _RUNTIME_IMPACT_MAP.get(ftype, "可能对目标系统的机密性、完整性或可用性造成影响。")

        # location：优先用 target 字段
        if not f.get("location") or f.get("location") == "N/A":
            f["location"] = (
                f.get("target")
                or f.get("url")
                or f.get("host")
                or "N/A"
            )

        # evidence：cve_skill 成功时提取关键行
        if ftype == "cve_skill" and f.get("vulnerable") and not f.get("evidence"):
            output = f.get("output_preview", "")
            for line in output.splitlines():
                if any(kw in line.lower() for kw in ("rce_success", "uid=", "root", "flag", "shell")):
                    f["evidence"] = line.strip()[:200]
                    break

        f.setdefault("location", "N/A")
        f.setdefault("description", "")
        f.setdefault("impact", "可能对目标系统的机密性、完整性或可用性造成影响。")

        return f

    def _render_findings_html(self, findings: List[Dict]) -> str:
        # 按严重程度排序
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        sorted_findings = sorted(findings, key=lambda f: order.get(f.get("_severity_normalized", "info"), 5))

        parts = []
        for f in sorted_findings:
            sev = f.get("_severity_normalized", "info")
            cvss = f.get("_cvss", {})
            rem = f.get("_remediation", _DEFAULT_REMEDIATION)

            evidence_row = ""
            if f.get("evidence"):
                evidence_row = f"<tr><td>证据</td><td><code>{_esc(str(f['evidence']))}</code></td></tr>"

            cve_row = ""
            if f.get("cve_id"):
                cve_id_val = _esc(str(f["cve_id"]))
                cve_row = (
                    f"<tr><td>CVE</td><td>"
                    f"<a href='https://nvd.nist.gov/vuln/detail/{cve_id_val}' "
                    f"style='color:#06b6d4' target='_blank'>{cve_id_val}</a></td></tr>"
                )

            refs_html = ""
            if rem.get("refs"):
                links = "".join(f'<a href="{r}" target="_blank">{r}</a>' for r in rem["refs"])
                refs_html = f'<div class="refs">参考链接：{links}</div>'

            vector = cvss.get("vector", "N/A")
            vector_short = vector.split("/")[0] if vector != "N/A" else "N/A"

            parts.append(_FINDING_HTML.format(
                sev_class=sev,
                severity=sev.upper(),
                title=_esc(f.get("title", "未知漏洞")),
                cvss_score=cvss.get("score", "N/A"),
                cvss_vector_short=vector_short,
                location=_esc(str(f.get("location", "N/A"))),
                description=_esc(str(f.get("description", ""))),
                evidence_row=evidence_row,
                impact=_esc(str(f.get("impact", ""))),
                cve_row=cve_row,
                remediation_detail=_esc(rem.get("detail", "")),
                refs_html=refs_html,
            ))

        return "\n".join(parts)


def _esc(s: str) -> str:
    """HTML 转义"""
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))
