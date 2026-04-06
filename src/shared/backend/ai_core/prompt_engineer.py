# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
提示词工程模块
专门为网络安全渗透测试设计的高质量提示词模板
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class PromptTemplate:
    """提示词模板"""
    name: str
    system_prompt: str
    user_prompt_template: str
    temperature: float = 0.3
    max_tokens: int = 2000
    response_format: str = "json"  # json, text, code
    required_fields: List[str] = field(default_factory=list)
    
    def format(self, **kwargs) -> Dict[str, Any]:
        """格式化提示词模板"""
        # 检查必需字段
        for field_name in self.required_fields:
            if field_name not in kwargs:
                raise ValueError(f"缺少必需字段: {field_name}")
        
        user_prompt = self.user_prompt_template.format(**kwargs)
        
        return {
            "system_prompt": self.system_prompt,
            "user_prompt": user_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": self.response_format
        }


class PromptEngineer:
    """
    提示词工程师
    专门为网络安全渗透测试设计的高质量提示词
    """
    
    def __init__(self):
        self.templates = {}
        self._init_templates()
    
    def _init_templates(self):
        """初始化所有提示词模板"""
        
        # 目标分析模板
        self.templates["target_analysis"] = PromptTemplate(
            name="target_analysis",
            system_prompt="你是一个资深网络安全专家，擅长目标分析和风险评估。请提供专业、准确的分析结果。",
            user_prompt_template="""请分析以下目标扫描结果并给出专业评估：

目标: {target}
扫描时间: {scan_time}
扫描结果概览:
{scan_summary}

详细扫描结果:
{detailed_results}

请基于以下维度提供分析报告:
1. 攻击面评估 (Attack Surface Assessment)
   - 开放端口和服务分析
   - 技术栈指纹识别
   - 已知漏洞识别

2. 风险评估 (Risk Assessment)
   - 高危漏洞识别
   - 潜在攻击向量
   - 安全配置问题

3. 目标画像 (Target Profile)
   - 目标类型 (Web服务器/数据库/应用服务器等)
   - 安全成熟度评估
   - 防御措施检测

4. 攻击优先级建议 (Attack Priority Recommendation)
   - 高优先级攻击向量
   - 中优先级攻击向量
   - 低优先级攻击向量

请以JSON格式返回，包含以下字段:
- attack_surface_score (0-10分)
- risk_level (low, medium, high, critical)
- critical_vulnerabilities (列表)
- recommended_attack_vectors (列表)
- security_recommendations (列表)
""",
            temperature=0.2,
            response_format="json",
            required_fields=["target", "scan_time", "scan_summary", "detailed_results"]
        )
        
        # 攻击路径规划模板
        self.templates["attack_planning"] = PromptTemplate(
            name="attack_planning",
            system_prompt="你是一个资深渗透测试专家，擅长攻击路径规划和风险评估。请提供专业、可行的攻击计划。",
            user_prompt_template="""基于以下目标分析结果，规划最佳攻击路径:

目标分析摘要:
{target_analysis}

可用工具和资源:
{available_tools}

约束条件:
{constraints}

请规划最佳攻击路径，考虑以下因素:
1. 攻击成功率 (Success Probability)
2. 攻击影响 (Attack Impact)
3. 隐蔽性 (Stealth)
4. 时间效率 (Time Efficiency)
5. 资源消耗 (Resource Consumption)

请提供:
1. 最佳攻击路径 (Primary Attack Path)
2. 备选路径 (Alternative Paths, 2个)
3. 风险评估 (Risk Assessment)
4. 预期结果 (Expected Outcomes)
5. 应急计划 (Contingency Plans)

请以JSON格式返回，包含以下字段:
- primary_path (详细步骤)
- alternative_paths (列表)
- success_probability (0-100%)
- estimated_time (分钟)
- risk_level (low, medium, high)
- required_tools (列表)
""",
            temperature=0.3,
            response_format="json",
            required_fields=["target_analysis", "available_tools", "constraints"]
        )
        
        # 漏洞利用代码生成模板
        self.templates["exploit_generation"] = PromptTemplate(
            name="exploit_generation",
            system_prompt="你是一个资深安全研究员，擅长编写安全、有效的漏洞利用代码。请编写专业、可靠的漏洞利用代码。",
            user_prompt_template="""为以下漏洞生成漏洞利用代码:

漏洞信息:
- 漏洞类型: {vulnerability_type}
- CVE编号: {cve_id}
- 受影响系统/软件: {affected_system}
- 漏洞描述: {description}
- 影响等级: {severity}

目标环境信息:
{target_environment}

约束条件:
{constraints}

请生成漏洞利用代码，要求:
1. 代码安全可靠，避免副作用
2. 包含适当的错误处理
3. 添加详细的注释说明
4. 考虑不同环境适配性
5. 包含使用说明

代码语言要求: {language}

请以代码块形式返回，包含:
- 完整代码实现
- 必要的依赖说明
- 使用示例
- 安全注意事项
""",
            temperature=0.4,
            max_tokens=4000,
            response_format="code",
            required_fields=["vulnerability_type", "affected_system", "description", "severity", "target_environment"]
        )
        
        # 渗透测试阶段指导模板
        self.templates["stage_guidance"] = PromptTemplate(
            name="stage_guidance",
            system_prompt="你是一个资深渗透测试专家，擅长指导渗透测试各个阶段的工作。请提供专业、实用的指导建议。",
            user_prompt_template="""为渗透测试的 {stage_name} 阶段提供指导:

当前阶段: {stage_name}
前阶段结果: {previous_results}
当前上下文: {context}

目标: {target}
可用工具: {available_tools}

请为当前阶段提供:
1. 阶段目标 (Stage Objectives)
2. 关键任务 (Key Tasks)
3. 推荐工具 (Recommended Tools)
4. 预期产出 (Expected Deliverables)
5. 常见陷阱和规避方法 (Common Pitfalls & Avoidance)
6. 成功标准 (Success Criteria)
7. 时间估算 (Time Estimation)

请以JSON格式返回，包含以下字段:
- objectives (列表)
- tasks (详细任务列表)
- tools (推荐工具列表)
- deliverables (预期产出)
- time_estimate (分钟)
""",
            temperature=0.3,
            response_format="json",
            required_fields=["stage_name", "previous_results", "context", "target", "available_tools"]
        )
        
        # 风险评估模板
        self.templates["risk_assessment"] = PromptTemplate(
            name="risk_assessment",
            system_prompt="你是一个资深安全风险评估专家，擅长评估攻击路径的风险和影响。请提供专业、准确的风险评估。",
            user_prompt_template="""评估以下攻击路径的风险:

攻击路径描述:
{attack_path_description}

目标环境:
{target_environment}

攻击者能力假设:
{attacker_capabilities}

请从以下维度评估风险:
1. 技术风险 (Technical Risk)
   - 攻击成功率
   - 技术复杂性
   - 依赖条件

2. 业务风险 (Business Risk)
   - 对业务的影响
   - 数据泄露风险
   - 系统可用性影响

3. 法律合规风险 (Legal & Compliance Risk)
   - 法律法规合规性
   - 合同义务
   - 行业标准

4. 声誉风险 (Reputational Risk)
   - 对组织声誉的影响
   - 客户信任度影响
   - 市场地位影响

请以JSON格式返回风险评估结果，包含:
- overall_risk_level (low, medium, high, critical)
- technical_risk_score (0-10)
- business_impact_score (0-10)
- probability_score (0-100%)
- mitigation_recommendations (列表)
""",
            temperature=0.25,
            response_format="json",
            required_fields=["attack_path_description", "target_environment", "attacker_capabilities"]
        )
    
    def get_template(self, template_name: str) -> PromptTemplate:
        """获取指定名称的模板"""
        if template_name not in self.templates:
            raise ValueError(f"模板 '{template_name}' 不存在")
        return self.templates[template_name]
    
    def create_target_analysis_prompt(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建目标分析提示词"""
        # 提取扫描信息
        target = scan_data.get("target", "未知目标")
        scan_time = scan_data.get("scan_time", "未知时间")
        
        # 生成扫描摘要
        scan_summary = self._generate_scan_summary(scan_data)
        
        # 生成详细结果
        detailed_results = self._generate_detailed_results(scan_data)
        
        # 使用模板
        template = self.templates["target_analysis"]
        return template.format(
            target=target,
            scan_time=scan_time,
            scan_summary=scan_summary,
            detailed_results=detailed_results
        )
    
    def create_attack_planning_prompt(self, target_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """创建攻击规划提示词"""
        # 获取可用工具
        available_tools = target_analysis.get("available_tools", ["nmap", "whatweb", "nuclei", "sqlmap"])
        
        # 获取约束条件
        constraints = target_analysis.get("constraints", {
            "time_limit": "60分钟",
            "stealth_required": True,
            "resource_limit": "中等"
        })
        
        # 使用模板
        template = self.templates["attack_planning"]
        return template.format(
            target_analysis=json.dumps(target_analysis, indent=2, ensure_ascii=False),
            available_tools=", ".join(available_tools),
            constraints=json.dumps(constraints, indent=2, ensure_ascii=False)
        )
    
    def create_code_generation_prompt(self, vulnerability: Dict[str, Any]) -> Dict[str, Any]:
        """创建代码生成提示词"""
        # 使用模板
        template = self.templates["exploit_generation"]
        return template.format(
            vulnerability_type=vulnerability.get("type", "未知类型"),
            cve_id=vulnerability.get("cve_id", "N/A"),
            affected_system=vulnerability.get("affected_system", "未知系统"),
            description=vulnerability.get("description", "未提供描述"),
            severity=vulnerability.get("severity", "medium"),
            target_environment=vulnerability.get("environment", "通用环境"),
            constraints=vulnerability.get("constraints", "无特殊约束"),
            language=vulnerability.get("language", "Python")
        )
    
    def create_stage_guidance_prompt(self, stage_info: Dict[str, Any]) -> Dict[str, Any]:
        """创建阶段指导提示词"""
        # 使用模板
        template = self.templates["stage_guidance"]
        return template.format(
            stage_name=stage_info.get("stage_name", "未知阶段"),
            previous_results=json.dumps(stage_info.get("previous_results", {}), indent=2, ensure_ascii=False),
            context=stage_info.get("context", "无上下文信息"),
            target=stage_info.get("target", "未知目标"),
            available_tools=", ".join(stage_info.get("available_tools", []))
        )
    
    def create_risk_assessment_prompt(self, risk_info: Dict[str, Any]) -> Dict[str, Any]:
        """创建风险评估提示词"""
        # 使用模板
        template = self.templates["risk_assessment"]
        return template.format(
            attack_path_description=risk_info.get("attack_path", "未提供攻击路径描述"),
            target_environment=risk_info.get("environment", "未提供目标环境"),
            attacker_capabilities=risk_info.get("attacker_capabilities", "中级攻击者能力")
        )
    
    def _generate_scan_summary(self, scan_data: Dict[str, Any]) -> str:
        """生成扫描摘要"""
        summary_parts = []
        
        if "nmap" in scan_data:
            nmap_result = scan_data["nmap"]
            ports = nmap_result.get("ports", [])
            if ports:
                summary_parts.append(f"开放端口: {len(ports)}个")
        
        if "whatweb" in scan_data:
            whatweb_result = scan_data["whatweb"]
            fingerprint = whatweb_result.get("fingerprint", {})
            if fingerprint.get("web_server"):
                summary_parts.append(f"Web服务器: {fingerprint['web_server']}")
        
        if "nuclei" in scan_data:
            nuclei_result = scan_data["nuclei"]
            vulnerabilities = nuclei_result.get("vulnerabilities", [])
            if vulnerabilities:
                critical = len([v for v in vulnerabilities if v.get("info", {}).get("severity") == "critical"])
                high = len([v for v in vulnerabilities if v.get("info", {}).get("severity") == "high"])
                summary_parts.append(f"漏洞: {len(vulnerabilities)}个 (严重: {critical}, 高危: {high})")
        
        if "sqlmap" in scan_data:
            sqlmap_result = scan_data["sqlmap"]
            injections = sqlmap_result.get("injections", [])
            if injections:
                summary_parts.append(f"SQL注入点: {len(injections)}个")
        
        return "\n".join(summary_parts) if summary_parts else "无显著发现"
    
    def _generate_detailed_results(self, scan_data: Dict[str, Any]) -> str:
        """生成详细结果"""
        details = []
        
        for tool_name, result in scan_data.items():
            if isinstance(result, dict):
                details.append(f"\n[{tool_name.upper()}]")
                
                if tool_name == "nmap" and "ports" in result:
                    ports = result["ports"][:5]  # 只显示前5个端口
                    for port in ports:
                        details.append(f"  端口 {port['port']}: {port.get('service', '未知服务')} ({port.get('state', '未知状态')})")
                
                elif tool_name == "whatweb" and "fingerprint" in result:
                    fp = result["fingerprint"]
                    for key, value in fp.items():
                        if value and isinstance(value, (str, list)):
                            if isinstance(value, list):
                                details.append(f"  {key}: {', '.join(value[:3])}")
                            else:
                                details.append(f"  {key}: {value}")
                
                elif tool_name == "nuclei" and "vulnerabilities" in result:
                    vulns = result["vulnerabilities"][:3]  # 只显示前3个漏洞
                    for i, vuln in enumerate(vulns, 1):
                        info = vuln.get("info", {})
                        details.append(f"  漏洞{i}: {info.get('name', '未知')} ({info.get('severity', '未知')})")
        
        return "\n".join(details) if details else "无详细结果"


# 测试代码
if __name__ == "__main__":
    # 测试PromptEngineer
    engineer = PromptEngineer()
    
    print("可用模板:")
    for name in engineer.templates.keys():
        print(f"  - {name}")
    
    # 测试目标分析提示词生成
    test_scan_data = {
        "target": "example.com",
        "scan_time": "2024-01-01 10:00:00",
        "nmap": {
            "ports": [
                {"port": 80, "service": "http", "state": "open"},
                {"port": 443, "service": "https", "state": "open"}
            ]
        },
        "whatweb": {
            "fingerprint": {
                "web_server": "nginx",
                "language": ["PHP"],
                "cms": ["WordPress"]
            }
        }
    }
    
    try:
        prompt = engineer.create_target_analysis_prompt(test_scan_data)
        print(f"\n生成的目标分析提示词:")
        print(f"系统提示词: {prompt['system_prompt'][:100]}...")
        print(f"用户提示词长度: {len(prompt['user_prompt'])} 字符")
    except Exception as e:
        print(f"生成提示词时出错: {e}")