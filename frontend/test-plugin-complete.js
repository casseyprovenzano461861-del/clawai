// 辅助函数
function getCategoryColorClass(category) {
    const cat = pluginCategories.find(c => c.id === category);
    return cat ? `bg-${cat.color}-500` : 'bg-gray-500';
}

function getCategoryBadgeClass(category) {
    const cat = pluginCategories.find(c => c.id === category);
    return cat ? `badge-${cat.color}` : 'badge-gray';
}

function getCategoryName(category) {
    const cat = pluginCategories.find(c => c.id === category);
    return cat ? cat.name : category;
}

function getPluginIcon(icon, category) {
    const cat = pluginCategories.find(c => c.id === category);
    const colorClass = cat ? `text-${cat.color}-500` : 'text-gray-500';
    
    const iconMap = {
        'shield': `<i class="fas fa-shield-alt ${colorClass} text-xl"></i>`,
        'database': `<i class="fas fa-database ${colorClass} text-xl"></i>`,
        'file-text': `<i class="fas fa-file-alt ${colorClass} text-xl"></i>`,
        'globe': `<i class="fas fa-globe ${colorClass} text-xl"></i>`,
        'brain': `<i class="fas fa-brain ${colorClass} text-xl"></i>`,
        'network': `<i class="fas fa-network-wired ${colorClass} text-xl"></i>`,
        'shield-check': `<i class="fas fa-shield-check ${colorClass} text-xl"></i>`,
        'layout': `<i class="fas fa-th-large ${colorClass} text-xl"></i>`
    };
    
    return iconMap[icon] || `<i class="fas fa-puzzle-piece ${colorClass} text-xl"></i>`;
}

function getStatusBadgeClass(status) {
    const statusMap = {
        'active': 'badge-green',
        'inactive': 'badge-orange',
        'available': 'badge-blue',
        'updating': 'badge-yellow',
        'error': 'badge-red'
    };
    return statusMap[status] || 'badge-gray';
}

function getStatusText(status) {
    const statusMap = {
        'active': '已激活',
        'inactive': '已禁用',
        'available': '可安装',
        'updating': '更新中',
        'error': '错误'
    };
    return statusMap[status] || status;
}

// 重置所有过滤
function resetAllFilters() {
    searchInput.value = '';
    categoryFilter.value = 'all';
    statusFilter.value = 'all';
    filterPlugins();
}

