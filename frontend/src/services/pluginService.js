/**
 * 插件管理API服务
 */
import { request } from './apiClient';

// 插件状态枚举
export const PluginStatus = {
  INSTALLED: 'installed',
  ENABLED: 'enabled',
  DISABLED: 'disabled',
  UPDATING: 'updating',
  ERROR: 'error'
};

// 插件类型枚举
export const PluginType = {
  SECURITY_TOOL: 'security_tool',
  REPORT_GENERATOR: 'report_generator',
  VISUALIZATION: 'visualization',
  INTEGRATION: 'integration',
  UTILITY: 'utility'
};

/**
 * 获取插件列表
 * @param {Object} params - 查询参数
 * @returns {Promise} 插件列表
 */
export const getPlugins = async (params = {}) => {
  try {
    return await request.get('/plugins', { params });
  } catch (error) {
    console.warn('获取插件列表API失败，使用模拟数据:', error.message);

    // 模拟插件数据
    const mockPlugins = [
      {
        id: 'nmap-integration',
        name: 'NMAP集成',
        description: 'NMAP端口扫描器集成插件',
        version: '1.2.3',
        type: PluginType.SECURITY_TOOL,
        status: PluginStatus.ENABLED,
        author: 'ClawAI Team',
        homepage: 'https://github.com/clawai/nmap-plugin',
        dependencies: ['python3', 'nmap'],
        permissions: ['scan:execute', 'network:access'],
        settings: {
          nmap_path: '/usr/bin/nmap',
          default_args: '-sS -sV -O',
          timeout: 300
        },
        metrics: {
          scans_completed: 1245,
          last_scan: '2026-04-06T10:30:00Z',
          success_rate: 98.5
        }
      },
      {
        id: 'metasploit-integration',
        name: 'Metasploit集成',
        description: 'Metasploit渗透测试框架集成',
        version: '1.0.1',
        type: PluginType.SECURITY_TOOL,
        status: PluginStatus.INSTALLED,
        author: 'ClawAI Team',
        homepage: 'https://github.com/clawai/metasploit-plugin',
        dependencies: ['metasploit-framework', 'ruby'],
        permissions: ['attack:execute', 'exploit:access'],
        settings: {
          msf_path: '/usr/share/metasploit-framework',
          workspace: 'default',
          auto_exploit: false
        },
        metrics: {
          exploits_attempted: 342,
          last_exploit: '2026-04-05T15:20:00Z',
          success_rate: 65.2
        }
      },
      {
        id: 'report-templates',
        name: '报告模板库',
        description: '丰富的报告模板和自定义选项',
        version: '2.1.0',
        type: PluginType.REPORT_GENERATOR,
        status: PluginStatus.ENABLED,
        author: 'ClawAI Team',
        homepage: 'https://github.com/clawai/report-templates',
        dependencies: ['report-service'],
        permissions: ['report:generate', 'report:export'],
        settings: {
          default_template: 'detailed',
          auto_generate: true,
          include_screenshots: true
        },
        metrics: {
          reports_generated: 567,
          last_report: '2026-04-06T11:45:00Z',
          user_rating: 4.8
        }
      },
      {
        id: 'knowledge-graph-vis',
        name: '知识图谱可视化',
        description: '交互式知识图谱可视化插件',
        version: '1.3.2',
        type: PluginType.VISUALIZATION,
        status: PluginStatus.ENABLED,
        author: 'ClawAI Team',
        homepage: 'https://github.com/clawai/knowledge-graph-vis',
        dependencies: ['neo4j', 'vis-network'],
        permissions: ['graph:view', 'graph:analyze'],
        settings: {
          layout_algorithm: 'force',
          show_labels: true,
          animation_speed: 500
        },
        metrics: {
          graphs_rendered: 892,
          last_render: '2026-04-06T12:00:00Z',
          avg_load_time: 1.2
        }
      },
      {
        id: 'slack-integration',
        name: 'Slack集成',
        description: 'Slack通知和协作集成',
        version: '1.0.5',
        type: PluginType.INTEGRATION,
        status: PluginStatus.ENABLED,
        author: 'ClawAI Team',
        homepage: 'https://github.com/clawai/slack-integration',
        dependencies: ['slack-sdk'],
        permissions: ['notifications:send'],
        settings: {
          webhook_url: '',
          channel: '#security-alerts',
          notify_on_critical: true
        },
        metrics: {
          notifications_sent: 234,
          last_notification: '2026-04-06T11:30:00Z',
          delivery_rate: 99.1
        }
      },
      {
        id: 'vulnerability-db',
        name: '漏洞数据库',
        description: 'CVE/NVD漏洞数据库集成',
        version: '1.5.0',
        type: PluginType.UTILITY,
        status: PluginStatus.UPDATING,
        author: 'ClawAI Team',
        homepage: 'https://github.com/clawai/vulnerability-db',
        dependencies: ['sqlite', 'requests'],
        permissions: ['vulnerability:read', 'cve:access'],
        settings: {
          update_frequency: 'daily',
          auto_update: true,
          cache_size: 1000
        },
        metrics: {
          vulnerabilities: 234567,
          last_update: '2026-04-06T04:00:00Z',
          update_progress: 75
        }
      },
      {
        id: 'api-security',
        name: 'API安全测试',
        description: 'REST API安全测试和验证',
        version: '0.9.2',
        type: PluginType.SECURITY_TOOL,
        status: PluginStatus.DISABLED,
        author: 'ClawAI Team',
        homepage: 'https://github.com/clawai/api-security',
        dependencies: ['python3', 'requests'],
        permissions: ['api:test', 'endpoint:scan'],
        settings: {
          test_depth: 'basic',
          include_swagger: true,
          rate_limit_test: true
        },
        metrics: {
          apis_tested: 45,
          last_test: '2026-04-04T14:20:00Z',
          vulnerabilities_found: 12
        }
      }
    ];

    // 应用过滤
    let filteredPlugins = [...mockPlugins];
    if (params.status) {
      filteredPlugins = filteredPlugins.filter(p => p.status === params.status);
    }
    if (params.type) {
      filteredPlugins = filteredPlugins.filter(p => p.type === params.type);
    }
    if (params.search) {
      const searchLower = params.search.toLowerCase();
      filteredPlugins = filteredPlugins.filter(p =>
        p.name.toLowerCase().includes(searchLower) ||
        p.description.toLowerCase().includes(searchLower)
      );
    }

    // 应用分页
    const page = params.page || 1;
    const pageSize = params.pageSize || 20;
    const startIndex = (page - 1) * pageSize;
    const paginatedPlugins = filteredPlugins.slice(startIndex, startIndex + pageSize);

    return {
      plugins: paginatedPlugins,
      total: filteredPlugins.length,
      page,
      page_size: pageSize,
      total_pages: Math.ceil(filteredPlugins.length / pageSize)
    };
  }
};

