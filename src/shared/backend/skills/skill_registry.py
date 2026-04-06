# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Skill注册机制 - 管理所有可用技能

要求：
1. 技能注册和发现
2. 根据上下文推荐技能
3. 技能依赖关系管理
"""

import importlib
import inspect
from typing import Dict, List, Any, Type, Optional
import logging
from .base_skill import BaseSkill

logger = logging.getLogger(__name__)


class SkillRegistry:
    """技能注册表"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SkillRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.skills: Dict[str, BaseSkill] = {}
        self.skill_categories: Dict[str, List[str]] = {}
        self._initialized = True
        logger.info("SkillRegistry初始化完成")
    
    def register_skill(self, skill: BaseSkill) -> None:
        """注册技能"""
        skill_name = skill.name
        
        if skill_name in self.skills:
            logger.warning(f"技能 '{skill_name}' 已存在，将被覆盖")
        
        self.skills[skill_name] = skill
        
        # 按类别组织
        category = skill.category
        if category not in self.skill_categories:
            self.skill_categories[category] = []
        
        if skill_name not in self.skill_categories[category]:
            self.skill_categories[category].append(skill_name)
        
        logger.info(f"注册技能: {skill_name} ({category})")
    
    def register_skill_class(self, skill_class: Type[BaseSkill]) -> None:
        """注册技能类"""
        try:
            skill_instance = skill_class()
            self.register_skill(skill_instance)
        except Exception as e:
            logger.error(f"注册技能类失败 {skill_class.__name__}: {str(e)}")
    
    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """获取技能"""
        return self.skills.get(skill_name)
    
    def get_all_skills(self) -> List[BaseSkill]:
        """获取所有技能"""
        return list(self.skills.values())
    
    def get_skills_by_category(self, category: str) -> List[BaseSkill]:
        """按类别获取技能"""
        skill_names = self.skill_categories.get(category, [])
        return [self.skills[name] for name in skill_names if name in self.skills]
    
    def get_available_skills(self, context: Dict[str, Any]) -> List[BaseSkill]:
        """
        获取当前上下文下可用的技能
        
        Args:
            context: 执行上下文
            
        Returns:
            List[BaseSkill]: 可用技能列表
        """
        available_skills = []
        
        for skill in self.skills.values():
            try:
                if skill.can_handle(context):
                    available_skills.append(skill)
            except Exception as e:
                logger.error(f"检查技能 {skill.name} 可用性时出错: {str(e)}")
        
        return available_skills
    
    def recommend_skills(self, context: Dict[str, Any], max_recommendations: int = 5) -> List[Dict[str, Any]]:
        """
        推荐最适合当前上下文的技能
        
        Args:
            context: 执行上下文
            max_recommendations: 最大推荐数量
            
        Returns:
            List[Dict[str, Any]]: 推荐技能信息列表
        """
        available_skills = self.get_available_skills(context)
        
        if not available_skills:
            return []
        
        # 计算技能优先级分数
        scored_skills = []
        for skill in available_skills:
            score = self._calculate_skill_score(skill, context)
            scored_skills.append({
                "skill": skill,
                "score": score,
                "info": skill.get_skill_info()
            })
        
        # 按分数降序排序
        scored_skills.sort(key=lambda x: x["score"], reverse=True)
        
        # 返回前N个推荐
        recommendations = []
        for item in scored_skills[:max_recommendations]:
            recommendations.append({
                "skill_name": item["skill"].name,
                "score": item["score"],
                "reason": self._generate_recommendation_reason(item["skill"], context),
                **item["info"]
            })
        
        return recommendations
    
    def _calculate_skill_score(self, skill: BaseSkill, context: Dict[str, Any]) -> float:
        """
        计算技能优先级分数
        
        Args:
            skill: 技能实例
            context: 执行上下文
            
        Returns:
            float: 优先级分数 (0-100)
        """
        score = 50.0  # 基础分数
        
        # 1. 难度权重（难度适中最好）
        difficulty = skill.difficulty
        if difficulty == "easy":
            score += 10
        elif difficulty == "medium":
            score += 15
        elif difficulty == "hard":
            score += 5
        elif difficulty == "expert":
            score += 0
        
        # 2. 工具可用性（如果工具已安装，加分）
        required_tools = skill.required_tools
        if required_tools:
            # 这里可以检查工具是否可用
            # 暂时假设所有工具都可用
            score += len(required_tools) * 2
        
        # 3. 前置技能检查（如果前置技能已执行，加分）
        prerequisites = skill.prerequisites
        if prerequisites:
            # 检查当前状态中是否已执行前置技能
            current_state = context.get("current_state", {})
            execution_history = context.get("execution_history", [])
            
            executed_skills = [item.get("skill") for item in execution_history]
            executed_skills = [s for s in executed_skills if s]
            
            prereq_met = all(prereq in executed_skills for prereq in prerequisites)
            if prereq_met:
                score += 20
            else:
                score -= 10  # 前置技能未满足，扣分
        
        # 4. 目标匹配度（根据上下文调整）
        target = context.get("target", "")
        scan_results = context.get("scan_results", {})
        
        # 根据扫描结果调整分数
        if "nmap" in scan_results and skill.name == "NmapScanSkill":
            score += 25  # 如果有nmap结果，nmap技能优先级高
        
        if "whatweb" in scan_results and skill.name == "WhatWebSkill":
            score += 20
        
        if "sqlmap" in scan_results and skill.name == "SQLInjectionSkill":
            score += 30
        
        # 5. 漏洞发现（如果有相关漏洞，相关技能优先级高）
        vulnerabilities = []
        if "nuclei" in scan_results:
            nuclei_data = scan_results["nuclei"]
            if isinstance(nuclei_data, dict) and "vulnerabilities" in nuclei_data:
                vulnerabilities = nuclei_data["vulnerabilities"]
        
        for vuln in vulnerabilities:
            vuln_name = vuln.get("name", "").lower()
            if "sql" in vuln_name and skill.name == "SQLInjectionSkill":
                score += 40
            if "rce" in vuln_name or "remote code execution" in vuln_name:
                if skill.name == "RCESkill":
                    score += 45
        
        # 确保分数在合理范围内
        return max(0, min(score, 100))
    
    def _generate_recommendation_reason(self, skill: BaseSkill, context: Dict[str, Any]) -> str:
        """生成推荐理由"""
        reasons = []
        
        # 基于技能类别
        category = skill.category
        if category == "reconnaissance":
            reasons.append("信息收集阶段必要技能")
        elif category == "vulnerability_scanning":
            reasons.append("漏洞检测关键技能")
        elif category == "exploitation":
            reasons.append("漏洞利用核心技能")
        elif category == "post_exploitation":
            reasons.append("后渗透阶段重要技能")
        
        # 基于扫描结果
        scan_results = context.get("scan_results", {})
        
        if "nmap" in scan_results and skill.name == "NmapScanSkill":
            reasons.append("已有端口扫描基础，可进行深度扫描")
        
        if "whatweb" in scan_results and skill.name == "WhatWebSkill":
            reasons.append("Web服务已识别，可进行技术栈分析")
        
        # 基于当前状态
        current_state = context.get("current_state", {})
        if "open_ports" in current_state and skill.name == "WhatWebSkill":
            reasons.append("端口扫描完成，可进行Web指纹识别")
        
        if "web_technologies" in current_state and skill.name == "SQLInjectionSkill":
            reasons.append("Web技术栈已识别，可进行SQL注入检测")
        
        # 如果没有特定理由，使用通用理由
        if not reasons:
            reasons.append("适合当前攻击阶段")
        
        return "；".join(reasons)
    
    def execute_skill(self, skill_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行指定技能
        
        Args:
            skill_name: 技能名称
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        skill = self.get_skill(skill_name)
        
        if not skill:
            return {
                "success": False,
                "error": f"技能 '{skill_name}' 未找到",
                "skill_name": skill_name
            }
        
        try:
            # 验证上下文
            is_valid, error_msg = skill.validate_context(context)
            if not is_valid:
                return {
                    "success": False,
                    "error": f"上下文验证失败: {error_msg}",
                    "skill_name": skill_name
                }
            
            # 记录执行开始
            skill.log_execution_start(context)
            
            # 执行技能
            result = skill.execute(context)
            
            # 确保结果包含必要字段
            if "success" not in result:
                result["success"] = False
            
            if "skill_name" not in result:
                result["skill_name"] = skill_name
            
            # 记录执行结束
            skill.log_execution_end(result)
            
            return result
            
        except Exception as e:
            logger.error(f"执行技能 {skill_name} 时出错: {str(e)}")
            return {
                "success": False,
                "error": f"执行失败: {str(e)}",
                "skill_name": skill_name,
                "exception": str(e)
            }
    
    def auto_discover_skills(self, module_path: str = "backend.skills") -> None:
        """
        自动发现并注册技能
        
        Args:
            module_path: 技能模块路径
        """
        try:
            # 动态导入技能模块
            skills_module = importlib.import_module(module_path)
            
            # 查找所有BaseSkill的子类
            for name, obj in inspect.getmembers(skills_module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseSkill) and 
                    obj != BaseSkill):
                    
                    try:
                        self.register_skill_class(obj)
                        logger.info(f"自动发现并注册技能类: {name}")
                    except Exception as e:
                        logger.error(f"注册技能类 {name} 失败: {str(e)}")
                        
        except ImportError as e:
            logger.error(f"导入技能模块失败 {module_path}: {str(e)}")
        except Exception as e:
            logger.error(f"自动发现技能失败: {str(e)}")
    
    def get_registry_info(self) -> Dict[str, Any]:
        """获取注册表信息"""
        return {
            "total_skills": len(self.skills),
            "categories": {
                category: len(skills) 
                for category, skills in self.skill_categories.items()
            },
            "skill_list": [
                {
                    "name": skill.name,
                    "category": skill.category,
                    "difficulty": skill.difficulty,
                    "description": skill.description[:50] + "..." if len(skill.description) > 50 else skill.description
                }
                for skill in self.skills.values()
            ]
        }


# 全局技能注册表实例
registry = SkillRegistry()