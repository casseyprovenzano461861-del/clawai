# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
离线AI模式 - 第1天任务：创建离线演示模式
返回预定义的响应，不调用API，确保演示稳定性
"""

import time
import json
from typing import Dict, List, Any, Optional


class OfflineAIMode:
    """离线AI模式，返回预定义的响应"""
    
    def __init__(self):
        self.response_cache = {}
        self._init_responses()
    
    def _init_responses(self):
        """初始化预定义响应"""
        # 基础响应模板
        self.responses = {
            "analyze_target": {
                "success": True,
                "analysis": {
                    "target": "demo-target.com",
                    "attack_surface": 8.5,
                    "vulnerabilities": 3,
                    "risk_level": "high",
                    "technologies": ["WordPress 5.8", "PHP 7.4", "Apache 2.4"],
                    "open_ports": [80, 443, 3306],
                    "recommendations": [
                        "优先利用RCE漏洞 (CVE-2023-1234)",
                        "SQL注入可作为备选方案",
                        "关注CMS插件漏洞"
                    ]
                },
                "model_used": "offline_mode",
                "response_time": 0.1
            },
            
            "plan_attack": {
                "success": True,
                "attack_plan": {
                    "selected_path_type": "rce_attack",
                    "selected_score": 8.5,
                    "confidence": 0.92,
                    "selection_reasons": [
                        "评分最高 (8.5分)",
                        "漏洞严重性: critical",
                        "攻击成功率: 85%",
                        "可直接获取系统控制权",
                        "攻击效果立竿见影"
                    ],
                    "alternative_paths": [
                        {"path_type": "sql_injection", "score": 7.2, "reason": "评分低1.3分"},
                        {"path_type": "cms_exploit", "score": 6.8, "reason": "评分低1.7分"}
                    ],
                    "decision_factors": {
                        "exploitability": 9.2,
                        "detection_risk": 2.1,
                        "success_rate": 0.85,
                        "time_efficiency": 7.8,
                        "resource_cost": 6.5
                    }
                },
                "model_used": "offline_mode",
                "response_time": 0.1
            },
            
            "compare_models": {
                "success": True,
                "model_comparison": {
                    "final_decision": "rce_attack",
                    "status": "consensus",
                    "confidence": 0.82,
                    "resolution_strategy": "consensus_voting",
                    "model_decisions": [
                        {
                            "model_name": "deepseek",
                            "decision": "rce_attack",
                            "confidence": 0.85,
                            "reasoning": "检测到严重RCE漏洞，攻击成功率高，目标系统存在未授权访问",
                            "confidence_level": "high"
                        },
                        {
                            "model_name": "openai",
                            "decision": "rce_attack",
                            "confidence": 0.78,
                            "reasoning": "存在远程代码执行漏洞，建议优先利用，系统补丁滞后",
                            "confidence_level": "medium"
                        },
                        {
                            "model_name": "claude",
                            "decision": "sql_injection",
                            "confidence": 0.65,
                            "reasoning": "SQL注入攻击更隐蔽，风险更低，适合长期潜伏",
                            "confidence_level": "low"
                        },
                        {
                            "model_name": "local",
                            "decision": "rce_attack",
                            "confidence": 0.55,
                            "reasoning": "RCE攻击虽然风险高，但成功率最可靠",
                            "confidence_level": "low"
                        }
                    ]
                },
                "model_used": "offline_mode",
                "response_time": 0.1
            },
            
            "explain_decision": {
                "success": True,
                "explanation": {
                    "explanation_type": "decision_reason",
                    "explanation_content": """决策分析报告:
1. 最终决策: rce_attack
2. 决策机制: consensus_voting
3. 模型投票: 3/4个模型支持此决策 (支持率: 75%)
4. 决策置信度: 82%
5. 主要支持理由:
   deepseek: 检测到严重RCE漏洞，攻击成功率高
   openai: 存在远程代码执行漏洞，建议优先利用
