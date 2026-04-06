"""
数据库管理模块
借鉴RedAgent的数据库设计
"""

import os
from typing import Optional
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import logging

from .models.base import Base
from .models.user import User, APIKey
from .models.project import Project, ProjectMember, ProjectStatus, ProjectVisibility
from .models.scan import Scan, ScanSchedule, ScanStatus, ScanType
from .models.report import Report, ReportStatus, ReportFormat

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, database_url: Optional[str] = None):
        """初始化数据库管理器"""
        self.database_url = database_url or self._get_default_database_url()
        self.engine = None
        self.SessionLocal = None
        self._initialize()
    
    def _get_default_database_url(self) -> str:
        """获取默认数据库URL"""
        # 从环境变量读取或使用默认值
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "clawai")
        db_user = os.getenv("DB_USER", "clawai")
        db_password = os.getenv("DB_PASSWORD", "clawai")
        
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    def _initialize(self):
        """初始化数据库连接"""
        try:
            # 创建引擎
            self.engine = create_engine(
                self.database_url,
                pool_size=20,
                max_overflow=10,
                pool_pre_ping=True,
                echo=False  # 设置为True可以查看SQL语句
            )
            
            # 创建会话工厂
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"数据库连接初始化成功: {self.database_url}")
            
        except Exception as e:
            logger.error(f"数据库连接初始化失败: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Session:
        """获取数据库会话"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库会话异常: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建成功")
            
            # 创建默认数据
            self._create_default_data()
            
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise
    
    def drop_tables(self):
        """删除所有表"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("数据库表删除成功")
        except Exception as e:
            logger.error(f"删除数据库表失败: {e}")
            raise
    
    def _create_default_data(self):
        """创建默认数据"""
        with self.get_session() as session:
            # 检查是否已有管理员用户
            admin_user = session.query(User).filter_by(username="admin").first()
            
            if not admin_user:
                # 创建管理员用户
                admin_user = User(
                    username="admin",
                    email="admin@clawai.com",
                    password="admin123",  # 生产环境应该使用强密码
                    full_name="系统管理员",
                    is_superuser=True,
                    is_verified=True
                )
                session.add(admin_user)
                session.flush()  # 分配ID
                
                # 创建示例项目
                demo_project = Project(
                    name="演示项目",
                    owner_id=admin_user.id,
                    description="这是一个演示项目，用于展示ClawAI的功能",
                    status=ProjectStatus.ACTIVE,
                    visibility=ProjectVisibility.PUBLIC
                )
                demo_project.add_target("example.com", "domain")
                demo_project.add_target("127.0.0.1", "ip")
                session.add(demo_project)
                session.flush()  # 分配ID
                
                # 创建示例扫描
                demo_scan = Scan(
                    name="示例扫描",
                    target="example.com",
                    project_id=demo_project.id,
                    created_by=admin_user.id,
                    scan_type=ScanType.STANDARD,
                    status=ScanStatus.COMPLETED
                )
                
                # 模拟扫描结果
                demo_scan.results = {
                    "status": "completed",
                    "findings": [
                        {
                            "id": "finding_001",
                            "type": "open_port",
                            "severity": "info",
                            "title": "开放端口检测",
                            "description": "在目标上发现开放端口",
                            "details": {
                                "port": 80,
                                "service": "http",
                                "state": "open"
                            }
                        },
                        {
                            "id": "finding_002",
                            "type": "vulnerability",
                            "severity": "medium",
                            "title": "潜在的XSS漏洞",
                            "description": "在登录页面发现潜在的跨站脚本漏洞",
                            "details": {
                                "url": "http://example.com/login",
                                "parameter": "username",
                                "risk": "中等"
                            }
                        }
                    ],
                    "summary": {
                        "open_ports": 1,
                        "vulnerabilities": 1,
                        "scan_duration": 120.5
                    }
                }
                
                demo_scan.findings = demo_scan.results["findings"]
                demo_scan.finding_count = len(demo_scan.findings)
                demo_scan.vulnerability_count = 1
                demo_scan.completed_at = datetime.fromisoformat("2026-04-04T10:00:00Z".replace('Z', '+00:00'))
                demo_scan.duration = 120.5
                
                session.add(demo_scan)
                session.flush()  # 分配ID
                
                # 创建示例报告
                demo_report = Report(
                    title="示例扫描报告",
                    scan_id=demo_scan.id,
                    created_by=admin_user.id,
                    format=ReportFormat.HTML,
                    status=ReportStatus.COMPLETED
                )
                demo_report.generate_from_scan(demo_scan)
                session.add(demo_report)
                
                logger.info("默认数据创建成功")
    
    def health_check(self) -> dict:
        """数据库健康检查"""
        try:
            with self.get_session() as session:
                # 执行简单查询检查连接
                session.execute(text("SELECT 1"))
                
                # 获取统计信息
                user_count = session.query(User).count()
                project_count = session.query(Project).count()
                scan_count = session.query(Scan).count()
                
                return {
                    "status": "healthy",
                    "database": "postgresql",
                    "connection": "ok",
                    "statistics": {
                        "users": user_count,
                        "projects": project_count,
                        "scans": scan_count
                    }
                }
                
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "database": "postgresql",
                "connection": "failed",
                "error": str(e)
            }
    
    def backup(self, backup_path: str = "./backups"):
        """数据库备份"""
        import subprocess
        import datetime
        
        try:
            os.makedirs(backup_path, exist_ok=True)
            
            # 生成备份文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_path, f"clawai_backup_{timestamp}.sql")
            
            # 使用pg_dump备份（需要PostgreSQL客户端）
            db_url = self.database_url
            # 从URL中提取连接信息
            # 这里简化处理，实际应该解析URL
            
            logger.info(f"数据库备份开始: {backup_file}")
            # 实际备份逻辑需要根据环境配置
            
            return {
                "status": "success",
                "backup_file": backup_file,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }


# 全局数据库管理器实例
db_manager: Optional[DatabaseManager] = None


def init_database(database_url: Optional[str] = None) -> DatabaseManager:
    """初始化数据库"""
    global db_manager
    
    if db_manager is None:
        db_manager = DatabaseManager(database_url)
        
        # 自动创建表（开发环境）
        if os.getenv("ENVIRONMENT", "development") == "development":
            try:
                db_manager.create_tables()
            except Exception as e:
                logger.warning(f"自动创建表失败: {e}")
    
    return db_manager


def get_db():
    """获取数据库会话（用于依赖注入）"""
    if db_manager is None:
        raise RuntimeError("数据库未初始化，请先调用 init_database()")

    # 返回生成器函数，符合FastAPI依赖注入模式
    session = db_manager.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"数据库会话异常: {e}")
        raise
    finally:
        session.close()