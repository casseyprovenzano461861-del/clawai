# -*- coding: utf-8 -*-
"""
FastAPI报告管理API端点
基于现有报告生成器和Report模型的完整报告系统
"""

import os
import uuid
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
import logging

from backend.database import get_db
from backend.models.report import Report, ReportStatus, ReportFormat
from backend.auth.fastapi_permissions import require_authentication, get_current_user
from backend.schemas.error import APIError, ErrorCode
# 尝试导入真实报告生成器
try:
    from backend.report.penetration_report_generator import PenetrationReportGenerator
    REPORT_GENERATOR_AVAILABLE = True
except ImportError:
    try:
        from src.shared.backend.report.penetration_report_generator import PenetrationReportGenerator
        REPORT_GENERATOR_AVAILABLE = True
    except ImportError:
        REPORT_GENERATOR_AVAILABLE = False
        PenetrationReportGenerator = None  # type: ignore

from backend.schemas.base import BaseSchema
from pydantic import Field, validator

# 创建路由器
router = APIRouter(prefix="/api/v1/reports", tags=["报告管理"])

logger = logging.getLogger(__name__)

# Pydantic模型
class ReportCreate(BaseSchema):
    """创建报告请求"""
    title: str = Field(..., min_length=1, max_length=200, description="报告标题")
    description: Optional[str] = Field(None, description="报告描述")
    format: ReportFormat = Field(default=ReportFormat.HTML, description="报告格式。支持: html（网页）、pdf（PDF，需安装 weasyprint）、markdown（Markdown 文本）、json（原始数据）")
    template: str = Field(default="standard", description="报告模板")
    target: Optional[str] = Field(None, description="目标地址或范围")
    scan_id: Optional[int] = Field(None, description="关联的扫描ID")
    project_id: Optional[str] = Field(None, description="关联的项目ID")
    # 报告元信息字段
    tester_name: Optional[str] = Field(None, description="测试人员姓名")
    client_name: Optional[str] = Field(None, description="委托方/客户名称")
    test_start_date: Optional[str] = Field(None, description="测试开始日期，如 2026-04-01")
    test_end_date: Optional[str] = Field(None, description="测试结束日期，如 2026-04-11")
    disclaimer: Optional[str] = Field(None, description="免责声明（留空使用默认声明）")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="生成参数")