6. 风险评估: 高风险高回报攻击，存在一定被检测风险
7. 替代方案: SQL注入攻击更隐蔽，但见效慢
8. 推荐原因: 时间效率最高，可快速获取系统控制权""",
                    "confidence_score": 0.85
                },
                "model_used": "offline_mode",
                "response_time": 0.1
            },
            
            "generate_workflow": {
                "success": True,
                "workflow": {
                    "stages": [
                        {
                            "name": "侦察阶段",
                            "description": "信息收集和目标识别",
                            "duration": "2.3s",
                            "tools": ["nmap", "masscan"],
                            "ai_guidance": "AI建议: 使用nmap进行端口扫描，masscan进行快速端口发现"
                        },
                        {
                            "name": "扫描阶段",
                            "description": "端口扫描和服务识别",
                            "duration": "3.1s",
                            "tools": ["whatweb", "nuclei"],
                            "ai_guidance": "AI建议: 使用whatweb识别Web技术，nuclei扫描已知漏洞"
                        },
                        {
                            "name": "漏洞分析",
                            "description": "漏洞检测和风险评估",
                            "duration": "4.5s",
                            "tools": ["nuclei", "nikto"],
                            "ai_guidance": "AI评估: 发现2个高危漏洞，建议优先利用RCE漏洞"
                        },
                        {
                            "name": "漏洞利用",
                            "description": "攻击执行和权限获取",
                            "duration": "5.2s",
                            "tools": ["exploit", "msfconsole"],
                            "ai_guidance": "AI推荐: 优先利用最易攻击的漏洞，使用编码绕过WAF"
                        },
                        {
                            "name": "后渗透",
                            "description": "横向移动和数据收集",
                            "duration": "7.8s",
                            "tools": ["mimikatz", "powersploit"],
                            "ai_guidance": "AI策略: 保持隐蔽，使用低交互攻击，收集敏感信息"
                        },
                        {
                            "name": "报告生成",
                            "description": "结果汇总和修复建议",
                            "duration": "1.5s",
                            "tools": ["report_generator"],
                            "ai_guidance": "AI总结: 生成详细报告，包含修复建议和风险评分"
                        }
                    ],
                    "total_time": 24.4,
                    "success_rate": 100
                },
                "model_used": "offline_mode",
                "response_time": 0.1
            }
        }
    
    def get_response(self, prompt_type: str, **kwargs) -> Dict[str, Any]:
        """
        获取预定义的响应
        
        Args:
            prompt_type: 提示类型，支持：
                - "analyze_target": 目标分析
                - "plan_attack": 攻击规划
                - "compare_models": 模型对比
                - "explain_decision": 决策解释
                - "generate_workflow": 工作流生成
            **kwargs: 额外参数，用于定制响应
            
        Returns:
            预定义的响应数据
        """
        # 检查是否有对应的响应类型
        if prompt_type not in self.responses:
            return {
                "success": False,
                "error": f"不支持的操作类型: {prompt_type}",
                "available_types": list(self.responses.keys())
            }
        
        # 获取基础响应
        response = self.responses[prompt_type].copy()
        
        # 根据参数定制响应
        if prompt_type == "analyze_target" and "target" in kwargs:
            response["analysis"]["target"] = kwargs["target"]
        
        elif prompt_type == "plan_attack" and "target" in kwargs:
            response["attack_plan"]["target"] = kwargs["target"]
        
        elif prompt_type == "generate_workflow" and "target" in kwargs:
            for stage in response["workflow"]["stages"]:
                if "AI建议" in stage["ai_guidance"]:
                    stage["ai_guidance"] = stage["ai_guidance"].replace("目标", kwargs["target"])
        
        # 添加时间戳
        import datetime
        response["timestamp"] = datetime.datetime.now().isoformat()
        
        # 模拟处理时间
        time.sleep(0.05)  # 50ms延迟，模拟处理时间
        
        return response
    
    def analyze_target(self, target: str) -> Dict[str, Any]:
        """分析目标（离线模式）"""
        return self.get_response("analyze_target", target=target)
    
    def plan_attack(self, target: str) -> Dict[str, Any]:
        """规划攻击（离线模式）"""
        return self.get_response("plan_attack", target=target)
    
    def compare_models(self) -> Dict[str, Any]:
        """比较模型决策（离线模式）"""
        return self.get_response("compare_models")
    
    def explain_decision(self) -> Dict[str, Any]:
        """解释决策（离线模式）"""
        return self.get_response("explain_decision")
    
    def generate_workflow(self, target: str) -> Dict[str, Any]:
        """生成工作流（离线模式）"""
        return self.get_response("generate_workflow", target=target)
    
    def interactive_dialogue(self, question: str) -> Dict[str, Any]:
        """交互式对话（离线模式）"""
        # 预定义的问答对
        qa_pairs = {
            "渗透测试": "渗透测试是模拟黑客攻击的授权安全测试，分为侦察、扫描、漏洞利用、后渗透、报告5个阶段。",
            "OWASP Top 10": "OWASP Top 10是十大Web应用安全风险，包括注入攻击、身份验证失效、敏感数据泄露等。",
            "CVE漏洞": "CVE是公共漏洞和暴露的标识符，如CVE-2023-1234表示2023年发现的第1234个漏洞。",
            "SQL注入": "SQL注入是通过输入恶意SQL代码攻击数据库的技术，可通过参数化查询防御。",
            "XSS攻击": "跨站脚本攻击是通过注入恶意JavaScript代码攻击用户浏览器的技术。",
            "RCE漏洞": "远程代码执行漏洞允许攻击者在目标系统上执行任意代码，通常是最危险的漏洞类型。",
            "ClawAI": "ClawAI是基于AI的自动化渗透测试系统，集成了37个安全工具，支持AI驱动的攻击链生成。"
        }
        
        # 查找最相关的回答
        for keyword, answer in qa_pairs.items():
            if keyword.lower() in question.lower():
                return {
                    "success": True,
                    "question": question,
                    "answer": answer + " (离线模式)",
                    "model_used": "offline_mode",
                    "response_time": 0.05,
                    "timestamp": time.time()
                }
        
        # 默认回答
        return {
            "success": True,
            "question": question,
            "answer": "这是一个很好的问题！作为离线AI，我可以提供渗透测试相关的专业建议。请询问关于安全测试、漏洞利用或ClawAI系统的问题。(离线模式)",
            "model_used": "offline_mode",
            "response_time": 0.05,
            "timestamp": time.time()
        }


class DemoCache:
    """演示缓存系统，提升离线演示性能"""
    
    def __init__(self):
        self.cache = {}
    
    def get(self, key: str) -> Any:
        """获取缓存值"""
        return self.cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存值"""
        self.cache[key] = {
            'value': value,
            'expires': time.time() + ttl
        }
    
    def clear_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, data in self.cache.items():
            if data['expires'] < current_time:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]


