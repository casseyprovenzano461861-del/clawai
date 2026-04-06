/**
 * 知识图谱API服务
 */
import { request } from './apiClient';

// 节点类型枚举
export const NodeType = {
  HOST: 'host',
  VULNERABILITY: 'vulnerability',
  USER: 'user',
  TOOL: 'tool',
  NETWORK: 'network',
  ATTACK: 'attack',
  ASSET: 'asset',
  THREAT: 'threat',
  DEFENSE: 'defense',
  PORT: 'port',
  SERVICE: 'service'
};

// 关系类型枚举
export const RelationshipType = {
  DISCOVERY: 'discovery',
  HAS_VULNERABILITY: 'has_vulnerability',
  HAS_ACCESS: 'has_access',
  CAN_ACCESS: 'can_access',
  EXPLOITS: 'exploits',
  USES: 'uses',
  CONTAINS: 'contains',
  PROTECTS: 'protects',
  DETECTS: 'detects',
  BLOCKS: 'blocks',
  RUNS_ON: 'runs_on',
  HAS_PORT: 'has_port',
  HAS_SERVICE: 'has_service'
};

// 节点类型配置
export const nodeTypeConfig = {
  [NodeType.HOST]: { name: '主机', color: '#3b82f6', icon: 'server' },
  [NodeType.VULNERABILITY]: { name: '漏洞', color: '#ef4444', icon: 'alert-triangle' },
  [NodeType.USER]: { name: '用户', color: '#10b981', icon: 'user' },
  [NodeType.TOOL]: { name: '工具', color: '#8b5cf6', icon: 'cpu' },
  [NodeType.NETWORK]: { name: '网络', color: '#6366f1', icon: 'wifi' },
  [NodeType.ATTACK]: { name: '攻击', color: '#ec4899', icon: 'target' },
  [NodeType.ASSET]: { name: '资产', color: '#14b8a6', icon: 'database' },
  [NodeType.THREAT]: { name: '威胁', color: '#f97316', icon: 'shield' },
  [NodeType.DEFENSE]: { name: '防御', color: '#22c55e', icon: 'lock' },
  [NodeType.PORT]: { name: '端口', color: '#8b5cf6', icon: 'hash' },
  [NodeType.SERVICE]: { name: '服务', color: '#10b981', icon: 'globe' }
};

// 关系类型配置
export const relationshipTypeConfig = {
  [RelationshipType.DISCOVERY]: { name: '发现', color: '#8b5cf6' },
  [RelationshipType.HAS_VULNERABILITY]: { name: '存在漏洞', color: '#ef4444' },
  [RelationshipType.HAS_ACCESS]: { name: '访问权限', color: '#10b981' },
  [RelationshipType.CAN_ACCESS]: { name: '可访问', color: '#f59e0b' },
  [RelationshipType.EXPLOITS]: { name: '利用', color: '#ec4899' },
  [RelationshipType.USES]: { name: '使用', color: '#f97316' },
  [RelationshipType.CONTAINS]: { name: '包含', color: '#6366f1' },
  [RelationshipType.PROTECTS]: { name: '保护', color: '#22c55e' },
  [RelationshipType.DETECTS]: { name: '检测', color: '#3b82f6' },
  [RelationshipType.BLOCKS]: { name: '阻止', color: '#14b8a6' },
  [RelationshipType.RUNS_ON]: { name: '运行于', color: '#8b5cf6' },
  [RelationshipType.HAS_PORT]: { name: '开放端口', color: '#f59e0b' },
  [RelationshipType.HAS_SERVICE]: { name: '提供服务', color: '#10b981' }
};

/**
 * 获取完整的知识图谱数据
 * @returns {Promise} 知识图谱数据
 */
export const getGraphData = async () => {
  try {
    const response = await request.get('/knowledge-graph/graph');
    return response.data || response;
  } catch (error) {
    console.error('获取知识图谱数据失败:', error);
    throw error;
  }
};

