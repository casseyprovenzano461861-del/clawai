# -*- coding: utf-8 -*-
"""
JWT 安全检测器 - ClawAI Demo 插件
检测 JWT 常见漏洞：alg:none 混淆、弱密钥、敏感信息泄露、过期校验缺失

插件规范：每个插件必须实现 ClawAIPlugin 接口
- plugin_id: str          唯一标识（与 plugin.json id 一致）
- run(target, context)    主执行函数，返回 Finding 列表
- health_check()          健康检查，返回 {"ok": bool, "message": str}
"""

import base64
import json
import re
import hashlib
import hmac
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("clawai.plugin.jwt_scanner")

# ── 内置弱密钥字典（生产环境建议使用外部字典文件）────────────────────────────
_WEAK_SECRETS = [
    "secret", "password", "123456", "qwerty", "letmein", "admin",
    "jwt_secret", "your-secret-key", "supersecret", "changeme",
    "mysecretkey", "secretkey", "key", "token", "jwt", "test",
    "development", "production", "app_secret", "flask_secret",
    "django-insecure", "your-256-bit-secret", "your-384-bit-secret",
    "your-512-bit-secret", "HS256", "HS384", "HS512",
]


class ClawAIPlugin:
    """ClawAI 插件基类接口（由 ClawAI 框架提供，此处为 Demo 内联定义）"""

    plugin_id: str = ""

    def run(self, target: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def health_check(self) -> Dict[str, Any]:
        return {"ok": True, "message": "ready"}

    def _finding(self, title: str, severity: str, description: str,
                 location: str = "", evidence: str = "",
                 remediation: str = "", cve: str = "") -> Dict[str, Any]:
        """构建标准 Finding 字典"""
        return {
            "type": self.plugin_id,
            "title": title,
            "severity": severity,        # critical / high / medium / low / info
            "description": description,
            "location": location,
            "evidence": evidence,
            "remediation": remediation,
            "cve": cve,
            "source": f"plugin:{self.plugin_id}",
        }


class JwtScannerPlugin(ClawAIPlugin):
    """JWT 安全检测器主类"""

    plugin_id = "jwt_scanner"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.check_alg_none = self.config.get("check_alg_none", True)
        self.check_weak_secret = self.config.get("check_weak_secret", True)
        self.timeout = self.config.get("timeout", 10)

    # ── 主入口 ────────────────────────────────────────────────────────────────

    def run(self, target: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        扫描目标响应中的 JWT token，检测安全问题

        Args:
            target:  目标 URL
            context: ClawAI 上下文，包含 http_responses / cookies / headers 等
        Returns:
            findings: Finding 字典列表
        """
        findings = []
        tokens = self._extract_tokens(context)

        if not tokens:
            logger.info(f"[jwt_scanner] 未在 {target} 响应中发现 JWT token")
            return findings

        logger.info(f"[jwt_scanner] 发现 {len(tokens)} 个 JWT token，开始分析")

        for token_str, token_location in tokens:
            header, payload = self._decode_token(token_str)
            if header is None:
                continue

            # 检测 alg:none
            if self.check_alg_none:
                f = self._check_alg_none(token_str, header, token_location)
                if f:
                    findings.append(f)

            # 检测弱密钥
            if self.check_weak_secret:
                f = self._check_weak_secret(token_str, header, token_location)
                if f:
                    findings.append(f)

            # 检测敏感声明泄露
            f = self._check_sensitive_claims(payload, token_location)
            if f:
                findings.append(f)

            # 检测过期时间
            f = self._check_expiry(payload, token_location)
            if f:
                findings.append(f)

        return findings

    # ── 辅助方法 ──────────────────────────────────────────────────────────────

    def _extract_tokens(self, context: Dict[str, Any]) -> List[tuple]:
        """从 context 中提取所有 JWT token"""
        jwt_pattern = re.compile(
            r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*'
        )
        tokens = []

        # 从 HTTP 响应头提取
        for resp in context.get("http_responses", []):
            for header_name, header_val in resp.get("headers", {}).items():
                for match in jwt_pattern.finditer(header_val):
                    tokens.append((match.group(), f"Header:{header_name}"))

            # 从响应体提取
            body = resp.get("body", "")
            for match in jwt_pattern.finditer(body):
                tokens.append((match.group(), "ResponseBody"))

        # 从 Cookie 提取
        for name, value in context.get("cookies", {}).items():
            for match in jwt_pattern.finditer(value):
                tokens.append((match.group(), f"Cookie:{name}"))

        # 去重
        seen = set()
        unique = []
        for t in tokens:
            if t[0] not in seen:
                seen.add(t[0])
                unique.append(t)
        return unique

    def _decode_token(self, token: str):
        """Base64url 解码 JWT header 和 payload"""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None, None

            def pad(s):
                return s + "=" * (-len(s) % 4)

            header = json.loads(base64.urlsafe_b64decode(pad(parts[0])))
            payload = json.loads(base64.urlsafe_b64decode(pad(parts[1])))
            return header, payload
        except Exception:
            return None, None

    def _check_alg_none(self, token: str, header: dict, location: str):
        """检测 alg:none 或大小写混淆的 none 算法"""
        alg = str(header.get("alg", "")).lower()
        if alg in ("none", "null", ""):
            return self._finding(
                title="JWT 算法设置为 none（签名绕过）",
                severity="critical",
                description=(
                    "JWT Header 中的 alg 字段设置为 none，意味着服务器可能接受无签名的 Token，"
                    "攻击者可伪造任意声明（如提升权限）而无需知道密钥。"
                ),
                location=location,
                evidence=f"alg={header.get('alg')}  token={token[:40]}...",
                remediation=(
                    "1. 服务端必须强制校验 alg 字段，拒绝接受 none/null 算法。\n"
                    "2. 使用白名单方式指定允许的算法（如仅允许 RS256 或 HS256）。\n"
                    "3. 升级 JWT 库至最新版本（多数现代库已修复此问题）。"
                ),
                cve="CVE-2015-9235",
            )
        return None

    def _check_weak_secret(self, token: str, header: dict, location: str):
        """使用内置字典尝试破解 HMAC 签名密钥"""
        alg = header.get("alg", "")
        if not alg.startswith("HS"):
            return None

        parts = token.split(".")
        message = f"{parts[0]}.{parts[1]}".encode()
        sig = base64.urlsafe_b64decode(parts[2] + "==")

        hash_map = {"HS256": hashlib.sha256, "HS384": hashlib.sha384, "HS512": hashlib.sha512}
        hash_func = hash_map.get(alg, hashlib.sha256)

        wordlist = self.config.get("wordlist", "builtin")
        candidates = _WEAK_SECRETS if wordlist == "builtin" else self._load_wordlist(wordlist)

        for secret in candidates:
            expected = hmac.new(secret.encode(), message, hash_func).digest()
            if hmac.compare_digest(expected, sig):
                return self._finding(
                    title=f"JWT 使用弱签名密钥（已破解）",
                    severity="critical",
                    description=(
                        f"JWT 使用 {alg} 算法签名，且密钥为常见弱密钥。"
                        "攻击者可使用此密钥伪造任意合法 Token。"
                    ),
                    location=location,
                    evidence=f"cracked_secret={secret!r}  alg={alg}",
                    remediation=(
                        "1. 立即轮换为强随机密钥（至少 256 位熵，推荐使用 secrets.token_hex(32)）。\n"
                        "2. 撤销当前所有已签发的 Token，强制用户重新登录。\n"
                        "3. 考虑迁移到非对称算法（RS256/ES256），避免密钥泄露风险。"
                    ),
                )
        return None

    def _check_sensitive_claims(self, payload: dict, location: str):
        """检测 payload 中是否包含敏感信息"""
        sensitive_keys = {"password", "passwd", "pwd", "secret", "api_key",
                          "credit_card", "ssn", "bank_account", "private_key"}
        found = [k for k in payload if k.lower() in sensitive_keys]
        if found:
            return self._finding(
                title="JWT Payload 包含敏感信息",
                severity="medium",
                description=(
                    f"JWT Payload 中发现敏感字段：{found}。"
                    "JWT 默认仅做 Base64url 编码，任何持有 Token 的人均可解码读取内容。"
                ),
                location=location,
                evidence=f"sensitive_fields={found}",
                remediation=(
                    "1. 不要在 JWT Payload 中存储密码、密钥等敏感信息。\n"
                    "2. 如需传输敏感数据，使用 JWE（JSON Web Encryption）对 Token 加密。\n"
                    "3. 遵循最小化原则，Payload 中只包含必要声明。"
                ),
            )
        return None

    def _check_expiry(self, payload: dict, location: str):
        """检测 Token 是否缺少过期时间声明"""
        if "exp" not in payload:
            return self._finding(
                title="JWT 缺少过期时间（exp）声明",
                severity="low",
                description=(
                    "JWT Payload 中未包含 exp（过期时间）声明，"
                    "Token 永不过期，一旦泄露将持续有效。"
                ),
                location=location,
                remediation=(
                    "1. 为所有 JWT 设置合理的过期时间（exp 声明），如 15 分钟~1 小时。\n"
                    "2. 实现 Token 撤销机制（黑名单或刷新 Token 模式）。"
                ),
            )
        return None

    def _load_wordlist(self, path: str) -> List[str]:
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception:
            return _WEAK_SECRETS

    def health_check(self) -> Dict[str, Any]:
        try:
            # 简单自检：尝试解码一个已知 JWT
            test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0In0.test"
            self._decode_token(test_token)
            return {"ok": True, "message": "jwt_scanner ready"}
        except Exception as e:
            return {"ok": False, "message": str(e)}


# ClawAI 框架通过此入口加载插件
def create_plugin(config=None) -> JwtScannerPlugin:
    return JwtScannerPlugin(config=config)
