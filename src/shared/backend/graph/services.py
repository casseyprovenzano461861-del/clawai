# -*- coding: utf-8 -*-
"""
知识图谱业务逻辑服务
提供高级业务功能，协调数据访问层和导入器
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .repository import get_repository
from .importers.importer_manager import get_importer_manager

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """知识图谱业务服务"""

    def __init__(self):
        """初始化服务"""
        self.repository = get_repository()
        self.importer_manager = get_importer_manager()

    def import_scan_result(self, scan_data: Any, scan_type: Optional[str] = None,
                           scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        导入扫描结果

        Args:
            scan_data: 扫描数据
            scan_type: 扫描类型（如nmap、sqlmap等）
            scan_id: 扫描ID

        Returns:
            导入结果
        """
        try:
            # 使用导入器管理器导入数据
            result = self.importer_manager.import_data(scan_data, scan_id, scan_type)

            if result['success']:
                logger.info(f"扫描结果导入成功: {result['stats'].get('nodes_created', 0)} 节点")
            else:
                logger.error(f"扫描结果导入失败: {result.get('error', '未知错误')}")

            return result

        except Exception as e:
            logger.error(f"导入扫描结果失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'scan_id': scan_id,
                'timestamp': datetime.now().isoformat()
            }

    def analyze_attack_paths(self, target_asset_id: Optional[str] = None,
                             max_depth: int = 5) -> Dict[str, Any]:
        """
        分析攻击路径

        Args:
            target_asset_id: 目标资产ID（如果为None则分析所有资产）
            max_depth: 最大路径深度

        Returns:
            攻击路径分析结果
        """
        try:
            if target_asset_id:
                # 分析特定资产的攻击路径
                # 这里需要实现具体逻辑
                attack_paths = self.repository.find_attack_paths(
                    start_node_type="vulnerability",
                    end_node_type="asset",
                    max_depth=max_depth
                )

                # 过滤出目标资产的路径
                filtered_paths = []
                for path in attack_paths:
                    # 检查路径是否包含目标资产
                    nodes = path.get('nodes', [])
                    for node in nodes:
                        if isinstance(node, dict) and node.get('id') == target_asset_id:
                            filtered_paths.append(path)
                            break

                attack_paths = filtered_paths
            else:
                # 分析所有攻击路径
                attack_paths = self.repository.find_attack_paths(max_depth=max_depth)

            # 计算风险评分
            risk_assessment = self._calculate_risk_assessment(attack_paths)

            return {
                'success': True,
                'data': {
                    'attack_paths': attack_paths,
                    'risk_assessment': risk_assessment,
                    'total_paths': len(attack_paths),
                    'target_asset': target_asset_id,
                    'max_depth': max_depth
                },
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"分析攻击路径失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _calculate_risk_assessment(self, attack_paths: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算风险评分

        Args:
            attack_paths: 攻击路径列表

        Returns:
            风险评估结果
        """
        try:
            if not attack_paths:
                return {
                    'overall_risk': '低',
                    'risk_score': 0,
                    'critical_paths': 0,
                    'high_risk_paths': 0,
                    'medium_risk_paths': 0,
                    'low_risk_paths': 0
                }

            # 计算每条路径的风险评分
            path_risks = []
            for path in attack_paths:
                risk_score = self._calculate_path_risk(path)
                path_risks.append({
                    'path_length': path.get('path_length', 0),
                    'risk_score': risk_score,
                    'risk_level': self._risk_score_to_level(risk_score)
                })

            # 计算总体风险
            total_risk_score = sum(r['risk_score'] for r in path_risks)
            avg_risk_score = total_risk_score / len(path_risks) if path_risks else 0

            # 统计不同风险级别的路径数量
            risk_counts = {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            }

            for risk in path_risks:
                level = risk['risk_level']
                if level in risk_counts:
                    risk_counts[level] += 1

            return {
                'overall_risk': self._risk_score_to_level(avg_risk_score),
                'risk_score': avg_risk_score,
                'critical_paths': risk_counts['critical'],
                'high_risk_paths': risk_counts['high'],
                'medium_risk_paths': risk_counts['medium'],
                'low_risk_paths': risk_counts['low'],
                'path_risks': path_risks
            }

        except Exception as e:
            logger.error(f"计算风险评分失败: {e}")
            return {
                'overall_risk': '未知',
                'risk_score': 0,
                'critical_paths': 0,
                'high_risk_paths': 0,
                'medium_risk_paths': 0,
                'low_risk_paths': 0
            }

    def _calculate_path_risk(self, path: Dict[str, Any]) -> float:
        """
        计算单条路径的风险评分

        Args:
            path: 攻击路径

        Returns:
            风险评分 (0-10)
        """
        try:
            # 基本评分基于路径长度
            path_length = path.get('path_length', 1)
            base_score = max(0, 10 - (path_length - 1) * 2)  # 路径越短风险越高

            # 检查节点类型和关系类型
            nodes = path.get('nodes', [])
            relationships = path.get('relationships', [])

            # 检查是否有高危漏洞
            high_risk_vuln = False
            for node in nodes:
                if isinstance(node, dict):
                    node_type = node.get('type', '')
                    if node_type == 'vulnerability':
                        severity = node.get('properties', {}).get('severity', '')
                        if severity == '高危':
                            high_risk_vuln = True
                            break

            if high_risk_vuln:
                base_score += 3

            # 检查关系类型
            critical_relations = 0
            for rel in relationships:
                if isinstance(rel, dict):
                    rel_type = rel.get('type', '').lower()
                    if 'exploit' in rel_type or 'access' in rel_type:
                        critical_relations += 1

            base_score += min(critical_relations, 2)

            return min(max(base_score, 0), 10)

        except Exception as e:
            logger.error(f"计算路径风险失败: {e}")
            return 5.0  # 默认中等风险

    def _risk_score_to_level(self, score: float) -> str:
        """
        将风险评分转换为风险级别

        Args:
            score: 风险评分 (0-10)

        Returns:
            风险级别
        """
        if score >= 8:
            return 'critical'
        elif score >= 6:
            return 'high'
        elif score >= 4:
            return 'medium'
        elif score >= 2:
            return 'low'
        else:
            return 'info'

    def get_security_recommendations(self, node_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取安全建议

        Args:
            node_id: 节点ID（如果为None则提供全局建议）

        Returns:
            安全建议
        """
        try:
            recommendations = []

            if node_id:
                # 获取特定节点的建议
                node_details = self.repository.get_node_details(node_id)
                node_type = node_details.get('node', {}).get('type', '')

                if node_type == 'vulnerability':
                    recommendations.append({
                        'priority': '高',
                        'action': '立即修复漏洞',
                        'description': '发现高危漏洞，建议立即应用安全补丁或修复配置',
                        'reference': 'CVE数据库和相关安全公告'
                    })
                elif node_type == 'server':
                    recommendations.append({
                        'priority': '中',
                        'action': '强化服务器安全配置',
                        'description': '建议更新操作系统、关闭不必要端口、配置防火墙',
                        'reference': 'CIS安全基准'
                    })
            else:
                # 全局建议
                stats = self.repository.get_graph_stats()
                total_vulns = sum(1 for k, v in stats.get('node_types', {}).items()
                                 if k == 'vulnerability')

                if total_vulns > 0:
                    recommendations.append({
                        'priority': '高',
                        'action': '修复发现的漏洞',
                        'description': f'发现 {total_vulns} 个漏洞，建议按优先级修复',
                        'reference': '漏洞扫描报告'
                    })

                recommendations.append({
                    'priority': '中',
                    'action': '定期安全扫描',
                    'description': '建议定期执行安全扫描，及时发现新威胁',
                    'reference': '安全运维最佳实践'
                })

                recommendations.append({
                    'priority': '低',
                    'action': '实施网络分段',
                    'description': '建议实施网络分段，限制攻击横向移动',
                    'reference': '零信任网络架构'
                })

            return {
                'success': True,
                'data': {
                    'recommendations': recommendations,
                    'count': len(recommendations),
                    'node_id': node_id
                },
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"获取安全建议失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def export_knowledge_graph(self, format: str = 'json') -> Dict[str, Any]:
        """
        导出知识图谱

        Args:
            format: 导出格式（json, csv, graphml等）

        Returns:
            导出结果
        """
        try:
            # 获取完整图谱数据
            graph_data = self.repository.get_graph_data()

            if format.lower() == 'json':
                export_data = graph_data
            elif format.lower() == 'csv':
                # 转换为CSV格式
                export_data = self._convert_to_csv(graph_data)
            else:
                raise ValueError(f"不支持的导出格式: {format}")

            return {
                'success': True,
                'data': export_data,
                'format': format,
                'metadata': {
                    'node_count': len(graph_data.get('nodes', [])),
                    'edge_count': len(graph_data.get('edges', [])),
                    'export_time': datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"导出知识图谱失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _convert_to_csv(self, graph_data: Dict[str, Any]) -> Dict[str, str]:
        """
        将图谱数据转换为CSV格式

        Args:
            graph_data: 图谱数据

        Returns:
            CSV数据字典（包含节点CSV和边CSV）
        """
        try:
            # 节点CSV
            nodes_csv = "id,label,type,properties\n"
            for node in graph_data.get('nodes', []):
                node_id = node.get('id', '').replace(',', ';')
                label = node.get('label', '').replace(',', ';')
                node_type = node.get('type', '').replace(',', ';')
                properties = str(node.get('properties', {})).replace(',', ';')
                nodes_csv += f"{node_id},{label},{node_type},{properties}\n"

            # 边CSV
            edges_csv = "id,source,target,label,type,properties\n"
            for edge in graph_data.get('edges', []):
                edge_id = edge.get('id', '').replace(',', ';')
                source = edge.get('source', '').replace(',', ';')
                target = edge.get('target', '').replace(',', ';')
                label = edge.get('label', '').replace(',', ';')
                edge_type = edge.get('type', '').replace(',', ';')
                properties = str(edge.get('properties', {})).replace(',', ';')
                edges_csv += f"{edge_id},{source},{target},{label},{edge_type},{properties}\n"

            return {
                'nodes': nodes_csv,
                'edges': edges_csv
            }
        except Exception as e:
            logger.error(f"转换为CSV失败: {e}")
            return {
                'nodes': '',
                'edges': ''
            }

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态信息
        """
        try:
            # 检查仓库
            repo_health = self.repository.health_check()

            # 检查导入器管理器
            importer_health = self.importer_manager.health_check()

            overall_healthy = (
                repo_health.get('status') == 'healthy' and
                importer_health.get('status') == 'healthy'
            )

            return {
                'status': 'healthy' if overall_healthy else 'unhealthy',
                'service': 'knowledge-graph-service',
                'components': {
                    'repository': repo_health,
                    'importer_manager': importer_health
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"服务健康检查失败: {e}")
            return {
                'status': 'unhealthy',
                'service': 'knowledge-graph-service',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# 全局服务实例
_service_instance: Optional[KnowledgeGraphService] = None


def get_service() -> KnowledgeGraphService:
    """
    获取全局知识图谱服务实例

    Returns:
        KnowledgeGraphService实例
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = KnowledgeGraphService()
    return _service_instance