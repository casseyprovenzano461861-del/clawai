# -*- coding: utf-8 -*-
"""
报告生成模块
实现安全测试报告的自动生成
"""

import json
import time
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ReportFormat(Enum):
    """报告格式"""
    HTML = "html"
    JSON = "json"
    MARKDOWN = "markdown"
    PDF = "pdf"


class VulnerabilitySeverity(Enum):
    """漏洞严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Vulnerability:
    """漏洞信息"""
    id: str
    name: str
    description: str
    severity: VulnerabilitySeverity
    cvss_score: float
    cve: Optional[str] = None
    reference: Optional[str] = None
    remediation: Optional[str] = None
    tool: Optional[str] = None


@dataclass
class ReportSection:
    """报告章节"""
    title: str
    content: str
    subsections: List['ReportSection'] = field(default_factory=list)


@dataclass
class SecurityReport:
    """安全测试报告"""
    report_id: str
    title: str
    target: str
    scan_date: str
    scanner: str
    version: str
    summary: str
    vulnerabilities: List[Vulnerability]
    sections: List[ReportSection]
    execution_time: float
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReportGenerator:
    """
    报告生成器
    负责生成安全测试报告
    """
    
    def __init__(self):
        """初始化报告生成器"""
        self.template_dir = os.path.join(os.path.dirname(__file__), "templates")
        os.makedirs(self.template_dir, exist_ok=True)
    
    def generate_report(self, report_data: Dict[str, Any], format: ReportFormat = ReportFormat.HTML) -> str:
        """生成报告"""
        # 创建报告对象
        report = self._create_report(report_data)
        
        # 根据格式生成报告
        if format == ReportFormat.HTML:
            return self._generate_html_report(report)
        elif format == ReportFormat.JSON:
            return self._generate_json_report(report)
        elif format == ReportFormat.MARKDOWN:
            return self._generate_markdown_report(report)
        elif format == ReportFormat.PDF:
            return self._generate_pdf_report(report)
        else:
            raise ValueError(f"不支持的报告格式: {format}")
    
    def _create_report(self, report_data: Dict[str, Any]) -> SecurityReport:
        """创建报告对象"""
        # 生成报告ID
        report_id = f"report_{int(time.time())}"
        
        # 提取基本信息
        target = report_data.get("target", "未知目标")
        scan_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        scanner = report_data.get("scanner", "ClawAI")
        version = report_data.get("version", "2.0.0")
        status = report_data.get("status", "completed")
        execution_time = report_data.get("execution_time", 0.0)
        
        # 生成摘要
        summary = self._generate_summary(report_data)
        
        # 提取漏洞信息
        vulnerabilities = self._extract_vulnerabilities(report_data)
        
        # 生成报告章节
        sections = self._generate_sections(report_data, vulnerabilities)
        
        return SecurityReport(
            report_id=report_id,
            title=f"{target} 安全测试报告",
            target=target,
            scan_date=scan_date,
            scanner=scanner,
            version=version,
            summary=summary,
            vulnerabilities=vulnerabilities,
            sections=sections,
            execution_time=execution_time,
            status=status,
            metadata=report_data.get("metadata", {})
        )
    
    def _generate_summary(self, report_data: Dict[str, Any]) -> str:
        """生成报告摘要"""
        # 统计漏洞数量
        vulnerabilities = report_data.get("vulnerabilities", [])
        critical_count = sum(1 for v in vulnerabilities if v.get("severity") == "critical")
        high_count = sum(1 for v in vulnerabilities if v.get("severity") == "high")
        medium_count = sum(1 for v in vulnerabilities if v.get("severity") == "medium")
        low_count = sum(1 for v in vulnerabilities if v.get("severity") == "low")
        
        # 生成摘要
        summary = f"对 {report_data.get('target', '未知目标')} 进行了安全测试，共发现 {len(vulnerabilities)} 个漏洞，其中严重 {critical_count} 个，高危 {high_count} 个，中危 {medium_count} 个，低危 {low_count} 个。"
        
        return summary
    
    def _extract_vulnerabilities(self, report_data: Dict[str, Any]) -> List[Vulnerability]:
        """提取漏洞信息"""
        vulnerabilities = []
        
        # 从报告数据中提取漏洞
        for vuln_data in report_data.get("vulnerabilities", []):
            # 转换严重程度
            severity = VulnerabilitySeverity(vuln_data.get("severity", "low"))
            
            # 创建漏洞对象
            vulnerability = Vulnerability(
                id=vuln_data.get("id", f"vuln_{len(vulnerabilities) + 1}"),
                name=vuln_data.get("name", "未知漏洞"),
                description=vuln_data.get("description", "无描述"),
                severity=severity,
                cvss_score=vuln_data.get("cvss_score", 0.0),
                cve=vuln_data.get("cve"),
                reference=vuln_data.get("reference"),
                remediation=vuln_data.get("remediation"),
                tool=vuln_data.get("tool")
            )
            
            vulnerabilities.append(vulnerability)
        
        # 按严重程度排序
        vulnerabilities.sort(key=lambda x: x.severity.value, reverse=True)
        
        return vulnerabilities
    
    def _generate_sections(self, report_data: Dict[str, Any], vulnerabilities: List[Vulnerability]) -> List[ReportSection]:
        """生成报告章节"""
        sections = []
        
        # 1. 执行摘要
        summary_section = ReportSection(
            title="1. 执行摘要",
            content=self._generate_summary(report_data)
        )
        sections.append(summary_section)
        
        # 2. 测试目标
        target_section = ReportSection(
            title="2. 测试目标",
            content=f"测试目标: {report_data.get('target', '未知目标')}\n" +
                   f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n" +
                   f"测试工具: {report_data.get('scanner', 'ClawAI')} {report_data.get('version', '2.0.0')}\n" +
                   f"执行时间: {report_data.get('execution_time', 0.0):.2f} 秒\n" +
                   f"测试状态: {report_data.get('status', 'completed')}"
        )
        sections.append(target_section)
        
        # 3. 漏洞摘要
        vuln_summary = """
        | 严重程度 | 数量 |
        |---------|------|
        | 严重    | {critical} |
        | 高危    | {high} |
        | 中危    | {medium} |
        | 低危    | {low} |
        | 信息    | {info} |
        | **总计** | **{total}** |
        """
        
        # 统计漏洞数量
        critical_count = sum(1 for v in vulnerabilities if v.severity == VulnerabilitySeverity.CRITICAL)
        high_count = sum(1 for v in vulnerabilities if v.severity == VulnerabilitySeverity.HIGH)
        medium_count = sum(1 for v in vulnerabilities if v.severity == VulnerabilitySeverity.MEDIUM)
        low_count = sum(1 for v in vulnerabilities if v.severity == VulnerabilitySeverity.LOW)
        info_count = sum(1 for v in vulnerabilities if v.severity == VulnerabilitySeverity.INFO)
        total_count = len(vulnerabilities)
        
        vuln_summary = vuln_summary.format(
            critical=critical_count,
            high=high_count,
            medium=medium_count,
            low=low_count,
            info=info_count,
            total=total_count
        )
        
        vuln_section = ReportSection(
            title="3. 漏洞摘要",
            content=vuln_summary
        )
        sections.append(vuln_section)
        
        # 4. 详细漏洞信息
        detailed_vuln_section = ReportSection(
            title="4. 详细漏洞信息",
            content=""
        )
        
        # 按严重程度分组漏洞
        for severity in [VulnerabilitySeverity.CRITICAL, VulnerabilitySeverity.HIGH, VulnerabilitySeverity.MEDIUM, VulnerabilitySeverity.LOW, VulnerabilitySeverity.INFO]:
            severity_vulns = [v for v in vulnerabilities if v.severity == severity]
            if severity_vulns:
                severity_section = ReportSection(
                    title=f"4.{list(VulnerabilitySeverity).index(severity) + 1} {severity.value.upper()} 漏洞",
                    content=""
                )
                
                for vuln in severity_vulns:
                    vuln_content = f"""
                    **漏洞名称**: {vuln.name}
                    **漏洞ID**: {vuln.id}
                    **严重程度**: {vuln.severity.value.upper()}
                    **CVSS评分**: {vuln.cvss_score}
                    **CVE编号**: {vuln.cve or "无"}
                    **描述**: {vuln.description}
                    **发现工具**: {vuln.tool or "未知"}
                    **参考链接**: {vuln.reference or "无"}
                    **修复建议**: {vuln.remediation or "无"}
                    """
                    
                    vuln_subsection = ReportSection(
                        title=vuln.name,
                        content=vuln_content
                    )
                    severity_section.subsections.append(vuln_subsection)
                
                detailed_vuln_section.subsections.append(severity_section)
        
        sections.append(detailed_vuln_section)
        
        # 5. 测试执行详情
        execution_section = ReportSection(
            title="5. 测试执行详情",
            content=""
        )
        
        # 从报告数据中提取执行详情
        if "execution_details" in report_data:
            for stage_name, stage_data in report_data["execution_details"].items():
                stage_content = f"""
                **状态**: {stage_data.get('status', '未知')}
                **开始时间**: {stage_data.get('start_time', '未知')}
                **结束时间**: {stage_data.get('end_time', '未知')}
                **执行时间**: {stage_data.get('execution_time', 0.0):.2f} 秒
                """
                
                if "tool_results" in stage_data:
                    stage_content += "\n**工具执行结果**:\n"
                    for tool_name, tool_result in stage_data["tool_results"].items():
                        stage_content += f"- {tool_name}: {'成功' if tool_result.get('success', False) else '失败'}\n"
                
                stage_subsection = ReportSection(
                    title=stage_name,
                    content=stage_content
                )
                execution_section.subsections.append(stage_subsection)
        
        sections.append(execution_section)
        
        # 6. 安全建议
        recommendations = [
            "及时更新系统和应用程序到最新版本",
            "实施网络访问控制，限制不必要的端口和服务",
            "使用强密码策略，并定期更换密码",
            "实施多因素认证",
            "定期进行安全扫描和渗透测试",
            "建立安全事件响应机制",
            "对员工进行安全意识培训"
        ]
        
        recommendations_content = "\n".join([f"- {rec}" for rec in recommendations])
        
        recommendations_section = ReportSection(
            title="6. 安全建议",
            content=recommendations_content
        )
        sections.append(recommendations_section)
        
        return sections
    
    def _generate_html_report(self, report: SecurityReport) -> str:
        """生成HTML格式报告"""
        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{report.title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1, h2, h3, h4 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .vulnerability {{ margin: 20px 0; padding: 15px; border-left: 4px solid #e74c3c; }}
                .critical {{ border-left-color: #e74c3c; }}
                .high {{ border-left-color: #f39c12; }}
                .medium {{ border-left-color: #f1c40f; }}
                .low {{ border-left-color: #2ecc71; }}
                .info {{ border-left-color: #3498db; }}
                .summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; }}
            </style>
        </head>
        <body>
            <h1>{report.title}</h1>
            <div class="summary">
                <h2>执行摘要</h2>
                <p>{report.summary}</p>
            </div>
        """
        
        # 添加报告内容
        for section in report.sections:
            html += f"<h2>{section.title}</h2>"
            html += f"<p>{section.content}</p>"
            
            for subsection in section.subsections:
                html += f"<h3>{subsection.title}</h3>"
                html += f"<p>{subsection.content}</p>"
                
                for subsubsection in subsection.subsections:
                    html += f"<h4>{subsubsection.title}</h4>"
                    html += f"<div class='vulnerability {subsubsection.content.lower().split('严重程度: ')[1].split('\n')[0].lower()}'>"
                    html += f"<p>{subsubsection.content}</p>"
                    html += "</div>"
        
        # 添加页脚
        html += f"""
            <div class="footer">
                <p>报告生成时间: {report.scan_date}</p>
                <p>报告生成工具: {report.scanner} {report.version}</p>
                <p>报告ID: {report.report_id}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_json_report(self, report: SecurityReport) -> str:
        """生成JSON格式报告"""
        report_data = {
            "report_id": report.report_id,
            "title": report.title,
            "target": report.target,
            "scan_date": report.scan_date,
            "scanner": report.scanner,
            "version": report.version,
            "summary": report.summary,
            "status": report.status,
            "execution_time": report.execution_time,
            "vulnerabilities": [],
            "sections": [],
            "metadata": report.metadata
        }
        
        # 添加漏洞信息
        for vuln in report.vulnerabilities:
            report_data["vulnerabilities"].append({
                "id": vuln.id,
                "name": vuln.name,
                "description": vuln.description,
                "severity": vuln.severity.value,
                "cvss_score": vuln.cvss_score,
                "cve": vuln.cve,
                "reference": vuln.reference,
                "remediation": vuln.remediation,
                "tool": vuln.tool
            })
        
        # 添加报告章节
        def add_section(section):
            section_data = {
                "title": section.title,
                "content": section.content,
                "subsections": []
            }
            
            for subsection in section.subsections:
                section_data["subsections"].append(add_section(subsection))
            
            return section_data
        
        for section in report.sections:
            report_data["sections"].append(add_section(section))
        
        return json.dumps(report_data, ensure_ascii=False, indent=2)
    
    def _generate_markdown_report(self, report: SecurityReport) -> str:
        """生成Markdown格式报告"""
        markdown = f"""
