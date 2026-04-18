/**
 * 插件管理API服务
 */
import { request } from './apiClient';
import { USE_MOCK_DATA } from './config';

// 插件状态枚举
export const PluginStatus = {
  ACTIVE: 'active',
  INSTALLED: 'installed',
  ENABLED: 'enabled',
  INACTIVE: 'inactive',
  DISABLED: 'disabled',
  AVAILABLE: 'available',
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
    if (USE_MOCK_DATA && import.meta.env.DEV) {
      console.warn('获取插件列表API失败，使用模拟数据:', error.message);

      // 模拟插件数据（与后端 _PLUGINS 保持一致）
      const mockPlugins = [
        { id: 'nmap',           name: 'Nmap 网络扫描器',       version: '7.94.0', description: '业界标准网络探测与安全审计工具，支持端口扫描、服务识别、OS检测、NSE脚本', author: 'Gordon Lyon',       category: 'scanner',     icon: '🔍', tags: ['network','port-scan'],     downloads: 125000, rating: 4.9, size: '8.2 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'masscan',        name: 'Masscan 高速扫描',       version: '1.3.2',  description: '互联网级别高速端口扫描器，速度可达每秒千万数据包',                         author: 'Robert Graham',     category: 'scanner',     icon: '⚡', tags: ['network','fast'],          downloads: 52000,  rating: 4.6, size: '1.8 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'rustscan',       name: 'RustScan 快速扫描',      version: '2.2.2',  description: 'Rust编写的超快端口扫描器，可与Nmap无缝集成',                               author: 'RustScan Team',     category: 'scanner',     icon: '🦀', tags: ['network','rust'],          downloads: 38000,  rating: 4.7, size: '5.4 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'httpx',          name: 'HTTPX HTTP探测',         version: '1.6.5',  description: '快速多功能HTTP工具包，支持批量探测HTTP/HTTPS服务状态、技术指纹',             author: 'ProjectDiscovery', category: 'scanner',     icon: '🌐', tags: ['http','web'],              downloads: 61000,  rating: 4.8, size: '12.3 MB',  installed: true,  enabled: true,  status: 'active' },
        { id: 'nuclei',         name: 'Nuclei 漏洞扫描',        version: '3.2.1',  description: '基于模板的漏洞扫描器，拥有7000+个CVE/漏洞模板库',                          author: 'ProjectDiscovery', category: 'scanner',     icon: '☢️', tags: ['vulnerability','cve'],     downloads: 67000,  rating: 4.8, size: '45 MB',    installed: true,  enabled: true,  status: 'active' },
        { id: 'nikto',          name: 'Nikto Web扫描',          version: '2.1.6',  description: 'Web服务器扫描器，检测6700+危险文件/CGI及配置问题',                         author: 'CIRT.net',          category: 'scanner',     icon: '🕵️', tags: ['web','server'],            downloads: 78000,  rating: 4.4, size: '2.1 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'whatweb',        name: 'WhatWeb 指纹识别',        version: '0.5.5',  description: 'Web应用指纹识别，支持1800+插件识别CMS/框架/服务器',                        author: 'Andrew Horton',     category: 'recon',       icon: '🏷️', tags: ['fingerprint','web'],       downloads: 41000,  rating: 4.5, size: '4.2 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'wafw00f',        name: 'WAFW00F WAF检测',         version: '2.2.0',  description: '自动检测目标是否部署了WAF，支持170+种WAF指纹',                             author: 'Enablesecurity',    category: 'recon',       icon: '🛡️', tags: ['waf','fingerprint'],       downloads: 33000,  rating: 4.4, size: '1.5 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'gobuster',       name: 'Gobuster 目录枚举',       version: '3.6.0',  description: 'Go编写的目录/文件/DNS/VHost暴力破解工具',                                  author: 'OJ Reeves',         category: 'scanner',     icon: '📂', tags: ['directory','fuzzing'],     downloads: 58000,  rating: 4.6, size: '7.8 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'dirsearch',      name: 'Dirsearch 目录扫描',      version: '0.4.3',  description: '高速Web路径暴力破解和目录枚举工具，内置庞大字典库',                         author: 'maurosoria',        category: 'scanner',     icon: '📁', tags: ['directory','web'],         downloads: 45000,  rating: 4.4, size: '3.8 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'ffuf',           name: 'FFUF 模糊测试',           version: '2.1.0',  description: 'Go编写的高速Web模糊测试工具',                                              author: 'joohoi',            category: 'scanner',     icon: '🎯', tags: ['fuzzing','web'],           downloads: 49000,  rating: 4.7, size: '9.1 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'feroxbuster',    name: 'Feroxbuster 递归枚举',    version: '2.10.4', description: 'Rust编写的快速递归内容发现工具',                                           author: 'epi052',            category: 'scanner',     icon: '🔄', tags: ['directory','recursive'],   downloads: 29000,  rating: 4.6, size: '11.2 MB',  installed: true,  enabled: true,  status: 'active' },
        { id: 'sqlmap',         name: 'SQLMap 注入检测',         version: '1.8.3',  description: '自动化SQL注入漏洞检测与利用，支持MySQL/PostgreSQL/Oracle/MSSQL等',         author: 'sqlmapproject',     category: 'exploit',     icon: '💉', tags: ['sql-injection','web'],     downloads: 89000,  rating: 4.7, size: '5.1 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'xsstrike',       name: 'XSStrike XSS检测',        version: '3.1.5',  description: '高级XSS检测套件，内置爬虫和模糊测试引擎',                                  author: 's0md3v',             category: 'exploit',     icon: '🎭', tags: ['xss','web'],               downloads: 31000,  rating: 4.5, size: '2.3 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'commix',         name: 'Commix 命令注入',         version: '3.9',    description: '自动化命令注入漏洞检测和利用工具',                                         author: 'commixproject',     category: 'exploit',     icon: '💻', tags: ['command-injection','rce'], downloads: 22000,  rating: 4.3, size: '4.7 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'tplmap',         name: 'Tplmap SSTI检测',         version: '0.5',    description: '服务器端模板注入漏洞自动检测与利用工具',                                   author: 'epinna',             category: 'exploit',     icon: '🧪', tags: ['ssti','web'],              downloads: 18000,  rating: 4.3, size: '3.1 MB',   installed: false, enabled: false, status: 'available' },
        { id: 'amass',          name: 'Amass 资产枚举',          version: '4.2.0',  description: '深度攻击面映射工具，整合50+数据源进行子域名枚举',                           author: 'OWASP',             category: 'recon',       icon: '🗺️', tags: ['subdomain','osint'],       downloads: 54000,  rating: 4.7, size: '18.6 MB',  installed: true,  enabled: true,  status: 'active' },
        { id: 'subfinder',      name: 'Subfinder 子域名发现',    version: '2.6.6',  description: '被动子域名发现工具，聚合47+数据源',                                        author: 'ProjectDiscovery', category: 'recon',       icon: '🔭', tags: ['subdomain','passive'],     downloads: 48000,  rating: 4.8, size: '8.9 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'sublist3r',      name: 'Sublist3r 子域名枚举',    version: '1.1',    description: 'OSINT子域名枚举工具，整合多个搜索引擎',                                    author: 'aboul3la',          category: 'recon',       icon: '📡', tags: ['subdomain','osint'],       downloads: 36000,  rating: 4.2, size: '1.4 MB',   installed: false, enabled: false, status: 'available' },
        { id: 'theharvester',   name: 'theHarvester 信息收集',   version: '4.4.0',  description: '通过搜索引擎收集邮件地址、子域名、IP等信息',                               author: 'laramies',          category: 'recon',       icon: '🌾', tags: ['email','osint'],           downloads: 42000,  rating: 4.4, size: '3.2 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'dnsrecon',       name: 'DNSRecon DNS侦察',        version: '1.1.4',  description: '全面的DNS枚举工具，支持区域传送、暴力枚举、反向查询',                       author: 'darkoperator',      category: 'recon',       icon: '🔎', tags: ['dns','recon'],             downloads: 29000,  rating: 4.3, size: '2.8 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'whois-tool',     name: 'WHOIS 查询工具',          version: '5.5.22', description: '查询域名/IP注册信息',                                                     author: 'IANA',              category: 'recon',       icon: '📋', tags: ['whois','domain'],          downloads: 65000,  rating: 4.1, size: '0.5 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'sslscan',        name: 'SSLScan SSL扫描',         version: '2.1.3',  description: '检测弱密码套件、协议版本、心脏滴血等SSL/TLS漏洞',                          author: 'rbsec',             category: 'scanner',     icon: '🔒', tags: ['ssl','tls'],               downloads: 27000,  rating: 4.5, size: '1.9 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'testssl',        name: 'TestSSL.sh TLS测试',      version: '3.2',    description: '全面的SSL/TLS测试工具',                                                   author: 'testssl.sh',        category: 'scanner',     icon: '🧩', tags: ['ssl','tls'],               downloads: 21000,  rating: 4.4, size: '2.7 MB',   installed: false, enabled: false, status: 'available' },
        { id: 'wpscan',         name: 'WPScan WordPress扫描',    version: '3.8.25', description: 'WordPress安全扫描器，枚举用户/插件/主题并检测已知漏洞',                    author: 'WPScan Team',       category: 'scanner',     icon: '📰', tags: ['wordpress','cms'],         downloads: 56000,  rating: 4.6, size: '4.3 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'enhanced-wpscan',name: '增强版 WPScan',           version: '3.8.25+',description: '集成AI分析的WordPress扫描器，自动关联CVE',                                author: 'ClawAI Team',       category: 'scanner',     icon: '🚀', tags: ['wordpress','ai'],          downloads: 8000,   rating: 4.8, size: '4.5 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'joomscan',       name: 'JoomScan Joomla扫描',     version: '0.0.7',  description: 'OWASP维护的Joomla CMS漏洞扫描器',                                         author: 'OWASP',             category: 'scanner',     icon: '🔩', tags: ['joomla','cms'],            downloads: 18000,  rating: 4.1, size: '1.1 MB',   installed: false, enabled: false, status: 'available' },
        { id: 'droopescan',     name: 'Droopescan CMS扫描',      version: '1.45.1', description: '支持Drupal/WordPress/Joomla等多CMS插件扫描',                              author: 'droope',            category: 'scanner',     icon: '🕸️', tags: ['drupal','cms'],            downloads: 14000,  rating: 4.0, size: '1.3 MB',   installed: false, enabled: false, status: 'available' },
        { id: 'cmsmap',         name: 'CMSMap CMS漏洞扫描',      version: '1.0',    description: '自动检测主流CMS漏洞',                                                     author: 'Dionach',           category: 'scanner',     icon: '🗂️', tags: ['cms','wordpress'],         downloads: 11000,  rating: 4.0, size: '0.9 MB',   installed: false, enabled: false, status: 'available' },
        { id: 'hydra',          name: 'Hydra 在线爆破',          version: '9.5',    description: '支持50+协议的快速在线密码破解工具',                                        author: 'vanhauser-thc',     category: 'brute-force', icon: '🔓', tags: ['brute-force','login'],     downloads: 78000,  rating: 4.3, size: '1.2 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'medusa',         name: 'Medusa 并行爆破',         version: '2.2',    description: '高速并行网络登录密码破解工具',                                             author: 'foofus.net',        category: 'brute-force', icon: '🐍', tags: ['brute-force','parallel'],  downloads: 25000,  rating: 4.1, size: '0.8 MB',   installed: false, enabled: false, status: 'available' },
        { id: 'hashcat',        name: 'Hashcat GPU破解',         version: '6.2.6',  description: '世界最快GPU密码恢复工具，支持350+哈希算法',                                author: 'hashcat.net',       category: 'brute-force', icon: '⚙️', tags: ['hash','gpu'],              downloads: 92000,  rating: 4.9, size: '22 MB',    installed: true,  enabled: true,  status: 'active' },
        { id: 'john',           name: 'John the Ripper',         version: '1.9.0',  description: '经典密码破解工具，支持字典和暴力破解',                                     author: 'openwall',          category: 'brute-force', icon: '🔑', tags: ['hash','dictionary'],       downloads: 105000, rating: 4.5, size: '3.1 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'metasploit',     name: 'Metasploit 框架',         version: '6.4.0',  description: '世界最广泛使用的渗透测试框架，提供2000+漏洞利用模块',                       author: 'Rapid7',            category: 'exploit',     icon: '💀', tags: ['exploit','post-exploit'],  downloads: 234000, rating: 4.9, size: '512 MB',   installed: false, enabled: false, status: 'available' },
        { id: 'impacket',       name: 'Impacket 网络协议',       version: '0.12.0', description: 'Python网络协议工具集，支持SMB/NTLM/Kerberos等Windows协议',                author: 'SecureAuth',        category: 'post-exploit',icon: '🧰', tags: ['windows','smb','kerberos'],downloads: 47000,  rating: 4.7, size: '8.4 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'evil-winrm',     name: 'Evil-WinRM 远程管理',     version: '3.5',    description: '专为渗透测试设计的WinRM Shell',                                           author: 'Hackplayers',       category: 'post-exploit',icon: '😈', tags: ['windows','winrm'],         downloads: 32000,  rating: 4.6, size: '2.1 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'crackmapexec',   name: 'CrackMapExec 内网渗透',   version: '5.4.0',  description: '内网评估瑞士军刀，支持SMB/LDAP/MSSQL批量认证',                            author: 'byt3bl33d3r',       category: 'post-exploit',icon: '🗡️', tags: ['windows','smb','ad'],      downloads: 38000,  rating: 4.7, size: '15.6 MB',  installed: true,  enabled: true,  status: 'active' },
        { id: 'searchsploit',   name: 'SearchSploit 漏洞库',     version: '4.6.0',  description: 'Exploit-DB离线查询工具，收录40000+公开漏洞利用代码',                       author: 'Offensive Security',category: 'exploit',     icon: '🔬', tags: ['exploit-db','cve'],        downloads: 61000,  rating: 4.8, size: '1.1 GB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'ai-report-gen',  name: 'AI 智能报告生成器',        version: '1.2.0',  description: '基于AI的渗透测试报告自动生成，支持HTML/PDF/JSON多格式',                    author: 'ClawAI Team',       category: 'reporting',   icon: '📊', tags: ['ai','report'],             downloads: 15000,  rating: 4.5, size: '2.3 MB',   installed: true,  enabled: true,  status: 'active' },
        { id: 'burpsuite-integration', name: 'Burp Suite 集成',  version: '2024.1', description: 'Web应用安全测试平台集成，支持代理拦截和主动/被动扫描',                      author: 'PortSwigger',       category: 'proxy',       icon: '🕷️', tags: ['web','proxy'],             downloads: 98000,  rating: 4.6, size: '156 MB',   installed: false, enabled: false, status: 'available' },
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
      success: true,
      data: paginatedPlugins,
      total: filteredPlugins.length,
      page,
      page_size: pageSize,
      total_pages: Math.ceil(filteredPlugins.length / pageSize)
    };
    } else {
      throw error;
    }
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
    if (USE_MOCK_DATA && import.meta.env.DEV) {
      console.warn('获取插件详情API失败，使用模拟数据:', error.message);

      // 从模拟插件列表中查找
      const mockPlugins = await getPlugins();
      const plugin = mockPlugins.plugins.find(p => p.id === pluginId);

      if (plugin) {
        return plugin;
      }
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
    if (USE_MOCK_DATA && import.meta.env.DEV) {
      console.warn('安装插件API失败，使用模拟响应:', error.message);

      // 模拟安装响应
      return {
      success: true,
      plugin_id: pluginId,
      status: PluginStatus.INSTALLED,
      message: '插件安装成功',
      installed_at: new Date().toISOString()
    };
    } else {
      throw error;
    }
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
    if (USE_MOCK_DATA && import.meta.env.DEV) {
      console.warn('启用插件API失败，使用模拟响应:', error.message);

      // 模拟启用响应
      return {
      success: true,
      plugin_id: pluginId,
      status: PluginStatus.ENABLED,
      message: '插件已启用',
      enabled_at: new Date().toISOString()
    };
    } else {
      throw error;
    }
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
    if (USE_MOCK_DATA && import.meta.env.DEV) {
      console.warn('禁用插件API失败，使用模拟响应:', error.message);

      // 模拟禁用响应
      return {
      success: true,
      plugin_id: pluginId,
      status: PluginStatus.DISABLED,
      message: '插件已禁用',
      disabled_at: new Date().toISOString()
    };
    } else {
      throw error;
    }
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
    if (USE_MOCK_DATA && import.meta.env.DEV) {
      console.warn('卸载插件API失败，使用模拟响应:', error.message);

      // 模拟卸载响应
      return {
      success: true,
      plugin_id: pluginId,
      message: '插件已卸载',
      uninstalled_at: new Date().toISOString()
    };
    } else {
      throw error;
    }
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
    if (USE_MOCK_DATA && import.meta.env.DEV) {
      console.warn('更新插件API失败，使用模拟响应:', error.message);

      // 模拟更新响应
      return {
      success: true,
      plugin_id: pluginId,
      status: PluginStatus.UPDATING,
      message: '插件更新开始',
      update_started_at: new Date().toISOString()
    };
    } else {
      throw error;
    }
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
    if (USE_MOCK_DATA && import.meta.env.DEV) {
      console.warn('获取插件设置API失败，使用模拟数据:', error.message);

      // 模拟插件设置
      const plugin = await getPlugin(pluginId);
      return plugin.settings || {};
    } else {
      throw error;
    }
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
    if (USE_MOCK_DATA && import.meta.env.DEV) {
      console.warn('更新插件设置API失败，使用模拟响应:', error.message);

      // 模拟更新响应
      return {
      success: true,
      plugin_id: pluginId,
      message: '插件设置已更新',
      updated_at: new Date().toISOString(),
      settings: settings
    };
    } else {
      throw error;
    }
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
    if (USE_MOCK_DATA && import.meta.env.DEV) {
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
    } else {
      throw error;
    }
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