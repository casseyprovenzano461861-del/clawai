# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
CVE专项检测模块
针对比赛要求的特定CVE漏洞进行检测
"""

import subprocess
import json
import re
import requests
from typing import Dict, List, Any, Optional
from .security.sanitize import safe_execute, SecurityError

class CVEDetector:
    """CVE专项检测器"""
    
    # 比赛要求的CVE漏洞列表
    TARGET_CVES = {
        # Struts2 漏洞
        "S2-045": {
            "name": "Apache Struts2 S2-045 (CVE-2017-5638)",
            "type": "rce",
            "platform": "web",
            "detection_methods": ["nuclei", "custom"],
            "nuclei_template": "cves/2017/CVE-2017-5638.yaml",
            "description": "Struts2 Jakarta Multipart Parser RCE"
        },
        "S2-057": {
            "name": "Apache Struts2 S2-057 (CVE-2018-11776)",
            "type": "rce",
            "platform": "web",
            "detection_methods": ["nuclei", "custom"],
            "nuclei_template": "cves/2018/CVE-2018-11776.yaml",
            "description": "Struts2 Namespace RCE"
        },
        
        # ThinkPHP 漏洞
        "ThinkPHP-5.0.23-rce": {
            "name": "ThinkPHP 5.0.23 RCE",
            "type": "rce",
            "platform": "web",
            "detection_methods": ["nuclei", "custom"],
            "nuclei_template": "technologies/thinkphp-rce.yaml",
            "description": "ThinkPHP 5.0.23 远程代码执行"
        },
        
        # WebLogic 漏洞
        "CVE-2023-21839": {
            "name": "Oracle WebLogic CVE-2023-21839",
            "type": "rce",
            "platform": "web",
            "detection_methods": ["nuclei", "custom"],
            "nuclei_template": "cves/2023/CVE-2023-21839.yaml",
            "description": "WebLogic T3/IIOP反序列化RCE"
        },
        
        # Tomcat 漏洞
        "CVE-2017-12615": {
            "name": "Apache Tomcat CVE-2017-12615",
            "type": "file_upload",
            "platform": "web",
            "detection_methods": ["nuclei", "custom"],
            "nuclei_template": "cves/2017/CVE-2017-12615.yaml",
            "description": "Tomcat PUT方法任意文件上传"
        },
        
        # PHP 漏洞
        "CVE-2019-11043": {
            "name": "PHP CVE-2019-11043",
            "type": "rce",
            "platform": "web",
            "detection_methods": ["nuclei", "custom"],
            "nuclei_template": "cves/2019/CVE-2019-11043.yaml",
            "description": "PHP-FPM远程代码执行"
        },
        
        # ActiveMQ 漏洞
        "CVE-2022-41678": {
            "name": "Apache ActiveMQ CVE-2022-41678",
            "type": "rce",
            "platform": "web",
            "detection_methods": ["nuclei", "custom"],
            "nuclei_template": "cves/2022/CVE-2022-41678.yaml",
            "description": "ActiveMQ远程代码执行"
        },
        
        # JBoss 漏洞
        "CVE-2017-7504": {
            "name": "JBoss CVE-2017-7504",
            "type": "rce",
            "platform": "web",
            "detection_methods": ["nuclei", "custom"],
            "nuclei_template": "cves/2017/CVE-2017-7504.yaml",
            "description": "JBoss JMXInvokerServlet反序列化"
        },
        
        # Shiro 漏洞
        "CVE-2016-4437": {
            "name": "Apache Shiro CVE-2016-4437",
            "type": "deserialization",
            "platform": "web",
            "detection_methods": ["nuclei", "custom"],
            "nuclei_template": "cves/2016/CVE-2016-4437.yaml",
            "description": "Shiro RememberMe反序列化"
        },
        
        # Fastjson 漏洞
        "fastjson-1.2.24-rce": {
            "name": "Fastjson 1.2.24 RCE",
            "type": "deserialization",
            "platform": "web",
            "detection_methods": ["nuclei", "custom"],
            "nuclei_template": "technologies/fastjson-rce.yaml",
            "description": "Fastjson反序列化RCE"
        },
        "fastjson-1.2.47-rce": {
            "name": "Fastjson 1.2.47 RCE",
            "type": "deserialization",
            "platform": "web",
            "detection_methods": ["nuclei", "custom"],
            "nuclei_template": "technologies/fastjson-rce.yaml",
            "description": "Fastjson反序列化RCE"
        },
        
        # Django 漏洞
        "CVE-2022-34265": {
            "name": "Django CVE-2022-34265",
            "type": "sql_injection",
            "platform": "web",
            "detection_methods": ["nuclei", "custom"],
            "nuclei_template": "cves/2022/CVE-2022-34265.yaml",
            "description": "Django Trunc函数SQL注入"
        },
        
        # Flask 漏洞
        "Flask-SSTI": {
            "name": "Flask SSTI",
            "type": "ssti",
            "platform": "web",
            "detection_methods": ["nuclei", "custom"],
            "nuclei_template": "technologies/flask-ssti.yaml",
            "description": "Flask模板注入"
        },
        
        # GeoServer 漏洞
        "CVE-2024-36401": {
            "name": "GeoServer CVE-2024-36401",
            "type": "rce",
            "platform": "web",
            "detection_methods": ["nuclei", "custom"],
            "nuclei_template": "cves/2024/CVE-2024-36401.yaml",
            "description": "GeoServer OGC Filter RCE"
        },
    }
    
    def __init__(self, nuclei_path: str = r"C:\Tools\nuclei\nuclei.exe"):
        self.nuclei_path = nuclei_path
    
    def detect_with_nuclei(self, target: str, cve_id: str) -> Dict:
        """使用nuclei检测特定CVE"""
        cve_info = self.TARGET_CVES.get(cve_id)
        if not cve_info:
            return {
                "cve": cve_id,
                "detected": False,
                "error": f"未知CVE: {cve_id}"
            }
        
        try:
            # 使用nuclei的特定模板检测
            cmd = [
                self.nuclei_path,
                '-u', target,
                '-t', cve_info["nuclei_template"],
                '-json',
                '-silent',
                '-timeout', '30'
            ]
            
            returncode, stdout, stderr = safe_execute(cmd, timeout=60)
            
            if returncode != 0 and returncode != 1:
                return {
                    "cve": cve_id,
                    "detected": False,
                    "error": f"nuclei执行失败: {returncode}"
                }
            
            # 解析输出
            vulnerabilities = []
            for line in stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    vulnerabilities.append({
                        "name": data.get('info', {}).get('name', 'Unknown'),
                        "severity": data.get('info', {}).get('severity', 'unknown'),
                        "matched": data.get('matched-at', '')
                    })
                except json.JSONDecodeError:
                    continue
            
            return {
                "cve": cve_id,
                "name": cve_info["name"],
                "detected": len(vulnerabilities) > 0,
                "vulnerabilities": vulnerabilities,
                "description": cve_info["description"]
            }
            
        except TimeoutError:
            return {
                "cve": cve_id,
                "detected": False,
                "error": "检测超时"
            }
        except SecurityError as e:
            return {
                "cve": cve_id,
                "detected": False,
                "error": f"安全违规: {str(e)}"
            }
        except Exception as e:
            return {
                "cve": cve_id,
                "detected": False,
                "error": str(e)
            }
    
    def detect_all_cves(self, target: str) -> Dict:
        """检测所有目标CVE"""
        results = {}
        detected_count = 0
        
        print(f"开始检测目标: {target}")
        print(f"需要检测的CVE数量: {len(self.TARGET_CVES)}")
        
        for cve_id, cve_info in self.TARGET_CVES.items():
            print(f"检测 {cve_id}: {cve_info['name']}...")
            
            result = self.detect_with_nuclei(target, cve_id)
            results[cve_id] = result
            
            if result.get("detected", False):
                detected_count += 1
                print(f"  ✅ 检测到漏洞")
            else:
                print(f"  ❌ 未检测到")
        
        # 计算检测率
        total_cves = len(self.TARGET_CVES)
        detection_rate = (detected_count / total_cves * 100) if total_cves > 0 else 0
        
        return {
            "target": target,
            "total_cves": total_cves,
            "detected_count": detected_count,
            "detection_rate": round(detection_rate, 2),
            "results": results,
            "summary": {
                "detection_rate_percent": detection_rate,
                "meets_requirement": detection_rate >= 1.0,  # 比赛要求 ≥1%
                "detected_cves": [cve_id for cve_id, result in results.items() if result.get("detected", False)]
            }
        }
    
    def generate_cve_report(self, detection_results: Dict) -> str:
        """生成CVE检测报告"""
        target = detection_results.get("target", "Unknown")
        total = detection_results.get("total_cves", 0)
        detected = detection_results.get("detected_count", 0)
        rate = detection_results.get("detection_rate", 0)
        
        report = f"""
{'='*80}
CVE专项检测报告
{'='*80}

目标: {target}
检测时间: {self._get_current_time()}

📊 检测统计:
  总CVE数量: {total} 个
  检测到漏洞: {detected} 个
  检测率: {rate}%
  满足比赛要求(≥1%): {'✅' if rate >= 1.0 else '❌'}

🔍 详细检测结果:
"""
        
        results = detection_results.get("results", {})
        for cve_id, result in results.items():
            detected = result.get("detected", False)
            name = result.get("name", "Unknown")
            
            if detected:
                report += f"\n✅ {cve_id}: {name}"
                vulns = result.get("vulnerabilities", [])
                for vuln in vulns:
                    report += f"\n    - {vuln.get('name')} ({vuln.get('severity')})"
            else:
                report += f"\n❌ {cve_id}: {name}"
                if result.get("error"):
                    report += f"\n    原因: {result.get('error')}"
        
        report += f"\n\n{'='*80}"
        report += f"\n检测完成"
        report += f"\n{'='*80}"
        
        return report
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def test_vulhub_targets(self):
        """测试Vulhub靶机"""
        vulhub_targets = {
            "Struts2 S2-045": "http://localhost:8080/struts2-showcase/",
            "Struts2 S2-057": "http://localhost:8080/struts2-showcase/",
            "ThinkPHP RCE": "http://localhost:8080/",
            "WebLogic CVE-2023-21839": "http://localhost:7001/",
            "Tomcat CVE-2017-12615": "http://localhost:8080/",
            "PHP CVE-2019-11043": "http://localhost:8080/",
            "ActiveMQ CVE-2022-41678": "http://localhost:8161/",
            "JBoss CVE-2017-7504": "http://localhost:8080/",
            "Shiro CVE-2016-4437": "http://localhost:8080/",
            "Fastjson 1.2.24": "http://localhost:8080/",
            "Fastjson 1.2.47": "http://localhost:8080/",
            "Django CVE-2022-34265": "http://localhost:8000/",
            "Flask SSTI": "http://localhost:8000/",
            "GeoServer CVE-2024-36401": "http://localhost:8080/",
        }
        
        print("Vulhub靶机测试配置:")
        for name, url in vulhub_targets.items():
            print(f"  {name}: {url}")


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) != 2:
        print("用法: python cve_detector.py <target_url>")
        print("示例: python cve_detector.py http://localhost:8080")
        print("示例: python cve_detector.py http://example.com")
        sys.exit(1)
    
    target = sys.argv[1]
    detector = CVEDetector()
    
    try:
        print(f"开始CVE专项检测...")
        results = detector.detect_all_cves(target)
        
        # 生成报告
        report = detector.generate_cve_report(results)
        print(report)
        
        # 保存结果
        with open("cve_detection_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n结果已保存到: cve_detection_results.json")
        
    except Exception as e:
        print(f"检测失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
