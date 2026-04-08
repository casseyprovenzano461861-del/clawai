# 智能路径规划器
# 实现动态攻击路径生成、评估和优化

import time
from typing import Dict, List, Any, Optional

class DynamicPathPlanner:
    """动态路径规划器"""
    
    def __init__(self):
        self.path_generators = {
            "web": self._generate_web_paths,
            "services": self._generate_service_paths,
            "database": self._generate_database_paths,
            "internal": self._generate_lateral_paths
        }
    
    def plan_attack_path(self, target_info: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """规划攻击路径"""
        # 1. 路径生成
        candidate_paths = self._generate_candidate_paths(target_info)
        
        # 2. 路径评估
        evaluated_paths = self._evaluate_paths(candidate_paths, constraints)
        
        # 3. 路径优化
        optimized_paths = self._optimize_paths(evaluated_paths)
        
        # 4. 路径选择
        selected_path = self._select_best_path(optimized_paths)
        
        return selected_path
    
    def _generate_candidate_paths(self, target_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成候选路径"""
        paths = []
        
        # 基于目标类型生成路径
        for target_type, generator in self.path_generators.items():
            if target_type in target_info.get("target_types", []):
                target_paths = generator(target_info)
                paths.extend(target_paths)
        
        # 生成混合路径
        if len(target_info.get("target_types", [])) > 1:
            mixed_paths = self._generate_mixed_paths(target_info)
            paths.extend(mixed_paths)
        
        return paths
    
    def _generate_web_paths(self, target_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成Web攻击路径"""
        paths = []
        
        # Web扫描 -> SQL注入 -> 权限提升
        paths.append({
            "id": f"web_path_1_{int(time.time())}",
            "name": "Web扫描 -> SQL注入 -> 权限提升",
            "steps": [
                {"step": 1, "action": "web_scan", "tool": "nikto", "description": "扫描Web应用漏洞"},
                {"step": 2, "action": "sql_injection", "tool": "sqlmap", "description": "检测SQL注入漏洞"},
                {"step": 3, "action": "privilege_escalation", "tool": "metasploit", "description": "尝试权限提升"}
            ],
            "target_type": "web",
            "complexity": "medium"
        })
        
        # 目录扫描 -> XSS -> 会话劫持
        paths.append({
            "id": f"web_path_2_{int(time.time())}",
            "name": "目录扫描 -> XSS -> 会话劫持",
            "steps": [
                {"step": 1, "action": "directory_scan", "tool": "dirsearch", "description": "扫描敏感目录"},
                {"step": 2, "action": "xss_test", "tool": "xsstrike", "description": "检测XSS漏洞"},
                {"step": 3, "action": "session_hijacking", "tool": "burpsuite", "description": "尝试会话劫持"}
            ],
            "target_type": "web",
            "complexity": "medium"
        })
        
        return paths
    
    def _generate_service_paths(self, target_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成服务攻击路径"""
        paths = []
        
        # 服务枚举 -> 漏洞扫描 -> 远程代码执行
        paths.append({
            "id": f"service_path_1_{int(time.time())}",
            "name": "服务枚举 -> 漏洞扫描 -> 远程代码执行",
            "steps": [
                {"step": 1, "action": "service_enumeration", "tool": "nmap", "description": "枚举开放服务"},
                {"step": 2, "action": "vulnerability_scan", "tool": "nuclei", "description": "扫描服务漏洞"},
                {"step": 3, "action": "remote_code_execution", "tool": "metasploit", "description": "尝试远程代码执行"}
            ],
            "target_type": "services",
            "complexity": "high"
        })
        
        return paths
    
    def _generate_database_paths(self, target_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成数据库攻击路径"""
        paths = []
        
        # 数据库发现 -> 弱密码检测 -> 数据窃取
        paths.append({
            "id": f"database_path_1_{int(time.time())}",
            "name": "数据库发现 -> 弱密码检测 -> 数据窃取",
            "steps": [
                {"step": 1, "action": "database_discovery", "tool": "nmap", "description": "发现数据库服务"},
                {"step": 2, "action": "password_attack", "tool": "hydra", "description": "检测弱密码"},
                {"step": 3, "action": "data_exfiltration", "tool": "sqlmap", "description": "窃取敏感数据"}
            ],
            "target_type": "database",
            "complexity": "high"
        })
        
        return paths
    
    def _generate_lateral_paths(self, target_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成内网横向移动路径"""
        paths = []
        
        # 网络发现 -> 主机扫描 -> 横向移动
        paths.append({
            "id": f"lateral_path_1_{int(time.time())}",
            "name": "网络发现 -> 主机扫描 -> 横向移动",
            "steps": [
                {"step": 1, "action": "network_discovery", "tool": "nmap", "description": "发现内网网络"},
                {"step": 2, "action": "host_scanning", "tool": "nmap", "description": "扫描内网主机"},
                {"step": 3, "action": "lateral_movement", "tool": "metasploit", "description": "尝试横向移动"}
            ],
            "target_type": "internal",
            "complexity": "high"
        })
        
        return paths
    
    def _generate_mixed_paths(self, target_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成混合攻击路径"""
        paths = []
        
        # Web -> 数据库 -> 内网
        if all(t in target_info.get("target_types", []) for t in ["web", "database", "internal"]):
            paths.append({
                "id": f"mixed_path_1_{int(time.time())}",
                "name": "Web -> 数据库 -> 内网",
                "steps": [
                    {"step": 1, "action": "web_scan", "tool": "nikto", "description": "扫描Web应用"},
                    {"step": 2, "action": "sql_injection", "tool": "sqlmap", "description": "获取数据库访问权限"},
                    {"step": 3, "action": "pivot", "tool": "metasploit", "description": "通过数据库服务器进入内网"},
                    {"step": 4, "action": "lateral_movement", "tool": "metasploit", "description": "内网横向移动"}
                ],
                "target_type": "mixed",
                "complexity": "very_high"
            })
        
        return paths
    
    def _evaluate_paths(self, paths: List[Dict[str, Any]], constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """评估路径"""
        evaluated_paths = []
        
        for path in paths:
            evaluation = {
                "success_rate": self._calculate_success_rate(path),
                "time_cost": self._estimate_time_cost(path),
                "risk_level": self._assess_risk_level(path, constraints),
                "resource_consumption": self._estimate_resource_consumption(path),
                "stealthiness": self._assess_stealthiness(path, constraints)
            }
            
            # 计算综合评分
            score = self._calculate_path_score(evaluation, constraints)
            
            evaluated_path = path.copy()
            evaluated_path["evaluation"] = evaluation
            evaluated_path["score"] = score
            
            evaluated_paths.append(evaluated_path)
        
        return evaluated_paths
    
    def _calculate_success_rate(self, path: Dict[str, Any]) -> float:
        """计算成功率"""
        # 基于步骤数量和复杂度评估成功率
        step_count = len(path.get("steps", []))
        complexity = path.get("complexity", "medium")
        
        base_rate = {
            "low": 0.9,
            "medium": 0.7,
            "high": 0.5,
            "very_high": 0.3
        }[complexity]
        
        # 每增加一步，成功率降低10%
        success_rate = base_rate * (0.9 ** (step_count - 1))
        
        return max(success_rate, 0.1)  # 最低10%
    
    def _estimate_time_cost(self, path: Dict[str, Any]) -> int:
        """估计时间成本（秒）"""
        # 基于步骤数量和复杂度评估时间
        step_count = len(path.get("steps", []))
        complexity = path.get("complexity", "medium")
        
        base_time = {
            "low": 300,    # 5分钟
            "medium": 600,  # 10分钟
            "high": 1200,   # 20分钟
            "very_high": 1800  # 30分钟
        }[complexity]
        
        # 每增加一步，时间增加50%
        time_cost = base_time * (1.5 ** (step_count - 1))
        
        return int(time_cost)
    
    def _assess_risk_level(self, path: Dict[str, Any], constraints: Dict[str, Any]) -> str:
        """评估风险等级"""
        complexity = path.get("complexity", "medium")
        
        # 基于复杂度和约束条件评估风险
        if constraints.get("stealth_required"):
            risk_map = {
                "low": "medium",
                "medium": "high",
                "high": "very_high",
                "very_high": "critical"
            }
        else:
            risk_map = {
                "low": "low",
                "medium": "medium",
                "high": "high",
                "very_high": "very_high"
            }
        
        return risk_map[complexity]
    
    def _estimate_resource_consumption(self, path: Dict[str, Any]) -> Dict[str, float]:
        """估计资源消耗"""
        step_count = len(path.get("steps", []))
        complexity = path.get("complexity", "medium")
        
        # 基于复杂度评估资源消耗
        base_consumption = {
            "low": {"cpu": 0.2, "memory": 0.3, "network": 0.1},
            "medium": {"cpu": 0.4, "memory": 0.5, "network": 0.3},
            "high": {"cpu": 0.6, "memory": 0.7, "network": 0.5},
            "very_high": {"cpu": 0.8, "memory": 0.9, "network": 0.7}
        }[complexity]
        
        # 每增加一步，资源消耗增加20%
        multiplier = 1.0 + (step_count - 1) * 0.2
        
        return {
            "cpu": min(base_consumption["cpu"] * multiplier, 1.0),
            "memory": min(base_consumption["memory"] * multiplier, 1.0),
            "network": min(base_consumption["network"] * multiplier, 1.0)
        }
    
    def _assess_stealthiness(self, path: Dict[str, Any], constraints: Dict[str, Any]) -> float:
        """评估隐蔽性"""
        # 基于工具和步骤评估隐蔽性
        steps = path.get("steps", [])
        
        # 工具隐蔽性评分
        tool_stealth = {
            "nmap": 0.7,  # 可配置为隐蔽模式
            "nikto": 0.6,  # 相对隐蔽
            "dirsearch": 0.5,  # 可能产生大量请求
            "sqlmap": 0.4,  # 可能产生大量请求
            "metasploit": 0.3,  # 较为明显
            "hydra": 0.2,  # 暴力破解，非常明显
            "burpsuite": 0.6,  # 可配置为隐蔽模式
            "xsstrike": 0.5,  # 可能产生大量请求
            "nuclei": 0.6  # 相对隐蔽
        }
        
        # 计算平均隐蔽性
        if steps:
            avg_stealth = sum(tool_stealth.get(step.get("tool", ""), 0.5) for step in steps) / len(steps)
        else:
            avg_stealth = 0.5
        
        # 如果需要隐蔽性，降低对高风险工具的评分
        if constraints.get("stealth_required"):
            avg_stealth *= 0.8
        
        return avg_stealth
    
    def _calculate_path_score(self, evaluation: Dict[str, Any], constraints: Dict[str, Any]) -> float:
        """计算路径评分"""
        # 权重配置
        weights = {
            "success_rate": 0.3,
            "time_cost": -0.2,  # 时间越短越好
            "risk_level": -0.2,  # 风险越低越好
            "resource_consumption": -0.1,  # 资源消耗越低越好
            "stealthiness": 0.2  # 隐蔽性越高越好
        }
        
        # 转换风险等级为数值
        risk_values = {
            "low": 0.1,
            "medium": 0.3,
            "high": 0.6,
            "very_high": 0.8,
            "critical": 1.0
        }
        
        # 转换时间成本为0-1范围内的值（假设最大时间为3600秒）
        time_value = min(evaluation["time_cost"] / 3600, 1.0)
        
        # 计算资源消耗平均值
        resource_value = (evaluation["resource_consumption"]["cpu"] + 
                        evaluation["resource_consumption"]["memory"] + 
                        evaluation["resource_consumption"]["network"]) / 3
        
        # 计算加权评分
        score = (
            evaluation["success_rate"] * weights["success_rate"] +
            time_value * weights["time_cost"] +
            risk_values[evaluation["risk_level"]] * weights["risk_level"] +
            resource_value * weights["resource_consumption"] +
            evaluation["stealthiness"] * weights["stealthiness"]
        )
        
        # 归一化到0-1范围
        score = (score + 0.5)  # 调整到0-1范围
        return max(min(score, 1.0), 0.0)
    
    def _optimize_paths(self, evaluated_paths: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """优化路径"""
        # 按评分排序
        optimized_paths = sorted(evaluated_paths, key=lambda x: x.get("score", 0), reverse=True)
        
        # 保留前5个最优路径
        return optimized_paths[:5]
    
    def _select_best_path(self, optimized_paths: List[Dict[str, Any]]) -> Dict[str, Any]:
        """选择最佳路径"""
        if not optimized_paths:
            return {
                "id": f"default_path_{int(time.time())}",
                "name": "默认路径",
                "steps": [],
                "score": 0.0,
                "evaluation": {}
            }
        
        # 返回评分最高的路径
        return optimized_paths[0]
    
    def adjust_path(self, path: Dict[str, Any], execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """根据执行结果调整路径"""
        adjusted_path = path.copy()
        steps = adjusted_path.get("steps", [])
        
        # 分析执行结果
        for i, step in enumerate(steps):
            step_id = step.get("step")
            if step_id in execution_results:
                result = execution_results[step_id]
                
                # 如果步骤失败，尝试替换为备选工具
                if not result.get("success"):
                    steps[i] = self._replace_failed_step(step, result)
                
                # 如果步骤成功，根据结果调整后续步骤
                else:
                    steps = self._adjust_subsequent_steps(steps, i, result)
        
        adjusted_path["steps"] = steps
        adjusted_path["adjusted"] = True
        adjusted_path["adjustment_time"] = time.time()
        
        return adjusted_path
    
    def _replace_failed_step(self, step: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """替换失败的步骤"""
        # 备选工具映射
        alternatives = {
            "nikto": "whatweb",
            "sqlmap": "sqlmap"  # 无备选，继续使用
        }
        
        alternative_tool = alternatives.get(step.get("tool"), step.get("tool"))
        
        return {
            "step": step.get("step"),
            "action": step.get("action"),
            "tool": alternative_tool,
            "description": f"{step.get('description')} (备选工具)"
        }
    
    def _adjust_subsequent_steps(self, steps: List[Dict[str, Any]], current_step: int, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """调整后续步骤"""
        # 根据当前步骤的结果调整后续步骤
        # 这里可以添加更复杂的逻辑，例如根据发现的漏洞调整后续攻击策略
        return steps
