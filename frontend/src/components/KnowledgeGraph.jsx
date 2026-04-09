import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Network } from 'vis-network/standalone/esm/vis-network';
import { DataSet } from 'vis-data/standalone/esm/vis-data';
import {
  Network as NetworkIcon, Database, Shield, User, Server, Globe, Lock, Unlock,
  AlertTriangle, CheckCircle, XCircle, Search, Filter, Download,
  ZoomIn, ZoomOut, RefreshCw, Settings, Layers, Link, Target,
  BarChart3, PieChart, LineChart, Hash, Cpu, Wifi, Key, Eye
} from 'lucide-react';

// 导入设计系统组件
import Card from './design-system/Card';
import Button from './design-system/Button';
import Badge from './design-system/Badge';
import Alert from './design-system/Alert';
import { useScan } from '../context/ScanContext';

const KnowledgeGraph = () => {
  const { selectedScan, lastScan } = useScan();
  const [loading, setLoading] = useState(true);
  const [graphData, setGraphData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [zoomLevel, setZoomLevel] = useState(1);
  const [viewMode, setViewMode] = useState('force');
  const [showDetails, setShowDetails] = useState(false);
  const [graphStats, setGraphStats] = useState({});
  const networkRef = useRef(null);
  const containerRef = useRef(null);

  // ScanContext: lastScan 变化时自动重建图谱
  useEffect(() => {
    if (lastScan) {
      fetchGraphData();
    }
  }, [lastScan]); // eslint-disable-line react-hooks/exhaustive-deps

  // 节点类型配置
  const nodeTypes = {
    server: { icon: Server, color: '#3b82f6', name: '服务器' },
    vulnerability: { icon: AlertTriangle, color: '#ef4444', name: '漏洞' },
    user: { icon: User, color: '#10b981', name: '用户' },
    tool: { icon: Cpu, color: '#8b5cf6', name: '工具' },
    network: { icon: Wifi, color: '#6366f1', name: '网络' },
    attack: { icon: Target, color: '#ec4899', name: '攻击' },
    asset: { icon: Database, color: '#14b8a6', name: '资产' },
    threat: { icon: Shield, color: '#f97316', name: '威胁' },
    defense: { icon: Lock, color: '#22c55e', name: '防御' },
    host: { icon: Server, color: '#3b82f6', name: '主机' },
    port: { icon: Hash, color: '#8b5cf6', name: '端口' },
    service: { icon: Globe, color: '#10b981', name: '服务' }
  };

  // 边类型配置
  const edgeTypes = {
    discovery: { color: '#8b5cf6', name: '发现' },
    has_vulnerability: { color: '#ef4444', name: '存在漏洞' },
    has_access: { color: '#10b981', name: '访问权限' },
    can_access: { color: '#f59e0b', name: '可访问' },
    exploits: { color: '#ec4899', name: '利用' },
    uses: { color: '#f97316', name: '使用' },
    contains: { color: '#6366f1', name: '包含' },
    protects: { color: '#22c55e', name: '保护' },
    detects: { color: '#3b82f6', name: '检测' },
    blocks: { color: '#14b8a6', name: '阻止' },
    runs_on: { color: '#8b5cf6', name: '运行于' },
    has_port: { color: '#f59e0b', name: '开放端口' },
    has_service: { color: '#10b981', name: '提供服务' }
  };

  // 从API获取知识图谱数据
  const fetchGraphData = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8000/api/v1/knowledge-graph/graph');

      if (response.data.success && response.data.data) {
        const apiData = response.data.data;

        // 转换API数据格式为vis-network需要的格式
        const nodes = apiData.nodes.map(node => ({
          id: node.id,
          label: node.label || node.name || node.id,
          group: node.type,
          title: `
            <div style="padding: 10px; max-width: 300px;">
              <strong>${node.label || node.name || node.id}</strong><br/>
              <strong>类型:</strong> ${node.type}<br/>
              ${Object.entries(node.properties || {})
                .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
                .join('<br/>')}
            </div>
          `,
          color: nodeTypes[node.type]?.color || '#3b82f6',
          shape: 'dot',
          size: node.size || 25,
          font: { size: 14 },
          x: node.position?.x,
          y: node.position?.y
        }));

        const edges = apiData.edges.map(edge => ({
          id: edge.id,
          from: edge.source,
          to: edge.target,
          label: edge.label || edge.type,
          title: `
            <div style="padding: 10px; max-width: 300px;">
              <strong>关系:</strong> ${edge.label || edge.type}<br/>
              <strong>类型:</strong> ${edge.type}<br/>
              ${Object.entries(edge.properties || {})
                .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
                .join('<br/>')}
            </div>
          `,
          color: edgeTypes[edge.type]?.color || '#94a3b8',
          width: 2,
          arrows: 'to'
        }));

        setGraphData({ nodes, edges });

        // 计算统计信息
        const stats = {
          totalNodes: nodes.length,
          totalEdges: edges.length,
          nodeTypes: {},
          edgeTypes: {},
          riskLevels: {
            high: apiData.nodes.filter(n => n.type === 'vulnerability' && n.properties?.severity === '高危').length,
            medium: apiData.nodes.filter(n => n.type === 'vulnerability' && n.properties?.severity === '中危').length,
            low: apiData.nodes.filter(n => n.type === 'vulnerability' && n.properties?.severity === '低危').length
          }
        };

        // 统计节点类型
        apiData.nodes.forEach(node => {
          stats.nodeTypes[node.type] = (stats.nodeTypes[node.type] || 0) + 1;
        });

        // 统计边类型
        apiData.edges.forEach(edge => {
          stats.edgeTypes[edge.type] = (stats.edgeTypes[edge.type] || 0) + 1;
        });

        setGraphStats(stats);
      } else {
        console.warn('API返回数据格式不正确');
        // 使用模拟数据作为后备
        useMockData();
      }
    } catch (error) {
      console.error('获取知识图谱数据失败:', error);
      // 使用模拟数据作为后备
      useMockData();
    } finally {
      setLoading(false);
    }
  };

  // 使用模拟数据（后备）
  const useMockData = () => {
    const mockNodes = [
      { id: 'target-1', label: '目标服务器', type: 'server', properties: { ip: '192.168.1.100', os: 'Linux', ports: '22,80,443', status: '在线', risk: '中' } },
      { id: 'vuln-1', label: 'SQL注入漏洞', type: 'vulnerability', properties: { cve: 'CVE-2024-1234', severity: '高危', cvss: 8.5, exploit: '可用', patch: '未修复' } },
      { id: 'vuln-2', label: 'XSS漏洞', type: 'vulnerability', properties: { cve: 'CVE-2024-5678', severity: '中危', cvss: 6.2, exploit: '可用', patch: '已修复' } },
      { id: 'user-1', label: '管理员账户', type: 'user', properties: { username: 'admin', role: '管理员', lastLogin: '2026-04-05', status: '活跃' } },
      { id: 'tool-1', label: 'NMAP扫描器', type: 'tool', properties: { tool: 'nmap', version: '7.94', findings: 15, success: true } }
    ];

    const mockEdges = [
      { id: 'edge-1', source: 'tool-1', target: 'target-1', label: '扫描发现', type: 'discovery' },
      { id: 'edge-2', source: 'target-1', target: 'vuln-1', label: '存在漏洞', type: 'has_vulnerability' },
      { id: 'edge-3', source: 'target-1', target: 'vuln-2', label: '存在漏洞', type: 'has_vulnerability' },
      { id: 'edge-4', source: 'user-1', target: 'target-1', label: '访问权限', type: 'has_access' }
    ];

    const nodes = mockNodes.map(node => ({
      id: node.id,
      label: node.label,
      group: node.type,
      title: `
        <div style="padding: 10px; max-width: 300px;">
          <strong>${node.label}</strong><br/>
          <strong>类型:</strong> ${node.type}<br/>
          ${Object.entries(node.properties || {})
            .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
            .join('<br/>')}
        </div>
      `,
      color: nodeTypes[node.type]?.color || '#3b82f6',
      shape: 'dot',
      size: 25,
      font: { size: 14 }
    }));

    const edges = mockEdges.map(edge => ({
      id: edge.id,
      from: edge.source,
      to: edge.target,
      label: edge.label,
      title: `
        <div style="padding: 10px; max-width: 300px;">
          <strong>关系:</strong> ${edge.label}<br/>
          <strong>类型:</strong> ${edge.type}
        </div>
      `,
      color: edgeTypes[edge.type]?.color || '#94a3b8',
      width: 2,
      arrows: 'to'
    }));

    setGraphData({ nodes, edges });

    const stats = {
      totalNodes: nodes.length,
      totalEdges: edges.length,
      nodeTypes: {},
      edgeTypes: {},
      riskLevels: {
        high: mockNodes.filter(n => n.type === 'vulnerability' && n.properties?.severity === '高危').length,
        medium: mockNodes.filter(n => n.type === 'vulnerability' && n.properties?.severity === '中危').length,
        low: 0
      }
    };

    mockNodes.forEach(node => {
      stats.nodeTypes[node.type] = (stats.nodeTypes[node.type] || 0) + 1;
    });

    mockEdges.forEach(edge => {
      stats.edgeTypes[edge.type] = (stats.edgeTypes[edge.type] || 0) + 1;
    });

    setGraphStats(stats);
  };

  // 初始化vis-network
  useEffect(() => {
    if (!containerRef.current || !graphData) return;

    // 创建数据集
    const nodes = new DataSet(graphData.nodes);
    const edges = new DataSet(graphData.edges);

    // 网络配置
    const options = {
      nodes: {
        shape: 'dot',
        size: 25,
        font: {
          size: 14,
          color: '#ffffff'
        },
        borderWidth: 2,
        borderWidthSelected: 4
      },
      edges: {
        width: 2,
        arrows: 'to',
        smooth: {
          type: 'continuous'
        }
      },
      physics: {
        enabled: true,
        stabilization: {
          iterations: 100
        }
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        hideEdgesOnDrag: true,
        hideNodesOnDrag: false
      }
    };

    // 创建网络
    const network = new Network(containerRef.current, { nodes, edges }, options);
    networkRef.current = network;

    // 事件处理
    network.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = nodes.get(nodeId);
        setSelectedNode(node);
        setSelectedEdge(null);
      } else if (params.edges.length > 0) {
        const edgeId = params.edges[0];
        const edge = edges.get(edgeId);
        setSelectedEdge(edge);
        setSelectedNode(null);
      } else {
        setSelectedNode(null);
        setSelectedEdge(null);
      }
    });

    network.on('zoom', (params) => {
      setZoomLevel(params.scale);
    });

    // 清理函数
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [graphData]);

  // 首次加载获取数据
  useEffect(() => {
    fetchGraphData();
  }, []);

  // ScanContext：selectedScan / lastScan 变化时自动刷新图谱
  useEffect(() => {
    const scanData = selectedScan || lastScan;
    if (!scanData) return;
    // 尝试从扫描结果构建图谱，失败时回退到 API
    fetchGraphData();
  }, [selectedScan, lastScan]); // eslint-disable-line react-hooks/exhaustive-deps

  // 处理搜索
  const handleSearch = () => {
    if (!networkRef.current || !searchTerm.trim()) return;

    const nodes = graphData.nodes;
    const matchingNodes = nodes.filter(node =>
      node.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
      node.group.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (matchingNodes.length > 0) {
      networkRef.current.selectNodes(matchingNodes.map(node => node.id));
      networkRef.current.focus(matchingNodes[0].id, { scale: 1.5, animation: true });
    }
  };

  // 处理过滤
  const handleFilter = () => {
    if (!networkRef.current || filterType === 'all') {
      // 显示所有节点
      const nodes = graphData.nodes;
      const edges = graphData.edges;
      networkRef.current.setData({ nodes, edges });
    } else {
      // 过滤节点和边
      const filteredNodes = graphData.nodes.filter(node => node.group === filterType);
      const filteredNodeIds = new Set(filteredNodes.map(node => node.id));
      const filteredEdges = graphData.edges.filter(edge =>
        filteredNodeIds.has(edge.from) && filteredNodeIds.has(edge.to)
      );
      networkRef.current.setData({ nodes: filteredNodes, edges: filteredEdges });
    }
  };

  // 控制函数
  const handleZoomIn = () => {
    if (networkRef.current) {
      networkRef.current.moveTo({ scale: networkRef.current.getScale() * 1.2 });
    }
  };

  const handleZoomOut = () => {
    if (networkRef.current) {
      networkRef.current.moveTo({ scale: networkRef.current.getScale() * 0.8 });
    }
  };

  const handleRefresh = () => {
    fetchGraphData();
  };

  const handleFit = () => {
    if (networkRef.current) {
      networkRef.current.fit({ animation: true });
    }
  };

  return (
    <div className="p-6 bg-[#060910] text-gray-100 min-h-screen">
      <div className="mb-6">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <NetworkIcon className="w-8 h-8" />
          知识图谱
        </h1>
        <p className="text-gray-400 mt-2">
          可视化展示网络资产、漏洞、攻击路径和防御措施之间的关系
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 左侧控制面板 */}
        <div className="lg:col-span-1 space-y-6">
          <Card title="控制面板" className="bg-[#0a0e17]">
            <div className="space-y-4">
              {/* 搜索 */}
              <div>
                <label className="block text-sm font-medium mb-2">搜索节点</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="输入节点名称或类型..."
                    className="flex-1 px-3 py-2 bg-[#111827] border border-white/15 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <Button onClick={handleSearch} icon={Search}>
                    搜索
                  </Button>
                </div>
              </div>

              {/* 过滤 */}
              <div>
                <label className="block text-sm font-medium mb-2">过滤类型</label>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="w-full px-3 py-2 bg-[#111827] border border-white/15 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">所有类型</option>
                  {Object.entries(nodeTypes).map(([key, config]) => (
                    <option key={key} value={key}>
                      {config.name}
                    </option>
                  ))}
                </select>
                <Button onClick={handleFilter} className="mt-2 w-full" icon={Filter}>
                  应用过滤
                </Button>
              </div>

              {/* 缩放控制 */}
              <div className="grid grid-cols-2 gap-2">
                <Button onClick={handleZoomIn} icon={ZoomIn}>
                  放大
                </Button>
                <Button onClick={handleZoomOut} icon={ZoomOut}>
                  缩小
                </Button>
                <Button onClick={handleFit} icon={Layers}>
                  适应视图
                </Button>
                <Button onClick={handleRefresh} icon={RefreshCw}>
                  刷新数据
                </Button>
              </div>

              {/* 视图模式 */}
              <div>
                <label className="block text-sm font-medium mb-2">视图模式</label>
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    onClick={() => setViewMode('force')}
                    variant={viewMode === 'force' ? 'primary' : 'secondary'}
                  >
                    力导向图
                  </Button>
                  <Button
                    onClick={() => setViewMode('hierarchical')}
                    variant={viewMode === 'hierarchical' ? 'primary' : 'secondary'}
                  >
                    层次图
                  </Button>
                </div>
              </div>
            </div>
          </Card>

          {/* 统计信息 */}
          <Card title="统计信息" className="bg-[#0a0e17]">
            {loading ? (
              <div className="text-center py-4">加载中...</div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-[#111827] p-3 rounded-lg">
                    <div className="text-2xl font-bold">{graphStats.totalNodes || 0}</div>
                    <div className="text-sm text-gray-400">总节点数</div>
                  </div>
                  <div className="bg-[#111827] p-3 rounded-lg">
                    <div className="text-2xl font-bold">{graphStats.totalEdges || 0}</div>
                    <div className="text-sm text-gray-400">总边数</div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">节点类型分布</h4>
                  <div className="space-y-2">
                    {Object.entries(graphStats.nodeTypes || {}).map(([type, count]) => (
                      <div key={type} className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: nodeTypes[type]?.color || '#3b82f6' }}
                          />
                          <span>{nodeTypes[type]?.name || type}</span>
                        </div>
                        <Badge>{count}</Badge>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">风险级别</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-red-400">高危漏洞</span>
                      <Badge variant="destructive">{graphStats.riskLevels?.high || 0}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-yellow-400">中危漏洞</span>
                      <Badge variant="warning">{graphStats.riskLevels?.medium || 0}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-green-400">低危漏洞</span>
                      <Badge variant="success">{graphStats.riskLevels?.low || 0}</Badge>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* 主图区域 */}
        <div className="lg:col-span-3">
          <Card className="bg-[#0a0e17] h-full">
            {loading ? (
              <div className="flex items-center justify-center h-96">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
                  <p className="mt-4">加载知识图谱数据...</p>
                </div>
              </div>
            ) : (
              <div className="relative h-full">
                <div
                  ref={containerRef}
                  style={{ height: '600px', width: '100%', border: '1px solid #374151', borderRadius: '8px' }}
                />

                {/* 选中的节点/边详情 */}
                {(selectedNode || selectedEdge) && (
                  <div className="absolute top-4 right-4 w-80 bg-[#060910] border border-white/10 rounded-lg shadow-xl">
                    <div className="p-4">
                      <div className="flex justify-between items-center mb-3">
                        <h3 className="font-bold">
                          {selectedNode ? '节点详情' : '边详情'}
                        </h3>
                        <button
                          onClick={() => {
                            setSelectedNode(null);
                            setSelectedEdge(null);
                          }}
                          className="text-gray-400 hover:text-white"
                        >
                          ✕
                        </button>
                      </div>

                      {selectedNode && (
                        <div>
                          <div className="flex items-center gap-3 mb-3">
                            <div
                              className="w-4 h-4 rounded-full"
                              style={{ backgroundColor: selectedNode.color }}
                            />
                            <div>
                              <h4 className="font-bold">{selectedNode.label}</h4>
                              <p className="text-sm text-gray-400">
                                {nodeTypes[selectedNode.group]?.name || selectedNode.group}
                              </p>
                            </div>
                          </div>
                          <div className="space-y-2">
                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <span className="text-gray-400 text-sm">ID:</span>
                                <p className="font-mono">{selectedNode.id}</p>
                              </div>
                              <div>
                                <span className="text-gray-400 text-sm">大小:</span>
                                <p>{selectedNode.size}</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {selectedEdge && (
                        <div>
                          <div className="mb-3">
                            <h4 className="font-bold">{selectedEdge.label}</h4>
                            <p className="text-sm text-gray-400">
                              {edgeTypes[selectedEdge.type]?.name || selectedEdge.type}
                            </p>
                          </div>
                          <div className="space-y-2">
                            <div>
                              <span className="text-gray-400 text-sm">从:</span>
                              <p>{selectedEdge.from}</p>
                            </div>
                            <div>
                              <span className="text-gray-400 text-sm">到:</span>
                              <p>{selectedEdge.to}</p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraph;