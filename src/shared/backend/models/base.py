"""
数据库基础模型
借鉴RedAgent的数据模型设计
"""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Column, DateTime, Integer, String, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class BaseModel(Base):
    """基础模型类"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        import datetime
        result = {}
        for column in self.__table__.columns:
            if column.name in ['is_deleted']:
                continue
            value = getattr(self, column.name)
            if isinstance(value, datetime.datetime):
                result[column.name] = value.isoformat()
            elif isinstance(value, datetime.date):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result
    
    def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.updated_at = datetime.utcnow()