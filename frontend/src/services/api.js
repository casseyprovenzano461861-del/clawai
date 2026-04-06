/**
 * 统一API服务层
 * 提供统一的API调用接口，包含错误处理、认证头管理和数据转换
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

/**
 * API请求配置
 */
const defaultConfig = {
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * 获取认证头
 */
function getAuthHeaders() {
  const token = localStorage.getItem('token') || '';
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * 统一请求处理
 * @param {string} endpoint - API端点
 * @param {Object} options - 请求选项
 * @returns {Promise<any>} 响应数据
 */
async function request(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;

  const headers = {
    ...defaultConfig.headers,
    ...getAuthHeaders(),
    ...options.headers,
  };

  const config = {
    ...defaultConfig,
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const errorText = await response.text();
      let errorData;
      try {
        errorData = JSON.parse(errorText);
      } catch {
        errorData = { message: errorText || '请求失败' };
      }

      const error = new Error(errorData.message || `HTTP ${response.status}`);
      error.status = response.status;
      error.data = errorData;
      throw error;
    }

    // 空响应处理
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }

    return response.text();
  } catch (error) {
    console.error('API请求失败:', {
      endpoint,
      error: error.message,
      status: error.status,
      data: error.data,
    });

    // 网络错误处理
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('网络连接失败，请检查服务器状态');
    }

    throw error;
  }
}

/**
 * API服务对象
 */
export const api = {
  // 基础请求方法
  get: (endpoint, options = {}) => request(endpoint, { ...options, method: 'GET' }),
  post: (endpoint, data, options = {}) => request(endpoint, {
    ...options,
    method: 'POST',
    body: JSON.stringify(data)
  }),
  put: (endpoint, data, options = {}) => request(endpoint, {
    ...options,
    method: 'PUT',
    body: JSON.stringify(data)
  }),
  delete: (endpoint, options = {}) => request(endpoint, { ...options, method: 'DELETE' }),
  patch: (endpoint, data, options = {}) => request(endpoint, {
    ...options,
    method: 'PATCH',
    body: JSON.stringify(data)
  }),

  // 认证相关API
  auth: {
    login: (credentials) => api.post('/auth/login', credentials),
    register: (userData) => api.post('/auth/register', userData),
    logout: () => api.post('/auth/logout'),
    getCurrentUser: () => api.get('/auth/me'),
    refreshToken: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken }),
  },

  // 用户管理API
  users: {
    list: (params = {}) => api.get('/api/v1/users', { params }),
    get: (userId) => api.get(`/api/v1/users/${userId}`),
    create: (userData) => api.post('/api/v1/users', userData),
    update: (userId, userData) => api.put(`/api/v1/users/${userId}`, userData),
    delete: (userId) => api.delete(`/api/v1/users/${userId}`),
    resetPassword: (userId, passwordData) => api.post(`/api/v1/users/${userId}/reset-password`, passwordData),
  },

  // 知识图谱API
  knowledgeGraph: {
    getGraph: () => api.get('/api/v1/knowledge-graph/graph'),
    getStats: () => api.get('/api/v1/knowledge-graph/stats'),
    getNodeDetails: (nodeId) => api.get(`/api/v1/knowledge-graph/node/${nodeId}`),
    getEdgeDetails: (edgeId) => api.get(`/api/v1/knowledge-graph/edge/${edgeId}`),
    search: (query, filters = {}) => api.get('/api/v1/knowledge-graph/search', { params: { query, ...filters } }),
    getConfig: () => api.get('/api/v1/knowledge-graph/config'),
    health: () => api.get('/api/v1/knowledge-graph/health'),
  },

  // 报告管理API
  reports: {
    list: (params = {}) => api.get('/api/v1/reports', { params }),
    get: (reportId) => api.get(`/api/v1/reports/${reportId}`),
    generate: (reportData) => api.post('/api/v1/reports/generate', reportData),
    download: (reportId, format = 'html') => api.get(`/api/v1/reports/${reportId}/download?format=${format}`),
    delete: (reportId) => api.delete(`/api/v1/reports/${reportId}`),
  },

  // RBAC管理API
  rbac: {
    getRoles: () => api.get('/rbac/roles'),
    createRole: (roleData) => api.post('/rbac/roles', roleData),
    deleteRole: (roleName) => api.delete(`/rbac/roles/${roleName}`),
    getUserRoles: (username) => api.get(`/rbac/users/${username}/roles`),
    assignRole: (username, roleName) => api.post(`/rbac/users/${username}/roles`, { role: roleName }),
    removeRole: (username, roleName) => api.delete(`/rbac/users/${username}/roles/${roleName}`),
    getUserPermissions: (username) => api.get(`/rbac/users/${username}/permissions`),
    checkPermission: (permission) => api.post('/rbac/check-permission', { permission }),
    getStats: () => api.get('/rbac/stats'),
  },

  // 工具管理API
  tools: {
    list: () => api.get('/tools'),
    execute: (toolData) => api.post('/tools/execute', toolData),
  },

  // 扫描管理API
  scans: {
    list: (params = {}) => api.get('/api/v1/scans', { params }),
    get: (scanId) => api.get(`/api/v1/scans/${scanId}`),
    create: (scanData) => api.post('/api/v1/scans', scanData),
    update: (scanId, scanData) => api.put(`/api/v1/scans/${scanId}`, scanData),
    delete: (scanId) => api.delete(`/api/v1/scans/${scanId}`),
    execute: (scanId) => api.post(`/api/v1/scans/${scanId}/execute`),
  },

  // 插件管理API
  plugins: {
    list: (params = {}) => api.get('/api/v1/plugins', { params }),
    install: (pluginData) => api.post('/api/v1/plugins/install', pluginData),
    uninstall: (pluginId) => api.post(`/api/v1/plugins/${pluginId}/uninstall`),
    enable: (pluginId) => api.post(`/api/v1/plugins/${pluginId}/enable`),
    disable: (pluginId) => api.post(`/api/v1/plugins/${pluginId}/disable`),
  },

  // 系统健康检查
  health: {
    auth: () => api.get('/auth/health'),
    main: () => api.get('/api/v1/health'),
    knowledgeGraph: () => api.knowledgeGraph.health(),
  },
};

/**
 * 设置认证令牌
 * @param {string} token - JWT令牌
 */
export function setAuthToken(token) {
  localStorage.setItem('token', token);
}

/**
 * 清除认证令牌
 */
export function clearAuthToken() {
  localStorage.removeItem('token');
}

/**
 * 检查是否已认证
 * @returns {boolean} 是否已认证
 */
export function isAuthenticated() {
  return !!localStorage.getItem('token');
}

/**
 * 获取当前令牌
 * @returns {string|null} 当前令牌
 */
export function getAuthToken() {
  return localStorage.getItem('token');
}

/**
 * 请求拦截器（可扩展）
 */
export const interceptors = {
  request: [],
  response: [],

  useRequest(interceptor) {
    this.request.push(interceptor);
  },

  useResponse(interceptor) {
    this.response.push(interceptor);
  },
};

// 默认导出
export default api;