class ReportUpdate(BaseSchema):
    """更新报告请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="报告标题")
    description: Optional[str] = Field(None, description="报告描述")
    status: Optional[ReportStatus] = Field(None, description="报告状态")

class ReportResponse(BaseSchema):
    """报告响应"""
    id: int
    title: str
    description: Optional[str]
    status: ReportStatus
    format: ReportFormat
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]
    download_url: Optional[str]
    file_size: Optional[int]
    report_metadata: Dict[str, Any]

    class Config:
        from_attributes = True

class ReportListResponse(BaseSchema):
    """报告列表响应"""
    reports: List[ReportResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# 报告生成器实例
report_generator = PenetrationReportGenerator() if REPORT_GENERATOR_AVAILABLE else None

# ── 内存降级存储（数据库不可用时使用）────────────────────────────
_mem_reports: Dict[int, Dict[str, Any]] = {}
_mem_report_id = 1

def _new_mem_id() -> int:
    global _mem_report_id
    mid = _mem_report_id
    _mem_report_id += 1
    return mid

def _db_ok(db) -> bool:
    """检查数据库连接是否可用"""
    try:
        db.execute("SELECT 1")
        return True
    except Exception:
        return False

@router.post("/generate")  # response_model 不强制，兼容内存降级
async def generate_report(
    background_tasks: BackgroundTasks,
    report_data: ReportCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """
    生成新报告

    创建报告记录并异步生成报告内容。数据库不可用时使用内存存储。
    """
    try:
        # 尝试数据库存储
        report = Report(
            title=report_data.title,
            description=report_data.description,
            format=report_data.format,
            status=ReportStatus.GENERATING,
            created_by=current_user.get('user_id'),
            report_metadata={
                "template": report_data.template,
                "target": report_data.target,
                "scan_id": report_data.scan_id,
                "project_id": report_data.project_id,
                "tester_name": report_data.tester_name,
                "client_name": report_data.client_name,
                "test_start_date": report_data.test_start_date,
                "test_end_date": report_data.test_end_date,
                "parameters": report_data.parameters,
                "generator": "penetration_report_generator",
                "supported_formats": ["html", "pdf", "markdown", "json"],
            }
        )

        db.add(report)
        db.commit()
        db.refresh(report)

        # 在后台生成报告内容
        background_tasks.add_task(
            generate_report_content,
            report.id,
            report_data,
            current_user,
            db
        )

        return report

    except Exception as e:
        logger.warning(f"数据库不可用，使用内存存储生成报告: {e}")
        # 内存降级
        now = datetime.utcnow().isoformat() + "Z"
        mid = _new_mem_id()
        mem_report = {
            "id": mid,
            "title": report_data.title,
            "description": report_data.description or "",
            "format": report_data.format.value if hasattr(report_data.format, 'value') else str(report_data.format),
            "status": "generating",
            "created_by": current_user.get('user_id', 'anonymous'),
            "created_at": now,
            "updated_at": now,
            "finding_count": 0,
            "vulnerability_count": 0,
            "file_path": None,
            "rendered_content": None,
            "content": None,
            "report_metadata": {
                "template": report_data.template,
                "target": report_data.target,
            },
        }
        _mem_reports[mid] = mem_report

        # 后台生成内容
        background_tasks.add_task(
            _generate_mem_report_content,
            mid,
            report_data,
        )
        return mem_report


async def _generate_mem_report_content(report_id: int, report_data: ReportCreate):
    """内存模式下后台生成报告内容"""
    import asyncio
    await asyncio.sleep(0.5)  # 模拟异步生成
    mem = _mem_reports.get(report_id)
    if not mem:
        return
    try:
        if report_generator is not None:
            report_dict = report_generator.generate_report(
                target=report_data.target or "unknown",
                findings=[],
                report_format=mem["format"],
                template=report_data.template,
            )
            fmt = mem["format"]
            if fmt == "markdown":
                rendered = report_generator.generate_markdown_report(report_dict)
            else:
                rendered = report_generator.generate_html_report(report_dict)
            mem["rendered_content"] = rendered
            mem["content"] = json.dumps(report_dict, ensure_ascii=False)
            stats = report_dict.get("statistics", {})
            mem["finding_count"] = sum(stats.values())
            mem["vulnerability_count"] = stats.get("critical", 0) + stats.get("high", 0) + stats.get("medium", 0)
        else:
            mem["rendered_content"] = f"# {mem['title']}\n\n报告生成器未安装，请配置 PenetrationReportGenerator。"
            mem["content"] = "{}"
        mem["status"] = "completed"
    except Exception as e:
        logger.error(f"内存报告生成失败: {e}")
        mem["status"] = "failed"
    mem["updated_at"] = datetime.utcnow().isoformat() + "Z"


async def generate_report_content(
    report_id: int,
    report_data: ReportCreate,
    current_user: Dict[str, Any],
    db: Session
):
    """后台生成报告内容"""
    try:
        # 获取报告
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            logger.error(f"报告不存在: {report_id}")
            return

        # 生成报告内容（从 scan 获取真实数据或使用传入的 findings）
        try:
            if PenetrationReportGenerator is None:
                raise ImportError("PenetrationReportGenerator 不可用")
            generator = PenetrationReportGenerator()

            # 从 scan_id 读取真实 findings
            findings = []
            target = report_data.target or "unknown"
            duration = None
            scan_type = "standard"

            scan_id = report_data.scan_id or report_data.parameters.get("scan_id")
            if scan_id:
                try:
                    from backend.models.scan import Scan
                except ImportError:
                    try:
                        from src.shared.backend.models.scan import Scan
                    except ImportError:
                        Scan = None

                if Scan is not None:
                    scan_obj = db.query(Scan).filter(Scan.id == scan_id).first()
                    if scan_obj:
                        findings = scan_obj.findings or []
                        target = scan_obj.target or target
                        duration = scan_obj.duration
                        scan_type = scan_obj.scan_type.value if hasattr(scan_obj.scan_type, "value") else "standard"

            # 生成报告
            report_dict = generator.generate_report(
                target=target,
                findings=findings,
                report_format=report_data.format.value,
                template=report_data.template,
                include_executive_summary=True,
                include_technical_details=True,
                include_recommendations=True,
                scan_type=scan_type,
                duration=duration,
                # 增补字段
                project_id=report_data.project_id,
                tester_name=report_data.tester_name,
                client_name=report_data.client_name,
                test_start_date=report_data.test_start_date,
                test_end_date=report_data.test_end_date,
                disclaimer=report_data.disclaimer,
            )

            # 保存报告内容（按格式决定渲染方式）
            fmt = report_data.format.value
            report.content = json.dumps(report_dict, ensure_ascii=False, indent=2)
            if fmt == "markdown":
                report.rendered_content = generator.generate_markdown_report(report_dict)
            elif fmt == "pdf":
                pdf_bytes = generator.generate_pdf_report(report_dict)
                if pdf_bytes:
                    report.rendered_content = f"[PDF binary {len(pdf_bytes)} bytes]"
                else:
                    # weasyprint 未安装，降级为 HTML
                    report.rendered_content = generator.generate_html_report(report_dict)
            else:
                report.rendered_content = generator.generate_html_report(report_dict)

            # 更新统计
            stats = report_dict.get("statistics", {})
            report.finding_count = sum(stats.values())
            report.vulnerability_count = stats.get("critical", 0) + stats.get("high", 0) + stats.get("medium", 0)
            report.status = ReportStatus.COMPLETED

            # 生成文件路径（后缀与格式一致）
            reports_dir = "data/reports"
            os.makedirs(reports_dir, exist_ok=True)
            ext = {"pdf": "html", "json": "json", "markdown": "md"}.get(fmt, fmt)  # pdf 降级存 html
            filename = f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
            filepath = os.path.join(reports_dir, filename)

            write_content = report.rendered_content or ""
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(write_content)

            report.file_path = filepath
            report.file_size = os.path.getsize(filepath)
            report.download_url = f"/api/v1/reports/{report_id}/download"

        except Exception as gen_error:
            logger.error(f"报告生成失败: {gen_error}", exc_info=True)
            report.status = ReportStatus.FAILED
            report.report_metadata["error"] = str(gen_error)

        db.commit()
        logger.info(f"报告生成完成: {report_id}")

    except Exception as e:
        logger.error(f"报告内容生成任务失败: {e}", exc_info=True)

@router.get("")  # response_model 不强制，兼容内存降级 dict
async def list_reports(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[ReportStatus] = Query(None, description="状态过滤"),
    format: Optional[ReportFormat] = Query(None, description="格式过滤"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取报告列表"""
    try:
        query = db.query(Report)

        # 过滤条件
        if status:
            query = query.filter(Report.status == status)
        if format:
            query = query.filter(Report.format == format)

        # 权限过滤：普通用户只能看到自己创建的报告
        if current_user.get('role') != 'admin':
            query = query.filter(Report.created_by == current_user.get('user_id'))

        # 分页
        total = query.count()
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size

        reports = query.order_by(Report.created_at.desc()).offset(offset).limit(page_size).all()

        return ReportListResponse(
            reports=[r for r in reports],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except Exception as e:
        logger.warning(f"数据库查询报告失败，降级使用内存存储: {e}")
        # 数据库不可用时，返回内存中的报告
        mem_list = list(_mem_reports.values())
        total = len(mem_list)
        total_pages = max(1, (total + page_size - 1) // page_size)
        offset = (page - 1) * page_size
        page_items = mem_list[offset: offset + page_size]
        return ReportListResponse(
            reports=page_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取报告详情"""
    try:
        report = db.query(Report).filter(Report.id == report_id).first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=APIError(
                    code=ErrorCode.NOT_FOUND,
                    message=f"报告 {report_id} 未找到",
                    severity="low"
                ).model_dump()
            )

        # 权限检查
        if current_user.get('role') != 'admin' and report.created_by != current_user.get('user_id'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=APIError(
                    code=ErrorCode.FORBIDDEN,
                    message="没有权限访问此报告",
                    severity="medium"
                ).model_dump()
            )

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取报告详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="获取报告详情失败",
                severity="high"
            ).model_dump()
        )

@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    format: str = Query("html", description="下载格式"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """下载报告文件"""
    try:
        report = db.query(Report).filter(Report.id == report_id).first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=APIError(
                    code=ErrorCode.NOT_FOUND,
                    message=f"报告 {report_id} 未找到",
                    severity="low"
                ).model_dump()
            )

        if report.status != ReportStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=APIError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="报告尚未生成完成",
                    severity="medium"
                ).model_dump()
            )

        # 权限检查
        if current_user.get('role') != 'admin' and report.created_by != current_user.get('user_id'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=APIError(
                    code=ErrorCode.FORBIDDEN,
                    message="没有权限下载此报告",
                    severity="medium"
                ).model_dump()
            )

        # 检查文件是否存在
        if not report.file_path or not os.path.exists(report.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=APIError(
                    code=ErrorCode.NOT_FOUND,
                    message="报告文件不存在",
                    severity="low"
                ).model_dump()
            )

        # 根据格式返回文件
        if format == "html" and report.file_path.endswith('.html'):
            return FileResponse(
                report.file_path,
                media_type="text/html",
                filename=f"report_{report_id}.html"
            )
        elif format == "json":
            # 返回JSON格式
            return {
                "id": report.id,
                "title": report.title,
                "content": report.content,
                "metadata": report.report_metadata
            }
        else:
            # 默认返回文件
            return FileResponse(
                report.file_path,
                filename=os.path.basename(report.file_path)
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载报告失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="下载报告失败",
                severity="high"
            ).model_dump()
        )

@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """删除报告"""
    try:
        report = db.query(Report).filter(Report.id == report_id).first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=APIError(
                    code=ErrorCode.NOT_FOUND,
                    message=f"报告 {report_id} 未找到",
                    severity="low"
                ).model_dump()
            )

        # 权限检查
        if current_user.get('role') != 'admin' and report.created_by != current_user.get('user_id'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=APIError(
                    code=ErrorCode.FORBIDDEN,
                    message="没有权限删除此报告",
                    severity="medium"
                ).model_dump()
            )

        # 删除文件
        if report.file_path and os.path.exists(report.file_path):
            try:
                os.remove(report.file_path)
            except Exception as e:
                logger.warning(f"删除报告文件失败: {e}")

        db.delete(report)
        db.commit()

        return {"success": True, "message": "报告删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除报告失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="删除报告失败",
                severity="high"
            ).model_dump()
        )

@router.get("/{report_id}/status")
async def get_report_status(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取报告生成状态"""
    try:
        report = db.query(Report).filter(Report.id == report_id).first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=APIError(
                    code=ErrorCode.NOT_FOUND,
                    message=f"报告 {report_id} 未找到",
                    severity="low"
                ).model_dump()
            )

        # 权限检查
        if current_user.get('role') != 'admin' and report.created_by != current_user.get('user_id'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=APIError(
                    code=ErrorCode.FORBIDDEN,
                    message="没有权限访问此报告",
                    severity="medium"
                ).model_dump()
            )

        return {
            "id": report.id,
            "status": report.status,
            "progress": report.report_metadata.get("progress", 0),
            "message": report.report_metadata.get("message", "")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取报告状态失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="获取报告状态失败",
                severity="high"
            ).model_dump()
        )

# 健康检查端点
@router.get("/health")
async def reports_health():
    """报告服务健康检查"""
    return {
        "status": "healthy",
        "service": "reports-api",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }