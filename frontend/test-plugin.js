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

let plugins = [...mockPlugins];
let activeTab = 'installed';

// 获取DOM元素
const pluginList = document.getElementById('pluginList');
const categoryDistribution = document.getElementById('categoryDistribution');
const searchInput = document.getElementById('searchInput');
const categoryFilter = document.getElementById('categoryFilter');
const statusFilter = document.getElementById('statusFilter');
const resetFilters = document.getElementById('resetFilters');
const installPluginBtn = document.getElementById('installPluginBtn');
const tabInstalled = document.getElementById('tabInstalled');
const tabAvailable = document.getElementById('tabAvailable');
const tabUpdates = document.getElementById('tabUpdates');
const tabSettings = document.getElementById('tabSettings');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    renderPluginList();
    renderCategoryDistribution();
    
    // 事件监听
    searchInput.addEventListener('input', filterPlugins);
    categoryFilter.addEventListener('change', filterPlugins);
    statusFilter.addEventListener('change', filterPlugins);
    resetFilters.addEventListener('click', resetAllFilters);
    installPluginBtn.addEventListener('click', showInstallModal);
    
    // 标签页事件
    tabInstalled.addEventListener('click', () => switchTab('installed'));
    tabAvailable.addEventListener('click', () => switchTab('available'));
    tabUpdates.addEventListener('click', () => switchTab('updates'));
    tabSettings.addEventListener('click', () => switchTab('settings'));
});

// 切换标签页
function switchTab(tab) {
    activeTab = tab;
    
    // 更新标签页样式
    [tabInstalled, tabAvailable, tabUpdates, tabSettings].forEach(t => {
        t.classList.remove('active');
    });
    
    document.getElementById(`tab${tab.charAt(0).toUpperCase() + tab.slice(1)}`).classList.add('active');
    
    // 重新渲染插件列表
    filterPlugins();
}

// 渲染插件列表
function renderPluginList(filteredPlugins = plugins) {
    pluginList.innerHTML = '';
    
    // 根据当前标签页过滤
    let displayPlugins = filteredPlugins.filter(plugin => {
        if (activeTab === 'installed' && !plugin.installed) return false;
        if (activeTab === 'available' && plugin.installed) return false;
        if (activeTab === 'updates' && plugin.status !== 'updating') return false;
        return true;
    });
    
    if (displayPlugins.length === 0) {
        pluginList.innerHTML = `
            <div class="stat-card p-8 text-center">
                <i class="fas fa-box text-5xl text-gray-500 mb-4"></i>
                <h3 class="text-xl font-semibold mb-2">未找到插件</h3>
                <p class="text-gray-400 mb-6">
                    ${activeTab === 'installed' 
                        ? '您还没有安装任何插件。'
                        : activeTab === 'available'
                        ? '没有可用的插件。'
                        : '没有需要更新的插件。'}
                </p>
                ${activeTab === 'installed' ? `
                    <button class="button button-primary" onclick="switchTab('available')">
                        <i class="fas fa-download mr-2"></i>
                        浏览可安装插件
                    </button>
                ` : ''}
            </div>
        `;
        return;
    }
    
    displayPlugins.forEach(plugin => {
        const pluginCard = document.createElement('div');
        pluginCard.className = 'plugin-card';
        pluginCard.innerHTML = `
            <div class="flex flex-col md:flex-row md:items-center justify-between mb-4">
                <div class="flex items-start mb-4 md:mb-0">
                    <div class="p-3 rounded-lg ${getCategoryColorClass(plugin.category)}/10 mr-4">
                        ${getPluginIcon(plugin.icon, plugin.category)}
                    </div>
                    
                    <div>
                        <div class="flex items-center">
                            <h3 class="text-lg font-semibold mr-2">${plugin.name}</h3>
                            <span class="badge ${getCategoryBadgeClass(plugin.category)}">
                                ${getCategoryName(plugin.category)}
                            </span>
                        </div>
                        <p class="text-sm opacity-70 mt-1">${plugin.description}</p>
                        <div class="flex items-center mt-2 space-x-4">
                            <div class="flex items-center text-sm">
                                <i class="fas fa-star text-yellow-500 mr-1"></i>
                                <span>${plugin.rating}</span>
                                <span class="opacity-70 ml-1">(${plugin.downloads} 下载)</span>
                            </div>
                            <div class="text-sm opacity-70">版本 ${plugin.version}</div>
                            <div class="text-sm opacity-70">作者: ${plugin.author}</div>
                        </div>
                    </div>
                </div>
                
                <div class="flex flex-col items-end">
                    <span class="badge ${getStatusBadgeClass(plugin.status)} mb-2">
                        ${getStatusText(plugin.status)}
                    </span>
                    <div class="text-sm opacity-70">${plugin.size}</div>
                </div>
            </div>
            
            <div class="flex flex-col md:flex-row md:items-center justify-between pt-4 border-t border-gray-700/50">
                <div class="flex flex-wrap gap-2 mb-4 md:mb-0">
                    ${plugin.permissions.slice(0, 3).map(permission => `
                        <span class="badge badge-outline">${permission}</span>
                    `).join('')}
                    ${plugin.permissions.length > 3 ? `
                        <span class="badge badge-outline">+${plugin.permissions.length - 3} 更多</span>
                    ` : ''}
                </div>
                
                <div class="flex items-center space-x-2">
                    <button class="button button-ghost view-plugin" data-id="${plugin.id}">
                        <i class="fas fa-info-circle mr-1"></i>
                        详情
                    </button>
                    
                    ${plugin.installed ? `
                        ${plugin.status === 'updating' ? `
                            <button class="button button-outline" disabled>
                                <i class="fas fa-sync-alt mr-1 animate-spin"></i>
                                更新中
                            </button>
                        ` : `
                            <button class="button button-outline update-plugin" data-id="${plugin.id}">
                                <i class="fas fa-sync-alt mr-1"></i>
                                更新
                            </button>
                        `}
                        
                        <button class="button ${plugin.enabled ? 'button-outline' : 'button-primary'} toggle-plugin" data-id="${plugin.id}">
                            ${plugin.enabled ? `
                                <i class="fas fa-stop-circle mr-1"></i>
                                禁用
                            ` : `
                                <i class="fas fa-play mr-1"></i>
                                激活
                            `}
                        </button>
                        
                        <button class="button button-ghost uninstall-plugin" data-id="${plugin.id}" style="color: #ef4444;">
                            <i class="fas fa-trash mr-1"></i>
                            卸载
                        </button>
                    ` : `
                        <button class="button button-primary install-plugin" data-id="${plugin.id}">
                            <i class="fas fa-download mr-1"></i>
                            安装
                        </button>
                    `}
                    
                    <button class="button button-ghost">
                        <i class="fas fa-ellipsis-v"></i>
                    </button>
                </div>
            </div>
        `;
        pluginList.appendChild(pluginCard);
    });
    
    // 添加事件监听器
    document.querySelectorAll('.view-plugin').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pluginId = e.target.closest('button').dataset.id;
            viewPlugin(pluginId);
        });
    });
    
    document.querySelectorAll('.install-plugin').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pluginId = e.target.closest('button').dataset.id;
            installPlugin(pluginId);
        });
    });
    
    document.querySelectorAll('.uninstall-plugin').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pluginId = e.target.closest('button').dataset.id;
            uninstallPlugin(pluginId);
        });
    });
    
    document.querySelectorAll('.toggle-plugin').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pluginId = e.target.closest('button').dataset.id;
            togglePlugin(pluginId);
        });
    });
    
    document.querySelectorAll('.update-plugin').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pluginId = e.target.closest('button').dataset.id;
            updatePlugin(pluginId);
        });
    });
}