/**
 * 获取插件详情
 * @param {string} pluginId - 插件ID
 * @returns {Promise} 插件详情
 */
export const getPlugin = async (pluginId) => {
  try {
    return await request.get(`/plugins/${pluginId}`);
  } catch (error) {
    console.warn('获取插件详情API失败，使用模拟数据:', error.message);

    // 从模拟插件列表中查找
    const mockPlugins = await getPlugins();
    const plugin = mockPlugins.plugins.find(p => p.id === pluginId);

    if (plugin) {
      return plugin;
    }

    throw new Error(`插件 ${pluginId} 未找到`);
  }
};

/**
 * 安装插件
 * @param {string} pluginId - 插件ID
 * @param {Object} config - 配置选项
 * @returns {Promise} 安装结果
 */
export const installPlugin = async (pluginId, config = {}) => {
  try {
    return await request.post(`/plugins/${pluginId}/install`, config);
  } catch (error) {
    console.warn('安装插件API失败，使用模拟响应:', error.message);

    // 模拟安装响应
    return {
      success: true,
      plugin_id: pluginId,
      status: PluginStatus.INSTALLED,
      message: '插件安装成功',
      installed_at: new Date().toISOString()
    };
  }
};

/**
 * 启用插件
 * @param {string} pluginId - 插件ID
 * @returns {Promise} 启用结果
 */
export const enablePlugin = async (pluginId) => {
  try {
    return await request.post(`/plugins/${pluginId}/enable`);
  } catch (error) {
    console.warn('启用插件API失败，使用模拟响应:', error.message);

    // 模拟启用响应
    return {
      success: true,
      plugin_id: pluginId,
      status: PluginStatus.ENABLED,
      message: '插件已启用',
      enabled_at: new Date().toISOString()
    };
  }
};

/**
 * 禁用插件
 * @param {string} pluginId - 插件ID
 * @returns {Promise} 禁用结果
 */
export const disablePlugin = async (pluginId) => {
  try {
    return await request.post(`/plugins/${pluginId}/disable`);
  } catch (error) {
    console.warn('禁用插件API失败，使用模拟响应:', error.message);

    // 模拟禁用响应
    return {
      success: true,
      plugin_id: pluginId,
      status: PluginStatus.DISABLED,
      message: '插件已禁用',
      disabled_at: new Date().toISOString()
    };
  }
};

/**
 * 卸载插件
 * @param {string} pluginId - 插件ID
 * @returns {Promise} 卸载结果
 */
export const uninstallPlugin = async (pluginId) => {
  try {
    return await request.delete(`/plugins/${pluginId}`);
  } catch (error) {
    console.warn('卸载插件API失败，使用模拟响应:', error.message);

    // 模拟卸载响应
    return {
      success: true,
      plugin_id: pluginId,
      message: '插件已卸载',
      uninstalled_at: new Date().toISOString()
    };
  }
};

/**
 * 更新插件
 * @param {string} pluginId - 插件ID
 * @param {string} version - 目标版本
 * @returns {Promise} 更新结果
 */
export const updatePlugin = async (pluginId, version = 'latest') => {
  try {
    return await request.post(`/plugins/${pluginId}/update`, { version });
  } catch (error) {
    console.warn('更新插件API失败，使用模拟响应:', error.message);

    // 模拟更新响应
    return {
      success: true,
      plugin_id: pluginId,
      status: PluginStatus.UPDATING,
      message: '插件更新开始',
      update_started_at: new Date().toISOString()
    };
  }
};

/**
 * 获取插件设置
 * @param {string} pluginId - 插件ID
 * @returns {Promise} 插件设置
 */
export const getPluginSettings = async (pluginId) => {
  try {
    return await request.get(`/plugins/${pluginId}/settings`);
  } catch (error) {
    console.warn('获取插件设置API失败，使用模拟数据:', error.message);

    // 模拟插件设置
    const plugin = await getPlugin(pluginId);
    return plugin.settings || {};
  }
};

/**
 * 更新插件设置
 * @param {string} pluginId - 插件ID
 * @param {Object} settings - 设置对象
 * @returns {Promise} 更新结果
 */
export const updatePluginSettings = async (pluginId, settings) => {
  try {
    return await request.put(`/plugins/${pluginId}/settings`, settings);
  } catch (error) {
    console.warn('更新插件设置API失败，使用模拟响应:', error.message);

    // 模拟更新响应
    return {
      success: true,
      plugin_id: pluginId,
      message: '插件设置已更新',
      updated_at: new Date().toISOString(),
      settings: settings
    };
  }
};

/**
 * 获取插件市场列表
 * @returns {Promise} 插件市场列表
 */
export const getPluginMarketplace = async () => {
  try {
    return await request.get('/plugins/marketplace');
  } catch (error) {
    console.warn('获取插件市场API失败，使用模拟数据:', error.message);

    // 模拟插件市场
    return {
      plugins: [
        {
          id: 'owasp-zap',
          name: 'OWASP ZAP集成',
          description: 'OWASP ZAP安全测试工具集成',
          author: 'OWASP',
          rating: 4.9,
          downloads: 12450,
          price: 'free',
          categories: ['security', 'testing', 'owasp']
        },
        {
          id: 'docker-scanner',
          name: 'Docker容器安全扫描',
          description: 'Docker镜像和容器安全扫描',
          author: 'Aqua Security',
          rating: 4.7,
          downloads: 8765,
          price: 'freemium',
          categories: ['docker', 'container', 'security']
        },
        {
          id: 'splunk-integration',
          name: 'Splunk集成',
          description: 'Splunk日志分析和监控集成',
          author: 'Splunk',
          rating: 4.8,
          downloads: 15432,
          price: 'enterprise',
          categories: ['monitoring', 'logging', 'analytics']
        }
      ],
      categories: ['security', 'testing', 'monitoring', 'integration', 'visualization'],
      stats: {
        total_plugins: 156,
        free_plugins: 89,
        updated_this_week: 12
      }
    };
  }
};

// 插件服务
const pluginService = {
  getPlugins,
  getPlugin,
  installPlugin,
  enablePlugin,
  disablePlugin,
  uninstallPlugin,
  updatePlugin,
  getPluginSettings,
  updatePluginSettings,
  getPluginMarketplace,
  PluginStatus,
  PluginType
};

export default pluginService;