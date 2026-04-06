# -*- coding: utf-8 -*-
"""
导入器管理器
管理各种扫描结果导入器，提供统一的导入接口
"""

import logging
from typing import Dict, List, Any, Optional, Type
from datetime import datetime

from .base_importer import BaseImporter
from .nmap_importer import NmapImporter

logger = logging.getLogger(__name__)


class ImporterManager:
    """导入器管理器"""

    def __init__(self):
        """初始化导入器管理器"""
        self.importers: List[BaseImporter] = []
        self._register_default_importers()

    def _register_default_importers(self):
        """注册默认导入器"""
        self.register_importer(NmapImporter)
        # 可以在这里注册更多导入器
        # self.register_importer(SqlmapImporter)
        # self.register_importer(NiktoImporter)

    def register_importer(self, importer_class: Type[BaseImporter]):
        """
        注册导入器

        Args:
            importer_class: 导入器类
        """
        try:
            importer = importer_class()
            self.importers.append(importer)
            logger.info(f"注册导入器: {importer_class.__name__}")
        except Exception as e:
            logger.error(f"注册导入器失败: {importer_class.__name__}, 错误: {e}")

    def find_suitable_importer(self, data: Any) -> Optional[BaseImporter]:
        """
        查找适合的导入器

        Args:
            data: 要导入的数据

        Returns:
            适合的导入器实例，如果没有则返回None
        """
        for importer in self.importers:
            try:
                if importer.can_import(data):
                    logger.info(f"找到适合的导入器: {importer.__class__.__name__}")
                    return importer
            except Exception as e:
                logger.error(f"检查导入器 {importer.__class__.__name__} 失败: {e}")

        logger.warning("没有找到适合的导入器")
        return None

    def import_data(self, data: Any, scan_id: Optional[str] = None,
                    data_type: Optional[str] = None) -> Dict[str, Any]:
        """
        导入数据

        Args:
            data: 要导入的数据
            scan_id: 扫描任务ID
            data_type: 数据类型（可选，如果指定则使用对应导入器）

        Returns:
            导入结果
        """
        start_time = datetime.now()

        # 查找导入器
        importer = None
        if data_type:
            # 根据数据类型查找特定导入器
            for imp in self.importers:
                if imp.__class__.__name__.lower().startswith(data_type.lower()):
                    importer = imp
                    break

        if not importer:
            # 自动检测导入器
            importer = self.find_suitable_importer(data)

        if not importer:
            return {
                'success': False,
                'error': '没有找到适合的导入器',
                'scan_id': scan_id,
                'timestamp': start_time.isoformat()
            }

        try:
            # 执行导入
            import_stats = importer.import_data(data, scan_id)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                'success': True,
                'scan_id': scan_id,
                'importer': importer.__class__.__name__,
                'stats': import_stats,
                'timestamp': end_time.isoformat(),
                'duration_seconds': duration
            }

            logger.info(f"数据导入成功: {import_stats.get('nodes_created', 0)} 节点, "
                       f"{import_stats.get('edges_created', 0)} 边, "
                       f"耗时: {duration:.2f} 秒")

            return result

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            error_msg = f"数据导入失败: {str(e)}"
            logger.error(error_msg)

            return {
                'success': False,
                'error': error_msg,
                'scan_id': scan_id,
                'importer': importer.__class__.__name__,
                'timestamp': end_time.isoformat(),
                'duration_seconds': duration
            }

    def get_available_importers(self) -> List[Dict[str, Any]]:
        """
        获取可用导入器列表

        Returns:
            导入器信息列表
        """
        importers_info = []
        for importer in self.importers:
            importers_info.append({
                'name': importer.__class__.__name__,
                'description': importer.__class__.__doc__ or '',
                'supported_formats': self._get_importer_formats(importer)
            })
        return importers_info

    def _get_importer_formats(self, importer: BaseImporter) -> List[str]:
        """
        获取导入器支持的格式

        Args:
            importer: 导入器实例

        Returns:
            支持的格式列表
        """
        # 这里可以根据导入器类型返回具体格式
        # 目前返回简单的描述
        if isinstance(importer, NmapImporter):
            return ['XML', 'JSON', 'Nmap输出格式']
        # 其他导入器的格式
        return ['未知格式']

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态信息
        """
        try:
            importer_count = len(self.importers)
            available_importers = self.get_available_importers()

            return {
                'status': 'healthy',
                'service': 'importer-manager',
                'importer_count': importer_count,
                'available_importers': [imp['name'] for imp in available_importers],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"导入器管理器健康检查失败: {e}")
            return {
                'status': 'unhealthy',
                'service': 'importer-manager',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# 全局管理器实例
_manager_instance: Optional[ImporterManager] = None


def get_importer_manager() -> ImporterManager:
    """
    获取全局导入器管理器实例

    Returns:
        ImporterManager实例
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ImporterManager()
    return _manager_instance