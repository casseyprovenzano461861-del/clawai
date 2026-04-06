# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
生产数据库初始化脚本
用于初始化ClawAI生产环境的数据库
"""

import sqlite3
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path


def create_backup(db_path: str) -> str:
    """创建数据库备份"""
    if not os.path.exists(db_path):
        return ""
    
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"clawai_backup_{timestamp}.db"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"[成功] 数据库已备份到: {backup_path}")
        return str(backup_path)
    except Exception as e:
        print(f"[警告]  备份失败: {e}")
        return ""


def init_production_database():
    """初始化生产数据库"""
    db_path = "clawai_production.db"
    
    print("🚀 开始初始化生产数据库")
    print("=" * 60)
    
    # 创建备份（如果存在）
    backup_path = ""
    if os.path.exists(db_path):
        print(f"发现现有数据库: {db_path}")
        backup_path = create_backup(db_path)
    
    # 创建新数据库
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n[统计] 创建数据库表...")
        
        # 1. 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            mfa_secret TEXT,
            mfa_enabled BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            failed_login_attempts INTEGER DEFAULT 0,
            account_locked_until TIMESTAMP,
            last_password_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            password_history TEXT DEFAULT '[]'  -- JSON格式存储最近5次密码哈希
        )
        ''')
        print("  [成功] 用户表创建完成")
        
        # 2. 创建审计日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            action TEXT NOT NULL,
            resource TEXT,
            ip_address TEXT,
            user_agent TEXT,
            details TEXT,
            severity TEXT CHECK(severity IN ('low', 'medium', 'high', 'critical')),
            status TEXT CHECK(status IN ('success', 'failure', 'warning')),
            session_id TEXT,
            request_id TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        )
        ''')
        print("  [成功] 审计日志表创建完成")
        
        # 3. 创建扫描结果表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id TEXT UNIQUE NOT NULL,
            target TEXT NOT NULL,
            scan_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
            results TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            user_id INTEGER,
            duration_seconds REAL,
            error_message TEXT,
            metadata TEXT DEFAULT '{}',  -- JSON格式的元数据
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        )
        ''')
        print("  [成功] 扫描结果表创建完成")
        
        # 4. 创建漏洞表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vulnerabilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cve_id TEXT,
            name TEXT NOT NULL,
            description TEXT,
            severity TEXT CHECK(severity IN ('low', 'medium', 'high', 'critical')),
            cvss_score REAL,
            affected_components TEXT,  -- JSON格式
            detection_method TEXT,
            remediation TEXT,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scan_id TEXT,
            target TEXT,
            status TEXT DEFAULT 'open' CHECK(status IN ('open', 'in_progress', 'resolved', 'false_positive')),
            assigned_to INTEGER,
            due_date TIMESTAMP,
            FOREIGN KEY (scan_id) REFERENCES scan_results (scan_id) ON DELETE CASCADE,
            FOREIGN KEY (assigned_to) REFERENCES users (id) ON DELETE SET NULL
        )
        ''')
        print("  [成功] 漏洞表创建完成")
        
        # 5. 创建API密钥表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_hash TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            scopes TEXT DEFAULT '[]',  -- JSON格式的权限范围
            rate_limit_per_minute INTEGER DEFAULT 60,
            rate_limit_per_hour INTEGER DEFAULT 1000,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            last_used_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            usage_count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        ''')
        print("  [成功] API密钥表创建完成")
        
        # 6. 创建会话表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_valid BOOLEAN DEFAULT 1,
            invalidated_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        ''')
        print("  [成功] 会话表创建完成")
        
        # 7. 创建工作流表（与现有系统兼容）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflows (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            definition TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            is_active BOOLEAN DEFAULT 1,
            version INTEGER DEFAULT 1,
            FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL
        )
        ''')
        print("  [成功] 工作流表创建完成")
        
        # 8. 创建工作流执行表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflow_executions (
            id VARCHAR(50) PRIMARY KEY,
            workflow_id VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            progress INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            result TEXT,
            error_message TEXT,
            user_id INTEGER,
            metadata TEXT DEFAULT '{}',
            FOREIGN KEY (workflow_id) REFERENCES workflows (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        )
        ''')
        print("  [成功] 工作流执行表创建完成")
        
        # 9. 创建任务表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id VARCHAR(50) PRIMARY KEY,
            execution_id VARCHAR(50) NOT NULL,
            name VARCHAR(255) NOT NULL,
            type VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            progress INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            result TEXT,
            error_message TEXT,
            tool_name VARCHAR(100),
            parameters TEXT,
            FOREIGN KEY (execution_id) REFERENCES workflow_executions (id) ON DELETE CASCADE
        )
        ''')
        print("  [成功] 任务表创建完成")
        
        # 10. 创建工具统计表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tool_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_name VARCHAR(100) NOT NULL,
            execution_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            total_duration REAL DEFAULT 0,
            avg_duration REAL DEFAULT 0,
            last_executed_at TIMESTAMP,
            last_error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print("  [成功] 工具统计表创建完成")
        
        # 创建索引以提高查询性能
        print("\n[图表] 创建数据库索引...")
        
        indexes = [
            # 用户表索引
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
            
            # 审计日志表索引
            "CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)",
            "CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_logs(severity)",
            
            # 扫描结果表索引
            "CREATE INDEX IF NOT EXISTS idx_scan_user_id ON scan_results(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_scan_status ON scan_results(status)",
            "CREATE INDEX IF NOT EXISTS idx_scan_created_at ON scan_results(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_scan_target ON scan_results(target)",
            
            # 漏洞表索引
            "CREATE INDEX IF NOT EXISTS idx_vuln_severity ON vulnerabilities(severity)",
            "CREATE INDEX IF NOT EXISTS idx_vuln_status ON vulnerabilities(status)",
            "CREATE INDEX IF NOT EXISTS idx_vuln_scan_id ON vulnerabilities(scan_id)",
            "CREATE INDEX IF NOT EXISTS idx_vuln_cve_id ON vulnerabilities(cve_id)",
            
            # 工作流相关索引
            "CREATE INDEX IF NOT EXISTS idx_workflow_exec_status ON workflow_executions(status)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_exec_user ON workflow_executions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_execution_id ON tasks(execution_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
            
            # 会话表索引
            "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)",
        ]
        
        for idx_sql in indexes:
            try:
                cursor.execute(idx_sql)
            except Exception as e:
                print(f"  [警告]  创建索引失败: {e}")
        
        print("  [成功] 数据库索引创建完成")
        
        # 创建默认管理员账户（需要在首次登录后修改密码）
        print("\n👤 创建默认管理员账户...")
        cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash, role, is_active)
        VALUES (?, ?, ?, ?, ?)
        ''', ('admin', 'admin@clawai.local', 'CHANGE_ON_FIRST_LOGIN', 'admin', 1))
        
        if cursor.rowcount > 0:
            print("  [成功] 默认管理员账户已创建")
            print("  [警告]  重要：首次登录后必须修改密码！")
        else:
            print("  ℹ️  管理员账户已存在，跳过创建")
        
        # 创建默认API密钥（用于系统集成）
        print("\n🔑 创建系统API密钥...")
        import hashlib
        import secrets
        
        system_api_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(system_api_key.encode()).hexdigest()
        
        cursor.execute('''
        INSERT OR IGNORE INTO api_keys (key_hash, name, user_id, scopes, is_active)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            key_hash,
            'System Integration Key',
            1,  # 假设管理员ID为1
            '["system:*", "scan:*", "report:*"]',
            1
        ))
        
        if cursor.rowcount > 0:
            print(f"  [成功] 系统API密钥已创建: {system_api_key}")
            print("  [警告]  请妥善保管此密钥，它将只显示一次！")
            
            # 保存API密钥到安全文件
            secrets_dir = Path("secrets")
            secrets_dir.mkdir(exist_ok=True)
            
            api_key_file = secrets_dir / "system_api_key.txt"
            with open(api_key_file, 'w', encoding='utf-8') as f:
                f.write(f"System API Key: {system_api_key}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("Scopes: system:*, scan:*, report:*\n")
                f.write("[警告]  Warning: Keep this file secure!\n")
            
            print(f"  💾 API密钥已保存到: {api_key_file}")
        else:
            print("  ℹ️  系统API密钥已存在，跳过创建")
        
        # 提交所有更改
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 60)
        print(f"[庆祝] 生产数据库初始化完成！")
        print(f"📁 数据库文件: {db_path}")
        if backup_path:
            print(f"[文件] 备份文件: {backup_path}")
        print(f"👤 管理员账户: admin / CHANGE_ON_FIRST_LOGIN")
        print("\n[列表] 下一步：")
        print("  1. 首次登录后立即修改管理员密码")
        print("  2. 配置 .env.production 中的数据库路径")
        print("  3. 运行数据库迁移测试")
        print("  4. 验证所有功能正常工作")
        
        return True
        
    except Exception as e:
        print(f"[失败] 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_database_integrity():
    """验证数据库完整性"""
    db_path = "clawai_production.db"
    
    if not os.path.exists(db_path):
        print(f"[失败] 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n[搜索] 验证数据库完整性...")
        
        # 检查所有表是否存在
        tables = [
            'users', 'audit_logs', 'scan_results', 'vulnerabilities',
            'api_keys', 'sessions', 'workflows', 'workflow_executions',
            'tasks', 'tool_statistics'
        ]
        
        missing_tables = []
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                missing_tables.append(table)
        
        if missing_tables:
            print(f"  [警告]  缺少表: {', '.join(missing_tables)}")
        else:
            print("  [成功] 所有表都存在")
        
        # 检查表结构
        print("\n[统计] 检查表结构...")
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [col[1] for col in cursor.fetchall()]
        required_columns = ['username', 'email', 'password_hash', 'role']
        
        for col in required_columns:
            if col in user_columns:
                print(f"  [成功] 用户表包含 {col} 列")
            else:
                print(f"  [失败] 用户表缺少 {col} 列")
        
        # 检查数据完整性
        print("\n[图表] 检查数据完整性...")
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count > 0:
            print(f"  [成功] 找到 {admin_count} 个管理员账户")
        else:
            print("  [警告]  未找到管理员账户")
        
        # 检查索引
        print("\n📑 检查数据库索引...")
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
        index_count = cursor.fetchone()[0]
        print(f"  [成功] 找到 {index_count} 个索引")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("[成功] 数据库完整性验证完成")
        return True
        
    except Exception as e:
        print(f"[失败] 数据库验证失败: {e}")
        return False


def main():
    """主函数"""
    print("🔧 ClawAI 生产数据库初始化工具")
    print("=" * 60)
    
    import argparse
    parser = argparse.ArgumentParser(description='ClawAI生产数据库管理')
    parser.add_argument('--init', action='store_true', help='初始化生产数据库')
    parser.add_argument('--verify', action='store_true', help='验证数据库完整性')
    parser.add_argument('--backup', action='store_true', help='创建数据库备份')
    parser.add_argument('--restore', type=str, help='从备份文件恢复数据库')
    parser.add_argument('--db-path', type=str, default='clawai_production.db', help='数据库文件路径')
    
    args = parser.parse_args()
    
    try:
        success = True
        
        if args.init:
            success = init_production_database() and success
        
        if args.verify:
            success = verify_database_integrity() and success
        
        if args.backup:
            backup_path = create_backup(args.db_path)
            if backup_path:
                print(f"[成功] 备份创建成功: {backup_path}")
                success = True
            else:
                print(f"[失败] 备份创建失败")
                success = False
        
        if args.restore:
            if os.path.exists(args.restore):
                try:
                    shutil.copy2(args.restore, args.db_path)
                    print(f"[成功] 数据库已从 {args.restore} 恢复")
                    success = True
                except Exception as e:
                    print(f"[失败] 恢复失败: {e}")
                    success = False
            else:
                print(f"[失败] 备份文件不存在: {args.restore}")
                success = False
        
        if not any([args.init, args.verify, args.backup, args.restore]):
            # 默认执行初始化和验证
            success = init_production_database() and verify_database_integrity()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"[失败] 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())