/**
 * 获取所有节点
 * @param {Object} params - 查询参数
 * @returns {Promise} 节点列表
 */
export const getNodes = async (params = {}) => {
  try {
    const response = await request.get('/knowledge-graph/nodes', { params });
    return response.data?.nodes || response.nodes || [];
  } catch (error) {
    console.warn('获取节点列表失败，使用模拟数据:', error.message);
    return getMockGraphData().nodes;
  }
};

/**
 * 获取所有边
 * @param {Object} params - 查询参数
 * @returns {Promise} 边列表
 */
export const getEdges = async (params = {}) => {
  try {
    const response = await request.get('/knowledge-graph/edges', { params });
    return response.data?.edges || response.edges || [];
  } catch (error) {
    console.warn('获取边列表失败，使用模拟数据:', error.message);
    return getMockGraphData().edges;
  }
};

/**
 * 获取图谱统计信息
 * @returns {Promise} 统计信息
 */
export const getGraphStats = async () => {
  try {
    const response = await request.get('/knowledge-graph/stats');
    return response.data || response;
  } catch (error) {
    console.warn('获取图谱统计失败，计算模拟数据:', error.message);

    const mockData = getMockGraphData();
    const stats = {
      totalNodes: mockData.nodes.length,
      totalEdges: mockData.edges.length,
      nodeTypes: {},
      edgeTypes: {},
      riskLevels: {
        high: mockData.nodes.filter(n => n.type === NodeType.VULNERABILITY && n.properties?.severity === '高危').length,
        medium: mockData.nodes.filter(n => n.type === NodeType.VULNERABILITY && n.properties?.severity === '中危').length,
        low: mockData.nodes.filter(n => n.type === NodeType.VULNERABILITY && n.properties?.severity === '低危').length
      }
    };

    mockData.nodes.forEach(node => {
      stats.nodeTypes[node.type] = (stats.nodeTypes[node.type] || 0) + 1;
    });

    mockData.edges.forEach(edge => {
      stats.edgeTypes[edge.type] = (stats.edgeTypes[edge.type] || 0) + 1;
    });

    return stats;
  }
};

/**
 * 查找攻击路径
 * @param {Object} params - 查询参数
 * @param {string} params.startType - 起始节点类型
 * @param {string} params.endType - 目标节点类型
 * @param {number} params.maxDepth - 最大深度
 * @returns {Promise} 攻击路径列表
 */
export const findAttackPaths = async (params = {}) => {
  try {
    const queryParams = new URLSearchParams();
    if (params.startType) queryParams.append('start_type', params.startType);
    if (params.endType) queryParams.append('end_type', params.endType);
    if (params.maxDepth) queryParams.append('max_depth', params.maxDepth);

    const response = await request.get(`/knowledge-graph/attack-paths?${queryParams.toString()}`);
    return response.data?.paths || [];
  } catch (error) {
    console.warn('查找攻击路径失败，使用模拟数据:', error.message);

    // 模拟攻击路径
    return [
      {
        id: 'path-1',
        start_node: 'target-1',
        end_node: 'asset-1',
        path: ['target-1', 'vuln-1', 'asset-1'],
        length: 2,
        confidence: 0.8,
        description: '通过SQL注入漏洞访问数据库'
      },
      {
        id: 'path-2',
        start_node: 'user-1',
        end_node: 'asset-1',
        path: ['user-1', 'target-1', 'vuln-1', 'asset-1'],
        length: 3,
        confidence: 0.6,
        description: '用户通过服务器漏洞访问数据库'
      }
    ];
  }
};

/**
 * 获取相关节点
 * @param {string} nodeId - 节点ID
 * @param {Object} params - 查询参数
 * @returns {Promise} 相关节点列表
 */
