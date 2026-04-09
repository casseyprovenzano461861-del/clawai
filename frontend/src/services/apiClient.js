/**
 * API客户端配置和基础请求函数
 */
import axios from 'axios';

// API基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE || 'http://localhost:8001/api/v1';

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30秒超时
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  }
});

// 请求拦截器：添加认证令牌
apiClient.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器：处理错误和令牌刷新
apiClient.interceptors.response.use(
  (response) => {
    // 处理标准响应格式
    if (response.data && response.data.success === false) {
      return Promise.reject(new Error(response.data.detail || '请求失败'));
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // 处理401错误：尝试刷新令牌
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          // 尝试刷新令牌
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken
          });

          if (response.data.access_token) {
            localStorage.setItem('access_token', response.data.access_token);
            // 更新原请求的Authorization头
            originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
            return apiClient(originalRequest);
          }
        }
      } catch (refreshError) {
        // 刷新失败，跳转到登录页
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // 处理其他错误
    const errorMessage = error.response?.data?.detail ||
                        error.response?.data?.message ||
                        error.message ||
                        '请求失败';

    console.error('API请求错误:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      message: errorMessage
    });

    return Promise.reject(new Error(errorMessage));
  }
);

// 通用请求方法
export const request = {
  // GET请求
  get: (url, config = {}) =>
    apiClient.get(url, config).then(response => response.data),

  // POST请求
  post: (url, data, config = {}) =>
    apiClient.post(url, data, config).then(response => response.data),

  // PUT请求
  put: (url, data, config = {}) =>
    apiClient.put(url, data, config).then(response => response.data),

  // DELETE请求
  delete: (url, config = {}) =>
    apiClient.delete(url, config).then(response => response.data),

  // PATCH请求
  patch: (url, data, config = {}) =>
    apiClient.patch(url, data, config).then(response => response.data),
};

// 设置认证令牌
export const setAuthTokens = (accessToken, refreshToken) => {
  if (accessToken) {
    localStorage.setItem('access_token', accessToken);
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
  }
  if (refreshToken) {
    localStorage.setItem('refresh_token', refreshToken);
  }
};

// 清除认证令牌
export const clearAuthTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  delete apiClient.defaults.headers.common['Authorization'];
};

// 检查是否已认证
export const isAuthenticated = () => {
  return !!localStorage.getItem('access_token');
};

// 获取当前用户信息
export const getCurrentUser = () => {
  const userStr = localStorage.getItem('current_user');
  return userStr ? JSON.parse(userStr) : null;
};

// 设置当前用户信息
export const setCurrentUser = (user) => {
  localStorage.setItem('current_user', JSON.stringify(user));
};

// 向后兼容：单数形式别名
export const setAuthToken = (token) => setAuthTokens(token);
export const clearAuthToken = () => clearAuthTokens();
export const getAuthToken = () => localStorage.getItem('access_token');

/**
 * API服务对象 - 提供命名空间的API方法
 */
export const api = {
  // 基础请求方法
  get: (endpoint, options = {}) => request.get(endpoint, options),
  post: (endpoint, data, options = {}) => request.post(endpoint, data, options),
  put: (endpoint, data, options = {}) => request.put(endpoint, data, options),
  delete: (endpoint, options = {}) => request.delete(endpoint, options),
  patch: (endpoint, data, options = {}) => request.patch(endpoint, data, options),

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
    list: (params = {}) => api.get('/users', { params }),
    get: (userId) => api.get(`/users/${userId}`),
    create: (userData) => api.post('/users', userData),
    update: (userId, userData) => api.put(`/users/${userId}`, userData),
    delete: (userId) => api.delete(`/users/${userId}`),
    resetPassword: (userId, passwordData) => api.post(`/users/${userId}/reset-password`, passwordData),
  },

  // 知识图谱API
  knowledgeGraph: {
    getGraph: () => api.get('/knowledge-graph/graph'),
    getStats: () => api.get('/knowledge-graph/stats'),
    getNodeDetails: (nodeId) => api.get(`/knowledge-graph/node/${nodeId}`),
    getEdgeDetails: (edgeId) => api.get(`/knowledge-graph/edge/${edgeId}`),
    search: (query, filters = {}) => api.get('/knowledge-graph/search', { params: { query, ...filters } }),
    getConfig: () => api.get('/knowledge-graph/config'),
    health: () => api.get('/knowledge-graph/health'),
  },

  // 报告管理API
  reports: {
    list: (params = {}) => api.get('/reports', { params }),
    get: (reportId) => api.get(`/reports/${reportId}`),
    generate: (reportData) => api.post('/reports/generate', reportData),
    download: (reportId, format = 'html') => api.get(`/reports/${reportId}/download?format=${format}`),
    delete: (reportId) => api.delete(`/reports/${reportId}`),
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
    list: (params = {}) => api.get('/scans', { params }),
    get: (scanId) => api.get(`/scans/${scanId}`),
    create: (scanData) => api.post('/scans', scanData),
    update: (scanId, scanData) => api.put(`/scans/${scanId}`, scanData),
    delete: (scanId) => api.delete(`/scans/${scanId}`),
    execute: (scanId) => api.post(`/scans/${scanId}/execute`),
  },

  // 插件管理API
  plugins: {
    list: (params = {}) => api.get('/plugins', { params }),
    install: (pluginData) => api.post('/plugins/install', pluginData),
    uninstall: (pluginId) => api.post(`/plugins/${pluginId}/uninstall`),
    enable: (pluginId) => api.post(`/plugins/${pluginId}/enable`),
    disable: (pluginId) => api.post(`/plugins/${pluginId}/disable`),
  },

  // 系统健康检查
  health: {
    auth: () => api.get('/auth/health'),
    main: () => api.get('/health'),
    knowledgeGraph: () => api.knowledgeGraph.health(),
  },
};

// 导出axios实例
export default apiClient;
