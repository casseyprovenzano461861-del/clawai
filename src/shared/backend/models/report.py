"""
报告模型
借鉴PentAGI的报告系统设计
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, Any, List, Optional

from .base import BaseModel


class ReportStatus(PyEnum):
    """报告状态枚举"""
    GENERATING = "generating"  # 生成中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败


class ReportFormat(PyEnum):
    """报告格式枚举"""
    HTML = "html"              # HTML格式
    PDF = "pdf"                # PDF格式
    JSON = "json"              # JSON格式
    MARKDOWN = "markdown"      # Markdown格式


class Report(BaseModel):
    """报告模型"""
    __tablename__ = "reports"
    
    # 基本信息
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # 状态信息
    status = Column(Enum(ReportStatus), default=ReportStatus.GENERATING, nullable=False)
    format = Column(Enum(ReportFormat), default=ReportFormat.HTML, nullable=False)
    
    # 内容信息
    content = Column(Text, nullable=True)          # 报告内容（原始）
    rendered_content = Column(Text, nullable=True) # 渲染后的内容
    report_metadata = Column(JSON, default=dict, nullable=False)  # 报告元数据
    
    # 文件信息
    file_path = Column(String(500), nullable=True)  # 文件路径
    file_size = Column(Integer, nullable=True)      # 文件大小（字节）
    download_url = Column(String(500), nullable=True)  # 下载URL
    
    # 统计信息
    page_count = Column(Integer, default=0, nullable=False)
    finding_count = Column(Integer, default=0, nullable=False)
    vulnerability_count = Column(Integer, default=0, nullable=False)
    
    # 外键关系
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 关系
    scan = relationship("Scan", back_populates="reports")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __init__(self, title: str, scan_id: int, created_by: int, **kwargs):
        """初始化报告"""
        super().__init__(**kwargs)
        self.title = title
        self.scan_id = scan_id
        self.created_by = created_by
        
        # 默认元数据
        self.report_metadata = {
            "template": "default",
            "language": "zh-CN",
            "sections": [
                "executive_summary",
                "methodology",
                "findings",
                "recommendations",
                "appendix"
            ],
            "styles": {
                "theme": "light",
                "font": "Arial",
                "colors": {
                    "critical": "#ff4444",
                    "high": "#ff8800",
                    "medium": "#ffbb33",
                    "low": "#00C851",
                    "info": "#33b5e5"
                }
            }
        }
    
    def generate_from_scan(self, scan: 'Scan'):
        """从扫描结果生成报告"""
        self.status = ReportStatus.GENERATING

        # 获取格式字符串
        format_str = self.format.value if hasattr(self.format, 'value') else self.format

        # 提取扫描信息
        scan_data = scan.to_dict(include_details=True)

        # 生成报告内容
        self.content = self._generate_content(scan_data, format_str)
        self.rendered_content = self._render_content(self.content, format_str)

        # 更新统计信息
        self.finding_count = scan.finding_count
        self.vulnerability_count = scan.vulnerability_count

        # 标记为完成
        self.status = ReportStatus.COMPLETED

        # 生成文件（如果需要）
        if format_str != ReportFormat.JSON.value:
            self._generate_file()
    
    def _generate_content(self, scan_data: Dict[str, Any], format_str: str) -> str:
        """生成报告内容"""
        # 这里应该根据格式生成不同的内容
        # 简化版本，返回JSON格式
        import json

        report_data = {
            "report": {
                "title": self.title,
                "scan": scan_data,
                "generated_at": datetime.utcnow().isoformat(),
                "metadata": self.report_metadata
            }
        }

        if format_str == ReportFormat.JSON.value:
            return json.dumps(report_data, indent=2, ensure_ascii=False)
        else:
            # 其他格式需要模板渲染
            return json.dumps(report_data, ensure_ascii=False)
    
    def _render_content(self, content: str, format_str: str) -> str:
        """渲染报告内容"""
        if format_str == ReportFormat.HTML.value:
            return self._render_html(content)
        elif format_str == ReportFormat.PDF.value:
            return self._render_pdf(content)
        elif format_str == ReportFormat.MARKDOWN.value:
            return self._render_markdown(content)
        else:
            return content
    
    def _render_html(self, content: str) -> str:
        """渲染为HTML"""
        # 简化版本，实际应该使用模板引擎
        try:
            import json
            data = json.loads(content)
            
            html = f"""
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{data['report']['title']}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #333; }}
                    .finding {{ margin: 20px 0; padding: 15px; border-left: 4px solid #333; }}
                    .critical {{ border-color: #ff4444; }}
                    .high {{ border-color: #ff8800; }}
                    .medium {{ border-color: #ffbb33; }}
                    .low {{ border-color: #00C851; }}
                </style>
            </head>
            <body>
                <h1>{data['report']['title']}</h1>
                <p>生成时间: {data['report']['generated_at']}</p>
                <p>扫描目标: {data['report']['scan'].get('target', 'N/A')}</p>
                <p>发现数量: {data['report']['scan'].get('finding_count', 0)}</p>
            </body>
            </html>
            """
            return html
        except Exception:
            return f"<html><body><h1>{self.title}</h1><pre>{content}</pre></body></html>"
    
    def _render_markdown(self, content: str) -> str:
        """渲染为Markdown"""
        try:
            import json
            data = json.loads(content)
            
            markdown = f"""
            # {data['report']['title']}
            
            **生成时间**: {data['report']['generated_at']}  
            **扫描目标**: {data['report']['scan'].get('target', 'N/A')}  
            **发现数量**: {data['report']['scan'].get('finding_count', 0)}  
            
            ## 扫描摘要
            
            状态: {data['report']['scan'].get('status', 'N/A')}  
            类型: {data['report']['scan'].get('scan_type', 'N/A')}  
            时长: {data['report']['scan'].get('duration', 0)}秒  
            
            ## 发现的问题
            """
            return markdown
        except Exception:
            return f"# {self.title}\n\n{content}"
    
    def _render_pdf(self, content: str) -> str:
        """渲染为PDF"""
        # PDF渲染需要额外的库，这里返回HTML内容供转换
        return self._render_html(content)
    
    def _generate_file(self):
        """生成报告文件"""
        import os
        import uuid
        
        # 创建报告目录
        reports_dir = os.path.join("data", "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # 生成文件名
        format_str = self.format.value if hasattr(self.format, 'value') else self.format
        filename = f"{uuid.uuid4().hex}.{format_str}"
        filepath = os.path.join(reports_dir, filename)
        
        # 保存文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.rendered_content)
        
        # 更新文件信息
        self.file_path = filepath
        self.file_size = os.path.getsize(filepath)
        self.download_url = f"/api/reports/{self.id}/download"
    
    def to_dict(self, include_content: bool = False) -> Dict[str, Any]:
        """转换为字典"""
        data = super().to_dict()
        
        # 添加枚举值的字符串表示
        data["status"] = self.status.value if hasattr(self.status, 'value') else self.status
        data["format"] = self.format.value if hasattr(self.format, 'value') else self.format
        
        # 添加扫描信息
        if self.scan:
            data["scan"] = self.scan.to_dict()
        
        # 添加创建者信息
        if self.creator:
            data["creator"] = self.creator.to_dict()
        
        # 是否包含内容
        if not include_content:
            data.pop("content", None)
            data.pop("rendered_content", None)
        
        return data