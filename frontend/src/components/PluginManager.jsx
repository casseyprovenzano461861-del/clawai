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

  // 本地兜底数据（API 不可用时显示）
  const mockPlugins = [
    // 端口扫描
    { id:'nmap',            name:'Nmap 网络扫描器',       version:'7.94.0', author:'Gordon Lyon',        description:'业界标准网络探测与安全审计工具，支持端口扫描、服务识别、OS检测', category:'scanner',     status:'active',    installed:true,  enabled:true,  rating:4.9, downloads:125000, size:'8.2 MB',   permissions:['network:scan','port:detect'], icon:'🔍', license:'GPL-2.0' },
    { id:'masscan',         name:'Masscan 高速扫描',       version:'1.3.2',  author:'Robert Graham',      description:'互联网级别高速端口扫描器，速度可达每秒千万数据包',              category:'scanner',     status:'active',    installed:true,  enabled:true,  rating:4.6, downloads:52000,  size:'1.8 MB',   permissions:['network:scan'],               icon:'⚡', license:'AGPL' },
    { id:'rustscan',        name:'RustScan 快速扫描',      version:'2.2.2',  author:'RustScan Team',      description:'Rust编写的超快端口扫描器，与Nmap无缝集成',                     category:'scanner',     status:'active',    installed:true,  enabled:true,  rating:4.7, downloads:38000,  size:'5.4 MB',   permissions:['network:scan'],               icon:'🦀', license:'GPL-3.0' },
    { id:'httpx',           name:'HTTPX HTTP探测',         version:'1.6.5',  author:'ProjectDiscovery',   description:'快速多功能HTTP工具包，支持批量探测状态、技术指纹',               category:'scanner',     status:'active',    installed:true,  enabled:true,  rating:4.8, downloads:61000,  size:'12.3 MB',  permissions:['http:probe'],                 icon:'🌐', license:'MIT' },
    // Web扫描
    { id:'nuclei',          name:'Nuclei 漏洞扫描',        version:'3.2.1',  author:'ProjectDiscovery',   description:'基于模板的漏洞扫描器，7000+个CVE模板库',                       category:'scanner',     status:'active',    installed:true,  enabled:true,  rating:4.8, downloads:67000,  size:'45 MB',    permissions:['vulnerability:scan'],         icon:'☢️', license:'MIT' },
    { id:'nikto',           name:'Nikto Web扫描',          version:'2.1.6',  author:'CIRT.net',           description:'Web服务器扫描器，检测6700+危险文件及配置问题',                category:'scanner',     status:'active',    installed:true,  enabled:true,  rating:4.4, downloads:78000,  size:'2.1 MB',   permissions:['web:scan'],                   icon:'🕵️', license:'GPL-2.0' },
    { id:'whatweb',         name:'WhatWeb 指纹识别',        version:'0.5.5',  author:'Andrew Horton',      description:'Web应用指纹识别，支持1800+插件',                               category:'recon',       status:'active',    installed:true,  enabled:true,  rating:4.5, downloads:41000,  size:'4.2 MB',   permissions:['fingerprint:web'],            icon:'🏷️', license:'GPL-2.0' },
    { id:'wafw00f',         name:'WAFW00F WAF检测',         version:'2.2.0',  author:'Enablesecurity',     description:'自动检测WAF，支持170+种WAF指纹',                               category:'recon',       status:'active',    installed:true,  enabled:true,  rating:4.4, downloads:33000,  size:'1.5 MB',   permissions:['waf:detect'],                 icon:'🛡️', license:'BSD' },
    // 目录枚举
    { id:'gobuster',        name:'Gobuster 目录枚举',       version:'3.6.0',  author:'OJ Reeves',          description:'Go编写的目录/DNS/VHost暴力破解工具',                           category:'scanner',     status:'active',    installed:true,  enabled:true,  rating:4.6, downloads:58000,  size:'7.8 MB',   permissions:['directory:fuzz'],             icon:'📂', license:'Apache-2.0' },
    { id:'dirsearch',       name:'Dirsearch 目录扫描',      version:'0.4.3',  author:'maurosoria',         description:'高速Web路径暴力破解工具，内置庞大字典库',                       category:'scanner',     status:'active',    installed:true,  enabled:true,  rating:4.4, downloads:45000,  size:'3.8 MB',   permissions:['directory:fuzz'],             icon:'📁', license:'GPL-2.0' },
    { id:'ffuf',            name:'FFUF 模糊测试',           version:'2.1.0',  author:'joohoi',             description:'Go编写的高速Web模糊测试工具',                                  category:'scanner',     status:'active',    installed:true,  enabled:true,  rating:4.7, downloads:49000,  size:'9.1 MB',   permissions:['web:fuzz'],                   icon:'🎯', license:'MIT' },
    { id:'feroxbuster',     name:'Feroxbuster 递归枚举',    version:'2.10.4', author:'epi052',             description:'Rust编写的快速递归内容发现工具',                               category:'scanner',     status:'active',    installed:true,  enabled:true,  rating:4.6, downloads:29000,  size:'11.2 MB',  permissions:['directory:fuzz'],             icon:'🔄', license:'MIT' },
    // SQL注入/Web攻击
    { id:'sqlmap',          name:'SQLMap 注入检测',         version:'1.8.3',  author:'sqlmapproject',      description:'自动化SQL注入漏洞检测与利用',                                  category:'exploit',     status:'active',    installed:true,  enabled:true,  rating:4.7, downloads:89000,  size:'5.1 MB',   permissions:['sql:inject'],                 icon:'💉', license:'GPL-2.0' },
    { id:'xsstrike',        name:'XSStrike XSS检测',        version:'3.1.5',  author:'s0md3v',             description:'高级XSS检测套件，内置爬虫和模糊测试引擎',                       category:'exploit',     status:'active',    installed:true,  enabled:true,  rating:4.5, downloads:31000,  size:'2.3 MB',   permissions:['xss:test'],                   icon:'🎭', license:'GPL-3.0' },
    { id:'commix',          name:'Commix 命令注入',         version:'3.9',    author:'commixproject',      description:'自动化命令注入漏洞检测和利用工具',                              category:'exploit',     status:'active',    installed:true,  enabled:true,  rating:4.3, downloads:22000,  size:'4.7 MB',   permissions:['rce:test'],                   icon:'💻', license:'GPL-3.0' },
    { id:'tplmap',          name:'Tplmap SSTI检测',         version:'0.5',    author:'epinna',             description:'服务器端模板注入漏洞自动检测与利用',                            category:'exploit',     status:'available', installed:false, enabled:false, rating:4.3, downloads:18000,  size:'3.1 MB',   permissions:['ssti:test'],                  icon:'🧪', license:'MIT' },
    // 信息收集
    { id:'amass',           name:'Amass 资产枚举',          version:'4.2.0',  author:'OWASP',              description:'深度攻击面映射工具，整合50+数据源',                             category:'recon',       status:'active',    installed:true,  enabled:true,  rating:4.7, downloads:54000,  size:'18.6 MB',  permissions:['subdomain:enum'],             icon:'🗺️', license:'Apache-2.0' },
    { id:'subfinder',       name:'Subfinder 子域名发现',    version:'2.6.6',  author:'ProjectDiscovery',   description:'被动子域名发现，聚合47+数据源',                                 category:'recon',       status:'active',    installed:true,  enabled:true,  rating:4.8, downloads:48000,  size:'8.9 MB',   permissions:['subdomain:enum'],             icon:'🔭', license:'MIT' },
    { id:'sublist3r',       name:'Sublist3r 子域名枚举',    version:'1.1',    author:'aboul3la',           description:'OSINT子域名枚举，整合多搜索引擎',                              category:'recon',       status:'available', installed:false, enabled:false, rating:4.2, downloads:36000,  size:'1.4 MB',   permissions:['subdomain:enum'],             icon:'📡', license:'GPL-2.0' },
    { id:'theharvester',    name:'theHarvester 信息收集',   version:'4.4.0',  author:'laramies',           description:'收集邮件地址、子域名、IP等OSINT信息',                          category:'recon',       status:'active',    installed:true,  enabled:true,  rating:4.4, downloads:42000,  size:'3.2 MB',   permissions:['osint:collect'],              icon:'🌾', license:'GPL-2.0' },
    { id:'dnsrecon',        name:'DNSRecon DNS侦察',        version:'1.1.4',  author:'darkoperator',       description:'全面DNS枚举：区域传送、暴力枚举、反向查询',                    category:'recon',       status:'active',    installed:true,  enabled:true,  rating:4.3, downloads:29000,  size:'2.8 MB',   permissions:['dns:recon'],                  icon:'🔎', license:'GPL-2.0' },
    { id:'whois-tool',      name:'WHOIS 查询工具',          version:'5.5.22', author:'IANA',               description:'查询域名/IP注册信息',                                         category:'recon',       status:'active',    installed:true,  enabled:true,  rating:4.1, downloads:65000,  size:'0.5 MB',   permissions:['whois:query'],                icon:'📋', license:'MIT' },
    // SSL/TLS
    { id:'sslscan',         name:'SSLScan SSL扫描',         version:'2.1.3',  author:'rbsec',              description:'检测弱密码套件、协议版本、心脏滴血等SSL漏洞',                  category:'scanner',     status:'active',    installed:true,  enabled:true,  rating:4.5, downloads:27000,  size:'1.9 MB',   permissions:['ssl:scan'],                   icon:'🔒', license:'GPL-3.0' },
    { id:'testssl',         name:'TestSSL.sh TLS测试',      version:'3.2',    author:'testssl.sh',         description:'全面SSL/TLS测试工具',                                         category:'scanner',     status:'available', installed:false, enabled:false, rating:4.4, downloads:21000,  size:'2.7 MB',   permissions:['ssl:test'],                   icon:'🧩', license:'GPL-2.0' },
    // CMS扫描
    { id:'wpscan',          name:'WPScan WordPress扫描',    version:'3.8.25', author:'WPScan Team',        description:'WordPress安全扫描器，枚举用户/插件/主题并检测漏洞',             category:'scanner',     status:'active',    installed:true,  enabled:true,  rating:4.6, downloads:56000,  size:'4.3 MB',   permissions:['wordpress:scan'],             icon:'📰', license:'WPScan' },
    { id:'enhanced-wpscan', name:'增强版 WPScan',           version:'3.8.25+',author:'ClawAI Team',        description:'集成AI分析的WordPress扫描器，自动关联CVE',                     category:'scanner',     status:'active',    installed:true,  enabled:true,  rating:4.8, downloads:8000,   size:'4.5 MB',   permissions:['wordpress:scan','ai:analyze'],icon:'🚀', license:'MIT' },
    { id:'joomscan',        name:'JoomScan Joomla扫描',     version:'0.0.7',  author:'OWASP',              description:'OWASP维护的Joomla CMS漏洞扫描器',                             category:'scanner',     status:'available', installed:false, enabled:false, rating:4.1, downloads:18000,  size:'1.1 MB',   permissions:['joomla:scan'],                icon:'🔩', license:'GPL-3.0' },
    { id:'droopescan',      name:'Droopescan CMS扫描',      version:'1.45.1', author:'droope',             description:'支持Drupal/WordPress/Joomla多CMS扫描',                        category:'scanner',     status:'available', installed:false, enabled:false, rating:4.0, downloads:14000,  size:'1.3 MB',   permissions:['cms:scan'],                   icon:'🕸️', license:'GPL-3.0' },
    { id:'cmsmap',          name:'CMSMap CMS漏洞扫描',      version:'1.0',    author:'Dionach',            description:'自动检测主流CMS漏洞',                                         category:'scanner',     status:'available', installed:false, enabled:false, rating:4.0, downloads:11000,  size:'0.9 MB',   permissions:['cms:scan'],                   icon:'🗂️', license:'GPL-3.0' },
    // 密码破解
    { id:'hydra',           name:'Hydra 在线爆破',          version:'9.5',    author:'vanhauser-thc',      description:'支持50+协议的快速在线密码破解工具',                             category:'brute-force', status:'active',    installed:true,  enabled:true,  rating:4.3, downloads:78000,  size:'1.2 MB',   permissions:['brute:force'],                icon:'🔓', license:'AGPL' },
    { id:'medusa',          name:'Medusa 并行爆破',         version:'2.2',    author:'foofus.net',         description:'高速并行网络登录密码破解工具',                                 category:'brute-force', status:'available', installed:false, enabled:false, rating:4.1, downloads:25000,  size:'0.8 MB',   permissions:['brute:force'],                icon:'🐍', license:'GPL-2.0' },
    { id:'hashcat',         name:'Hashcat GPU破解',         version:'6.2.6',  author:'hashcat.net',        description:'世界最快GPU密码恢复工具，支持350+哈希算法',                     category:'brute-force', status:'active',    installed:true,  enabled:true,  rating:4.9, downloads:92000,  size:'22 MB',    permissions:['hash:crack'],                 icon:'⚙️', license:'MIT' },
    { id:'john',            name:'John the Ripper',         version:'1.9.0',  author:'openwall',           description:'经典密码破解工具，字典和暴力破解',                              category:'brute-force', status:'active',    installed:true,  enabled:true,  rating:4.5, downloads:105000, size:'3.1 MB',   permissions:['hash:crack'],                 icon:'🔑', license:'GPL-2.0' },
    // 后渗透
    { id:'metasploit',      name:'Metasploit 框架',         version:'6.4.0',  author:'Rapid7',             description:'世界最广泛使用的渗透测试框架，2000+漏洞利用模块',               category:'exploit',     status:'available', installed:false, enabled:false, rating:4.9, downloads:234000, size:'512 MB',   permissions:['exploit:run'],                icon:'💀', license:'BSD' },
    { id:'impacket',        name:'Impacket 网络协议',       version:'0.12.0', author:'SecureAuth',         description:'Python网络协议工具集，SMB/NTLM/Kerberos',                     category:'post-exploit',status:'active',    installed:true,  enabled:true,  rating:4.7, downloads:47000,  size:'8.4 MB',   permissions:['smb:attack','kerberos:attack'],icon:'🧰', license:'Apache-2.0' },
    { id:'evil-winrm',      name:'Evil-WinRM 远程管理',     version:'3.5',    author:'Hackplayers',        description:'专为渗透测试设计的WinRM Shell',                                category:'post-exploit',status:'active',    installed:true,  enabled:true,  rating:4.6, downloads:32000,  size:'2.1 MB',   permissions:['winrm:shell'],                icon:'😈', license:'MIT' },
    { id:'crackmapexec',    name:'CrackMapExec 内网渗透',   version:'5.4.0',  author:'byt3bl33d3r',        description:'内网评估瑞士军刀，SMB/LDAP/MSSQL批量认证',                    category:'post-exploit',status:'active',    installed:true,  enabled:true,  rating:4.7, downloads:38000,  size:'15.6 MB',  permissions:['smb:attack','lateral:move'],  icon:'🗡️', license:'BSD' },
    { id:'searchsploit',    name:'SearchSploit 漏洞库',     version:'4.6.0',  author:'Offensive Security', description:'Exploit-DB离线查询，40000+公开漏洞利用代码',                   category:'exploit',     status:'active',    installed:true,  enabled:true,  rating:4.8, downloads:61000,  size:'1.1 GB',   permissions:['exploitdb:search'],           icon:'🔬', license:'GPL-2.0' },
    // 报告/代理
    { id:'ai-report-gen',   name:'AI 智能报告生成器',        version:'1.2.0',  author:'ClawAI Team',        description:'基于AI的渗透测试报告自动生成，支持多格式导出',                   category:'reporting',   status:'active',    installed:true,  enabled:true,  rating:4.5, downloads:15000,  size:'2.3 MB',   permissions:['report:generate'],            icon:'📊', license:'MIT' },
    { id:'burpsuite-integration', name:'Burp Suite 集成',   version:'2024.1', author:'PortSwigger',        description:'Web应用安全测试平台集成，代理拦截和主动扫描',                   category:'proxy',       status:'available', installed:false, enabled:false, rating:4.6, downloads:98000,  size:'156 MB',   permissions:['proxy:intercept'],            icon:'🕷️', license:'商业' },
  ];

  // 插件类别
  const pluginCategories = [
    { id: 'all',          name: '所有类别',   color: 'gray' },
    { id: 'scanner',      name: '扫描器',     color: 'blue',   icon: 'shield' },
    { id: 'exploit',      name: '漏洞利用',   color: 'red',    icon: 'code' },
    { id: 'recon',        name: '信息收集',   color: 'cyan',   icon: 'search' },
    { id: 'post-exploit', name: '后渗透',     color: 'orange', icon: 'lock' },
    { id: 'brute-force',  name: '密码破解',   color: 'yellow', icon: 'key' },
    { id: 'proxy',        name: '代理工具',   color: 'purple', icon: 'network' },
    { id: 'reporting',    name: '报告生成',   color: 'green',  icon: 'file-text' },
    // 旧 mock 数据类别（向后兼容）
    { id: 'database',     name: '数据库',     color: 'green',  icon: 'database' },
    { id: 'export',       name: '导出工具',   color: 'purple', icon: 'file-text' },
    { id: 'crawler',      name: '爬虫',       color: 'orange', icon: 'globe' },
    { id: 'ai',           name: '人工智能',   color: 'pink',   icon: 'brain' },
    { id: 'api',          name: 'API工具',    color: 'indigo', icon: 'network' },
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
      const res = await pluginService.getPlugins();
      // API 返回 { success, data, total } 结构
      const list = Array.isArray(res) ? res : (res?.data || res?.plugins || []);
      // 统一数据格式
      const normalized = list.map(p => ({
        id: p.id,
        name: p.name,
        version: p.version,
        author: p.author,
        description: p.description,
        category: p.category || p.type || 'other',
        status: p.status,
        installed: p.installed ?? (p.status === 'active'),
        enabled: p.enabled ?? (p.status === 'active'),
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
      setPlugins(normalized.length > 0 ? normalized : mockPlugins);
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
        
        <div className="flex flex-col md:flex-row md:items-center justify-between pt-4 border-t border-white/10/50">
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
    <div className="min-h-screen bg-[#060910] text-white">
      {/* 插件管理头部 */}
      <div className="bg-[#0a0e17]/85 backdrop-blur-sm border-b border-white/10 sticky top-0 z-50">
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
        <div className="flex border-b border-white/10 mb-6">
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
                <span className="ml-2 px-2 py-1 text-xs rounded-full bg-[#111827]">
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
                  className="pl-10 pr-4 py-2 bg-[#0a0e17] border border-white/10 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
                />
              </div>

              {/* 类别过滤 */}
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="px-4 py-2 bg-[#0a0e17] border border-white/10 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                className="px-4 py-2 bg-[#0a0e17] border border-white/10 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                    <div key={category.id} className="p-4 rounded-lg bg-[#0a0e17]/60">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center">
                          <Badge variant={category.color} size="sm" className="mr-3">
                            {category.name}
                          </Badge>
                          <span className="text-sm opacity-70">{count} 个插件</span>
                        </div>
                        <div className="text-sm font-medium">{percent.toFixed(1)}%</div>
                      </div>
                      <div className="w-full h-2 bg-[#111827] rounded-full overflow-hidden">
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
                      <div className="w-32 h-2 bg-[#111827] rounded-full overflow-hidden">
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
                      <div className="w-32 h-2 bg-[#111827] rounded-full overflow-hidden">
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
                  <div className="p-3 rounded-lg bg-[#0a0e17]/60">
                    <div className="text-sm opacity-70 mb-1">插件API</div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-green-500/100 mr-2"></div>
                      <span className="font-medium">运行正常</span>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-[#0a0e17]/60">
                    <div className="text-sm opacity-70 mb-1">沙箱环境</div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-green-500/100 mr-2"></div>
                      <span className="font-medium">已启用</span>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-[#0a0e17]/60">
                    <div className="text-sm opacity-70 mb-1">安全扫描</div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-green-500/100 mr-2"></div>
                      <span className="font-medium">已通过</span>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-[#0a0e17]/60">
                    <div className="text-sm opacity-70 mb-1">依赖检查</div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-green-500/100 mr-2"></div>
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
      <div className="mt-12 py-6 border-t border-white/8">
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
          <div className="bg-[#0a0e17] rounded-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
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
                  <div className="px-4 py-2 bg-[#111827] rounded-lg">{selectedPlugin.id}</div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">版本</label>
                  <div className="px-4 py-2 bg-[#111827] rounded-lg">{selectedPlugin.version}</div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">作者</label>
                  <div className="px-4 py-2 bg-[#111827] rounded-lg">{selectedPlugin.author}</div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">许可证</label>
                  <div className="px-4 py-2 bg-[#111827] rounded-lg">{selectedPlugin.license}</div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">大小</label>
                  <div className="px-4 py-2 bg-[#111827] rounded-lg">{selectedPlugin.size}</div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">最后更新</label>
                  <div className="px-4 py-2 bg-[#111827] rounded-lg">{selectedPlugin.lastUpdated}</div>
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
          <div className="bg-[#0a0e17] rounded-xl max-w-md w-full p-6">
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
                  className="w-full px-4 py-2 bg-[#111827] border border-white/15 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="输入插件URL或GitHub仓库地址"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">版本</label>
                <select className="w-full px-4 py-2 bg-[#111827] border border-white/15 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
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