# {report.title}

## 执行摘要
{report.summary}

## 测试信息
- 测试目标: {report.target}
- 扫描时间: {report.scan_date}
- 扫描工具: {report.scanner} {report.version}
- 执行时间: {report.execution_time:.2f} 秒
- 测试状态: {report.status}
- 报告ID: {report.report_id}

"""
        
        # 添加报告内容
        for section in report.sections:
            if section.title.startswith("1."):
                continue  # 跳过执行摘要，已在上面添加
            
            markdown += f"\n## {section.title}\n"
            markdown += f"{section.content}\n"
            
            for subsection in section.subsections:
                markdown += f"\n### {subsection.title}\n"
                markdown += f"{subsection.content}\n"
                
                for subsubsection in subsection.subsections:
                    markdown += f"\n#### {subsubsection.title}\n"
                    markdown += f"{subsubsection.content}\n"
        
        return markdown
    
    def _generate_pdf_report(self, report: SecurityReport) -> str:
        """生成PDF格式报告"""
        # 这里只是返回Markdown格式，实际项目中可以使用PDF库生成真正的PDF
        return self._generate_markdown_report(report)
    
    def save_report(self, report_content: str, format: ReportFormat, output_path: str):
        """保存报告到文件"""
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 保存报告
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return output_path


# 测试代码
if __name__ == "__main__":
    # 初始化报告生成器
    generator = ReportGenerator()
    
    print("=" * 80)
    print("报告生成模块测试")
    print("=" * 80)
    
    # 测试数据
    test_data = {
        "target": "example.com",
        "scanner": "ClawAI",
        "version": "2.0.0",
        "status": "completed",
        "execution_time": 123.45,
        "vulnerabilities": [
            {
                "id": "VULN-001",
                "name": "SQL注入漏洞",
                "description": "目标网站存在SQL注入漏洞，攻击者可以通过注入恶意SQL语句获取数据库信息",
                "severity": "high",
                "cvss_score": 8.5,
                "cve": "CVE-2023-1234",
                "reference": "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-1234",
                "remediation": "使用参数化查询，避免直接拼接SQL语句",
                "tool": "sqlmap"
            },
            {
                "id": "VULN-002",
                "name": "跨站脚本漏洞",
                "description": "目标网站存在XSS漏洞，攻击者可以注入恶意脚本",
                "severity": "medium",
                "cvss_score": 6.1,
                "cve": "CVE-2023-5678",
                "reference": "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-5678",
                "remediation": "对用户输入进行适当的转义和过滤",
                "tool": "nuclei"
            },
            {
                "id": "VULN-003",
                "name": "弱密码策略",
                "description": "目标系统使用弱密码策略，容易被暴力破解",
                "severity": "low",
                "cvss_score": 3.1,
                "remediation": "实施强密码策略，包括长度要求和复杂度要求",
                "tool": "hydra"
            }
        ],
        "execution_details": {
            "信息收集": {
                "status": "success",
                "start_time": "2024-01-01 10:00:00",
                "end_time": "2024-01-01 10:05:00",
                "execution_time": 300.0,
                "tool_results": {
                    "nmap": {"success": True},
                    "subfinder": {"success": True}
                }
            },
            "漏洞扫描": {
                "status": "success",
                "start_time": "2024-01-01 10:05:00",
                "end_time": "2024-01-01 10:15:00",
                "execution_time": 600.0,
                "tool_results": {
                    "nuclei": {"success": True},
                    "nikto": {"success": True}
                }
            },
            "漏洞利用": {
                "status": "partial_success",
                "start_time": "2024-01-01 10:15:00",
                "end_time": "2024-01-01 10:20:00",
                "execution_time": 300.0,
                "tool_results": {
                    "sqlmap": {"success": True},
                    "exploitdb": {"success": False}
                }
            }
        }
    }
    
    # 测试1: 生成HTML报告
    print("\n测试1: 生成HTML报告")
    html_report = generator.generate_report(test_data, ReportFormat.HTML)
    print(f"HTML报告长度: {len(html_report)} 字符")
    print("HTML报告预览:")
    print(html_report[:500] + "...")
    
    # 测试2: 生成JSON报告
    print("\n测试2: 生成JSON报告")
    json_report = generator.generate_report(test_data, ReportFormat.JSON)
    print(f"JSON报告长度: {len(json_report)} 字符")
    print("JSON报告预览:")
    print(json_report[:500] + "...")
    
    # 测试3: 生成Markdown报告
    print("\n测试3: 生成Markdown报告")
    markdown_report = generator.generate_report(test_data, ReportFormat.MARKDOWN)
    print(f"Markdown报告长度: {len(markdown_report)} 字符")
    print("Markdown报告预览:")
    print(markdown_report[:500] + "...")
    
    # 测试4: 保存报告
    print("\n测试4: 保存报告")
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    html_path = os.path.join(output_dir, "test_report.html")
    json_path = os.path.join(output_dir, "test_report.json")
    markdown_path = os.path.join(output_dir, "test_report.md")
    
    generator.save_report(html_report, ReportFormat.HTML, html_path)
    generator.save_report(json_report, ReportFormat.JSON, json_path)
    generator.save_report(markdown_report, ReportFormat.MARKDOWN, markdown_path)
    
    print(f"HTML报告保存到: {html_path}")
    print(f"JSON报告保存到: {json_path}")
    print(f"Markdown报告保存到: {markdown_path}")
    
    print("\n" + "=" * 80)
    print("测试完成")
