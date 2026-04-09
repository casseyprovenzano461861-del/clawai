#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI CLI 扫描结果导出模块
支持将扫描会话导出为 JSON、Markdown、HTML 格式。
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.cli.config import get_config

logger = logging.getLogger(__name__)

# 按严重级别排序权重
_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4, "unknown": 5}


def _session_to_dict(session) -> Dict[str, Any]:
    """将 Session dataclass 或 dict 转换为纯 dict"""
    if isinstance(session, dict):
        return session
    if hasattr(session, "__dataclass_fields__"):
        messages = []
        for msg in getattr(session, "messages", []):
            messages.append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if hasattr(msg.timestamp, "isoformat") else str(msg.timestamp),
                "metadata": getattr(msg, "metadata", {}),
            })
        return {
            "session_id": session.session_id,
            "target": session.target,
            "phase": session.phase,
            "findings": session.findings,
            "messages": messages,
            "created_at": session.created_at.isoformat() if hasattr(session.created_at, "isoformat") else str(session.created_at),
            "updated_at": session.updated_at.isoformat() if hasattr(session.updated_at, "isoformat") else str(session.updated_at),
        }
    raise TypeError(f"不支持的 session 类型: {type(session)}")


class Exporter:
    """扫描结果导出器"""

    def __init__(self, export_dir: Optional[Path] = None):
        self._dir = export_dir or get_config().export_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 公共入口
    # ------------------------------------------------------------------

    def export(self, session, fmt: str = "markdown", filename: Optional[str] = None) -> Path:
        """
        导出会话结果。

        Args:
            session: Session dataclass 或 dict
            fmt: 'json' | 'markdown' | 'html'
            filename: 可选，不含扩展名的文件名；默认按 session_id + 时间戳生成

        Returns:
            导出文件的 Path 对象
        """
        data = _session_to_dict(session)
        fmt = fmt.lower().strip()

        if filename is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            sid = data.get("session_id", "unknown")
            filename = f"{sid}_{ts}"

        ext_map = {"json": ".json", "markdown": ".md", "md": ".md", "html": ".html"}
        ext = ext_map.get(fmt, ".md")
        path = self._dir / f"{filename}{ext}"

        if fmt == "json":
            self._export_json(data, path)
        elif fmt in ("markdown", "md"):
            self._export_markdown(data, path)
        elif fmt == "html":
            self._export_html(data, path)
        else:
            raise ValueError(f"不支持的格式: {fmt}（支持: json, markdown, html）")

        logger.info(f"导出完成: {path}")
        return path

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------

    def _export_json(self, data: Dict[str, Any], path: Path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Markdown
    # ------------------------------------------------------------------

    def _export_markdown(self, data: Dict[str, Any], path: Path):
        lines = []
        target = data.get("target") or "未指定"
        created = data.get("created_at", "")
        phase = data.get("phase", "")
        findings: List[Dict] = data.get("findings", [])
        messages: List[Dict] = data.get("messages", [])

        lines.append(f"# ClawAI 渗透测试报告")
        lines.append(f"")
        lines.append(f"| 字段 | 值 |")
        lines.append(f"|------|----|")
        lines.append(f"| **目标** | `{target}` |")
        lines.append(f"| **会话 ID** | `{data.get('session_id', '')}` |")
        lines.append(f"| **阶段** | {phase} |")
        lines.append(f"| **创建时间** | {created} |")
        lines.append(f"| **发现数量** | {len(findings)} |")
        lines.append(f"")

        # 摘要
        critical = sum(1 for f in findings if f.get("severity", "").lower() == "critical")
        high = sum(1 for f in findings if f.get("severity", "").lower() == "high")
        medium = sum(1 for f in findings if f.get("severity", "").lower() == "medium")
        low = sum(1 for f in findings if f.get("severity", "").lower() == "low")

        lines.append(f"## 风险摘要")
        lines.append(f"")
        lines.append(f"| 严重 | 高 | 中 | 低 |")
        lines.append(f"|------|----|----|-----|")
        lines.append(f"| {critical} | {high} | {medium} | {low} |")
        lines.append(f"")

        # 发现列表
        if findings:
            lines.append(f"## 发现的问题")
            lines.append(f"")
            sorted_findings = sorted(findings, key=lambda f: _SEVERITY_ORDER.get(f.get("severity", "unknown").lower(), 5))
            for i, finding in enumerate(sorted_findings, 1):
                sev = finding.get("severity", "info").upper()
                ftype = finding.get("type", "未知")
                title = finding.get("title", ftype)
                lines.append(f"### {i}. {title}")
                lines.append(f"")
                lines.append(f"- **严重程度**: `{sev}`")
                if finding.get("url"):
                    lines.append(f"- **位置**: `{finding['url']}`")
                if finding.get("command"):
                    lines.append(f"- **命令**: `{finding['command']}`")
                if finding.get("output_preview"):
                    lines.append(f"- **输出预览**:")
                    lines.append(f"  ```")
                    lines.append(f"  {finding['output_preview'][:300]}")
                    lines.append(f"  ```")
                lines.append(f"")
        else:
            lines.append(f"## 发现的问题")
            lines.append(f"")
            lines.append(f"> 本次扫描未记录发现。")
            lines.append(f"")

        # 对话历史（可选，仅包含 assistant 消息摘要）
        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
        if assistant_msgs:
            lines.append(f"## AI 分析摘要")
            lines.append(f"")
            for msg in assistant_msgs[-5:]:  # 最后5条
                ts = msg.get("timestamp", "")
                content = msg.get("content", "").strip()[:500]
                lines.append(f"**[{ts}]**")
                lines.append(f"")
                lines.append(content)
                lines.append(f"")

        lines.append(f"---")
        lines.append(f"*报告由 ClawAI 自动生成 · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    # ------------------------------------------------------------------
    # HTML
    # ------------------------------------------------------------------

    def _export_html(self, data: Dict[str, Any], path: Path):
        target = data.get("target") or "未指定"
        created = data.get("created_at", "")
        phase = data.get("phase", "")
        findings: List[Dict] = data.get("findings", [])
        session_id = data.get("session_id", "")

        sev_color = {
            "critical": "#dc2626",
            "high": "#ea580c",
            "medium": "#d97706",
            "low": "#65a30d",
            "info": "#2563eb",
        }

        critical = sum(1 for f in findings if f.get("severity", "").lower() == "critical")
        high = sum(1 for f in findings if f.get("severity", "").lower() == "high")
        medium = sum(1 for f in findings if f.get("severity", "").lower() == "medium")
        low = sum(1 for f in findings if f.get("severity", "").lower() == "low")

        # 发现列表 HTML
        findings_html = ""
        if findings:
            sorted_findings = sorted(findings, key=lambda f: _SEVERITY_ORDER.get(f.get("severity", "unknown").lower(), 5))
            for finding in sorted_findings:
                sev = finding.get("severity", "info").lower()
                color = sev_color.get(sev, "#6b7280")
                ftype = finding.get("type", "未知")
                title = finding.get("title", ftype)
                url = finding.get("url", "")
                cmd = finding.get("command", "")
                preview = finding.get("output_preview", "")[:300]

                findings_html += f"""
        <div class="finding">
            <div class="finding-header">
                <span class="badge" style="background:{color}">{sev.upper()}</span>
                <strong>{_escape_html(title)}</strong>
            </div>
            {'<p><b>位置:</b> <code>' + _escape_html(url) + '</code></p>' if url else ''}
            {'<p><b>命令:</b> <code>' + _escape_html(cmd) + '</code></p>' if cmd else ''}
            {'<pre>' + _escape_html(preview) + '</pre>' if preview else ''}
        </div>"""
        else:
            findings_html = "<p>本次扫描未记录发现。</p>"

        html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ClawAI 渗透测试报告 - {_escape_html(target)}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  h1 {{ color: #38bdf8; border-bottom: 2px solid #1e3a5f; padding-bottom: 10px; }}
  h2 {{ color: #7dd3fc; margin-top: 30px; }}
  .meta-table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
  .meta-table td {{ padding: 8px 12px; border: 1px solid #1e3a5f; }}
  .meta-table td:first-child {{ background: #1e3a5f; font-weight: bold; width: 140px; }}
  .summary-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0; }}
  .stat-card {{ background: #1e293b; border-radius: 8px; padding: 16px; text-align: center; }}
  .stat-card .num {{ font-size: 2em; font-weight: bold; }}
  .finding {{ background: #1e293b; border-radius: 8px; padding: 16px; margin: 12px 0; border-left: 4px solid #334155; }}
  .finding-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
  .badge {{ padding: 3px 10px; border-radius: 4px; color: #fff; font-size: 0.8em; font-weight: bold; }}
  code {{ background: #0f172a; padding: 2px 6px; border-radius: 4px; font-family: monospace; }}
  pre {{ background: #0f172a; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 0.85em; }}
  footer {{ margin-top: 40px; text-align: center; color: #64748b; font-size: 0.85em; }}
</style>
</head>
<body>
<div class="container">
  <h1>ClawAI 渗透测试报告</h1>
  <table class="meta-table">
    <tr><td>目标</td><td><code>{_escape_html(target)}</code></td></tr>
    <tr><td>会话 ID</td><td><code>{_escape_html(session_id)}</code></td></tr>
    <tr><td>阶段</td><td>{_escape_html(phase)}</td></tr>
    <tr><td>创建时间</td><td>{_escape_html(created)}</td></tr>
    <tr><td>发现数量</td><td>{len(findings)}</td></tr>
  </table>

  <h2>风险摘要</h2>
  <div class="summary-grid">
    <div class="stat-card"><div class="num" style="color:#dc2626">{critical}</div><div>严重</div></div>
    <div class="stat-card"><div class="num" style="color:#ea580c">{high}</div><div>高</div></div>
    <div class="stat-card"><div class="num" style="color:#d97706">{medium}</div><div>中</div></div>
    <div class="stat-card"><div class="num" style="color:#65a30d">{low}</div><div>低</div></div>
  </div>

  <h2>发现的问题</h2>
  {findings_html}

  <footer>报告由 ClawAI 自动生成 &middot; {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</footer>
</div>
</body>
</html>"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)


def _escape_html(text: str) -> str:
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


# ------------------------------------------------------------------
# 便捷函数
# ------------------------------------------------------------------

def export_session(session, fmt: str = "markdown", filename: Optional[str] = None,
                   export_dir: Optional[Path] = None) -> Path:
    """
    快速导出会话结果。

    Args:
        session: Session dataclass 或 dict
        fmt: 'json' | 'markdown' | 'html'
        filename: 可选文件名（不含扩展名）
        export_dir: 可选导出目录，默认使用配置中的 export_dir

    Returns:
        导出文件路径
    """
    return Exporter(export_dir).export(session, fmt=fmt, filename=filename)