def test_offline_mode():
    """测试离线模式"""
    print("=" * 60)
    print("离线AI模式测试")
    print("=" * 60)
    
    offline = OfflineAIMode()
    
    # 测试目标分析
    print("\n1. 测试目标分析:")
    result = offline.analyze_target("demo-target.com")
    print(f"目标: {result['analysis']['target']}")
    print(f"攻击面评分: {result['analysis']['attack_surface']}/10")
    print(f"漏洞数量: {result['analysis']['vulnerabilities']}")
    
    # 测试攻击规划
    print("\n2. 测试攻击规划:")
    result = offline.plan_attack("demo-target.com")
    print(f"最优攻击路径: {result['attack_plan']['selected_path_type']}")
    print(f"评分: {result['attack_plan']['selected_score']}/10")
    print(f"置信度: {result['attack_plan']['confidence']*100:.0f}%")
    
    # 测试模型对比
    print("\n3. 测试模型对比:")
    result = offline.compare_models()
    print(f"最终决策: {result['model_comparison']['final_decision']}")
    print(f"决策状态: {result['model_comparison']['status']}")
    print(f"综合置信度: {result['model_comparison']['confidence']*100:.0f}%")
    
    # 测试交互式对话
    print("\n4. 测试交互式对话:")
    result = offline.interactive_dialogue("什么是渗透测试？")
    print(f"问题: {result['question']}")
    print(f"回答: {result['answer'][:100]}...")
    
    print("\n" + "=" * 60)
    print("离线AI模式测试完成")
    return True


if __name__ == "__main__":
    success = test_offline_mode()
    if success:
        print("\n[SUCCESS] 离线AI模式测试通过!")
    else:
        print("\n[FAILED] 离线AI模式测试失败!")


<environment_details>
<｜DSML｜parameter name="task_progress" string="true">- [x] 检查现有演示材料
- [x] 修复演示脚本 (competition_demo.py)
- [ ] 创建演示PPT大纲 (ClawAI_Demo_Presentation.md)
- [ ] 创建视频脚本 (demo_video_script.md)
- [x] 准备3个预配置演示场景
- [x] 创建离线演示模式
- [x] 测试演示脚本
- [x] 创建演示数据目录和场景文件
- [ ] 验证离线模式