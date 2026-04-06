# -*- coding: utf-8 -*-
"""
数据库模块初始化
提供数据库连接和模型定义
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class Database:
    """SQLite数据库管理类"""
    
    def __init__(self, db_path: str = "clawai_workflows.db"):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
    
    def connect(self) -> sqlite3.Connection:
        """建立数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            # 启用JSON支持
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def init_database(self):
        """初始化数据库表"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # 创建workflows表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflows (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            version VARCHAR(20) NOT NULL,
            description TEXT,
            definition TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 创建workflow_executions表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_executions (
            id VARCHAR(50) PRIMARY KEY,
            workflow_id VARCHAR(50) NOT NULL,
            target VARCHAR(255) NOT NULL,
            status VARCHAR(20) NOT NULL,
            progress INTEGER DEFAULT 0,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            result TEXT,
            created_by VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (workflow_id) REFERENCES workflows(id)
        )
        """)
        
        # 创建tasks表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id VARCHAR(50) PRIMARY KEY,
            execution_id VARCHAR(50) NOT NULL,
            step_id VARCHAR(50) NOT NULL,
            tool_name VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL,
            progress INTEGER DEFAULT 0,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            result TEXT,
            logs TEXT,
            error_message TEXT,
            FOREIGN KEY (execution_id) REFERENCES workflow_executions(id)
        )
        """)
        
        conn.commit()
        print("数据库表创建完成")
    
    def insert_workflow(self, workflow_data: Dict[str, Any]) -> str:
        """
        插入工作流模板
        
        Args:
            workflow_data: 工作流数据
            
        Returns:
            工作流ID
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        workflow_id = workflow_data.get("id")
        if not workflow_id:
            raise ValueError("工作流ID不能为空")
        
        cursor.execute("""
        INSERT INTO workflows (id, name, version, description, definition)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            version = excluded.version,
            description = excluded.description,
            definition = excluded.definition,
            updated_at = CURRENT_TIMESTAMP
        """, (
            workflow_id,
            workflow_data.get("name", ""),
            workflow_data.get("version", "1.0"),
            workflow_data.get("description", ""),
            json.dumps(workflow_data.get("definition", {}))
        ))
        
        conn.commit()
        return workflow_id
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流模板
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流数据或None
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id, name, version, description, definition, created_at, updated_at
        FROM workflows
        WHERE id = ?
        """, (workflow_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            "id": row["id"],
            "name": row["name"],
            "version": row["version"],
            "description": row["description"],
            "definition": json.loads(row["definition"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """
        获取所有工作流模板列表
        
        Returns:
            工作流列表
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id, name, version, description, created_at, updated_at
        FROM workflows
        ORDER BY updated_at DESC
        """)
        
        workflows = []
        for row in cursor.fetchall():
            workflows.append({
                "id": row["id"],
                "name": row["name"],
                "version": row["version"],
                "description": row["description"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        
        return workflows
    
    def insert_execution(self, execution_data: Dict[str, Any]) -> str:
        """
        插入工作流执行记录
        
        Args:
            execution_data: 执行数据
            
        Returns:
            执行ID
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        execution_id = execution_data.get("id")
        if not execution_id:
            raise ValueError("执行ID不能为空")
        
        cursor.execute("""
        INSERT INTO workflow_executions 
        (id, workflow_id, target, status, progress, started_at, completed_at, result, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execution_id,
            execution_data.get("workflow_id"),
            execution_data.get("target"),
            execution_data.get("status", "pending"),
            execution_data.get("progress", 0),
            execution_data.get("started_at"),
            execution_data.get("completed_at"),
            json.dumps(execution_data.get("result", {})),
            execution_data.get("created_by")
        ))
        
        conn.commit()
        return execution_id
    
    def update_execution(self, execution_id: str, updates: Dict[str, Any]):
        """
        更新工作流执行记录
        
        Args:
            execution_id: 执行ID
            updates: 更新字段
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # 构建更新语句
        update_fields = []
        update_values = []
        
        if "status" in updates:
            update_fields.append("status = ?")
            update_values.append(updates["status"])
        
        if "progress" in updates:
            update_fields.append("progress = ?")
            update_values.append(updates["progress"])
        
        if "started_at" in updates:
            update_fields.append("started_at = ?")
            update_values.append(updates["started_at"])
        
        if "completed_at" in updates:
            update_fields.append("completed_at = ?")
            update_values.append(updates["completed_at"])
        
        if "result" in updates:
            update_fields.append("result = ?")
            update_values.append(json.dumps(updates["result"]))
        
        if not update_fields:
            return
        
        update_values.append(execution_id)
        
        sql = f"""
        UPDATE workflow_executions
        SET {', '.join(update_fields)}
        WHERE id = ?
        """
        
        cursor.execute(sql, tuple(update_values))
        conn.commit()
    
    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流执行记录
        
        Args:
            execution_id: 执行ID
            
        Returns:
            执行数据或None
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id, workflow_id, target, status, progress, started_at, completed_at, result, created_by, created_at
        FROM workflow_executions
        WHERE id = ?
        """, (execution_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        result = row["result"]
        if result:
            result = json.loads(result)
        
        return {
            "id": row["id"],
            "workflow_id": row["workflow_id"],
            "target": row["target"],
            "status": row["status"],
            "progress": row["progress"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "result": result,
            "created_by": row["created_by"],
            "created_at": row["created_at"]
        }
    
    def list_executions(
        self, 
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取执行记录列表
        
        Args:
            workflow_id: 工作流ID过滤
            status: 状态过滤
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            执行记录列表
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        where_clauses = []
        params = []
        
        if workflow_id:
            where_clauses.append("workflow_id = ?")
            params.append(workflow_id)
        
        if status:
            where_clauses.append("status = ?")
            params.append(status)
        
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)
        
        sql = f"""
        SELECT id, workflow_id, target, status, progress, started_at, completed_at, created_by, created_at
        FROM workflow_executions
        {where_sql}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        cursor.execute(sql, tuple(params))
        
        executions = []
        for row in cursor.fetchall():
            executions.append({
                "id": row["id"],
                "workflow_id": row["workflow_id"],
                "target": row["target"],
                "status": row["status"],
                "progress": row["progress"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "created_by": row["created_by"],
                "created_at": row["created_at"]
            })
        
        return executions
    
    def insert_task(self, task_data: Dict[str, Any]) -> str:
        """
        插入任务记录
        
        Args:
            task_data: 任务数据
            
        Returns:
            任务ID
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        task_id = task_data.get("id")
        if not task_id:
            raise ValueError("任务ID不能为空")
        
        cursor.execute("""
        INSERT INTO tasks 
        (id, execution_id, step_id, tool_name, status, progress, started_at, completed_at, result, logs, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id,
            task_data.get("execution_id"),
            task_data.get("step_id"),
            task_data.get("tool_name"),
            task_data.get("status", "pending"),
            task_data.get("progress", 0),
            task_data.get("started_at"),
            task_data.get("completed_at"),
            json.dumps(task_data.get("result", {})),
            task_data.get("logs", ""),
            task_data.get("error_message")
        ))
        
        conn.commit()
        return task_id
    
    def update_task(self, task_id: str, updates: Dict[str, Any]):
        """
        更新任务记录
        
        Args:
            task_id: 任务ID
            updates: 更新字段
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # 构建更新语句
        update_fields = []
        update_values = []
        
        if "status" in updates:
            update_fields.append("status = ?")
            update_values.append(updates["status"])
        
        if "progress" in updates:
            update_fields.append("progress = ?")
            update_values.append(updates["progress"])
        
        if "started_at" in updates:
            update_fields.append("started_at = ?")
            update_values.append(updates["started_at"])
        
        if "completed_at" in updates:
            update_fields.append("completed_at = ?")
            update_values.append(updates["completed_at"])
        
        if "result" in updates:
            update_fields.append("result = ?")
            update_values.append(json.dumps(updates["result"]))
        
        if "logs" in updates:
            update_fields.append("logs = ?")
            update_values.append(updates["logs"])
        
        if "error_message" in updates:
            update_fields.append("error_message = ?")
            update_values.append(updates["error_message"])
        
        if not update_fields:
            return
        
        update_values.append(task_id)
        
        sql = f"""
        UPDATE tasks
        SET {', '.join(update_fields)}
        WHERE id = ?
        """
        
        cursor.execute(sql, tuple(update_values))
        conn.commit()
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务记录
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务数据或None
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id, execution_id, step_id, tool_name, status, progress, started_at, completed_at, result, logs, error_message
        FROM tasks
        WHERE id = ?
        """, (task_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        result = row["result"]
        if result:
            result = json.loads(result)
        
        return {
            "id": row["id"],
            "execution_id": row["execution_id"],
            "step_id": row["step_id"],
            "tool_name": row["tool_name"],
            "status": row["status"],
            "progress": row["progress"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "result": result,
            "logs": row["logs"],
            "error_message": row["error_message"]
        }
    
    def get_execution_tasks(self, execution_id: str) -> List[Dict[str, Any]]:
        """
        获取执行的所有任务
        
        Args:
            execution_id: 执行ID
            
        Returns:
            任务列表
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id, step_id, tool_name, status, progress, started_at, completed_at
        FROM tasks
        WHERE execution_id = ?
        ORDER BY step_id
        """, (execution_id,))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                "id": row["id"],
                "step_id": row["step_id"],
                "tool_name": row["tool_name"],
                "status": row["status"],
                "progress": row["progress"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"]
            })
        
        return tasks


# 全局数据库实例
db_instance = None


def get_database() -> Database:
    """
    获取数据库实例（单例模式）
    
    Returns:
        Database实例
    """
    global db_instance
    if db_instance is None:
        db_instance = Database()
        db_instance.init_database()
    return db_instance