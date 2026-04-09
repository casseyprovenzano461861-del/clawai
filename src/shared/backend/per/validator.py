# -*- coding: utf-8 -*-
"""
ValidatorAgent - 漏洞验证层

职责：接收 P-E-R Executor 发现的疑似漏洞信号，
      调用 EnhancedVulnerabilityDetector 进行二次确认，
      返回带证据的 ValidationResult。

设计原则：
- 复用 vuln_detector.py，零重复代码
- 同步执行（P-E-R 任务图中作为独立 validation 节点）
- 失败安全：验证器异常不影响主流程，降级为 unverified
"""

import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# 漏洞类型到后续建议的映射
_SUGGESTED_NEXT = {
    "sqli": "dump 数据库（sqlmap --dump），尝试读取敏感文件（--file-read）",
    "xss": "构造 cookie 窃取 payload，尝试 CSRF 联动",
    "rce": "建立反向 shell，进行权限提升",
    "lfi": "尝试读取 /etc/passwd、SSH 私钥，配合日志文件 RCE",
    "ssrf": "探测内网服务（169.254.169.254 云元数据、Redis、内网 HTTP）",
    "ssti": "升级为 RCE（{{ ''.__class__.__mro__[1].__subclasses__() }}）",
    "xxe": "读取敏感文件，尝试 SSRF 联动",
    "rfi": "托管恶意 PHP 文件，远程包含执行",
    "file_upload": "上传 webshell，获取 RCE",
    "auth_bypass": "访问管理后台，导出数据",
    "default": "深入分析漏洞影响范围，评估利用可行性",
}


@dataclass
class ValidationResult:
    """漏洞验证结果

    Attributes:
        verified:      漏洞是否通过二次确认（真实成立）
        vuln_type:     漏洞类型（sqli/xss/rce/...）
        target:        被测目标 URL
        evidence:      证据列表（payload、响应片段、时间差等）
        confidence:    置信度 0.0~1.0
        exploit_proof: 可直接写入报告的证明文本
        suggested_next: 建议的后续攻击步骤
        raw_findings:  原始 DetectedVulnerability 对象列表（供调试）
        error:         验证过程中的异常信息（失败安全）
    """
    verified: bool = False
    vuln_type: str = "unknown"
    target: str = ""
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.0
    exploit_proof: str = ""
    suggested_next: str = ""
    raw_findings: List[Any] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verified": self.verified,
            "vuln_type": self.vuln_type,
            "target": self.target,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "exploit_proof": self.exploit_proof,
            "suggested_next": self.suggested_next,
            "error": self.error,
        }


class VulnValidatorAgent:
    """漏洞验证代理

    在 P-E-R 循环中作为独立验证节点，由 Reflector 在检测到
    vuln_found 信号后触发。

    使用方式：
        validator = VulnValidatorAgent()
        result = validator.validate(finding, target)
        if result.verified:
            # 写入 evidence，触发报告
    """

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def validate(self, finding: Dict[str, Any], target: str) -> ValidationResult:
        """验证疑似漏洞是否真实成立

        Args:
            finding: Executor/Skill 产出的疑似漏洞信号，必须包含 "type" 字段
            target:  目标 URL（若 finding 中有 url 字段则优先使用）

        Returns:
            ValidationResult，verified=True 表示漏洞确认成立
        """
        vuln_type = finding.get("type", "unknown").lower()
        effective_target = finding.get("url") or finding.get("target") or target

        logger.info(f"[ValidatorAgent] 开始验证: {vuln_type} @ {effective_target}")
        start = time.time()

        try:
            result = self._dispatch(vuln_type, effective_target, finding)
        except Exception as exc:
            logger.warning(f"[ValidatorAgent] 验证异常（失败安全）: {exc}")
            result = ValidationResult(
                verified=False,
                vuln_type=vuln_type,
                target=effective_target,
                confidence=0.0,
                exploit_proof="验证过程发生异常，无法确认漏洞",
                suggested_next=_SUGGESTED_NEXT.get(vuln_type, _SUGGESTED_NEXT["default"]),
                error=str(exc),
            )

        elapsed = time.time() - start
        logger.info(
            f"[ValidatorAgent] 验证完成: verified={result.verified}, "
            f"confidence={result.confidence:.2f}, elapsed={elapsed:.1f}s"
        )
        return result

    # ------------------------------------------------------------------
    # 内部：按漏洞类型分派
    # ------------------------------------------------------------------

    def _dispatch(self, vuln_type: str, target: str, finding: Dict[str, Any]) -> ValidationResult:
        """按漏洞类型分派到对应检测器"""
        try:
            from backend.vuln_detector import EnhancedVulnerabilityDetector
        except ImportError:
            try:
                import sys
                import os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
                from vuln_detector import EnhancedVulnerabilityDetector
            except ImportError as e:
                raise RuntimeError(f"无法导入 EnhancedVulnerabilityDetector: {e}")

        detector = EnhancedVulnerabilityDetector(timeout=self.timeout)

        # 按类型选择检测方法
        type_map = {
            "sqli":              detector._detect_sqli,
            "sql_injection":     detector._detect_sqli,
            "xss":               detector._detect_xss,
            "rce":               detector._detect_rce,
            "command_injection": detector._detect_rce,
            "lfi":               detector._detect_lfi,
            "path_traversal":    detector._detect_lfi,
            "ssrf":              detector._detect_ssrf,
            "ssti":              detector._detect_ssti,
            "xxe":               detector._detect_xxe,
            "sensitive":         detector._detect_sensitive_info,
            "info_disclosure":   detector._detect_sensitive_info,
        }

        detect_fn = type_map.get(vuln_type)
        if detect_fn is None:
            # 未知类型：全量检测，取最高置信度结果
            logger.debug(f"[ValidatorAgent] 未知类型 {vuln_type!r}，执行全量检测")
            findings = detector.detect(target)
        else:
            findings = detect_fn(target)

        return self._build_result(findings, vuln_type, target, finding)

    def _build_result(
        self,
        findings: list,
        vuln_type: str,
        target: str,
        original_finding: Dict[str, Any],
    ) -> ValidationResult:
        """将 DetectedVulnerability 列表转换为 ValidationResult"""

        if not findings:
            return ValidationResult(
                verified=False,
                vuln_type=vuln_type,
                target=target,
                confidence=0.1,
                exploit_proof="二次验证未能复现漏洞，可能是误报或目标已修复",
                suggested_next="尝试不同 payload 变体，或人工确认",
                raw_findings=[],
            )

        # 选取置信度最高的发现
        best = max(findings, key=lambda v: (v.verified, v.cvss_score))

        evidence_lines = []
        for ev in best.evidence[:5]:
            if ev.payload:
                evidence_lines.append(f"Payload: {ev.payload}")
            if ev.indicator:
                evidence_lines.append(f"Indicator: {ev.indicator}")
            if ev.response:
                evidence_lines.append(f"Response excerpt: {ev.response[:120]}")

        # 置信度：已验证 0.90+，未验证但有迹象 0.60
        confidence = 0.92 if best.verified else 0.62

        if best.verified:
            proof = (
                f"[已验证] {best.title}\n"
                f"目标: {best.url}\n"
                f"CVSS: {best.cvss_score}\n"
                f"证据数: {len(best.evidence)}\n"
                f"修复建议: {best.remediation}"
            )
        else:
            proof = (
                f"[疑似] {best.title}（未二次确认）\n"
                f"目标: {best.url}\n"
                f"CVSS: {best.cvss_score}\n"
                f"修复建议: {best.remediation}"
            )

        return ValidationResult(
            verified=best.verified,
            vuln_type=vuln_type,
            target=target,
            evidence=evidence_lines,
            confidence=confidence,
            exploit_proof=proof,
            suggested_next=_SUGGESTED_NEXT.get(vuln_type, _SUGGESTED_NEXT["default"]),
            raw_findings=findings,
        )
