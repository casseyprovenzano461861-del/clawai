import React, { useState, useEffect } from 'react';
import {
  Package, Plug, Settings, Download, Upload, Trash2, RefreshCw,
  Play, StopCircle, CheckCircle, XCircle, AlertCircle, Search,
  Filter, Star, ExternalLink, Code, Shield, Database, Network,
  BarChart3, FileText, Globe, Lock, Unlock, MoreVertical,
  ChevronRight, ChevronDown, Info, HelpCircle, DownloadCloud
} from 'lucide-react';

// 导入设计系统组件
import Card from './design-system/Card';
import Button from './design-system/Button';
import Badge from './design-system/Badge';
import Alert from './design-system/Alert';

// 导入插件服务
import pluginService, {
  PluginStatus,
  PluginType
} from '../services/pluginService';

const PluginManager = () => {
  const [plugins, setPlugins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedPlugin, setSelectedPlugin] = useState(null);
  const [showPluginModal, setShowPluginModal] = useState(false);
  const [showInstallModal, setShowInstallModal] = useState(false);
  const [activeTab, setActiveTab] = useState('installed');

  // 模拟插件数据
  const mockPlugins = [
    {
      id: 'nmap-scanner',
      name: 'NMAP 扫描器',
      version: '2.1.0',
      author: 'ClawAI Team',
      description: '高级网络扫描和端口检测插件',
      category: 'scanner',
      status: 'active',
      installed: true,
      enabled: true,
      rating: 4.8,
      downloads: 1245,
      lastUpdated: '2026-04-01',
      size: '2.4 MB',
      dependencies: ['python-nmap', 'networkx'],
      permissions: ['network:scan', 'port:detect', 'service:identify'],
      icon: 'shield',
      homepage: 'https://github.com/clawai/nmap-scanner',
      license: 'MIT'
    },
    {
      id: 'vulnerability-db',
      name: '漏洞数据库',
      version: '1.3.2',
      author: 'Security Research Team',
      description: '集成CVE/NVD漏洞数据库，提供实时漏洞信息',
      category: 'database',
      status: 'active',
      installed: true,
      enabled: true,
      rating: 4.9,
      downloads: 892,
      lastUpdated: '2026-03-28',
      size: '15.7 MB',
      dependencies: ['requests', 'sqlite3'],
      permissions: ['vuln:read', 'cve:query', 'db:update'],
      icon: 'database',
      homepage: 'https://github.com/clawai/vulnerability-db',
      license: 'Apache-2.0'
    },
    {
      id: 'report-exporter',
      name: '报告导出器',
      version: '1.2.1',
      author: 'ClawAI Team',
      description: '支持多种格式的报告导出（PDF、HTML、JSON、CSV）',
      category: 'export',
      status: 'active',
      installed: true,
      enabled: true,
      rating: 4.7,
      downloads: 756,
      lastUpdated: '2026-03-25',
      size: '1.8 MB',
      dependencies: ['reportlab', 'pandas'],
      permissions: ['report:export', 'file:write'],
      icon: 'file-text',
      homepage: 'https://github.com/clawai/report-exporter',
      license: 'MIT'
    },
    {
      id: 'web-crawler',
      name: 'Web爬虫',
      version: '1.0.3',
      author: 'Web Security Team',
      description: '高级Web爬虫，支持JavaScript渲染和表单发现',
      category: 'crawler',
      status: 'inactive',
      installed: true,
      enabled: false,
      rating: 4.5,
      downloads: 432,
      lastUpdated: '2026-03-20',
      size: '3.2 MB',
      dependencies: ['selenium', 'beautifulsoup4'],
      permissions: ['web:crawl', 'js:execute', 'form:detect'],
      icon: 'globe',
      homepage: 'https://github.com/clawai/web-crawler',
      license: 'GPL-3.0'
    },
    {
      id: 'ai-threat-detector',
      name: 'AI威胁检测器',
      version: '0.9.1',
      author: 'AI Research Lab',
      description: '基于机器学习的异常检测和威胁识别',
      category: 'ai',
      status: 'available',
      installed: false,
      enabled: false,
      rating: 4.6,
      downloads: 321,
      lastUpdated: '2026-04-05',
      size: '8.5 MB',
      dependencies: ['tensorflow', 'scikit-learn', 'numpy'],
      permissions: ['ai:analyze', 'threat:detect', 'anomaly:identify'],
      icon: 'brain',
      homepage: 'https://github.com/clawai/ai-threat-detector',
      license: 'MIT'
    },
    {
      id: 'api-security',
      name: 'API安全测试',
      version: '1.1.0',
      author: 'API Security Team',
      description: 'REST API安全测试和漏洞扫描',
      category: 'api',
      status: 'available',
      installed: false,
      enabled: false,
      rating: 4.4,
      downloads: 287,
      lastUpdated: '2026-03-30',
      size: '2.1 MB',
      dependencies: ['requests', 'jsonschema'],
      permissions: ['api:test', 'endpoint:scan', 'auth:test'],
      icon: 'network',
      homepage: 'https://github.com/clawai/api-security',
      license: 'MIT'
    },
    {
      id: 'compliance-checker',
      name: '合规性检查器',
      version: '1.0.2',
      author: 'Compliance Team',
      description: 'GDPR、HIPAA、PCI-DSS等合规性检查',
      category: 'compliance',
      status: 'available',
      installed: false,
      enabled: false,
      rating: 4.3,
      downloads: 198,
      lastUpdated: '2026-03-22',
      size: '4.3 MB',
      dependencies: ['yaml', 'json'],
      permissions: ['compliance:check', 'regulation:validate'],
      icon: 'shield-check',
      homepage: 'https://github.com/clawai/compliance-checker',
      license: 'Apache-2.0'
    },
    {
      id: 'dashboard-widgets',
      name: '仪表盘小部件',
      version: '1.2.0',
      author: 'UI Team',
      description: '额外的仪表盘小部件和可视化组件',
      category: 'ui',
      status: 'available',
      installed: false,
      enabled: false,
      rating: 4.7,
      downloads: 543,
      lastUpdated: '2026-04-02',
      size: '1.2 MB',
      dependencies: ['react-chartjs-2', 'recharts'],
      permissions: ['ui:widget', 'dashboard:customize'],
      icon: 'layout',
      homepage: 'https://github.com/clawai/dashboard-widgets',
      license: 'MIT'
    }
  ];

  // 插件类别
  const pluginCategories = [
    { id: 'all', name: '所有类别', color: 'gray' },
    { id: 'scanner', name: '扫描器', color: 'blue', icon: 'shield' },
    { id: 'database', name: '数据库', color: 'green', icon: 'database' },
    { id: 'export', name: '导出工具', color: 'purple', icon: 'file-text' },
    { id: 'crawler', name: '爬虫', color: 'orange', icon: 'globe' },
    { id: 'ai', name: '人工智能', color: 'red', icon: 'brain' },
    { id: 'api', name: 'API工具', color: 'indigo', icon: 'network' },
    { id: 'compliance', name: '合规性', color: 'yellow', icon: 'shield-check' },
    { id: 'ui', name: '界面组件', color: 'pink', icon: 'layout' }
  ];

  // 插件状态
  const pluginStatuses = [
    { id: 'all', name: '所有状态' },
    { id: 'active', name: '已激活' },
    { id: 'inactive', name: '已禁用' },
    { id: 'available', name: '可安装' },
    { id: 'updating', name: '更新中' },
    { id: 'error', name: '错误' }
  ];

  useEffect(() => {
    fetchPlugins();
  }, []);

  // 从API获取插件列表
  const fetchPlugins = async () => {
    setLoading(true);
    try {
      const data = await pluginService.getPlugins();
      // 统一数据格式
      const normalized = data.map(p => ({
        id: p.id,
        name: p.name,
        version: p.version,
        author: p.author,
        description: p.description,
        category: p.type || p.category || 'other',
        status: p.status,
        installed: p.status !== PluginStatus.AVAILABLE,
        enabled: p.status === PluginStatus.ACTIVE,
        rating: p.rating || 4.5,
        downloads: p.downloads || 0,
        lastUpdated: p.last_updated || p.lastUpdated || '',
        size: p.size || 'N/A',
        dependencies: p.dependencies || [],
        permissions: p.permissions || [],
        icon: p.icon || 'shield',
        homepage: p.homepage || '#',
        license: p.license || 'MIT'
      }));
      setPlugins(normalized);
    } catch (error) {
      console.error('获取插件列表失败，使用模拟数据:', error);
      setPlugins(mockPlugins);
    } finally {
      setLoading(false);
    }
  };

  const filteredPlugins = plugins.filter(plugin => {
    // 根据标签页过滤
    if (activeTab === 'installed' && !plugin.installed) return false;
    if (activeTab === 'available' && plugin.installed) return false;
    if (activeTab === 'updates' && plugin.status !== 'updating') return false;

    // 搜索过滤
    const matchesSearch = searchTerm === '' || 
      plugin.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      plugin.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      plugin.author.toLowerCase().includes(searchTerm.toLowerCase());
    
    // 类别过滤
    const matchesCategory = filterCategory === 'all' || plugin.category === filterCategory;
    
    // 状态过滤
    const matchesStatus = filterStatus === 'all' || plugin.status === filterStatus;
    
    return matchesSearch && matchesCategory && matchesStatus;
  });

  const getCategoryColor = (category) => {
    const cat = pluginCategories.find(c => c.id === category);
    return cat ? cat.color : 'gray';
  };

  const getCategoryName = (category) => {
    const cat = pluginCategories.find(c => c.id === category);
    return cat ? cat.name : category;
  };

  const getStatusColor = (status) => {
    const statusMap = {
      active: 'green',
      inactive: 'orange',
      available: 'blue',
      updating: 'yellow',
      error: 'red'
    };
    return statusMap[status] || 'gray';
  };

  const getStatusText = (status) => {
    const statusMap = {
      active: '已激活',
      inactive: '已禁用',
      available: '可安装',
      updating: '更新中',
      error: '错误'
    };
    return statusMap[status] || status;
  };

  const handleInstallPlugin = async (pluginId) => {
    try {
      await pluginService.installPlugin(pluginId);
      setPlugins(prev => prev.map(plugin =>
        plugin.id === pluginId
          ? { ...plugin, installed: true, enabled: true, status: PluginStatus.ACTIVE }
          : plugin
      ));
    } catch (error) {
      console.error('安装插件失败:', error);
      alert(`安装失败: ${error.message || '请稍后重试'}`);
    }
  };

  const handleUninstallPlugin = async (pluginId) => {
    const plugin = plugins.find(p => p.id === pluginId);
    if (plugin && window.confirm(`确定要卸载插件 "${plugin.name}" 吗？`)) {
      try {
        await pluginService.uninstallPlugin(pluginId);
        setPlugins(prev => prev.map(p =>
          p.id === pluginId
            ? { ...p, installed: false, enabled: false, status: PluginStatus.AVAILABLE }
            : p
        ));
      } catch (error) {
        console.error('卸载插件失败:', error);
        alert(`卸载失败: ${error.message || '请稍后重试'}`);
      }
    }
  };

  const handleTogglePlugin = async (pluginId) => {
    const plugin = plugins.find(p => p.id === pluginId);
    if (!plugin) return;
    const newEnabled = !plugin.enabled;
    try {
      if (newEnabled) {
        await pluginService.enablePlugin(pluginId);
      } else {
        await pluginService.disablePlugin(pluginId);
      }
      setPlugins(prev => prev.map(p =>
        p.id === pluginId
          ? { ...p, enabled: newEnabled, status: newEnabled ? PluginStatus.ACTIVE : PluginStatus.INACTIVE }
          : p
      ));
    } catch (error) {
      console.error('切换插件状态失败:', error);
      alert(`操作失败: ${error.message || '请稍后重试'}`);
    }
  };

  const handleUpdatePlugin = async (pluginId) => {
    const plugin = plugins.find(p => p.id === pluginId);
    if (!plugin) return;
    // 先在UI中标记为更新中
    setPlugins(prev => prev.map(p =>
      p.id === pluginId ? { ...p, status: PluginStatus.UPDATING } : p
    ));
    try {
      await pluginService.updatePlugin(pluginId);
      // 更新完成，刷新插件列表
      await fetchPlugins();
    } catch (error) {
      console.error('更新插件失败:', error);
      // 恢复原状态
      setPlugins(prev => prev.map(p =>
        p.id === pluginId ? { ...p, status: plugin.status } : p
      ));
      alert(`更新失败: ${error.message || '请稍后重试'}`);
    }
  };

  const handleViewPlugin = (plugin) => {
    setSelectedPlugin(plugin);
    setShowPluginModal(true);
  };

  const StatCard = ({ icon: Icon, title, value, color = 'blue', change }) => {
    const colorClasses = {
      blue: 'text-blue-500',
      green: 'text-green-500',
      red: 'text-red-500',
      purple: 'text-purple-500',
      orange: 'text-orange-500',
      indigo: 'text-indigo-500',
      yellow: 'text-yellow-500',
      pink: 'text-pink-500'
    };

    return (
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div className={`p-2 rounded-lg ${colorClasses[color]}/10`}>
            <Icon className={`w-5 h-5 ${colorClasses[color]}`} />
          </div>
          {change && (
            <Badge variant={change > 0 ? 'success' : 'danger'} size="sm">
              {change > 0 ? '+' : ''}{change}
            </Badge>
          )}
        </div>
        <div className="text-2xl font-bold mb-1">{value}</div>
        <div className="text-sm opacity-70">{title}</div>
      </Card>
    );
  };

  const PluginCard = ({ plugin }) => {
    const categoryColor = getCategoryColor(plugin.category);
    const statusColor = getStatusColor(plugin.status);
    
    return (
      <Card className="p-4 hover:border-blue-500/50 transition-all duration-300">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-4">
          <div className="flex items-start mb-4 md:mb-0">
            <div className={`p-3 rounded-lg bg-${categoryColor}-500/10 mr-4`}>
              {plugin.icon === 'shield' && <Shield className={`w-6 h-6 text-${categoryColor}-500`} />}
              {plugin.icon === 'database' && <Database className={`w-6 h-6 text-${categoryColor}-500`} />}
              {plugin.icon === 'file-text' && <FileText className={`w-6 h-6 text-${categoryColor}-500`} />}
              {plugin.icon === 'globe' && <Globe className={`w-6 h-6 text-${categoryColor}-500`} />}
              {plugin.icon === 'brain' && <BarChart3 className={`w-6 h-6 text-${categoryColor}-500`} />}
              {plugin.icon === 'network' && <Network className={`w-6 h-6 text-${categoryColor}-500`} />}
              {plugin.icon === 'shield-check' && <Shield className={`w-6 h-6 text-${categoryColor}-500`} />}
              {plugin.icon === 'layout' && <Settings className={`w-6 h-6 text-${categoryColor}-500`} />}
            </div>
            
            <div>
              <div className="flex items-center">
                <h3 className="text-lg font-semibold mr-2">{plugin.name}</h3>
                <Badge variant={categoryColor} size="sm">
                  {getCategoryName(plugin.category)}
                </Badge>
              </div>
              <p className="text-sm opacity-70 mt-1">{plugin.description}</p>
              <div className="flex items-center mt-2 space-x-4">
                <div className="flex items-center text-sm">
                  <Star className="w-4 h-4 text-yellow-500 mr-1" />
                  <span>{plugin.rating}</span>
                  <span className="opacity-70 ml-1">({plugin.downloads} 下载)</span>
                </div>
                <div className="text-sm opacity-70">版本 {plugin.version}</div>
                <div className="text-sm opacity-70">作者: {plugin.author}</div>
              </div>
            </div>
          </div>
          
          <div className="flex flex-col items-end">
            <Badge variant={statusColor} size="sm" className="mb-2">
              {getStatusText(plugin.status)}
            </Badge>
            <div className="text-sm opacity-70">{plugin.size}</div>
          </div>
        </div>
        
        <div className="flex flex-col md:flex-row md:items-center justify-between pt-4 border-t border-gray-700/50">
          <div className="flex flex-wrap gap-2 mb-4 md:mb-0">
            {plugin.permissions.slice(0, 3).map(permission => (
              <Badge key={permission} variant="outline" size="xs">
                {permission}
              </Badge>
            ))}
            {plugin.permissions.length > 3 && (
              <Badge variant="outline" size="xs">
                +{plugin.permissions.length - 3} 更多
              </Badge>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleViewPlugin(plugin)}
              className="flex items-center"
            >
              <Info className="w-4 h-4 mr-1" />
              详情
            </Button>
            
            {plugin.installed ? (
              <>
                {plugin.status === 'updating' ? (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled
                    className="flex items-center"
                  >
                    <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
                    更新中
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleUpdatePlugin(plugin.id)}
                    className="flex items-center"
                  >
                    <RefreshCw className="w-4 h-4 mr-1" />
                    更新
                  </Button>
                )}
                
                <Button
                  variant={plugin.enabled ? "outline" : "primary"}
                  size="sm"
                  onClick={() => handleTogglePlugin(plugin.id)}
                  className="flex items-center"
                >
                  {plugin.enabled ? (
                    <>
                      <StopCircle className="w-4 h-4 mr-1" />
                      禁用
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-1" />
                      激活
                    </>
                  )}
                </Button>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleUninstallPlugin(plugin.id)}
                  className="flex items-center text-red-500 hover:text-red-400"
                >
                  <Trash2 className="w-4 h-4 mr-1" />
                  卸载
                </Button>
              </>
            ) : (
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleInstallPlugin(plugin.id)}
                className="flex items-center"
              >
                <Download className="w-4 h-4 mr-1" />
                安装
              </Button>
            )}
            
            <Button
              variant="ghost"
              size="sm"
              className="flex items-center"
            >
              <MoreVertical className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-400">加载插件数据...</p>
        </div>
      </div>
    );
  }

  // 计算统计
  const installedCount = plugins.filter(p => p.installed).length;
  const activeCount = plugins.filter(p => p.enabled).length;
  const availableCount = plugins.filter(p => !p.installed).length;
  const updateCount = plugins.filter(p => p.status === 'updating').length;
  const totalSize = plugins
    .filter(p => p.installed)
    .reduce((sum, p) => sum + parseFloat(p.size), 0)
    .toFixed(1);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* 插件管理头部 */}
      <div className="bg-gray-800/80 backdrop-blur-sm border-b border-gray-700 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">插件管理系统</h1>
              <p className="text-gray-400 mt-1">扩展ClawAI功能，安装和管理插件</p>
            </div>
            
            <div className="flex items-center space-x-3 mt-4 md:mt-0">
              <Button
                variant="outline"
                className="flex items-center"
              >
                <Upload className="w-4 h-4 mr-2" />
                上传插件
              </Button>
              
              <Button
                variant="primary"
                onClick={() => setShowInstallModal(true)}
                className="flex items-center"
              >
                <DownloadCloud className="w-4 h-4 mr-2" />
                从商店安装
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8">
        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <StatCard 
            icon={Package}
            title="已安装插件"
            value={installedCount}
            change={3}
            color="blue"
          />
          <StatCard 
            icon={Plug}
            title="激活插件"
            value={activeCount}
            change={2}
            color="green"
          />
          <StatCard 
            icon={Download}
            title="可安装插件"
            value={availableCount}
            change={5}
            color="purple"
          />
          <StatCard 
            icon={RefreshCw}
            title="待更新"
            value={updateCount}
            change={0}
            color="orange"
          />
          <StatCard 
            icon={Database}
            title="总大小"
            value={`${totalSize} MB`}
            change={4.2}
            color="indigo"
          />
        </div>

        {/* 标签页导航 */}
        <div className="flex border-b border-gray-700 mb-6">
          {[
            { id: 'installed', name: '已安装', count: installedCount },
            { id: 'available', name: '可安装', count: availableCount },
            { id: 'updates', name: '更新', count: updateCount },
            { id: 'settings', name: '设置', count: 0 }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-500'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              {tab.name}
              {tab.count > 0 && (
                <span className="ml-2 px-2 py-1 text-xs rounded-full bg-gray-700">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* 控制面板 */}
        <Card className="mb-8">
          <div className="flex flex-col md:flex-row items-center justify-between p-4">
            <div className="flex flex-col md:flex-row items-center space-y-4 md:space-y-0 md:space-x-4 mb-4 md:mb-0">
              {/* 搜索框 */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 opacity-50" />
                <input
                  type="text"
                  placeholder="搜索插件..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
                />
              </div>

              {/* 类别过滤 */}
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {pluginCategories.map(category => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>

              {/* 状态过滤 */}
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {pluginStatuses.map(status => (
                  <option key={status.id} value={status.id}>
                    {status.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                className="flex items-center"
                onClick={() => {
                  setSearchTerm('');
                  setFilterCategory('all');
                  setFilterStatus('all');
                }}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                重置过滤
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                className="flex items-center"
              >
                <Filter className="w-4 h-4 mr-2" />
                高级过滤
              </Button>
            </div>
          </div>
        </Card>

        {/* 插件列表 */}
        <div className="space-y-4">
          {filteredPlugins.length === 0 ? (
            <Card className="p-8 text-center">
              <Package className="w-16 h-16 mx-auto text-gray-500 mb-4" />
              <h3 className="text-xl font-semibold mb-2">未找到插件</h3>
              <p className="text-gray-400 mb-6">
                {activeTab === 'installed' 
                  ? '您还没有安装任何插件。'
                  : activeTab === 'available'
                  ? '没有可用的插件。'
                  : '没有需要更新的插件。'}
              </p>
              {activeTab === 'installed' && (
                <Button
                  variant="primary"
                  onClick={() => setActiveTab('available')}
                  className="flex items-center mx-auto"
                >
                  <Download className="w-4 h-4 mr-2" />
                  浏览可安装插件
                </Button>
              )}
            </Card>
          ) : (
            filteredPlugins.map(plugin => (
              <PluginCard key={plugin.id} plugin={plugin} />
            ))
          )}
        </div>

        {/* 类别分布 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
          <Card>
            <div className="flex items-center mb-6">
              <BarChart3 className="w-6 h-6 text-blue-400 mr-2" />
              <h2 className="text-xl font-semibold">插件类别分布</h2>
            </div>

            <div className="space-y-4">
              {pluginCategories
                .filter(cat => cat.id !== 'all')
                .map(category => {
                  const count = plugins.filter(p => p.category === category.id && p.installed).length;
                  const totalInstalled = installedCount;
                  const percent = totalInstalled > 0 ? (count / totalInstalled) * 100 : 0;
                  
                  return (
                    <div key={category.id} className="p-4 rounded-lg bg-gray-800/50">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center">
                          <Badge variant={category.color} size="sm" className="mr-3">
                            {category.name}
                          </Badge>
                          <span className="text-sm opacity-70">{count} 个插件</span>
                        </div>
                        <div className="text-sm font-medium">{percent.toFixed(1)}%</div>
                      </div>
                      <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div 
                          className={`h-full bg-${category.color}-500`}
                          style={{ width: `${percent}%` }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
            </div>
          </Card>

          <Card>
            <div className="flex items-center mb-6">
              <Settings className="w-6 h-6 text-green-400 mr-2" />
              <h2 className="text-xl font-semibold">系统信息</h2>
            </div>

            <div className="space-y-6">
              {/* 插件存储使用 */}
              <div>
                <h3 className="font-medium mb-3">插件存储使用</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">已安装插件</span>
                    <div className="flex items-center space-x-3">
                      <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-blue-500 to-green-500"
                          style={{ width: `${(installedCount / plugins.length) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">{installedCount}/{plugins.length}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">存储空间</span>
                    <div className="flex items-center space-x-3">
                      <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-blue-500 to-green-500"
                          style={{ width: `${(totalSize / 50) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">{totalSize} MB / 50 MB</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* 快速操作 */}
              <div>
                <h3 className="font-medium mb-3">快速操作</h3>
                <div className="grid grid-cols-2 gap-2">
                  <Button variant="outline" size="sm" fullWidth className="flex items-center justify-center">
                    <Download className="w-4 h-4 mr-2" />
                    批量安装
                  </Button>
                  <Button variant="outline" size="sm" fullWidth className="flex items-center justify-center">
                    <Upload className="w-4 h-4 mr-2" />
                    批量导出
                  </Button>
                  <Button variant="outline" size="sm" fullWidth className="flex items-center justify-center">
                    <RefreshCw className="w-4 h-4 mr-2" />
                    检查更新
                  </Button>
                  <Button variant="outline" size="sm" fullWidth className="flex items-center justify-center">
                    <Settings className="w-4 h-4 mr-2" />
                    插件设置
                  </Button>
                </div>
              </div>

              {/* 系统状态 */}
              <div>
                <h3 className="font-medium mb-3">系统状态</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-gray-800/50">
                    <div className="text-sm opacity-70 mb-1">插件API</div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                      <span className="font-medium">运行正常</span>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-800/50">
                    <div className="text-sm opacity-70 mb-1">沙箱环境</div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                      <span className="font-medium">已启用</span>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-800/50">
                    <div className="text-sm opacity-70 mb-1">安全扫描</div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                      <span className="font-medium">已通过</span>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-800/50">
                    <div className="text-sm opacity-70 mb-1">依赖检查</div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                      <span className="font-medium">无冲突</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* 底部信息栏 */}
      <div className="mt-12 py-6 border-t border-gray-800">
        <div className="container mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="mb-4 md:mb-0">
              <div className="flex items-center space-x-2">
                <Package className="w-5 h-5 text-blue-500" />
                <span className="font-medium">ClawAI 插件管理系统</span>
              </div>
              <div className="text-sm text-gray-400 mt-1">
                版本 2.0 | 支持插件扩展架构
              </div>
            </div>
            <div className="flex items-center space-x-4 text-sm">
              <span className="text-gray-400">状态: <span className="text-green-500">● 插件系统正常</span></span>
              <span className="text-gray-400">激活插件: <span className="font-medium">{activeCount}/{installedCount}</span></span>
              <button className="text-blue-400 hover:text-blue-300">
                插件开发文档
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 插件详情模态框 */}
      {showPluginModal && selectedPlugin && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold">插件详情 - {selectedPlugin.name}</h3>
              <button 
                onClick={() => setShowPluginModal(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">插件ID</label>
                  <div className="px-4 py-2 bg-gray-700 rounded-lg">{selectedPlugin.id}</div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">版本</label>
                  <div className="px-4 py-2 bg-gray-700 rounded-lg">{selectedPlugin.version}</div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">作者</label>
                  <div className="px-4 py-2 bg-gray-700 rounded-lg">{selectedPlugin.author}</div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">许可证</label>
                  <div className="px-4 py-2 bg-gray-700 rounded-lg">{selectedPlugin.license}</div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">大小</label>
                  <div className="px-4 py-2 bg-gray-700 rounded-lg">{selectedPlugin.size}</div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">最后更新</label>
                  <div className="px-4 py-2 bg-gray-700 rounded-lg">{selectedPlugin.lastUpdated}</div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-3">描述</h4>
                <p className="text-gray-300">{selectedPlugin.description}</p>
              </div>
              
              <div>
                <h4 className="font-medium mb-3">依赖项</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedPlugin.dependencies.map(dep => (
                    <Badge key={dep} variant="outline" size="sm">
                      {dep}
                    </Badge>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-3">权限</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedPlugin.permissions.map(perm => (
                    <Badge key={perm} variant="info" size="sm">
                      {perm}
                    </Badge>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-3">主页</h4>
                <a 
                  href={selectedPlugin.homepage} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 flex items-center"
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  {selectedPlugin.homepage}
                </a>
              </div>
              
              <div className="flex justify-end space-x-3 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setShowPluginModal(false)}
                >
                  关闭
                </Button>
                {selectedPlugin.installed ? (
                  <>
                    <Button
                      variant="outline"
                      onClick={() => handleUpdatePlugin(selectedPlugin.id)}
                    >
                      <RefreshCw className="w-4 h-4 mr-2" />
                      更新插件
                    </Button>
                    <Button
                      variant="primary"
                      onClick={() => handleTogglePlugin(selectedPlugin.id)}
                    >
                      {selectedPlugin.enabled ? '禁用插件' : '激活插件'}
                    </Button>
                  </>
                ) : (
                  <Button
                    variant="primary"
                    onClick={() => handleInstallPlugin(selectedPlugin.id)}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    安装插件
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 安装插件模态框（简化版） */}
      {showInstallModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold">从商店安装插件</h3>
              <button 
                onClick={() => setShowInstallModal(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">插件URL或ID</label>
                <input
                  type="text"
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="输入插件URL或GitHub仓库地址"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">版本</label>
                <select className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="latest">最新版本</option>
                  <option value="stable">稳定版本</option>
                  <option value="beta">测试版本</option>
                  <option value="specific">指定版本</option>
                </select>
              </div>
              
              <Alert variant="info" className="mb-4">
                <Info className="w-4 h-4 mr-2" />
                插件将从官方商店或GitHub仓库下载并安装
              </Alert>
              
              <div className="flex justify-end space-x-3 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setShowInstallModal(false)}
                >
                  取消
                </Button>
                <Button
                  variant="primary"
                  onClick={() => {
                    alert('插件安装功能（模拟）');
                    setShowInstallModal(false);
                  }}
                >
                  <Download className="w-4 h-4 mr-2" />
                  安装
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PluginManager;
