/**
 * API客户端配置和基础请求函数
 */
import axios from 'axios';

// API基础URL
const API_BASE_URL = 'http://localhost:8888/api/v1';

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

// 导出axios实例
export default apiClient;