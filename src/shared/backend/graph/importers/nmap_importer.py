# -*- coding: utf-8 -*-
"""
Nmap扫描结果导入器
将Nmap扫描结果转换为知识图谱节点和关系
"""

import re
import json
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_importer import BaseImporter
from ..models import NodeModel, EdgeModel

logger = logging.getLogger(__name__)


class NmapImporter(BaseImporter):
    """Nmap扫描结果导入器"""

    def can_import(self, data: Any) -> bool:
        """
        检查是否可以导入Nmap数据

        Args:
            data: 要检查的数据（可以是XML字符串、字典、文件路径等）

        Returns:
            是否可以导入
        """
        if isinstance(data, str):
            # 检查是否为XML格式（Nmap通常输出XML）
            if data.strip().startswith('<?xml'):
                return True
            # 检查是否为文件路径
            if data.endswith('.xml'):
                return True
            # 检查是否包含nmap特定标记
            if 'nmaprun' in data.lower() or 'nmap' in data.lower():
                return True

        # 如果是字典，检查是否包含nmap结构
        if isinstance(data, dict):
            if 'nmaprun' in data or 'scaninfo' in data:
                return True

        return False

    def import_data(self, data: Any, scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        导入Nmap扫描结果

        Args:
            data: Nmap扫描数据（XML字符串、字典或文件路径）
            scan_id: 扫描任务ID

        Returns:
            导入结果统计
        """
        try:
            # 解析数据
            parsed_data = self._parse_nmap_data(data)
            if not parsed_data:
                raise ValueError("无法解析Nmap数据")

            # 提取主机信息
            hosts = parsed_data.get('hosts', [])

            # 统计信息
            stats = {
                'total_hosts': len(hosts),
                'nodes_created': 0,
                'edges_created': 0,
                'errors': []
            }

            # 为扫描创建父节点
            scan_node_id = self._generate_node_id('scan', scan_id or 'nmap-scan')
            scan_node = self._create_scan_node(scan_node_id, parsed_data)
            if scan_node:
                stats['nodes_created'] += 1

            # 导入每个主机
            for host in hosts:
                try:
                    host_stats = self._import_host(host, scan_node_id, scan_id)
                    stats['nodes_created'] += host_stats['nodes_created']
                    stats['edges_created'] += host_stats['edges_created']
                except Exception as e:
                    error_msg = f"导入主机失败: {host.get('address', 'unknown')}, 错误: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)

            logger.info(f"Nmap导入完成: {stats['nodes_created']} 节点, {stats['edges_created']} 边")
            return stats

        except Exception as e:
            logger.error(f"导入Nmap数据失败: {e}")
            raise

    def _parse_nmap_data(self, data: Any) -> Optional[Dict[str, Any]]:
        """
        解析Nmap数据

        Args:
            data: Nmap数据

        Returns:
            解析后的数据字典
        """
        try:
            if isinstance(data, dict):
                return data

            if isinstance(data, str):
                # 如果是文件路径，读取文件
                if data.endswith('.xml'):
                    with open(data, 'r', encoding='utf-8') as f:
                        data = f.read()

                # 解析XML
                if data.strip().startswith('<?xml'):
                    return self._parse_nmap_xml(data)

                # 尝试解析JSON
                try:
                    return json.loads(data)
                except Exception as e:
                    logger.debug(f"Error: {e}")

            return None
        except Exception as e:
            logger.error(f"解析Nmap数据失败: {e}")
            return None

    def _parse_nmap_xml(self, xml_data: str) -> Dict[str, Any]:
        """
        解析Nmap XML数据

        Args:
            xml_data: XML字符串

        Returns:
            解析后的数据字典
        """
        try:
            root = ET.fromstring(xml_data)

            result = {
                'scan_info': {},
                'hosts': []
            }

            # 提取扫描信息
            scan_info = root.find('scaninfo')
            if scan_info is not None:
                result['scan_info'] = {
                    'type': scan_info.get('type', ''),
                    'protocol': scan_info.get('protocol', ''),
                    'num_services': scan_info.get('numservices', '')
                }

            # 提取主机信息
            for host in root.findall('host'):
                host_data = self._parse_host_element(host)
                if host_data:
                    result['hosts'].append(host_data)

            # 提取运行统计
            run_stats = root.find('runstats')
            if run_stats is not None:
                finished = run_stats.find('finished')
                if finished is not None:
                    result['scan_time'] = finished.get('time', '')
                    result['scan_duration'] = finished.get('elapsed', '')

            return result

        except Exception as e:
            logger.error(f"解析Nmap XML失败: {e}")
            return {'hosts': []}

    def _parse_host_element(self, host_element) -> Dict[str, Any]:
        """
        解析主机元素

        Args:
            host_element: XML主机元素

        Returns:
            主机数据字典
        """
        try:
            host_data = {
                'addresses': [],
                'ports': [],
                'os': {},
                'hostnames': []
            }

            # 提取状态
            status = host_element.find('status')
            if status is not None:
                host_data['status'] = status.get('state', 'unknown')
                host_data['reason'] = status.get('reason', '')

            # 提取地址
            for address in host_element.findall('address'):
                addr_data = {
                    'addr': address.get('addr', ''),
                    'addrtype': address.get('addrtype', ''),
                    'vendor': address.get('vendor', '')
                }
                host_data['addresses'].append(addr_data)

            # 提取主机名
            for hostname in host_element.findall('hostnames/hostname'):
                hostname_data = {
                    'name': hostname.get('name', ''),
                    'type': hostname.get('type', '')
                }
                host_data['hostnames'].append(hostname_data)

            # 提取端口
            ports_element = host_element.find('ports')
            if ports_element is not None:
                for port in ports_element.findall('port'):
                    port_data = self._parse_port_element(port)
                    if port_data:
                        host_data['ports'].append(port_data)

            # 提取操作系统信息
            os_element = host_element.find('os')
            if os_element is not None:
                os_match = os_element.find('osmatch')
                if os_match is not None:
                    host_data['os'] = {
                        'name': os_match.get('name', ''),
                        'accuracy': os_match.get('accuracy', ''),
                        'line': os_match.get('line', '')
                    }

            return host_data

        except Exception as e:
            logger.error(f"解析主机元素失败: {e}")
            return {}

    def _parse_port_element(self, port_element) -> Dict[str, Any]:
        """
        解析端口元素

        Args:
            port_element: XML端口元素

        Returns:
            端口数据字典
        """
        try:
            port_data = {
                'port_id': port_element.get('portid', ''),
                'protocol': port_element.get('protocol', ''),
                'state': {},
                'service': {}
            }

            # 提取端口状态
            state = port_element.find('state')
            if state is not None:
                port_data['state'] = {
                    'state': state.get('state', ''),
                    'reason': state.get('reason', ''),
                    'reason_ttl': state.get('reason_ttl', '')
                }

            # 提取服务信息
            service = port_element.find('service')
            if service is not None:
                port_data['service'] = {
                    'name': service.get('name', ''),
                    'product': service.get('product', ''),
                    'version': service.get('version', ''),
                    'extrainfo': service.get('extrainfo', ''),
                    'ostype': service.get('ostype', ''),
                    'method': service.get('method', ''),
                    'conf': service.get('conf', '')
                }

            return port_data

        except Exception as e:
            logger.error(f"解析端口元素失败: {e}")
            return {}

    def _create_scan_node(self, scan_node_id: str, scan_data: Dict[str, Any]) -> Optional[NodeModel]:
        """
        创建扫描节点

        Args:
            scan_node_id: 扫描节点ID
            scan_data: 扫描数据

        Returns:
            扫描节点模型
        """
        try:
            scan_info = scan_data.get('scan_info', {})
            scan_time = scan_data.get('scan_time', datetime.now().isoformat())

            node_data = {
                'id': scan_node_id,
                'label': f"Nmap扫描 - {scan_time}",
                'type': 'scan',
                'properties': {
                    'scanner': 'nmap',
                    'scan_type': scan_info.get('type', 'syn'),
                    'protocol': scan_info.get('protocol', 'tcp'),
                    'scan_time': scan_time,
                    'duration': scan_data.get('scan_duration', ''),
                    'total_hosts': len(scan_data.get('hosts', []))
                }
            }

            return self.create_node(node_data)
        except Exception as e:
            logger.error(f"创建扫描节点失败: {e}")
            return None

    def _import_host(self, host_data: Dict[str, Any], scan_node_id: str, scan_id: Optional[str]) -> Dict[str, Any]:
        """
        导入单个主机

        Args:
            host_data: 主机数据
            scan_node_id: 扫描节点ID
            scan_id: 扫描ID

        Returns:
            导入统计
        """
        stats = {
            'nodes_created': 0,
            'edges_created': 0
        }

        try:
            # 获取主机地址
            addresses = host_data.get('addresses', [])
            if not addresses:
                return stats

            # 使用第一个IP地址作为主机标识
            ip_address = None
            for addr in addresses:
                if addr.get('addrtype') == 'ipv4':
                    ip_address = addr.get('addr')
                    break

            if not ip_address:
                # 如果没有IPv4地址，使用第一个地址
                ip_address = addresses[0].get('addr', 'unknown')

            # 创建主机节点
            host_node_id = self._generate_node_id('server', ip_address, scan_id)
            host_node = self._create_host_node(host_node_id, host_data, ip_address)
            if host_node:
                stats['nodes_created'] += 1

                # 创建扫描到主机的边
                edge_data = {
                    'id': self._generate_edge_id('discovered', scan_node_id, host_node_id),
                    'source': scan_node_id,
                    'target': host_node_id,
                    'label': '扫描发现',
                    'type': 'discovery',
                    'properties': {
                        'scanner': 'nmap',
                        'timestamp': datetime.now().isoformat(),
                        'status': host_data.get('status', 'unknown')
                    }
                }

                try:
                    self.create_relationship(edge_data)
                    stats['edges_created'] += 1
                except Exception as e:
                    logger.error(f"创建扫描关系失败: {e}")

            # 导入端口和服务
            for port in host_data.get('ports', []):
                port_stats = self._import_port(port, host_node_id, scan_id)
                stats['nodes_created'] += port_stats['nodes_created']
                stats['edges_created'] += port_stats['edges_created']

            return stats

        except Exception as e:
            logger.error(f"导入主机失败: {e}")
            raise

    def _create_host_node(self, host_node_id: str, host_data: Dict[str, Any], ip_address: str) -> Optional[NodeModel]:
        """
        创建主机节点

        Args:
            host_node_id: 主机节点ID
            host_data: 主机数据
            ip_address: IP地址

        Returns:
            主机节点模型
        """
        try:
            # 提取主机名
            hostnames = host_data.get('hostnames', [])
            primary_hostname = ''
            if hostnames:
                primary_hostname = hostnames[0].get('name', '')

            # 提取操作系统信息
            os_info = host_data.get('os', {})
            os_name = os_info.get('name', 'Unknown')

            node_data = {
                'id': host_node_id,
                'label': primary_hostname or ip_address,
                'type': 'server',
                'properties': {
                    'ip': ip_address,
                    'hostname': primary_hostname,
                    'os': os_name,
                    'status': host_data.get('status', 'unknown'),
                    'ports_count': len(host_data.get('ports', [])),
                    'last_seen': datetime.now().isoformat()
                }
            }

            # 添加所有地址
            addresses = host_data.get('addresses', [])
            for i, addr in enumerate(addresses):
                if i < 5:  # 限制数量
                    node_data['properties'][f'address_{i+1}'] = f"{addr.get('addrtype')}: {addr.get('addr')}"

            return self.create_node(node_data)
        except Exception as e:
            logger.error(f"创建主机节点失败: {e}")
            return None

    def _import_port(self, port_data: Dict[str, Any], host_node_id: str, scan_id: Optional[str]) -> Dict[str, Any]:
        """
        导入端口

        Args:
            port_data: 端口数据
            host_node_id: 主机节点ID
            scan_id: 扫描ID

        Returns:
            导入统计
        """
        stats = {
            'nodes_created': 0,
            'edges_created': 0
        }

        try:
            port_id = port_data.get('port_id', '')
            protocol = port_data.get('protocol', 'tcp')
            service_data = port_data.get('service', {})

            # 创建服务节点（如果服务信息足够详细）
            service_name = service_data.get('name', '')
            if service_name and service_name not in ['unknown', '']:
                # 创建服务节点
                service_node_id = self._generate_node_id('service', f"{host_node_id}-{port_id}-{protocol}", scan_id)
                service_node = self._create_service_node(service_node_id, port_data, service_data)
                if service_node:
                    stats['nodes_created'] += 1

                    # 创建主机到服务的边
                    edge_data = {
                        'id': self._generate_edge_id('has_service', host_node_id, service_node_id),
                        'source': host_node_id,
                        'target': service_node_id,
                        'label': '运行服务',
                        'type': 'has_service',
                        'properties': {
                            'port': port_id,
                            'protocol': protocol,
                            'state': port_data.get('state', {}).get('state', ''),
                            'timestamp': datetime.now().isoformat()
                        }
                    }

                    try:
                        self.create_relationship(edge_data)
                        stats['edges_created'] += 1
                    except Exception as e:
                        logger.error(f"创建服务关系失败: {e}")

                    # 检查服务是否有已知漏洞
                    if self._is_service_vulnerable(service_data):
                        vuln_stats = self._create_vulnerability_node(service_node_id, service_data, scan_id)
                        stats['nodes_created'] += vuln_stats['nodes_created']
                        stats['edges_created'] += vuln_stats['edges_created']

            return stats

        except Exception as e:
            logger.error(f"导入端口失败: {e}")
            return stats

    def _create_service_node(self, service_node_id: str, port_data: Dict[str, Any],
                             service_data: Dict[str, Any]) -> Optional[NodeModel]:
        """
        创建服务节点

        Args:
            service_node_id: 服务节点ID
            port_data: 端口数据
            service_data: 服务数据

        Returns:
            服务节点模型
        """
        try:
            port_id = port_data.get('port_id', '')
            protocol = port_data.get('protocol', 'tcp')
            service_name = service_data.get('name', '')
            product = service_data.get('product', '')
            version = service_data.get('version', '')

            label = f"{service_name} {port_id}/{protocol}"
            if product:
                label = f"{product} {label}"
                if version:
                    label = f"{label} {version}"

            node_data = {
                'id': service_node_id,
                'label': label,
                'type': 'service',
                'properties': {
                    'port': port_id,
                    'protocol': protocol,
                    'service_name': service_name,
                    'product': product,
                    'version': version,
                    'extrainfo': service_data.get('extrainfo', ''),
                    'ostype': service_data.get('ostype', ''),
                    'method': service_data.get('method', ''),
                    'confidence': service_data.get('conf', ''),
                    'state': port_data.get('state', {}).get('state', '')
                }
            }

            return self.create_node(node_data)
        except Exception as e:
            logger.error(f"创建服务节点失败: {e}")
            return None

    def _is_service_vulnerable(self, service_data: Dict[str, Any]) -> bool:
        """
        检查服务是否有已知漏洞

        Args:
            service_data: 服务数据

        Returns:
            是否有已知漏洞
        """
        # 简单的启发式规则
        service_name = service_data.get('name', '').lower()
        product = service_data.get('product', '').lower()
        version = service_data.get('version', '')

        # 检查常见易受攻击的服务
        vulnerable_services = ['http', 'https', 'ftp', 'ssh', 'telnet', 'smb', 'rdp']
        if service_name in vulnerable_services:
            return True

        # 检查特定产品和版本
        if product and version:
            # 这里可以添加更复杂的漏洞检测逻辑
            # 例如检查已知的易受攻击版本
            pass

        return False

    def _create_vulnerability_node(self, service_node_id: str, service_data: Dict[str, Any],
                                   scan_id: Optional[str]) -> Dict[str, Any]:
        """
        创建漏洞节点

        Args:
            service_node_id: 服务节点ID
            service_data: 服务数据
            scan_id: 扫描ID

        Returns:
            导入统计
        """
        stats = {
            'nodes_created': 0,
            'edges_created': 0
        }

        try:
            # 生成漏洞节点ID
            vuln_node_id = self._generate_node_id('vulnerability', f"{service_node_id}-potential", scan_id)

            service_name = service_data.get('name', '')
            product = service_data.get('product', '')
            version = service_data.get('version', '')

            node_data = {
                'id': vuln_node_id,
                'label': f"潜在漏洞 - {service_name}",
                'type': 'vulnerability',
                'properties': {
                    'service': service_name,
                    'product': product,
                    'version': version,
                    'severity': '中危',
                    'confidence': '低',
                    'description': f"{product} {version} 可能存在已知漏洞",
                    'discovered': datetime.now().isoformat(),
                    'source': 'nmap_scan'
                }
            }

            vuln_node = self.create_node(node_data)
            if vuln_node:
                stats['nodes_created'] += 1

                # 创建服务到漏洞的边
                edge_data = {
                    'id': self._generate_edge_id('has_vulnerability', service_node_id, vuln_node_id),
                    'source': service_node_id,
                    'target': vuln_node_id,
                    'label': '存在漏洞',
                    'type': 'has_vulnerability',
                    'properties': {
                        'timestamp': datetime.now().isoformat(),
                        'confidence': '低',
                        'scanner': 'nmap'
                    }
                }

                try:
                    self.create_relationship(edge_data)
                    stats['edges_created'] += 1
                except Exception as e:
                    logger.error(f"创建漏洞关系失败: {e}")

        except Exception as e:
            logger.error(f"创建漏洞节点失败: {e}")

        return stats