// 渲染类别分布
function renderCategoryDistribution() {
    categoryDistribution.innerHTML = '';
    
    pluginCategories
        .filter(cat => cat.id !== 'all')
        .forEach(category => {
            const count = plugins.filter(p => p.category === category.id && p.installed).length;
            const totalInstalled = plugins.filter(p => p.installed).length;
            const percent = totalInstalled > 0 ? (count / totalInstalled) * 100 : 0;
            
            const categoryItem = document.createElement('div');
            categoryItem.className = 'p-4 rounded-lg bg-gray-800/50 mb-4';
            categoryItem.innerHTML = `
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center">
                        <span class="badge ${getCategoryBadgeClass(category.id)} mr-3">
                            ${category.name}
                        </span>
                        <span class="text-sm opacity-70">${count} 个插件</span>
                    </div>
                    <div class="text-sm font-medium">${percent.toFixed(1)}%</div>
                </div>
                <div class="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div class="h-full ${getCategoryColorClass(category.id)}" style="width: ${percent}%"></div>
                </div>
            `;
            categoryDistribution.appendChild(categoryItem);
        });
}

// 过滤插件
function filterPlugins() {
    const searchTerm = searchInput.value.toLowerCase();
    const selectedCategory = categoryFilter.value;
    const selectedStatus = statusFilter.value;
    
    const filtered = plugins.filter(plugin => {
        const matchesSearch = searchTerm === '' || 
            plugin.name.toLowerCase().includes(searchTerm) ||
            plugin.description.toLowerCase().includes(searchTerm) ||
            plugin.author.toLowerCase().includes(searchTerm);
        
        const matchesCategory = selectedCategory === 'all' || plugin.category === selectedCategory;
        const matchesStatus = selectedStatus === 'all' || plugin.status === selectedStatus;
        
        return matchesSearch && matchesCategory && matchesStatus;
    });
    
    renderPluginList(filtered);
}

// 重置所有过滤
function resetAllFilters