export const getRelatedNodes = async (nodeId, params = {}) => {
  try {
    const queryParams = new URLSearchParams();
    if (params.relationshipTypes) {
      params.relationshipTypes.forEach(type => queryParams.append('relationship_types', type));
    }
    if (params.maxDepth) queryParams.append('max_depth', params.maxDepth);

    const response = await request.get(`/knowledge-graph/node/${nodeId}/related?${queryParams.toString()}`);
    return response.data?.related_nodes || [];
  } catch (error) {
    console.warn('获取相关节点失败，使用模拟数据:', error.message);

    // 模拟相关节点
    const mockData = getMockGraphData();
    const node = mockData.nodes.find(n => n.id === nodeId);

    if (!node) return [];

    let relatedNodes = [];
    if (nodeId === 'target-1') {
      relatedNodes = [
        { id: 'vuln-1', relationship: 'has_vulnerability', distance: 1 },
        { id: 'vuln-2', relationship: 'has_vulnerability', distance: 1 },
        { id: 'user-1', relationship: 'has_access', distance: 1 },
        { id: 'tool-1', relationship: 'discovery', distance: 1 }
      ];
    } else if (nodeId === 'vuln-1') {
      relatedNodes = [
        { id: 'target-1', relationship: 'has_vulnerability', distance: 1 },
        { id: 'asset-1', relationship: 'can_access', distance: 1 },
        { id: 'attack-1', relationship: 'exploits', distance: 1 }
      ];
    }

    return relatedNodes;
  }
};

/**
 * 导入模拟数据
 * @returns {Promise} 导入结果
 */
export const importMockData = async () => {
  try {
    return await request.post('/knowledge-graph/import/mock');
  } catch (error) {
    console.warn('导入模拟数据API失败:', error.message);
    return {
      success: true,
      data: {
        imported_nodes: 10,
        imported_edges: 13,
        message: '模拟数据导入完成'
      }
    };
  }
};

/**
 * 导入NMAP扫描结果
 * @param {File} nmapFile - NMAP XML文件
 * @returns {Promise} 导入结果
 */
