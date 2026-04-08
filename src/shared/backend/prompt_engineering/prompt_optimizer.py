# -*- coding: utf-8 -*-
"""
提示优化器模块
用于优化提示的质量和效果
"""

import re
from typing import Dict, Any, List


class PromptOptimizer:
    """提示优化器类"""
    
    def __init__(self):
        self.optimization_rules = [
            self._optimize_clarity,
            self._optimize_specificity,
            self._optimize_structure,
            self._optimize_language,
            self._optimize_length
        ]
    
    def optimize(self, prompt: str) -> Dict[str, Any]:
        """优化提示"""
        original_prompt = prompt
        optimized_prompt = prompt
        suggestions = []
        
        # 应用所有优化规则
        for rule in self.optimization_rules:
            result = rule(optimized_prompt)
            optimized_prompt = result["prompt"]
            suggestions.extend(result["suggestions"])
        
        # 计算优化分数
        score = self._calculate_score(original_prompt, optimized_prompt)
        
        return {
            "original_prompt": original_prompt,
            "optimized_prompt": optimized_prompt,
            "suggestions": suggestions,
            "score": score
        }
    
    def _optimize_clarity(self, prompt: str) -> Dict[str, Any]:
        """优化提示的清晰度"""
        suggestions = []
        optimized_prompt = prompt
        
        # 检查模糊词汇
        vague_terms = ["一些", "某些", "可能", "或许", "大概", "差不多"]
        for term in vague_terms:
            if term in optimized_prompt:
                suggestions.append(f"替换模糊词汇 '{term}' 为更具体的描述")
                # 简单替换示例
                optimized_prompt = optimized_prompt.replace(f"{term}", "具体的")
        
        # 检查被动语态
        passive_patterns = [r'被\S+', r'由\S+']
        for pattern in passive_patterns:
            if re.search(pattern, optimized_prompt):
                suggestions.append("考虑使用主动语态以提高清晰度")
        
        return {"prompt": optimized_prompt, "suggestions": suggestions}
    
    def _optimize_specificity(self, prompt: str) -> Dict[str, Any]:
        """优化提示的具体性"""
        suggestions = []
        optimized_prompt = prompt
        
        # 检查缺少具体指令的情况
        if "请执行" not in optimized_prompt:
            suggestions.append("添加具体的执行指令，明确告诉模型应该做什么")
        
        # 检查缺少工具说明的情况
        if "使用" not in optimized_prompt:
            suggestions.append("添加工具使用说明，明确告诉模型应该使用哪些工具")
        
        # 检查缺少输出格式的情况
        if "提供" not in optimized_prompt:
            suggestions.append("添加输出格式说明，明确告诉模型应该如何输出结果")
        
        return {"prompt": optimized_prompt, "suggestions": suggestions}
    
    def _optimize_structure(self, prompt: str) -> Dict[str, Any]:
        """优化提示的结构"""
        suggestions = []
        optimized_prompt = prompt
        
        # 检查提示结构
        lines = optimized_prompt.strip().split('\n')
        if len(lines) < 3:
            suggestions.append("增加提示的结构层次，使用分段和编号提高可读性")
        
        # 检查是否有明确的任务描述
        task_keywords = ["任务", "目标", "要求", "执行"]
        has_task = any(keyword in optimized_prompt for keyword in task_keywords)
        if not has_task:
            suggestions.append("添加明确的任务描述，让模型清楚知道要做什么")
        
        return {"prompt": optimized_prompt, "suggestions": suggestions}
    
    def _optimize_language(self, prompt: str) -> Dict[str, Any]:
        """优化提示的语言"""
        suggestions = []
        optimized_prompt = prompt
        
        # 检查语言一致性
        if "你是" in optimized_prompt and "请" in optimized_prompt:
            suggestions.append("保持语言风格一致，使用正式、专业的语言")
        
        # 检查专业术语使用
        security_terms = ["漏洞", "扫描", "渗透", "利用", "权限", "安全"]
        has_security_terms = any(term in optimized_prompt for term in security_terms)
        if not has_security_terms:
            suggestions.append("使用专业的安全术语，提高提示的专业性")
        
        return {"prompt": optimized_prompt, "suggestions": suggestions}
    
    def _optimize_length(self, prompt: str) -> Dict[str, Any]:
        """优化提示的长度"""
        suggestions = []
        optimized_prompt = prompt
        
        # 检查提示长度
        word_count = len(optimized_prompt.split())
        if word_count < 50:
            suggestions.append("增加提示的详细程度，提供更多上下文信息")
        elif word_count > 500:
            suggestions.append("简化提示，删除不必要的细节，保持简洁明了")
        
        return {"prompt": optimized_prompt, "suggestions": suggestions}
    
    def _calculate_score(self, original_prompt: str, optimized_prompt: str) -> float:
        """计算提示优化分数"""
        score = 100.0
        
        # 检查关键元素
        key_elements = [
            "任务", "目标", "工具", "输出", "详细", "具体", "专业"
        ]
        for element in key_elements:
            if element not in optimized_prompt:
                score -= 10.0
        
        # 检查长度
        word_count = len(optimized_prompt.split())
        if word_count < 50:
            score -= 15.0
        elif word_count > 500:
            score -= 10.0
        
        # 确保分数在0-100之间
        score = max(0.0, min(100.0, score))
        
        return score
    
    def evaluate_prompt(self, prompt: str) -> Dict[str, Any]:
        """评估提示质量"""
        # 检查提示的关键要素
        evaluation = {
            "clarity": self._evaluate_clarity(prompt),
            "specificity": self._evaluate_specificity(prompt),
            "structure": self._evaluate_structure(prompt),
            "language": self._evaluate_language(prompt),
            "length": self._evaluate_length(prompt)
        }
        
        # 计算总体评分
        total_score = sum(evaluation.values()) / len(evaluation)
        
        return {
            "evaluation": evaluation,
            "total_score": total_score,
            "recommendations": self._generate_recommendations(evaluation)
        }
    
    def _evaluate_clarity(self, prompt: str) -> float:
        """评估提示的清晰度"""
        score = 100.0
        
        # 检查模糊词汇
        vague_terms = ["一些", "某些", "可能", "或许", "大概", "差不多"]
        for term in vague_terms:
            if term in prompt:
                score -= 10.0
        
        return max(0.0, score)
    
    def _evaluate_specificity(self, prompt: str) -> float:
        """评估提示的具体性"""
        score = 100.0
        
        # 检查关键要素
        required_elements = ["任务", "目标", "工具", "输出"]
        for element in required_elements:
            if element not in prompt:
                score -= 20.0
        
        return max(0.0, score)
    
    def _evaluate_structure(self, prompt: str) -> float:
        """评估提示的结构"""
        score = 100.0
        
        # 检查结构
        lines = prompt.strip().split('\n')
        if len(lines) < 3:
            score -= 30.0
        
        return max(0.0, score)
    
    def _evaluate_language(self, prompt: str) -> float:
        """评估提示的语言"""
        score = 100.0
        
        # 检查专业术语
        security_terms = ["漏洞", "扫描", "渗透", "利用", "权限", "安全"]
        has_security_terms = any(term in prompt for term in security_terms)
        if not has_security_terms:
            score -= 20.0
        
        return max(0.0, score)
    
    def _evaluate_length(self, prompt: str) -> float:
        """评估提示的长度"""
        score = 100.0
        
        # 检查长度
        word_count = len(prompt.split())
        if word_count < 50:
            score -= 30.0
        elif word_count > 500:
            score -= 20.0
        
        return max(0.0, score)
    
    def _generate_recommendations(self, evaluation: Dict[str, float]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if evaluation["clarity"] < 80:
            recommendations.append("提高提示的清晰度，避免使用模糊词汇")
        
        if evaluation["specificity"] < 80:
            recommendations.append("增加提示的具体性，明确任务目标和要求")
        
        if evaluation["structure"] < 80:
            recommendations.append("优化提示的结构，使用分段和编号提高可读性")
        
        if evaluation["language"] < 80:
            recommendations.append("使用专业的安全术语，保持语言风格一致")
        
        if evaluation["length"] < 80:
            recommendations.append("调整提示的长度，确保提供足够的信息但不过于冗长")
        
        return recommendations
