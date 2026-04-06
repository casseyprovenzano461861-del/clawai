"""
Pydantic 基础模型
提供所有Pydantic模型的基类和通用功能
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, validator


class BaseSchema(BaseModel):
    """基础模式类，所有Pydantic模型的基类"""

    model_config = ConfigDict(
        from_attributes=True,  # 允许从ORM对象创建
        populate_by_name=True,  # 允许使用别名
        arbitrary_types_allowed=True,  # 允许任意类型
        validate_assignment=True,  # 赋值时验证
    )

    def model_dump_jsonable(self) -> Dict[str, Any]:
        """转换为可JSON序列化的字典"""
        return self.model_dump(mode="json")


class TimestampMixin(BaseModel):
    """时间戳混入类"""
    created_at: Optional[datetime] = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(default_factory=datetime.now, description="更新时间")


class IDMixin(BaseModel):
    """ID混入类"""
    id: Optional[int] = Field(default=None, description="唯一标识符")


class PaginationParams(BaseSchema):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小，最大100")

    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """计算限制"""
        return self.page_size


class PaginatedResponse(BaseSchema):
    """分页响应"""
    items: List[Any] = Field(default_factory=list, description="数据项列表")
    total: int = Field(default=0, description="总数量")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页大小")
    total_pages: int = Field(default=0, description="总页数")

    @classmethod
    def create(
        cls,
        items: List[Any],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse":
        """创建分页响应"""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )