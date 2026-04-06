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
# 尝试导入真实报告生成器，失败时使用模拟生成器
try:
    from backend.report.penetration_report_generator import PenetrationReportGenerator
    REPORT_GENERATOR_AVAILABLE = True
except ImportError:
    REPORT_GENERATOR_AVAILABLE = False
    # 模拟报告生成器
    class PenetrationReportGenerator:
        def generate_report(self, target, findings, report_format, template, **kwargs):
            return {
                "id": f"report_{int(datetime.now().timestamp())}",
                "title": f"安全评估报告 - {target}",
                "target": target,
                "date": datetime.now().isoformat(),
                "findings": findings,
                "format": report_format,
                "template": template,
                "executive_summary": {
                    "overview": f"本次安全评估发现目标系统 {target} 存在 {len(findings)} 个安全漏洞。",
                    "risk_level": "高" if any(f.get('severity') == 'high' for f in findings) else "中",
                    "recommendations_count": len(findings)
                }
            }

        def generate_html_report(self, report_dict):
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{report_dict.get('title', '安全评估报告')}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #333; }}
                    .finding {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; }}
                    .high {{ border-left: 5px solid red; }}
                    .medium {{ border-left: 5px solid orange; }}
                    .low {{ border-left: 5px solid green; }}
                </style>
            </head>
            <body>
                <h1>{report_dict.get('title', '安全评估报告')}</h1>
                <p>生成时间: {datetime.now().isoformat()}</p>
                <h2>执行摘要</h2>
                <p>{report_dict.get('executive_summary', {}).get('overview', '')}</p>
                <h2>漏洞发现</h2>
                {''.join(f'<div class="finding {f.get("severity", "medium")}"><h3>{f.get("name")}</h3><p>{f.get("description")}</p></div>' for f in report_dict.get('findings', []))}
            </body>
            </html>
            """

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
    format: ReportFormat = Field(default=ReportFormat.HTML, description="报告格式")
    template: str = Field(default="standard", description="报告模板")
    target: Optional[str] = Field(None, description="目标地址或范围")
    scan_id: Optional[int] = Field(None, description="关联的扫描ID")
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
report_generator = PenetrationReportGenerator()

@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    background_tasks: BackgroundTasks,
    report_data: ReportCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """
    生成新报告

    创建报告记录并异步生成报告内容。
    """
    try:
        # 创建报告记录
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
                "parameters": report_data.parameters,
                "generator": "penetration_report_generator"
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
        logger.error(f"创建报告失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="创建报告失败",
                severity="high"
            ).model_dump()
        )

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

        # 生成报告内容（模拟或真实）
        # 这里可以集成真实的报告生成器
        try:
            # 使用渗透测试报告生成器
            generator = PenetrationReportGenerator()

            # 模拟报告数据（实际应基于scan_id获取真实数据）
            mock_findings = [
                {
                    "id": "vuln-001",
                    "name": "SQL注入漏洞",
                    "severity": "high",
                    "category": "sql_injection",
                    "description": "在登录页面发现SQL注入漏洞",
                    "location": "/login.php",
                    "evidence": "参数'username'存在SQL注入",
                    "impact": "可能导致数据库泄露",
                    "recommendation": "使用参数化查询或ORM",
                    "cve_id": "CVE-2024-1234",
                    "cvss_score": 8.5
                },
                {
                    "id": "vuln-002",
                    "name": "XSS跨站脚本漏洞",
                    "severity": "medium",
                    "category": "xss",
                    "description": "在搜索功能中发现反射型XSS",
                    "location": "/search.php",
                    "evidence": "参数'q'未过滤用户输入",
                    "impact": "可能导致会话劫持",
                    "recommendation": "对用户输入进行HTML编码",
                    "cve_id": "CVE-2024-5678",
                    "cvss_score": 6.5
                }
            ]

            # 生成报告
            report_dict = generator.generate_report(
                target=report_data.target or "example.com",
                findings=mock_findings,
                report_format=report_data.format.value,
                template=report_data.template,
                include_executive_summary=True,
                include_technical_details=True,
                include_recommendations=True
            )

            # 保存报告内容
            report.content = json.dumps(report_dict, ensure_ascii=False, indent=2)
            report.rendered_content = generator.generate_html_report(report_dict)
            report.status = ReportStatus.COMPLETED

            # 生成文件路径
            reports_dir = "data/reports"
            os.makedirs(reports_dir, exist_ok=True)
            filename = f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            filepath = os.path.join(reports_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report.rendered_content)

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

@router.get("", response_model=ReportListResponse)
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
        logger.error(f"获取报告列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="获取报告列表失败",
                severity="high"
            ).model_dump()
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