# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
WPScan WordPress安全扫描工具（基于BaseTool的新版本）
封装wpscan WordPress安全扫描功能，支持真实/模拟执行自动切换
"""

import subprocess
import json
import re
import sys
import os
import tempfile
from typing import Dict, List, Any, Optional

# 导入工具基类
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.tools.base_tool import (
    BaseTool, ToolExecutionMode, ToolCategory, 
    ToolPriority, ToolExecutionResult, register_tool
)


@register_tool
class WPScanTool(BaseTool):
    """WPScan WordPress安全扫描工具类（新版本）"""
    
    def __init__(self):
        super().__init__(
            tool_name="wpscan",
            command="wpscan",
            description="WordPress安全扫描器",
            category=ToolCategory.WEB_VULN,
            priority=ToolPriority.HIGH,
            requires_installation=True,
            fallback_to_simulated=True
        )
        
        # API密钥（可以在配置中设置）
        self.api_token = os.environ.get("WPSCAN_API_TOKEN", "")
        
        # 常见插件列表
        self.common_plugins = [
            {"name": "akismet", "version": "5.3", "description": "反垃圾邮件插件"},
            {"name": "yoast-seo", "version": "21.7", "description": "SEO优化插件"},
            {"name": "contact-form-7", "version": "5.8.6", "description": "联系表单插件"},
            {"name": "elementor", "version": "3.18.3", "description": "页面构建器"},
            {"name": "woocommerce", "version": "8.5.1", "description": "电子商务插件"}
        ]
        
        # 常见主题列表
        self.common_themes = [
            {"name": "twentytwentyfour", "version": "1.0", "description": "默认WordPress主题"},
            {"name": "astra", "version": "4.5.1", "description": "流行多功能主题"},
            {"name": "generatepress", "version": "3.3.1", "description": "轻量级主题"}
        ]
    
    def _parse_wpscan_json(self, json_output: str) -> Dict[str, Any]:
        """解析wpscan JSON输出"""
        try:
            data = json.loads(json_output)
            results = {
                "target": data.get("target_url", ""),
                "wordpress_version": None,
                "plugins": [],
                "themes": [],
                "users": [],
                "vulnerabilities": [],
                "configurations": {},
                "statistics": {}
            }
            
            # 提取版本信息
            if "version" in data and "number" in data["version"]:
                results["wordpress_version"] = data["version"]["number"]
            
            # 提取插件
            if "plugins" in data:
                for plugin in data["plugins"]:
                    plugin_info = {
                        "name": plugin.get("name", ""),
                        "version": plugin.get("version", ""),
                        "vulnerable": plugin.get("vulnerable", False),
                        "description": plugin.get("description", "")
                    }
                    results["plugins"].append(plugin_info)
            
            # 提取主题
            if "themes" in data:
                for theme in data["themes"]:
                    theme_info = {
                        "name": theme.get("name", ""),
                        "version": theme.get("version", ""),
                        "vulnerable": theme.get("vulnerable", False),
                        "description": theme.get("description", "")
                    }
                    results["themes"].append(theme_info)
            
            # 提取用户
            if "users" in data:
                for user in data["users"]:
                    user_info = {
                        "id": user.get("id", ""),
                        "username": user.get("username", ""),
                        "name": user.get("name", "")
                    }
                    results["users"].append(user_info)
            
            # 提取漏洞
            if "vulnerabilities" in data:
                for vuln in data["vulnerabilities"]:
                    vuln_info = {
                        "title": vuln.get("title", ""),
                        "description": vuln.get("description", ""),
                        "severity": vuln.get("severity", "info"),
                        "type": vuln.get("type", "unknown")
                    }
                    results["vulnerabilities"].append(vuln_info)
            
            # 提取统计信息
            if "statistics" in data:
                results["statistics"] = data["statistics"]
            else:
                results["statistics"] = {
                    "total_plugins": len(results["plugins"]),
                    "total_themes": len(results["themes"]),
                    "total_users": len(results["users"]),
                    "total_vulnerabilities": len(results["vulnerabilities"]),
                    "critical_vulnerabilities": len([v for v in results["vulnerabilities"] if v.get("severity") == "warning"])
                }
            
            return results
            
        except json.JSONDecodeError as e:
            self.logger.error(f"解析wpscan JSON输出失败: {e}")
            return {}
    
    def _execute_real(self, target: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """真实执行wpscan扫描"""
        if options is None:
            options = {}
        
        # 清理目标URL
        clean_target = target
        if not (target.startswith("http://") or target.startswith("https://")):
            clean_target = f"http://{target}"
        
        # 提取选项参数
        enumerate_plugins = options.get("enumerate_plugins", True)
        enumerate_themes = options.get("enumerate_themes", True)
        enumerate_users = options.get("enumerate_users", True)
        timeout = options.get("timeout", 600)  # 10分钟超时
        
        try:
            # 构建wpscan命令
            cmd = [
                self.command,
                '--url', clean_target,
                '--no-update',  # 不更新数据库
                '--format', 'json',
                '--disable-tls-checks',
                '--max-scan-duration', '00:10:00'  # 最大扫描时间10分钟
            ]
            
            # 添加API令牌（如果可用）
            if self.api_token:
                cmd.extend(['--api-token', self.api_token])
            
            # 添加枚举选项
            if enumerate_plugins:
                cmd.append('--enumerate')
                cmd.append('vp')  # 枚举易受攻击的插件
            if enumerate_themes:
                cmd.append('--enumerate')
                cmd.append('vt')  # 枚举易受攻击的主题
            if enumerate_users:
                cmd.append('--enumerate')
                cmd.append('u')   # 枚举用户
            
            self.logger.info(f"执行wpscan命令: {' '.join(cmd[:5])}...")  # 避免暴露完整命令
            
            # 执行命令
            result = self._run_command(cmd, timeout=timeout)
            
            # 解析结果
            if result.returncode == 0:
                results = self._parse_wpscan_json(result.stdout)
            else:
                # 如果wpscan返回非零错误码，但仍有输出，尝试解析
                if result.stdout:
                    try:
                        results = self._parse_wpscan_json(result.stdout)
                    except json.JSONDecodeError:
                        results = {
                            "target": clean_target,
                            "error": f"wpscan命令失败，返回码: {result.returncode}",
                            "stderr": result.stderr[:500]
                        }
                else:
                    results = {
                        "target": clean_target,
                        "error": f"wpscan命令失败，返回码: {result.returncode}",
                        "stderr": result.stderr[:500]
                    }
            
            return {
                "target": target,
                "clean_target": clean_target,
                "scan_results": results,
                "raw_output": result.stdout[:2000],
                "execution_mode": "real",
                "command_short": f"wpscan --url {clean_target} --format json",
                "return_code": result.returncode
            }
            
        except Exception as e:
            error_msg = f"wpscan执行错误: {str(e)}"
            if isinstance(e, subprocess.TimeoutExpired):
                error_msg = "wpscan扫描超时"
            elif isinstance(e, FileNotFoundError):
                error_msg = "未找到wpscan可执行文件"
            
            return {
                "target": target,
                "clean_target": clean_target,
                "scan_results": {"error": error_msg},
                "execution_mode": "real",
                "raw_output": error_msg
            }
    
    def _simulate_execution(self, target: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """模拟wpscan执行（当工具不可用时）"""
        import random
        import datetime
        
        # 清理目标URL
        clean_target = target
        if not (target.startswith("http://") or target.startswith("https://")):
            clean_target = f"http://{target}"
        
        # 模拟WordPress版本
        wordpress_versions = ["6.4.2", "6.3.1", "6.2.2", "5.9.5", "5.8.4"]
        wp_version = random.choice(wordpress_versions)
        
        # 模拟插件（随机选择3-5个）
        selected_plugins = random.sample(
            self.common_plugins, 
            random.randint(3, min(5, len(self.common_plugins)))
        )
        
        # 模拟主题（随机选择1-3个）
        selected_themes = random.sample(
            self.common_themes,
            random.randint(1, min(3, len(self.common_themes)))
        )
        
        # 模拟用户
        users = [
            {"id": "1", "username": "admin", "name": "Administrator"},
            {"id": "2", "username": "editor", "name": "Editor"}
        ]
        
        # 模拟漏洞（30%概率有漏洞）
        vulnerabilities = []
        if random.random() > 0.7:  # 30%概率发现漏洞
            common_vulns = [
                ("Outdated WordPress Version", f"WordPress {wp_version} is outdated, update to latest version", "warning", "version"),
                ("XML-RPC Enabled", "XML-RPC is enabled which can be abused for DDoS attacks", "warning", "configuration"),
                ("Directory Listing Enabled", "Directory listing is enabled on /wp-content/uploads/", "info", "configuration"),
                ("User Enumeration Possible", "User IDs can be enumerated via ?author= parameter", "info", "enumeration")
            ]
            
            vuln_count = random.randint(1, 3)
            selected_vulns = random.sample(common_vulns, vuln_count)
            
            for title, description, severity, vuln_type in selected_vulns:
                vulnerabilities.append({
                    "title": title,
                    "description": description,
                    "severity": severity,
                    "type": vuln_type
                })
        
        # 创建模拟结果
        simulated_data = {
            "target": clean_target,
            "wordpress_version": wp_version,
            "plugins": selected_plugins,
            "themes": selected_themes,
            "users": users,
            "vulnerabilities": vulnerabilities,
            "configurations": {
                "xmlrpc_enabled": random.choice([True, False]),
                "directory_listing": random.choice([True, False]),
                "debug_mode": random.choice([True, False])
            },
            "statistics": {
                "total_plugins": len(selected_plugins),
                "total_themes": len(selected_themes),
                "total_users": len(users),
                "total_vulnerabilities": len(vulnerabilities),
                "critical_vulnerabilities": len([v for v in vulnerabilities if v.get("severity") == "warning"])
            },
            "scan_timestamp": datetime.datetime.now().isoformat()
        }
        
        # 生成模拟的JSON输出（模仿wpscan格式）
        wpscan_format = {
            "target_url": clean_target,
            "version": {
                "number": wp_version,
                "release_date": "2023-12-01",
                "status": "outdated" if random.random() > 0.5 else "latest"
            },
            "plugins": selected_plugins,
            "themes": selected_themes,
            "users": users,
            "vulnerabilities": vulnerabilities,
            "statistics": simulated_data["statistics"]
        }
        
        simulated_json = json.dumps(wpscan_format, indent=2)
        
        return {
            "target": target,
            "clean_target": clean_target,
            "scan_results": simulated_data,
            "raw_output": simulated_json,
            "execution_mode": "simulated",
            "simulated": True,
            "note": "这是模拟数据，实际环境中请安装wpscan进行真实扫描",
            "installation_guide": """
