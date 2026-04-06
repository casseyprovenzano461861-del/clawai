# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
系统调度模块
负责协调调用各种安全扫描工具
"""

import sys
import os
from typing import Dict, Any

# 添加工具模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.nmap import NmapTool
from tools.nuclei import NucleiTool


class Orchestrator:
    """系统调度器类"""
    
    def __init__(self):
        """初始化调度器"""
        self.nmap_tool = NmapTool()
        self.nuclei_tool = NucleiTool()
    
    def run(self, target: str) -> Dict[str, Any]:
        """
        执行完整的扫描流程
        
        Args:
            target: 扫描目标
            
        Returns:
            整合后的扫描结果
            
        Example:
            {
                "target": "example.com",
                "recon": {...nmap结果...},
                "scan": {...nuclei结果...}
            }
        """
        # 验证目标
        if not target or not isinstance(target, str):
            raise ValueError("目标必须是有效的字符串")
        
        target = target.strip()
        if not target:
            raise ValueError("目标不能为空")
        
        # 准备结果容器
        result = {
            "target": target,
            "recon": None,
            "scan": None
        }
        
        try:
            # 第一步：执行nmap端口扫描
            print(f"开始nmap扫描: {target}")
            nmap_result = self.nmap_tool.run(target)
            result["recon"] = nmap_result
            print(f"nmap扫描完成，发现 {len(nmap_result.get('ports', []))} 个开放端口")
            
            # 第二步：执行nuclei漏洞扫描
            # 如果nmap发现开放端口，使用目标进行漏洞扫描
            # 注意：nuclei需要URL格式，这里简单处理
            if target.startswith('http://') or target.startswith('https://'):
                nuclei_target = target
            else:
                # 如果不是URL格式，假设为HTTP服务
                nuclei_target = f"http://{target}"
                
            print(f"开始nuclei扫描: {nuclei_target}")
            nuclei_result = self.nuclei_tool.run(nuclei_target)
            result["scan"] = nuclei_result
            print(f"nuclei扫描完成，发现 {len(nuclei_result.get('vulnerabilities', []))} 个漏洞")
            
        except Exception as e:
            # 记录错误但不中断整个流程
            result["error"] = str(e)
            print(f"扫描过程中发生错误: {str(e)}")
        
        return result


def main():
    """命令行入口点"""
    if len(sys.argv) != 2:
        print("用法: python orchestrator.py <target>")
        print("示例: python orchestrator.py example.com")
        print("示例: python orchestrator.py http://example.com")
        sys.exit(1)
    
    target = sys.argv[1]
    orchestrator = Orchestrator()
    
    try:
        result = orchestrator.run(target)
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"调度执行失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()