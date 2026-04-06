"""
数据服务模块
用户管理、项目管理、结果存储和实验数据管理
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
import logging

from .. import BaseModule, ModuleConfig

logger = logging.getLogger(__name__)


class DataServiceConfig(BaseModel):
    """数据服务配置"""
    database_url: str = "sqlite:///./data/databases/clawai.db"
    enabled: bool = True
    create_tables: bool = True
    pool_size: int = 5


# Pydantic模型
class UserCreate(BaseModel):
    """用户创建请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: Optional[str] = None
    created_at: datetime
    is_active: bool = True


class ProjectCreate(BaseModel):
    """项目创建请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    target_url: Optional[str] = None


class ProjectResponse(BaseModel):
    """项目响应"""
    id: int
    name: str
    description: Optional[str] = None
    target_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    owner_id: int


class ResultCreate(BaseModel):
    """结果创建请求"""
    project_id: int
    scan_type: str
    results: Dict[str, Any]
    status: str = "completed"


class ResultResponse(BaseModel):
    """结果响应"""
    id: int
    project_id: int
    scan_type: str
    results: Dict[str, Any]
    status: str
    created_at: datetime


class DataServiceModule(BaseModule):
    """数据服务模块"""

    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.data_config = DataServiceConfig(**config.config)
        self.db_engine = None
        self.SessionLocal = None
        self.Base = None

    def _setup_routes(self) -> None:
        """设置数据服务路由"""

        @self.router.get("/health")
        async def health_check():
            """数据服务健康检查"""
            return {
                "service": "data_service",
                "status": "healthy" if self._setup_complete else "unhealthy",
                "database_connected": self.db_engine is not None
            }

        @self.router.post("/users/register", response_model=UserResponse)
        async def register_user(user: UserCreate):
            """用户注册"""
            try:
                # 这里需要实际的数据库操作
                # 暂时返回模拟数据
                return UserResponse(
                    id=1,
                    username=user.username,
                    email=user.email,
                    created_at=datetime.now(),
                    is_active=True
                )
            except Exception as e:
                logger.error(f"用户注册失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"注册失败: {str(e)}"
                )

        @self.router.post("/users/login")
        async def login_user(login: UserLogin):
            """用户登录"""
            try:
                # 这里需要实际的认证逻辑
                # 暂时返回模拟令牌
                return {
                    "access_token": "mock_jwt_token",
                    "token_type": "bearer",
                    "username": login.username
                }
            except Exception as e:
                logger.error(f"用户登录失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误"
                )

        @self.router.post("/projects", response_model=ProjectResponse)
        async def create_project(project: ProjectCreate, current_user: Dict = Depends(lambda: {"id": 1, "username": "admin"})):
            """创建项目"""
            try:
                # 这里需要实际的数据库操作
                now = datetime.now()
                return ProjectResponse(
                    id=1,
                    name=project.name,
                    description=project.description,
                    target_url=project.target_url,
                    created_at=now,
                    updated_at=now,
                    owner_id=current_user["id"]
                )
            except Exception as e:
                logger.error(f"创建项目失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"创建项目失败: {str(e)}"
                )

        @self.router.get("/projects/{project_id}", response_model=ProjectResponse)
        async def get_project(project_id: int):
            """获取项目详情"""
            try:
                # 这里需要实际的数据库查询
                # 暂时返回模拟数据
                return ProjectResponse(
                    id=project_id,
                    name="测试项目",
                    description="这是一个测试项目",
                    target_url="http://example.com",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    owner_id=1
                )
            except Exception as e:
                logger.error(f"获取项目失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"项目不存在: {project_id}"
                )

        @self.router.post("/results", response_model=ResultResponse)
        async def create_result(result: ResultCreate):
            """创建扫描结果"""
            try:
                # 这里需要实际的数据库操作
                return ResultResponse(
                    id=1,
                    project_id=result.project_id,
                    scan_type=result.scan_type,
                    results=result.results,
                    status=result.status,
                    created_at=datetime.now()
                )
            except Exception as e:
                logger.error(f"创建结果失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"创建结果失败: {str(e)}"
                )

        @self.router.post("/experiments")
        async def create_experiment(experiment: Dict[str, Any]):
            """创建实验记录"""
            try:
                # 这里需要实际的数据库操作
                return {
                    "experiment_id": 1,
                    "name": experiment.get("name", "未命名实验"),
                    "status": "created",
                    "created_at": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"创建实验失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"创建实验失败: {str(e)}"
                )

    def _initialize(self) -> None:
        """初始化数据服务模块"""
        logger.info(f"正在初始化数据服务模块: {self.name}")

        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy.ext.declarative import declarative_base

            self.db_engine = create_engine(
                self.data_config.database_url,
                connect_args={"check_same_thread": False}
                if "sqlite" in self.data_config.database_url
                else {},
                pool_size=self.data_config.pool_size
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.db_engine)
            self.Base = declarative_base()

            # 创建表（如果配置要求）
            if self.data_config.create_tables:
                self._create_tables()

            logger.info(f"数据库连接成功: {self.data_config.database_url}")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            self.db_engine = None
            self.SessionLocal = None
            self.Base = None

        logger.info(f"数据服务模块 {self.name} 初始化完成")

    def _create_tables(self) -> None:
        """创建数据库表"""
        if not self.Base or not self.db_engine:
            return

        try:
            # 定义数据模型
            from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON

            class User(self.Base):
                __tablename__ = "users"
                id = Column(Integer, primary_key=True, index=True)
                username = Column(String(50), unique=True, index=True)
                email = Column(String(100), nullable=True)
                password_hash = Column(String(128))
                created_at = Column(DateTime, default=datetime.now)
                is_active = Column(Boolean, default=True)

            class Project(self.Base):
                __tablename__ = "projects"
                id = Column(Integer, primary_key=True, index=True)
                name = Column(String(100))
                description = Column(Text, nullable=True)
                target_url = Column(String(500), nullable=True)
                created_at = Column(DateTime, default=datetime.now)
                updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
                owner_id = Column(Integer)

            class Result(self.Base):
                __tablename__ = "results"
                id = Column(Integer, primary_key=True, index=True)
                project_id = Column(Integer)
                scan_type = Column(String(50))
                results = Column(JSON)
                status = Column(String(20), default="completed")
                created_at = Column(DateTime, default=datetime.now)

            # 创建所有表
            self.Base.metadata.create_all(bind=self.db_engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")

    def _cleanup(self) -> None:
        """清理数据服务模块资源"""
        logger.info(f"正在清理数据服务模块: {self.name}")

        if self.db_engine:
            try:
                self.db_engine.dispose()
                logger.info("数据库连接已关闭")
            except Exception as e:
                logger.error(f"关闭数据库连接失败: {e}")

        logger.info(f"数据服务模块 {self.name} 清理完成")

    def get_db_session(self):
        """获取数据库会话（供其他模块使用）"""
        if not self.SessionLocal:
            raise RuntimeError("数据服务模块未初始化")

        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


# 模块工厂函数
def create_module(config: ModuleConfig) -> DataServiceModule:
    """创建数据服务模块实例"""
    return DataServiceModule(config)