// 显示安装插件模态框
function showInstallModal() {
    const modalHtml = `
        <div class="modal-overlay" id="installModal">
            <div class="modal-content">
                <div class="flex items-center justify-between mb-6">
                    <h3 class="text-xl font-semibold">从商店安装插件</h3>
                    <button id="closeInstallModal" class="text-gray-400 hover:text-white">
                        ✕
                    </button>
                </div>
                
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium mb-2">插件URL或ID</label>
                        <input
                            type="text"
                            id="pluginUrl"
                            class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="输入插件URL或GitHub仓库地址"
                        />
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-2">版本</label>
                        <select id="pluginVersion" class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="latest">最新版本</option>
                            <option value="stable">稳定版本</option>
                            <option value="beta">测试版本</option>
                            <option value="specific">指定版本</option>
                        </select>
                    </div>
                    
                    <div class="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-sm">
                        <i class="fas fa-info-circle text-blue-500 mr-2"></i>
                        插件将从官方商店或GitHub仓库下载并安装
                    </div>
                    
                    <div class="flex justify-end space-x-3 pt-4">
                        <button id="cancelInstall" class="button button-outline">
                            取消
                        </button>
                        <button id="confirmInstall" class="button button-primary">
                            <i class="fas fa-download mr-2"></i>
                            安装
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 添加事件监听器
    document.getElementById('closeInstallModal').addEventListener('click', closeInstallModal);
    document.getElementById('cancelInstall').addEventListener('click', closeInstallModal);
    document.getElementById('confirmInstall').addEventListener('click', () => {
        alert('插件安装功能（模拟）');
        closeInstallModal();
    });
}

function closeInstallModal() {
    const modal = document.getElementById('installModal');
    if (modal) {
        modal.remove();
    }
}

// 查看插件详情
function viewPlugin(pluginId) {
    const plugin = plugins.find(p => p.id === pluginId);
    if (!plugin) return;
    
    const modalHtml = `
        <div class="modal-overlay" id="pluginDetailModal">
            <div class="modal-content">
                <div class="flex items-center justify-between mb-6">
                    <h3 class="text-xl font-semibold">插件详情 - ${plugin.name}</h3>
                    <button id="closeDetailModal" class="text-gray-400 hover:text-white">
                        ✕
                    </button>
                </div>
                
                <div class="space-y-6">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium mb-2">插件ID</label>
                            <div class="px-4 py-2 bg-gray-700 rounded-lg">${plugin.id}</div>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium mb-2">版本</label>
                            <div class="px-4 py-2 bg-gray-700 rounded-lg">${plugin.version}</div>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium mb-2">作者</label>
                            <div class="px-4 py-2 bg-gray-700 rounded-lg">${plugin.author}</div>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium mb-2">许可证</label>
                            <div class="px-4 py-2 bg-gray-700 rounded-lg">${plugin.license}</div>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium mb-2">大小</label>
                            <div class="px-4 py-2 bg-gray-700 rounded-lg">${plugin.size}</div>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium mb-2">最后更新</label>
                            <div class="px-4 py-2 bg-gray-700 rounded-lg">${plugin.lastUpdated}</div>
                        </div>
                    </div>
                    
                    <div>
                        <h4 class="font-medium mb-3">描述</h4>
                        <p class="text-gray-300">${plugin.description}</p>
                    </div>
                    
                    <div>
                        <h4 class="font-medium mb-3">依赖项</h4>
                        <div class="flex flex-wrap gap-2">
                            ${plugin.dependencies.map(dep => `
                                <span class="badge badge-outline">${dep}</span>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div>
                        <h4 class="font-medium mb-3">权限</h4>
                        <div class="flex flex-wrap gap-2">
                            ${plugin.permissions.map(perm => `
                                <span class="badge badge-blue">${perm}</span>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div>
                        <h4 class="font-medium mb-3">主页</h4>
                        <a 
                            href="${plugin.homepage}" 
                            target="_blank" 
                            rel="noopener noreferrer"
                            class="text-blue-400 hover:text-blue-300 flex items-center"
                        >
                            <i class="fas fa-external-link-alt mr-2"></i>
                            ${plugin.homepage}
                        </a>
                    </div>
                    
                    <div class="flex justify-end space-x-3 pt-4">
                        <button id="closeDetail" class="button button-outline">
                            关闭
                        </button>
                        ${plugin.installed ? `
                            <button id="updatePlugin" class="button button-outline" data-id="${plugin.id}">
                                <i class="fas fa-sync-alt mr-2"></i>
                                更新插件
                            </button>
                            <button id="togglePlugin" class="button button-primary" data-id="${plugin.id}">
                                ${plugin.enabled ? '禁用插件' : '激活插件'}
                            </button>
                        ` : `
                            <button id="installPlugin" class="button button-primary" data-id="${plugin.id}">
                                <i class="fas fa-download mr-2"></i>
                                安装插件
                            </button>
                        `}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 添加事件监听器
    document.getElementById('closeDetailModal').addEventListener('click', closeDetailModal);
    document.getElementById('closeDetail').addEventListener('click', closeDetailModal);
    
    if (plugin.installed) {
        document.getElementById('updatePlugin').addEventListener('click', () => {
            updatePlugin(plugin.id);
            closeDetailModal();
        });
        document.getElementById('togglePlugin').addEventListener('click', () => {
            togglePlugin(plugin.id);
            closeDetailModal();
        });
    } else {
        document.getElementById('installPlugin').addEventListener('click', () => {
            installPlugin(plugin.id);
            closeDetailModal();
        });
    }
}

function closeDetailModal() {
    const modal = document.getElementById('pluginDetailModal');
    if (modal) {
        modal.remove();
    }
}

// 安装插件
function installPlugin(pluginId) {
    const plugin = plugins.find(p => p.id === pluginId);
    if (plugin) {
        alert(`正在安装插件: ${plugin.name}`);
        plugins = plugins.map(p => {
            if (p.id === pluginId) {
                return { 
                    ...p, 
                    installed: true, 
                    enabled: true, 
                    status: 'active' 
                };
            }
            return p;
        });
        
        renderPluginList();
        renderCategoryDistribution();
        updateTabCounts();
    }
}

// 卸载插件
function uninstallPlugin(pluginId) {
    const plugin = plugins.find(p => p.id === pluginId);
    if (plugin && confirm(`确定要卸载插件 "${plugin.name}" 吗？`)) {
        plugins = plugins.map(p => {
            if (p.id === pluginId) {
                return { 
                    ...p, 
                    installed: false, 
                    enabled: false, 
                    status: 'available' 
                };
            }
            return p;
        });
        
        alert(`插件 ${plugin.name} 已卸载`);
        renderPluginList();
        renderCategoryDistribution();
        updateTabCounts();
    }
}

// 切换插件状态
function togglePlugin(pluginId) {
    plugins = plugins.map(plugin => {
        if (plugin.id === pluginId) {
            const newEnabled = !plugin.enabled;
            const newStatus = newEnabled ? 'active' : 'inactive';
            alert(`已将插件 ${plugin.name} ${newEnabled ? '激活' : '禁用'}`);
            return { ...plugin, enabled: newEnabled, status: newStatus };
        }
        return plugin;
    });
    
    renderPluginList();
    updateTabCounts();
}

// 更新插件
function updatePlugin(pluginId) {
    const plugin = plugins.find(p => p.id === pluginId);
    if (plugin) {
        alert(`正在更新插件: ${plugin.name}`);
        
        // 模拟更新过程
        plugins = plugins.map(p => {
            if (p.id === pluginId) {
                return { 
                    ...p, 
                    status: 'updating',
                    version: `${(parseFloat(p.version) + 0.1).toFixed(1)}`
                };
            }
            return p;
        });
        
        renderPluginList();
        
        // 3秒后完成更新
        setTimeout(() => {
            plugins = plugins.map(p => {
                if (p.id === pluginId) {
                    return { ...p, status: 'active' };
                }
                return p;
            });
            
            alert(`插件 ${plugin.name} 更新完成`);
            renderPluginList();
            updateTabCounts();
        }, 3000);
    }
}

// 更新标签页计数
function updateTabCounts() {
    const installedCount = plugins.filter(p => p.installed).length;
    const availableCount = plugins.filter(p => !p.installed).length;
    const updateCount = plugins.filter(p => p.status === 'updating').length;
    
    // 更新标签页计数显示
    const installedBadge = tabInstalled.querySelector('span');
    const availableBadge = tabAvailable.querySelector('span');
    const updatesBadge = tabUpdates.querySelector('span');
    
    if (installedBadge) installedBadge.textContent = installedCount;
    if (availableBadge) availableBadge.textContent = availableCount;
    if (updatesBadge) updatesBadge.textContent = updateCount;
    
    // 更新统计卡片
    updateStatsCards();
}

// 更新统计卡片
function updateStatsCards() {
    const installedCount = plugins.filter(p => p.installed).length;
    const activeCount = plugins.filter(p => p.enabled).length;
    const availableCount = plugins.filter(p => !p.installed).length;
    const updateCount = plugins.filter(p => p.status === 'updating').length;
    const totalSize = plugins
        .filter(p => p.installed)
        .reduce((sum, p) => sum + parseFloat(p.size), 0)
        .toFixed(1);
    
    // 这里可以更新统计卡片的显示
    console.log('统计更新:', {
        installedCount,
        activeCount,
        availableCount,
        updateCount,
        totalSize
    });
}

// 初始化标签页计数
updateTabCounts();