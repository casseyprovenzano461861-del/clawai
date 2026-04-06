# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
SQLInjectionSkill - SQL注入检测和利用技能

功能：
1. SQL注入点检测
2. 数据库信息提取
3. 数据窃取
"""

import random
import time
from typing import Dict, List, Any
from .base_skill import BaseSkill


class SQLInjectionSkill(BaseSkill):
    """SQL注入检测和利用技能"""
    
    def get_name(self) -> str:
        return "SQLInjectionSkill"
    
    def get_description(self) -> str:
        return "使用SQLMap检测和利用SQL注入漏洞"
    
    def get_category(self) -> str:
        return "exploitation"
    
    def get_difficulty(self) -> str:
        return "hard"
    
    def get_required_tools(self) -> List[str]:
        return ["sqlmap"]
    
    def get_prerequisites(self) -> List[str]:
        return ["NmapScanSkill", "WhatWebSkill"]  # 需要先进行端口扫描和Web指纹识别
    
    def get_success_rate(self) -> float:
        """获取技能成功率"""
        return 0.70  # SQL注入成功率中等
    
    def get_estimated_time(self) -> str:
        """获取预估执行时间"""
        return "10-20分钟"
    
    def can_handle(self, context: Dict[str, Any]) -> bool:
        """
        判断是否能处理当前上下文
        
        条件：
        1. 有目标地址
        2. 目标有Web服务
        3. 有数据库相关服务或疑似SQL注入点
        4. 尚未进行SQL注入检测或需要深度检测
        """
        if not context:
            return False
        
        target = context.get("target", "")
        if not target:
            return False
        
        # 检查是否有Web服务
        has_web_service = False
        scan_results = context.get("scan_results", {})
        current_state = context.get("current_state", {})
        
        # 检查Web服务
        if "web_technologies" in current_state:
            has_web_service = True
        elif "whatweb" in scan_results:
            has_web_service = True
        else:
            # 检查端口
            if "open_ports" in current_state:
                for port_info in current_state["open_ports"]:
                    if isinstance(port_info, dict):
                        service = port_info.get("service", "").lower()
                        port = port_info.get("port", 0)
                        if service in ["http", "https", "www", "web"] or port in [80, 443, 8080, 8443]:
                            has_web_service = True
                            break
        
        if not has_web_service:
            return False
        
        # 检查是否有数据库服务或疑似注入点
        has_database_or_injection = False
        
        # 检查数据库端口
        if "open_ports" in current_state:
            for port_info in current_state["open_ports"]:
                if isinstance(port_info, dict):
                    service = port_info.get("service", "").lower()
                    if any(db in service for db in ["mysql", "postgresql", "mssql", "oracle", "mongodb"]):
                        has_database_or_injection = True
                        break
        
        # 检查扫描结果中的SQL注入漏洞
        if "nuclei" in scan_results:
            nuclei_data = scan_results["nuclei"]
            if isinstance(nuclei_data, dict) and "vulnerabilities" in nuclei_data:
                for vuln in nuclei_data["vulnerabilities"]:
                    if isinstance(vuln, dict):
                        vuln_name = vuln.get("name", "").lower()
                        if "sql" in vuln_name or "injection" in vuln_name:
                            has_database_or_injection = True
                            break
        
        # 检查当前状态中的SQL注入
        if "sql_injections" in current_state:
            # 如果已有SQL注入信息，检查是否需要深度利用
            sql_injections = current_state["sql_injections"]
            if isinstance(sql_injections, list) and len(sql_injections) > 0:
                # 检查是否已进行深度利用
                for injection in sql_injections:
                    if isinstance(injection, dict) and injection.get("exploited", False):
                        # 已利用过，可能不需要再次利用
                        return False
                # 有注入点但未深度利用，可以处理
                return True
        
        # 检查是否有sqlmap扫描结果
        if "sqlmap" in scan_results:
            sqlmap_data = scan_results["sqlmap"]
            if isinstance(sqlmap_data, dict):
                # 如果已有详细的sqlmap结果，检查是否需要更新
                if "injections" in sqlmap_data:
                    injections = sqlmap_data["injections"]
                    if injections and len(injections) > 0:
                        # 已有注入点，检查是否已深度利用
                        for injection in injections:
                            if isinstance(injection, dict) and injection.get("exploited", False):
                                return False
                        # 有注入点但未深度利用
                        return True
        
        return has_database_or_injection
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行SQL注入检测和利用
        
        模拟执行，实际环境中应调用真实sqlmap命令
        """
        target = context.get("target", "")
        
        if not target:
            return {
                "success": False,
                "error": "缺少目标地址",
                "skill_name": self.name
            }
        
        try:
            # 模拟扫描过程
            self._simulate_scanning(target)
            
            # 生成模拟结果
            scan_result = self._generate_sqlmap_result(target, context)
            
            return {
                "success": True,
                "skill_name": self.name,
                "target": target,
                "sql_injections": scan_result["injections"],
                "database_info": scan_result["database_info"],
                "data_extracted": scan_result["data_extracted"],
                "scan_time": scan_result["scan_time"],
                "details": {
                    "command_used": f"sqlmap -u '{target}/login.php' --batch --level=3 --risk=2",
                    "parameters_tested": ["id", "username", "password", "search"],
                    "techniques_used": ["boolean-based blind", "time-based blind", "error-based"],
                    "payloads_generated": scan_result.get("payload_count", 15)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"SQL注入检测失败: {str(e)}",
                "skill_name": self.name,
                "target": target
            }
    
    def _simulate_scanning(self, target: str) -> None:
        """模拟扫描过程"""
        # SQL注入扫描通常较慢
        scan_time = random.uniform(5.0, 15.0)
        time.sleep(min(scan_time, 1.0))  # 实际等待时间缩短
    
    def _generate_sqlmap_result(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成模拟的SQLMap扫描结果"""
        
        # 从上下文获取技术栈信息
        tech_stack = {}
        current_state = context.get("current_state", {})
        
        if "web_technologies" in current_state:
            tech_stack = current_state["web_technologies"]
        
        # 确定数据库类型
        database_type = self._determine_database_type(tech_stack, context)
        
        # 生成注入点
        injections = self._generate_injection_points(target, database_type)
        
        # 生成数据库信息
        database_info = self._generate_database_info(database_type)
        
        # 生成提取的数据
        data_extracted = self._generate_extracted_data(database_type)
        
        return {
            "injections": injections,
            "database_info": database_info,
            "data_extracted": data_extracted,
            "payload_count": random.randint(10, 25),
            "scan_time": f"{random.uniform(4.5, 12.8):.1f} seconds"
        }
    
    def _determine_database_type(self, tech_stack: Dict[str, Any], context: Dict[str, Any]) -> str:
        """确定数据库类型"""
        
        # 从技术栈推断
        if tech_stack:
            server = tech_stack.get("server", [])
            language = tech_stack.get("language", [])
            
            # PHP通常搭配MySQL
            if any("php" in str(l).lower() for l in language):
                return "MySQL"
            
            # ASP.NET通常搭配SQL Server
            if any("asp" in str(l).lower() or ".net" in str(l).lower() for l in language):
                return "Microsoft SQL Server"
            
            # Java通常搭配MySQL或Oracle
            if any("java" in str(l).lower() for l in language):
                return random.choice(["MySQL", "Oracle"])
        
        # 从端口推断
        current_state = context.get("current_state", {})
        if "open_ports" in current_state:
            for port_info in current_state["open_ports"]:
                if isinstance(port_info, dict):
                    service = port_info.get("service", "").lower()
                    if "mysql" in service:
                        return "MySQL"
                    elif "postgresql" in service:
                        return "PostgreSQL"
                    elif "mssql" in service or "sql server" in service:
                        return "Microsoft SQL Server"
                    elif "oracle" in service:
                        return "Oracle"
        
        # 默认返回MySQL
        return "MySQL"
    
    def _generate_injection_points(self, target: str, db_type: str) -> List[Dict[str, Any]]:
        """生成注入点信息"""
        
        # 常见的注入参数
        parameters = ["id", "user_id", "product_id", "category", "search", 
                     "username", "email", "password", "token", "session"]
        
        # 选择1-3个参数作为注入点
        num_injections = random.randint(1, 3)
        selected_params = random.sample(parameters, num_injections)
        
        injections = []
        
        for param in selected_params:
            # 注入类型
            injection_types = ["boolean-based blind", "time-based blind", "error-based", "UNION query"]
            injection_type = random.choice(injection_types)
            
            # 严重程度
            severity = random.choice(["high", "critical"])
            
            # 是否可被利用
            exploitable = random.random() > 0.3  # 70%概率可被利用
            
            injection = {
                "parameter": param,
                "url": f"{target}/index.php?{param}=1",
                "type": injection_type,
                "severity": severity,
                "exploitable": exploitable,
                "database_type": db_type,
                "payload_example": self._generate_payload_example(param, injection_type, db_type)
            }
            
            if exploitable:
                injection["exploited"] = random.random() > 0.5  # 50%概率已利用
                if injection["exploited"]:
                    injection["exploitation_result"] = "成功获取数据库访问权限"
            
            injections.append(injection)
        
        return injections
    
    def _generate_payload_example(self, param: str, injection_type: str, db_type: str) -> str:
        """生成payload示例"""
        
        base_payloads = {
            "MySQL": {
                "boolean-based blind": f"1' AND '1'='1",
                "time-based blind": f"1' AND SLEEP(5)--",
                "error-based": f"1' AND EXTRACTVALUE(1,CONCAT(0x7e,(SELECT @@version),0x7e))--",
                "UNION query": f"1' UNION SELECT 1,2,3--"
            },
            "Microsoft SQL Server": {
                "boolean-based blind": f"1' AND '1'='1",
                "time-based blind": f"1'; WAITFOR DELAY '00:00:05'--",
                "error-based": f"1' AND 1=CONVERT(int,@@version)--",
                "UNION query": f"1' UNION SELECT 1,2,3--"
            },
            "PostgreSQL": {
                "boolean-based blind": f"1' AND '1'='1",
                "time-based blind": f"1' AND pg_sleep(5)--",
                "error-based": f"1' AND 1=CAST((SELECT version()) AS int)--",
                "UNION query": f"1' UNION SELECT 1,2,3--"
            }
        }
        
        db_payloads = base_payloads.get(db_type, base_payloads["MySQL"])
        return db_payloads.get(injection_type, f"1' OR '1'='1")
    
    def _generate_database_info(self, db_type: str) -> Dict[str, Any]:
        """生成数据库信息"""
        
        db_versions = {
            "MySQL": ["8.0.26", "5.7.35", "5.6.51"],
            "Microsoft SQL Server": ["2019", "2017", "2014"],
            "PostgreSQL": ["14.0", "13.4", "12.8"],
            "Oracle": ["19c", "18c", "12c"]
        }
        
        version = random.choice(db_versions.get(db_type, ["Unknown"]))
        
        return {
            "type": db_type,
            "version": version,
            "current_user": random.choice(["root", "admin", "sa", "postgres"]),
            "current_database": random.choice(["webapp", "maindb", "production", "test"]),
            "hostname": random.choice(["localhost", "db-server", f"db-{random.randint(1, 100)}"]),
            "tables_count": random.randint(5, 50),
            "is_dba": random.random() > 0.5  # 50%概率是DBA
        }
    
    def _generate_extracted_data(self, db_type: str) -> Dict[str, Any]:
        """生成提取的数据"""
        
        # 常见的表和数据
        tables = [
            {
                "name": "users",
                "columns": ["id", "username", "password_hash", "email", "created_at"],
                "row_count": random.randint(100, 10000),
                "sample_data": [
                    {"id": 1, "username": "admin", "email": "admin@example.com"},
                    {"id": 2, "username": "user1", "email": "user1@example.com"}
                ]
            },
            {
                "name": "products",
                "columns": ["id", "name", "price", "description", "category"],
                "row_count": random.randint(50, 5000),
                "sample_data": [
                    {"id": 1, "name": "Product A", "price": 99.99},
                    {"id": 2, "name": "Product B", "price": 149.99}
                ]
            },
            {
                "name": "orders",
                "columns": ["id", "user_id", "product_id", "quantity", "total", "order_date"],
                "row_count": random.randint(1000, 50000),
                "sample_data": [
                    {"id": 1, "user_id": 1, "total": 199.98},
                    {"id": 2, "user_id": 2, "total": 149.99}
                ]
            }
        ]
        
        # 选择1-2个表作为提取的数据
        num_tables = random.randint(1, 2)
        selected_tables = random.sample(tables, num_tables)
        
        # 敏感数据发现
        sensitive_data = []
        if random.random() > 0.4:  # 60%概率发现敏感数据
            sensitive_types = ["credit_card", "ssn", "password", "api_key", "personal_info"]
            for _ in range(random.randint(1, 3)):
                data_type = random.choice(sensitive_types)
                sensitive_data.append({
                    "type": data_type,
                    "table": random.choice(["users", "customers", "payments"]),
                    "column": random.choice(["credit_card_number", "ssn", "password", "api_key"]),
                    "count": random.randint(10, 1000)
                })
        
        return {
            "tables_extracted": selected_tables,
            "total_rows_extracted": sum(t["row_count"] for t in selected_tables),
            "sensitive_data_found": sensitive_data,
            "extraction_status": "部分数据提取完成" if len(selected_tables) < 3 else "完整数据提取完成"
        }
    
    def _extract_from_existing_scan(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        从现有扫描结果中提取SQL注入信息
        """
        if "sqlmap" not in scan_results:
            return {}
        
        sqlmap_data = scan_results["sqlmap"]
        if not isinstance(sqlmap_data, dict):
            return {}
        
        result = {
            "injections": [],
            "database_info": {},
            "data_extracted": {}
        }
        
        # 提取注入点
        if "injections" in sqlmap_data:
            result["injections"] = sqlmap_data["injections"]
        
        # 提取数据库信息
        if "database" in sqlmap_data:
            result["database_info"] = sqlmap_data["database"]
        
        # 提取数据
        if "data" in sqlmap_data:
            result["data_extracted"] = sqlmap_data["data"]
        
        return result