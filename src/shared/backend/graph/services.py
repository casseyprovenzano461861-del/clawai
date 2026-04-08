#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱服务
用于存储和检索渗透测试相关的知识
"""

import json
import os
from typing import Dict, List, Optional, Any


class KnowledgeBase:
    """知识库"""
    
    def __init__(self, data_dir: str = "data/knowledge"):
        """初始化知识库
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        self.vulnerabilities = []
        self.exploits = []
        self.recommendations = []
        
        # 创建数据目录
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 加载现有数据
        self._load_data()
    
    def store_vulnerability(self, vulnerability: Dict[str, Any]) -> str:
        """存储漏洞信息
        
        Args:
            vulnerability: 漏洞信息
            
        Returns:
            漏洞ID
        """
        # 生成漏洞ID
        vuln_id = f"vuln_{len(self.vulnerabilities) + 1}"
        vulnerability["id"] = vuln_id
        vulnerability["created_at"] = self._get_current_time()
        
        # 存储漏洞
        self.vulnerabilities.append(vulnerability)
        
        # 保存数据
        self._save_data()
        
        return vuln_id
    
    def store_exploit(self, exploit: Dict[str, Any]) -> str:
        """存储漏洞利用信息
        
        Args:
            exploit: 漏洞利用信息
            
        Returns:
            利用ID
        """
        # 生成利用ID
        exploit_id = f"exploit_{len(self.exploits) + 1}"
        exploit["id"] = exploit_id
        exploit["created_at"] = self._get_current_time()
        
        # 存储利用
        self.exploits.append(exploit)
        
        # 保存数据
        self._save_data()
        
        return exploit_id
    
    def store_recommendation(self, recommendation: Dict[str, Any]) -> str:
        """存储安全建议
        
        Args:
            recommendation: 安全建议
            
        Returns:
            建议ID
        """
        # 生成建议ID
        rec_id = f"rec_{len(self.recommendations) + 1}"
        recommendation["id"] = rec_id
        recommendation["created_at"] = self._get_current_time()
        
        # 存储建议
        self.recommendations.append(recommendation)
        
        # 保存数据
        self._save_data()
        
        return rec_id
    
    def retrieve_vulnerabilities(self, target: Optional[str] = None, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """检索相关漏洞
        
        Args:
            target: 目标系统
            severity: 严重程度
            
        Returns:
            漏洞列表
        """
        results = self.vulnerabilities
        
        # 按目标过滤
        if target:
            results = [v for v in results if target in str(v.get("location", ""))]
        
        # 按严重程度过滤
        if severity:
            results = [v for v in results if v.get("severity") == severity]
        
        return results
    
    def retrieve_exploits(self, vulnerability_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """检索漏洞利用方案
        
        Args:
            vulnerability_id: 漏洞ID
            
        Returns:
            利用方案列表
        """
        results = self.exploits
        
        # 按漏洞ID过滤
        if vulnerability_id:
            results = [e for e in results if e.get("vulnerability_id") == vulnerability_id]
        
        return results
    
    def retrieve_recommendations(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """检索安全建议
        
        Args:
            category: 建议类别
            
        Returns:
            建议列表
        """
        results = self.recommendations
        
        # 按类别过滤
        if category:
            results = [r for r in results if r.get("category") == category]
        
        return results
    
    def search_knowledge(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """搜索知识
        
        Args:
            query: 搜索关键词
            
        Returns:
            搜索结果
        """
        query = query.lower()
        
        # 搜索漏洞
        vuln_results = [v for v in self.vulnerabilities if query in str(v).lower()]
        
        # 搜索利用方案
        exploit_results = [e for e in self.exploits if query in str(e).lower()]
        
        # 搜索建议
        rec_results = [r for r in self.recommendations if query in str(r).lower()]
        
        return {
            "vulnerabilities": vuln_results,
            "exploits": exploit_results,
            "recommendations": rec_results
        }
    
    def get_statistics(self) -> Dict[str, int]:
        """获取知识库统计信息
        
        Returns:
            统计信息
        """
        return {
            "vulnerabilities_count": len(self.vulnerabilities),
            "exploits_count": len(self.exploits),
            "recommendations_count": len(self.recommendations)
        }
    
    def _load_data(self):
        """加载数据"""
        # 加载漏洞数据
        vuln_file = os.path.join(self.data_dir, "vulnerabilities.json")
        if os.path.exists(vuln_file):
            try:
                with open(vuln_file, "r", encoding="utf-8") as f:
                    self.vulnerabilities = json.load(f)
            except Exception:
                self.vulnerabilities = []
        
        # 加载利用数据
        exploit_file = os.path.join(self.data_dir, "exploits.json")
        if os.path.exists(exploit_file):
            try:
                with open(exploit_file, "r", encoding="utf-8") as f:
                    self.exploits = json.load(f)
            except Exception:
                self.exploits = []
        
        # 加载建议数据
        rec_file = os.path.join(self.data_dir, "recommendations.json")
        if os.path.exists(rec_file):
            try:
                with open(rec_file, "r", encoding="utf-8") as f:
                    self.recommendations = json.load(f)
            except Exception:
                self.recommendations = []
    
    def _save_data(self):
        """保存数据"""
        # 保存漏洞数据
        vuln_file = os.path.join(self.data_dir, "vulnerabilities.json")
        with open(vuln_file, "w", encoding="utf-8") as f:
            json.dump(self.vulnerabilities, f, indent=2, ensure_ascii=False)
        
        # 保存利用数据
        exploit_file = os.path.join(self.data_dir, "exploits.json")
        with open(exploit_file, "w", encoding="utf-8") as f:
            json.dump(self.exploits, f, indent=2, ensure_ascii=False)
        
        # 保存建议数据
        rec_file = os.path.join(self.data_dir, "recommendations.json")
        with open(rec_file, "w", encoding="utf-8") as f:
            json.dump(self.recommendations, f, indent=2, ensure_ascii=False)
    
    def _get_current_time(self) -> str:
        """获取当前时间
        
        Returns:
            当前时间字符串
        """
        import time
        return time.strftime("%Y-%m-%d %H:%M:%S")
    
    def clear_data(self):
        """清空数据"""
        self.vulnerabilities = []
        self.exploits = []
        self.recommendations = []
        self._save_data()


# 测试代码
if __name__ == "__main__":
    # 初始化知识库
    kb = KnowledgeBase()
    
    # 存储漏洞
    vuln_id = kb.store_vulnerability({
        "name": "SQL注入漏洞",
        "severity": "high",
        "description": "目标存在SQL注入漏洞",
        "location": "http://example.com/api?id=1",
        "tool": "nuclei"
    })
    print(f"存储漏洞成功，ID: {vuln_id}")
    
    # 存储利用方案
    exploit_id = kb.store_exploit({
        "vulnerability_id": vuln_id,
        "name": "SQL注入利用方案",
        "steps": ["确认漏洞", "提取数据", "提升权限"],
        "tools": ["sqlmap", "burp suite"],
        "difficulty": "medium"
    })
    print(f"存储利用方案成功，ID: {exploit_id}")
    
    # 存储安全建议
    rec_id = kb.store_recommendation({
        "category": "input_validation",
        "title": "使用参数化查询",
        "description": "使用参数化查询防止SQL注入攻击",
        "priority": "high"
    })
    print(f"存储安全建议成功，ID: {rec_id}")
    
    # 检索漏洞
    vulnerabilities = kb.retrieve_vulnerabilities(severity="high")
    print("\n检索高危漏洞:")
    for vuln in vulnerabilities:
        print(f"- {vuln['name']} (ID: {vuln['id']})")
    
    # 搜索知识
    results = kb.search_knowledge("SQL注入")
    print("\n搜索 'SQL注入':")
    print(f"找到 {len(results['vulnerabilities'])} 个漏洞")
    print(f"找到 {len(results['exploits'])} 个利用方案")
    
    # 获取统计信息
    stats = kb.get_statistics()
    print("\n知识库统计:")
    print(f"漏洞数量: {stats['vulnerabilities_count']}")
    print(f"利用方案数量: {stats['exploits_count']}")
    print(f"安全建议数量: {stats['recommendations_count']}")
