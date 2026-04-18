# -*- coding: utf-8 -*-
"""
服务指纹识别 → CVE Skill 自动分发

纯函数模块：输入 session.findings 列表，输出匹配的 CVE Skill 调用建议。
无副作用，可独立单元测试。

用法：
    from src.shared.backend.skills.fingerprint import match_findings
    matches = match_findings(session.findings)
    for m in matches:
        registry.execute(m.skill_id, {"target": m.target})
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse


# ─────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────

@dataclass
class FingerprintRule:
    """单条指纹规则"""
    id: str
    skill_id: str
    description: str
    target_format: str          # "url" 或 "host_port"
    ports: List[int] = field(default_factory=list)
    # nmap service/version 字段匹配（任一命中即得分）
    version_keywords: List[str] = field(default_factory=list)
    # curl Server: 响应头匹配
    server_keywords: List[str] = field(default_factory=list)
    # HTML <title> 匹配
    title_keywords: List[str] = field(default_factory=list)
    # URL 路径匹配（dirsearch 发现的路径 / curl 命令中的路径）
    path_keywords: List[str] = field(default_factory=list)
    # X-Powered-By 等 info_disclosure 匹配
    powered_by_keywords: List[str] = field(default_factory=list)
    # 基础分（规则本身的置信度权重）
    base_confidence: float = 0.5
    # 如果为 True，_build_skill_target 将使用根路径 / 而非保留 base_target 的路径
    # 适用于 Skill 内部自行拼接路径（如 GeoServer 自己拼 /geoserver/wfs）
    use_root_path: bool = False


@dataclass
class MatchResult:
    """单条匹配结果"""
    skill_id: str
    target: str                 # 直接传给 registry.execute 的 target 参数
    confidence: float           # 0.0 ~ 1.0
    reason: str                 # 人类可读的匹配原因
    description: str            # CVE 描述
    port: int = 0


# ─────────────────────────────────────────────
# 14 条指纹规则（覆盖全部 CVE Skills）
# ─────────────────────────────────────────────

FINGERPRINT_RULES: List[FingerprintRule] = [

    # ── WebLogic CVE-2023-21839 ──────────────────────────────
    FingerprintRule(
        id="weblogic_21839",
        skill_id="cve_weblogic_21839",
        description="WebLogic CVE-2023-21839 IIOP JNDI 注入",
        target_format="host_port",          # 特殊：需要 host:port 格式
        ports=[7001, 7002],
        version_keywords=["weblogic", "bea systems", "oracle weblogic", "oracle-weblogic"],
        server_keywords=["weblogic"],
        title_keywords=["weblogic server", "weblogic administration", "oracle weblogic",
                        "error 404--not found"],   # WebLogic 特有 404 页面
        base_confidence=0.9,   # 端口7001高度专属，命中置信度高
    ),

    # ── Struts2 S2-045 CVE-2017-5638 ────────────────────────
    FingerprintRule(
        id="struts2_s2045",
        skill_id="cve_s2_045",
        description="Struts2 S2-045 CVE-2017-5638 RCE",
        target_format="url",
        ports=[8080, 80, 443, 8443],
        version_keywords=["struts", "jakarta multipart", "apache-coyote"],
        server_keywords=["apache-coyote", "tomcat"],
        title_keywords=["struts2", "struts showcase", "welcome to struts"],
        path_keywords=[".action", "/struts2", "/s2-045"],
        base_confidence=0.65,
    ),

    # ── Struts2 S2-057 CVE-2018-11776 ───────────────────────
    FingerprintRule(
        id="struts2_s2057",
        skill_id="cve_s2_057",
        description="Struts2 S2-057 CVE-2018-11776 RCE",
        target_format="url",
        ports=[8080, 80, 443],
        version_keywords=["struts", "apache-coyote"],
        server_keywords=["apache-coyote", "tomcat"],
        title_keywords=["struts showcase", "struts2 showcase", "struts2-showcase"],
        path_keywords=["/struts2-showcase/", ".action"],
        base_confidence=0.65,
    ),

    # ── Struts2 S2-061 CVE-2020-17530 ───────────────────────
    FingerprintRule(
        id="struts2_s2061",
        skill_id="cve_s2_061",
        description="Struts2 S2-061 CVE-2020-17530 RCE",
        target_format="url",
        ports=[8080, 80, 443],
        version_keywords=["struts", "apache-coyote"],
        server_keywords=["apache-coyote", "tomcat", "jetty"],
        title_keywords=["s2-059 demo", "s2-061", "struts2", "struts showcase"],
        path_keywords=["/index.action", "/.action", "/s2-061"],
        base_confidence=0.60,
    ),

    # ── Tomcat CVE-2025-24813 会话反序列化 RCE ───────────────
    FingerprintRule(
        id="tomcat_2025_24813",
        skill_id="cve_tomcat_2025_24813",
        description="Apache Tomcat CVE-2025-24813 会话反序列化 RCE",
        target_format="url",
        ports=[8080, 8443, 80],
        version_keywords=["apache tomcat", "apache-coyote", "tomcat"],
        server_keywords=["apache-coyote", "tomcat"],
        title_keywords=["apache tomcat", "apache tomcat/9", "apache tomcat/10", "apache tomcat/11"],
        path_keywords=["/index.jsp", "/examples/"],
        base_confidence=0.70,
    ),

    # ── ThinkPHP 5.0.23 RCE ─────────────────────────────────
    FingerprintRule(
        id="thinkphp_rce",
        skill_id="cve_thinkphp_rce",
        description="ThinkPHP 5.0.23 RCE",
        target_format="url",
        ports=[8080, 80, 8000],
        version_keywords=["thinkphp", "think php"],
        server_keywords=["thinkphp"],  # 移除通用的 apache/nginx，避免误触发
        title_keywords=["thinkphp", "think framework", "欢迎使用 thinkphp"],
        path_keywords=["/index.php?s=captcha", "/thinkphp/"],
        powered_by_keywords=["thinkphp"],
        base_confidence=0.65,
    ),

    # ── Apache Shiro CVE-2016-4437 ───────────────────────────
    FingerprintRule(
        id="shiro_550",
        skill_id="cve_shiro_550",
        description="Apache Shiro CVE-2016-4437 RememberMe 反序列化",
        target_format="url",
        ports=[8080, 80, 443],
        version_keywords=["shiro", "apache shiro"],
        server_keywords=["tomcat", "apache-coyote", "jetty"],
        title_keywords=["login", "shiro", "remember me"],
        path_keywords=["/login", "/account/login"],
        powered_by_keywords=["shiro"],
        base_confidence=0.55,
    ),

    # ── FastJSON 1.2.24 RCE ──────────────────────────────────
    FingerprintRule(
        id="fastjson_1224",
        skill_id="cve_fastjson_1224",
        description="FastJSON 1.2.24 JNDI RCE",
        target_format="url",
        ports=[8090, 8080, 8888],
        version_keywords=["fastjson", "java", "spring"],
        server_keywords=["tomcat", "jetty", "spring"],
        path_keywords=["/api", "/json", "/fastjson"],
        base_confidence=0.45,
    ),

    # ── FastJSON 1.2.47 RCE ──────────────────────────────────
    FingerprintRule(
        id="fastjson_1247",
        skill_id="cve_fastjson_1247",
        description="FastJSON 1.2.47 loadClass 绕过 JNDI RCE",
        target_format="url",
        ports=[8090, 8080],
        version_keywords=["fastjson", "java"],
        server_keywords=["tomcat", "jetty"],
        path_keywords=["/api", "/json"],
        base_confidence=0.40,
    ),

    # ── Tomcat CVE-2017-12615 ────────────────────────────────
    FingerprintRule(
        id="tomcat_12615",
        skill_id="cve_tomcat_12615",
        description="Tomcat CVE-2017-12615 PUT Webshell",
        target_format="url",
        ports=[8080, 8443, 80],
        version_keywords=["apache tomcat", "tomcat", "coyote"],
        server_keywords=["apache-coyote", "apache tomcat"],
        title_keywords=["apache tomcat", "tomcat"],
        base_confidence=0.65,
    ),

    # ── PHP-FPM CVE-2019-11043 ───────────────────────────────
    FingerprintRule(
        id="php_fpm_11043",
        skill_id="cve_php_fpm_11043",
        description="PHP-FPM CVE-2019-11043 env_path_info RCE",
        target_format="url",
        ports=[8080, 80, 443],
        version_keywords=["php", "php-fpm", "nginx/php"],
        server_keywords=["nginx"],
        path_keywords=["/index.php", "/.php"],
        powered_by_keywords=["php"],
        base_confidence=0.5,
    ),

    # ── ActiveMQ CVE-2022-41678 ──────────────────────────────
    FingerprintRule(
        id="activemq_41678",
        skill_id="cve_activemq_41678",
        description="ActiveMQ CVE-2022-41678 Jolokia RCE",
        target_format="url",
        ports=[8161, 61616],           # 移除 8080，ActiveMQ Web 专用端口 8161
        version_keywords=["activemq", "apache activemq"],
        server_keywords=["activemq", "activemqrealm"],  # 移除通用的 jetty
        title_keywords=["activemq", "apache activemq"],
        path_keywords=["/admin/", "/api/jolokia/", "/activemq"],
        base_confidence=0.7,
    ),

    # ── JBoss CVE-2017-7504 ──────────────────────────────────
    FingerprintRule(
        id="jboss_7504",
        skill_id="cve_jboss_7504",
        description="JBoss CVE-2017-7504 HTTPServerIL 反序列化",
        target_format="url",
        ports=[8080, 1099, 4444],
        version_keywords=["jboss", "jboss as", "wildfly"],
        server_keywords=["jboss"],
        title_keywords=["jboss", "jboss as", "wildfly"],
        path_keywords=["/jbossmq-httpil/", "/jmx-console/", "/invoker/"],
        base_confidence=0.7,
    ),

    # ── Django CVE-2022-34265 ────────────────────────────────
    FingerprintRule(
        id="django_34265",
        skill_id="cve_django_34265",
        description="Django CVE-2022-34265 Trunc/Extract SQL 注入",
        target_format="url",
        ports=[8000, 80, 443],
        version_keywords=["django", "python/django", "wsgi"],
        server_keywords=["wsgiserver", "gunicorn", "uvicorn", "werkzeug"],
        title_keywords=["django", "site administration"],
        path_keywords=["/?date=", "/admin/"],
        powered_by_keywords=["django"],
        base_confidence=0.6,
    ),

    # ── Flask SSTI ───────────────────────────────────────────
    FingerprintRule(
        id="flask_ssti",
        skill_id="flask_ssti_exploit",
        description="Flask Jinja2 SSTI RCE",
        target_format="url",
        ports=[5000, 8000, 8080],
        version_keywords=["flask", "python/flask", "werkzeug"],
        server_keywords=["werkzeug", "gunicorn"],
        path_keywords=["/?name=", "/hello"],
        powered_by_keywords=["flask"],
        base_confidence=0.55,
    ),

    # ── GeoServer CVE-2024-36401 ─────────────────────────────
    FingerprintRule(
        id="geoserver_36401",
        skill_id="cve_geoserver_36401",
        description="GeoServer CVE-2024-36401 OGC eval 注入 RCE",
        target_format="url",
        ports=[8080, 80, 443],
        version_keywords=["geoserver"],
        server_keywords=["geoserver"],       # 移除通用的 jetty，GeoServer 专属
        title_keywords=["geoserver", "geoserver web admin"],
        path_keywords=["/geoserver/", "/geoserver/web/", "/wfs", "/wms"],
        base_confidence=0.75,
        use_root_path=True,   # Skill 内部自行拼接 /geoserver/wfs 路径
    ),

    # ── Fuel CMS CVE-2018-16763 ──────────────────────────────
    FingerprintRule(
        id="fuel_cms_rce",
        skill_id="fuel_cms_rce",
        description="Fuel CMS 1.4.1 未授权 RCE CVE-2018-16763",
        target_format="url",
        ports=[80, 443, 8080],
        version_keywords=["fuel cms", "fuelcms", "php/5", "php/7"],  # php version hint
        server_keywords=["apache"],  # Apache is a prerequisite, gives score
        title_keywords=["fuel cms", "welcome to fuel cms", "fuel: login"],
        path_keywords=["/structure/", "/fuel/", "/fuel/pages/", "index.php/fuel"],
        base_confidence=0.55,  # Skill does internal probing, so lower base is fine
        use_root_path=True,    # Skill will auto-detect the /structure/ path internally
    ),

    # ── Earth VulnHub Django XOR ─────────────────────────────
    FingerprintRule(
        id="earth_django_rce",
        skill_id="earth_django_rce",
        description="Earth VulnHub — XOR 解密 + Django CLI RCE + SUID reset_root",
        target_format="url",
        ports=[80, 443],
        version_keywords=["mod_wsgi", "python/3.9"],
        server_keywords=["mod_wsgi"],
        title_keywords=["earth secure messaging", "earth secure messaging service"],
        path_keywords=["/admin/", "/admin/login", "terratest"],
        powered_by_keywords=["mod_wsgi"],
        base_confidence=0.80,
    ),

    # ── Jangow busque.php 命令注入 ────────────────────────────
    FingerprintRule(
        id="jangow_cmd_injection",
        skill_id="jangow_cmd_injection",
        description="Jangow VulnHub — busque.php GET 参数直接传入 system() 命令注入 RCE",
        target_format="url",
        ports=[80, 443, 8080],
        version_keywords=[],
        server_keywords=["apache"],
        title_keywords=["grayscale", "start bootstrap", "buscar"],
        path_keywords=["busque", "site", "buscar"],
        powered_by_keywords=[],
        base_confidence=0.50,
        use_root_path=True,  # Skill 内部自动探测 /site/busque.php 路径
    ),

    # ── Jangow 完整攻击链 (busque.php + CVE-2017-16995) ──────
    FingerprintRule(
        id="jangow_full_pwn",
        skill_id="jangow_full_pwn",
        description="Jangow VulnHub — 完整攻击链：busque.php RCE + CVE-2017-16995 内核提权",
        target_format="url",
        ports=[80, 443, 8080],
        version_keywords=[],
        server_keywords=["apache"],
        title_keywords=["grayscale", "start bootstrap", "buscar", "jangow"],
        path_keywords=["busque", "site/busque", "buscar", "/site/"],
        powered_by_keywords=[],
        base_confidence=0.55,
        use_root_path=True,
    ),

    # ── WordPress 弱密码 + 主题编辑器 RCE ────────────────────
    FingerprintRule(
        id="wordpress_rce",
        skill_id="wordpress_rce",
        description="WordPress 弱密码登录 + 主题编辑器写入 Webshell RCE",
        target_format="url",
        ports=[80, 443, 8080],
        version_keywords=["wordpress", "wp"],
        server_keywords=["apache", "nginx"],
        title_keywords=["wordpress", "powered by wordpress", "just another wordpress site"],
        path_keywords=["/wp-admin", "/wp-login", "/wp-content", "/wp-includes", "/xmlrpc.php", "/?p="],
        powered_by_keywords=["wordpress", "wp"],
        base_confidence=0.70,
        use_root_path=True,
    ),
]

# 按 base_confidence 降序，高置信度优先
FINGERPRINT_RULES.sort(key=lambda r: r.base_confidence, reverse=True)


# ─────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────

def _normalize(s: str) -> str:
    return s.lower().strip() if s else ""


def _any_keyword(text: str, keywords: List[str]) -> bool:
    """text 中是否包含 keywords 中任意一个（不区分大小写）"""
    t = _normalize(text)
    return any(kw.lower() in t for kw in keywords)


def _extract_host(target: str) -> str:
    """从 URL 或 host:port 字符串中提取 hostname"""
    if "://" in target:
        return urlparse(target).hostname or target
    # host:port 格式
    return target.rsplit(":", 1)[0] if ":" in target else target


def _extract_port_from_target(target: str) -> Optional[int]:
    """从 URL 中提取端口，未明确指定时按 scheme 返回默认端口"""
    if "://" in target:
        p = urlparse(target)
        if p.port:
            return p.port
        return 443 if p.scheme == "https" else 80
    if ":" in target:
        try:
            return int(target.rsplit(":", 1)[1])
        except ValueError:
            pass
    return None


def _build_skill_target(base_target: str, port: int, fmt: str, use_root_path: bool = False) -> str:
    """构建 Skill 所需的 target 参数"""
    host = _extract_host(base_target)
    if fmt == "host_port":
        return f"{host}:{port}"
    scheme = "https" if port in (443, 8443) else "http"
    if use_root_path:
        # Skill 内部自行拼接路径（如 GeoServer），只需要 host:port
        return f"{scheme}://{host}:{port}/"
    # 如果 base_target 是带路径的 URL，保留其路径（如 /struts2-showcase/）
    if "://" in base_target:
        p = urlparse(base_target)
        path = p.path if p.path and p.path != "/" else "/"
    else:
        path = "/"
    return f"{scheme}://{host}:{port}{path}"


def _score_rule(
    rule: FingerprintRule,
    port: int,
    version_str: str,
    server_str: str,
    title_str: str,
    paths: List[str],
    powered_by: List[str],
) -> float:
    """
    计算单条规则对给定服务信息的匹配得分（0.0 ~ 1.0）。
    每类证据的命中都加分，返回综合得分。
    """
    score = 0.0
    hits = 0
    total_checks = 0

    # 端口匹配（强信号）
    total_checks += 1
    if port in rule.ports:
        score += 0.4
        hits += 1

    # version/nmap service 字段
    if rule.version_keywords:
        total_checks += 1
        if _any_keyword(version_str, rule.version_keywords):
            score += 0.3
            hits += 1

    # Server 响应头
    if rule.server_keywords:
        total_checks += 1
        if _any_keyword(server_str, rule.server_keywords):
            score += 0.25
            hits += 1

    # HTML title
    if rule.title_keywords:
        total_checks += 1
        if _any_keyword(title_str, rule.title_keywords):
            score += 0.2
            hits += 1

    # 路径关键词（dirsearch/curl 发现）
    if rule.path_keywords:
        total_checks += 1
        combined_paths = " ".join(paths)
        if _any_keyword(combined_paths, rule.path_keywords):
            score += 0.15
            hits += 1

    # X-Powered-By
    if rule.powered_by_keywords:
        total_checks += 1
        combined_pb = " ".join(powered_by)
        if _any_keyword(combined_pb, rule.powered_by_keywords):
            score += 0.2
            hits += 1

    # 必须至少命中 1 个证据才有效
    if hits < 1:
        return 0.0
    # 端口只命中、无其他特征 → 低置信度惩罚
    if hits == 1 and port in rule.ports:
        score *= 0.4

    # 评分策略：
    # - hits >= 2（端口 + 至少一项内容特征）→ 置信度至少为 base_confidence × 0.8
    #   (防止 base_confidence 太低把有效信号压到阈值以下)
    # - hits == 1（仅内容特征，无端口）→ 直接乘以 base_confidence
    raw = score * rule.base_confidence
    if hits >= 2:
        floor = rule.base_confidence * 0.8
        return min(max(raw, floor), 1.0)
    return min(raw, 1.0)


# ─────────────────────────────────────────────
# 核心公开函数
# ─────────────────────────────────────────────

def match_findings(findings: List[dict], base_target: str = "") -> List[MatchResult]:
    """
    根据 session.findings 列表匹配 CVE Skills。

    Args:
        findings: _parse_finding() 产生的结构化 finding 列表
        base_target: 扫描的原始目标（用于构建 skill target 参数）

    Returns:
        按置信度降序排列的 MatchResult 列表（已去重，每个 skill_id 只保留最高分）
    """
    # 聚合所有 findings 中的服务信息
    agg = _aggregate_findings(findings)

    best: dict[str, MatchResult] = {}   # skill_id → 最佳 MatchResult

    for svc in agg["services"]:
        port = svc["port"]
        version_str = svc.get("version", "")
        server_str = agg.get("server", "")
        title_str = agg.get("title", "")
        paths = agg.get("paths", [])
        powered_by = agg.get("powered_by", [])

        for rule in FINGERPRINT_RULES:
            sc = _score_rule(rule, port, version_str, server_str, title_str, paths, powered_by)
            if sc < 0.15:
                continue

            # 构建用于 skill 的 target
            tgt_base = base_target or svc.get("base_url", f"http://127.0.0.1:{port}/")
            skill_target = _build_skill_target(tgt_base, port, rule.target_format, rule.use_root_path)

            reason_parts = []
            if port in rule.ports:
                reason_parts.append(f"port={port}")
            if _any_keyword(version_str, rule.version_keywords):
                reason_parts.append(f"version='{version_str[:30]}'")
            if _any_keyword(server_str, rule.server_keywords):
                reason_parts.append(f"server='{server_str[:30]}'")
            if _any_keyword(title_str, rule.title_keywords):
                reason_parts.append(f"title='{title_str[:30]}'")

            m = MatchResult(
                skill_id=rule.skill_id,
                target=skill_target,
                confidence=sc,
                reason=", ".join(reason_parts) or "port match",
                description=rule.description,
                port=port,
            )

            # 保留每个 skill_id 的最高分
            if rule.skill_id not in best or best[rule.skill_id].confidence < sc:
                best[rule.skill_id] = m

    # 也对 http_probe 做轻量匹配（单独处理无端口上下文的情况）
    for finding in findings:
        if finding.get("type") != "http_probe":
            continue
        server = finding.get("server", "")
        title  = finding.get("title", "")
        pb     = finding.get("info_disclosure", [])
        paths  = finding.get("forms", []) + finding.get("interesting_paths", [])
        cmd    = finding.get("command", "")
        # 把 curl 命令中的 URL 路径也加入 paths，以匹配 path_keywords
        _url_m = re.search(r'https?://[^\s]+', cmd)
        if _url_m:
            paths = list(paths) + [_url_m.group(0)]

        # 从命令中提取端口（命令字符串需先提取其中的 URL）
        _url_for_port = _url_m.group(0) if _url_m else cmd
        port_in_cmd = _extract_port_from_target(_url_for_port) or 80

        for rule in FINGERPRINT_RULES:
            sc = _score_rule(rule, port_in_cmd, "", server, title, paths, pb)
            if sc < 0.2:
                continue

            tgt_base = base_target or cmd
            skill_target = _build_skill_target(tgt_base, port_in_cmd, rule.target_format, rule.use_root_path)

            reason_parts = []
            if _any_keyword(server, rule.server_keywords):
                reason_parts.append(f"Server: {server[:30]}")
            if _any_keyword(title, rule.title_keywords):
                reason_parts.append(f"Title: {title[:30]}")

            m = MatchResult(
                skill_id=rule.skill_id,
                target=skill_target,
                confidence=sc,
                reason=", ".join(reason_parts) or "http probe match",
                description=rule.description,
                port=port_in_cmd,
            )
            if rule.skill_id not in best or best[rule.skill_id].confidence < sc:
                best[rule.skill_id] = m

    results = sorted(best.values(), key=lambda x: x.confidence, reverse=True)
    return results


def _aggregate_findings(findings: List[dict]) -> dict:
    """
    从 findings 列表中聚合所有服务信息到一个结构中，
    供 match_findings 统一处理。
    """
    services = []      # [{port, version, service, base_url}]
    server = ""
    all_titles: List[str] = []  # 收集所有 title，最终合并为空格分隔字符串
    paths = []
    powered_by = []

    for f in findings:
        ftype = f.get("type", "")

        if ftype == "port_scan":
            raw_services = f.get("services", [])
            # services 可能是 list[dict] 或 dict{port_str: svc_str}
            if isinstance(raw_services, dict):
                # _parse_finding 返回的格式: {"7001": "weblogic/14.1.1", ...}
                for port_str, svc_str in raw_services.items():
                    try:
                        port = int(str(port_str).split("/")[0])
                    except (ValueError, TypeError):
                        port = 0
                    if port:
                        services.append({
                            "port": port,
                            "service": str(svc_str),
                            "version": str(svc_str),
                            "base_url": "",
                        })
            else:
                for svc in raw_services:
                    if isinstance(svc, dict):
                        try:
                            port = int(svc.get("port", 0))
                        except (ValueError, TypeError):
                            port = 0
                        if port:
                            services.append({
                                "port": port,
                                "service": svc.get("service", ""),
                                "version": svc.get("version", ""),
                                "base_url": "",
                            })
                    elif isinstance(svc, str):
                        # "80/http" 格式
                        m = re.match(r"(\d+)/?(.*)", svc)
                        if m:
                            try:
                                port = int(m.group(1))
                            except ValueError:
                                port = 0
                            if port:
                                services.append({
                                    "port": port,
                                    "service": m.group(2) or svc,
                                    "version": "",
                                    "base_url": "",
                                })
            # open_ports 补充（格式 "80" 或 "80/http"）
            for op in f.get("open_ports", []):
                m = re.match(r"(\d+)", str(op))
                if m:
                    port = int(m.group(1))
                    if not any(s["port"] == port for s in services):
                        services.append({"port": port, "service": str(op), "version": "", "base_url": ""})

        elif ftype == "http_probe":
            if f.get("server"):
                server = f["server"]
            if f.get("title"):
                t = f["title"].strip()
                if t and t not in all_titles:
                    all_titles.append(t)
            powered_by.extend(f.get("info_disclosure", []))
            paths.extend(f.get("forms", []))
            # 从命令中提取 URL，再从 URL 提取端口
            cmd = f.get("command", "")
            # 命令可能是 "curl -v http://host:port/path"，先提取其中的 URL
            url_match = re.search(r'https?://[^\s]+', cmd)
            url_for_port = url_match.group(0) if url_match else cmd
            port = _extract_port_from_target(url_for_port)
            if port and not any(s["port"] == port for s in services):
                services.append({
                    "port": port,
                    "service": "http",
                    "version": server,
                    "base_url": url_for_port,
                })

        elif ftype == "dir_enum":
            paths.extend(f.get("paths_found", []))
            paths.extend(f.get("interesting", []))

    # 确保 server 信息也注入到每个服务的 version 字段（用于关键词匹配）
    for svc in services:
        if server and not svc["version"]:
            svc["version"] = server

    # 合并所有收集到的 title 为单个字符串供关键词匹配
    title = " | ".join(all_titles)

    return {
        "services": services,
        "server": server,
        "title": title,
        "paths": paths,
        "powered_by": powered_by,
    }