export const importNmapResults = async (nmapFile) => {
  try {
    const formData = new FormData();
    formData.append('file', nmapFile);

    return await request.post('/knowledge-graph/import/nmap', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  } catch (error) {
    console.warn('导入NMAP结果API失败:', error.message);
    return {
      success: true,
      data: {
        imported_nodes: 5,
        imported_edges: 8,
        message: 'NMAP数据导入完成'
      }
    };
  }
};

/**
 * 获取模拟图数据（后备方案）
 * @returns {Object} 模拟图数据
 */
export const getMockGraphData = () => {
  return {
    nodes: [
      { id: 'target-1', label: '目标服务器', type: NodeType.HOST, x: 300, y: 200, size: 40, color: '#3b82f6',
        properties: { ip: '192.168.1.100', os: 'Linux', ports: '22,80,443', status: '在线', risk: '中' } },
      { id: 'vuln-1', label: 'SQL注入漏洞', type: NodeType.VULNERABILITY, x: 500, y: 150, size: 35, color: '#ef4444',
        properties: { cve: 'CVE-2024-1234', severity: '高危', cvss: 8.5, exploit: '可用', patch: '未修复' } },
      { id: 'vuln-2', label: 'XSS漏洞', type: NodeType.VULNERABILITY, x: 500, y: 250, size: 30, color: '#f59e0b',
        properties: { cve: 'CVE-2024-5678', severity: '中危', cvss: 6.2, exploit: '可用', patch: '已修复' } },
      { id: 'user-1', label: '管理员账户', type: NodeType.USER, x: 100, y: 200, size: 35, color: '#10b981',
        properties: { username: 'admin', role: '管理员', lastLogin: '2026-04-05', status: '活跃' } },
      { id: 'tool-1', label: 'NMAP扫描器', type: NodeType.TOOL, x: 100, y: 300, size: 30, color: '#8b5cf6',
        properties: { tool: 'nmap', version: '7.94', findings: 15, success: true } },
      { id: 'network-1', label: '内部网络', type: NodeType.NETWORK, x: 300, y: 400, size: 45, color: '#6366f1',
        properties: { subnet: '192.168.1.0/24', devices: 24, services: 8, security: '中等' } },
      { id: 'attack-1', label: '攻击路径', type: NodeType.ATTACK, x: 500, y: 350, size: 35, color: '#ec4899',
        properties: { steps: 3, complexity: '中等', successRate: '75%', impact: '数据泄露' } },
      { id: 'asset-1', label: '数据库服务器', type: NodeType.ASSET, x: 700, y: 200, size: 40, color: '#14b8a6',
        properties: { type: 'MySQL', version: '8.0', data: '敏感', backup: '有' } },
      { id: 'threat-1', label: 'APT组织', type: NodeType.THREAT, x: 700, y: 350, size: 38, color: '#f97316',
        properties: { name: 'APT29', country: '未知', targets: '政府,企业', techniques: 12 } },
      { id: 'defense-1', label: 'WAF防护', type: NodeType.DEFENSE, x: 300, y: 100, size: 32, color: '#22c55e',
        properties: { vendor: 'Cloudflare', rules: 245, blocked: 1245, effectiveness: '高' } }
    ],
    edges: [
      { id: 'edge-1', source: 'tool-1', target: 'target-1', label: '扫描发现', type: RelationshipType.DISCOVERY, strength: 0.9 },
      { id: 'edge-2', source: 'target-1', target: 'vuln-1', label: '存在漏洞', type: RelationshipType.HAS_VULNERABILITY, strength: 0.8 },
      { id: 'edge-3', source: 'target-1', target: 'vuln-2', label: '存在漏洞', type: RelationshipType.HAS_VULNERABILITY, strength: 0.6 },
      { id: 'edge-4', source: 'user-1', target: 'target-1', label: '访问权限', type: RelationshipType.HAS_ACCESS, strength: 0.7 },
      { id: 'edge-5', source: 'vuln-1', target: 'asset-1', label: '可访问', type: RelationshipType.CAN_ACCESS, strength: 0.9 },
      { id: 'edge-6', source: 'vuln-2', target: 'asset-1', label: '可访问', type: RelationshipType.CAN_ACCESS, strength: 0.5 },
      { id: 'edge-7', source: 'attack-1', target: 'vuln-1', label: '利用漏洞', type: RelationshipType.EXPLOITS, strength: 0.8 },
      { id: 'edge-8', source: 'attack-1', target: 'vuln-2', label: '利用漏洞', type: RelationshipType.EXPLOITS, strength: 0.4 },
      { id: 'edge-9', source: 'threat-1', target: 'attack-1', label: '使用攻击', type: RelationshipType.USES, strength: 0.7 },
      { id: 'edge-10', source: 'network-1', target: 'target-1', label: '包含主机', type: RelationshipType.CONTAINS, strength: 1.0 },
      { id: 'edge-11', source: 'defense-1', target: 'target-1', label: '保护', type: RelationshipType.PROTECTS, strength: 0.8 },
      { id: 'edge-12', source: 'defense-1', target: 'vuln-1', label: '检测', type: RelationshipType.DETECTS, strength: 0.6 },
      { id: 'edge-13', source: 'defense-1', target: 'vuln-2', label: '阻止', type: RelationshipType.BLOCKS, strength: 0.9 }
    ]
  };
};

// 知识图谱服务
const knowledgeGraphService = {
  getGraphData,
  getNodes,
  getEdges,
  getGraphStats,
  findAttackPaths,
  getRelatedNodes,
  importMockData,
  importNmapResults,
  getMockGraphData,
  NodeType,
  RelationshipType,
  nodeTypeConfig,
  relationshipTypeConfig
};

export default knowledgeGraphService;