wpscan安装指南:

  Docker方式（推荐）:
    docker pull wpscanteam/wpscan
    docker run -it --rm wpscanteam/wpscan --url https://example.com

  Ruby方式:
    gem install wpscan
  
  Linux (Kali/Ubuntu):
    sudo apt-get update
    sudo apt-get install wpscan
  
  Windows:
    1. 安装Ruby: https://rubyinstaller.org/
    2. 安装DevKit
    3. gem install wpscan

  API令牌（可选）:
    注册: https://wpscan.com/register
    设置环境变量: export WPSCAN_API_TOKEN=your_token_here
"""
        }
    
    def run(self, target: str) -> Dict[str, Any]:
        """执行wpscan扫描（兼容旧接口）"""
        result = self.execute(target)
        return result.output


def main():
    """命令行入口点"""
    if len(sys.argv) < 2:
        print("用法: python new_wpscan.py <target_url>")
        print("示例: python new_wpscan.py http://example.com")
        print("示例: python new_wpscan.py https://wordpress-site.com")
        print("选项:")
        print("  --no-plugins   不枚举插件")
        print("  --no-themes    不枚举主题")
        print("  --no-users     不枚举用户")
        print("  --api-token <token>  设置wpscan API令牌")
        sys.exit(1)
    
    target = sys.argv[1]
    
    # 解析选项
    options = {}
    options["enumerate_plugins"] = "--no-plugins" not in sys.argv
    options["enumerate_themes"] = "--no-themes" not in sys.argv
    options["enumerate_users"] = "--no-users" not in sys.argv
    
    # 解析API令牌
    api_token = None
    if "--api-token" in sys.argv:
        try:
            token_index = sys.argv.index("--api-token") + 1
            if token_index < len(sys.argv):
                api_token = sys.argv[token_index]
                os.environ["WPSCAN_API_TOKEN"] = api_token
        except (ValueError, IndexError):
            pass
    
    tool = WPScanTool()
    
    try:
        # 显示工具状态
        status = tool.get_status()
        print(f"工具状态: {'✅ 可用' if status['available'] else '❌ 不可用'}")
        if status['version']:
            print(f"版本信息: {status['version']}")
        
        if not status['available']:
            print("\n⚠️  工具不可用，将使用模拟模式")
            print("如需真实扫描，请安装wpscan")
        
        # 执行扫描
        result = tool.execute(target, options)
        
        # 输出结果摘要
        print(f"\n扫描目标: {result.output['target']}")
        print(f"执行模式: {result.output['execution_mode']}")
        
        if result.output.get('simulated'):
            print("⚠️  注意: 这是模拟数据")
        
        scan_results = result.output.get('scan_results', {})
        
        # 显示WordPress版本
        if scan_results.get('wordpress_version'):
            print(f"WordPress版本: {scan_results['wordpress_version']}")
        
        # 显示插件统计
        stats = scan_results.get('statistics', {})
        if stats:
            print(f"\n扫描统计:")
            print(f"  插件数量: {stats.get('total_plugins', 0)}")
            print(f"  主题数量: {stats.get('total_themes', 0)}")
            print(f"  用户数量: {stats.get('total_users', 0)}")
            print(f"  漏洞数量: {stats.get('total_vulnerabilities', 0)}")
            print(f"  严重漏洞: {stats.get('critical_vulnerabilities', 0)}")
        
        # 显示发现的漏洞
        vulnerabilities = scan_results.get('vulnerabilities', [])
        if vulnerabilities:
            print(f"\n发现的漏洞:")
            for i, vuln in enumerate(vulnerabilities[:5], 1):  # 只显示前5个
                severity = vuln.get('severity', 'info')
                severity_icon = "⚠️" if severity == "warning" else "ℹ️"
                print(f"  {severity_icon} {i}. {vuln.get('title', '未知漏洞')}")
                if vuln.get('description'):
                    print(f"     描述: {vuln['description'][:80]}...")
        
        # 显示安装指南（如果使用模拟模式）
        if result.output.get('simulated') and result.output.get('installation_guide'):
            print(f"\n安装指南: 请查看工具的installation_guide字段")
        
        # 可选的JSON输出
        if '--json' in sys.argv:
            print("\n完整JSON输出:")
            print(json.dumps(result.output, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"扫描失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()