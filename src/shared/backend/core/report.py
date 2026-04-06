# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
报告生成模块
用于生成完整的渗透测试报告
"""

import json
import sys
from datetime import datetime


class ReportGenerator:
    """报告生成器类"""
    
    def generate(self, scan_data):
        """
        生成渗透测试报告
        
        Args:
            scan_data: 扫描数据，包含target、recon、scan、analysis
            
        Returns:
            完整的渗透测试报告字符串
        """
        # 提取数据
        target = scan_data.get('target', '未知目标')
        recon = scan_data.get('recon', {})
        scan = scan_data.get('scan', {})
        analysis = scan_data.get('analysis', {})
        
        # 获取详细信息
        ports = recon.get('ports', [])
        vulnerabilities = scan.get('vulnerabilities', [])
        summary = analysis.get('summary', '')
        risk_level = analysis.get('risk_level', 'unknown')
        advice = analysis.get('advice', '')
        
        # 生成报告标题
        report = "=" * 60 + "\n"
        report += "渗透测试报告\n"
        report += "=" * 60 + "\n\n"
        
        # 报告基本信息
        report += "一、报告基本信息\n"
        report += "-" * 40 + "\n"
        report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"目标地址: {target}\n"
        report += f"报告编号: PT-{datetime.now().strftime('%Y%m%d%H%M')}\n\n"
        
        # 执行摘要
        report += "二、执行摘要\n"
        report += "-" * 40 + "\n"
        report += f"{summary}\n\n"
        
        # 端口扫描结果
        report += "三、端口扫描结果\n"
        report += "-" * 40 + "\n"
        if ports:
            report += f"发现 {len(ports)} 个开放端口:\n"
            for port in ports:
                port_num = port.get('port', '未知')
                service = port.get('service', '未知')
                report += f"  - 端口 {port_num}: {service}\n"
        else:
            report += "未发现开放端口\n"
        report += "\n"
        
        # 漏洞扫描结果
        report += "四、漏洞扫描结果\n"
        report += "-" * 40 + "\n"
        if vulnerabilities:
            report += f"发现 {len(vulnerabilities)} 个漏洞:\n"
            
            # 按严重程度分组
            vuln_by_severity = {}
            for vuln in vulnerabilities:
                severity = vuln.get('severity', 'unknown').upper()
                name = vuln.get('name', '未知漏洞')
                if severity not in vuln_by_severity:
                    vuln_by_severity[severity] = []
                vuln_by_severity[severity].append(name)
            
            # 按严重程度从高到低输出
            severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']
            for severity in severity_order:
                if severity in vuln_by_severity:
                    report += f"\n{severity} 级别漏洞 ({len(vuln_by_severity[severity])}个):\n"
                    for name in vuln_by_severity[severity]:
                        report += f"  - {name}\n"
        else:
            report += "未发现已知漏洞\n"
        report += "\n"
        
        # 风险评估
        report += "五、风险评估\n"
        report += "-" * 40 + "\n"
        risk_text = {
            'high': '高风险',
            'medium': '中风险', 
            'low': '低风险',
            'unknown': '未知风险'
        }
        report += f"风险等级: {risk_text.get(risk_level, '未知风险')}\n\n"
        
        # 修复建议
        report += "六、修复建议\n"
        report += "-" * 40 + "\n"
        report += f"{advice}\n\n"
        
        # 报告结尾
        report += "七、免责声明\n"
        report += "-" * 40 + "\n"
        report += "本报告仅用于安全测试目的，所有测试均在授权范围内进行。\n"
        report += "报告内容仅供参考，建议由专业安全团队进行验证和修复。\n\n"
        
        report += "=" * 60 + "\n"
        report += "报告结束\n"
        report += "=" * 60 + "\n"
        
        return report


def main():
    """命令行入口点"""
    if len(sys.argv) != 2:
        print("用法: python  <scan_data_json> - report.py:126")
        print("示例: python  '{\"target\":\"example.com\",\"recon\":{\"ports\":[]},\"scan\":{\"vulnerabilities\":[]},\"analysis\":{\"summary\":\"测试\",\"risk_level\":\"low\",\"advice\":\"建议\"}}' - report.py:127")
        sys.exit(1)
    
    try:
        # 解析输入JSON
        scan_data = json.loads(sys.argv[1])
        
        # 生成报告
        generator = ReportGenerator()
        report = generator.generate(scan_data)
        
        # 输出报告
        print(report)
        
    except json.JSONDecodeError:
        print("错误: 输入不是有效的JSON格式 - report.py:142")
        sys.exit(1)
    except Exception as e:
        print(f"报告生成失败: {str(e)} - report.py:145")
        sys.exit(1)


if __name__ == "__main__":
    main()