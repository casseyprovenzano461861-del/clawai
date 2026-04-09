/**
 * 用户管理API服务
 */
import { request, getCurrentUser, setCurrentUser } from './apiClient';
import { USE_MOCK_DATA } from './config';

// 用户状态枚举
export const UserStatus = {
  ACTIVE: 'active',
  INACTIVE: 'inactive',
  SUSPENDED: 'suspended',
  LOCKED: 'locked'
};

// 用户角色枚举
export const UserRole = {
  ADMIN: 'admin',
  USER: 'user',
  ANALYST: 'analyst',
  VIEWER: 'viewer',
  DEVELOPER: 'developer'
};

// 权限分类
export const PermissionCategory = {
  SYSTEM: '系统管理',
  SECURITY: '安全操作',
  TOOLS: '工具使用',
  REPORTS: '报告管理',
  DATA: '数据访问'
};

/**
 * 用户登录
 * @param {Object} credentials - 登录凭据
 * @param {string} credentials.username - 用户名
 * @param {string} credentials.password - 密码
 * @returns {Promise} 登录结果
 */
export const login = async (credentials) => {
  try {
    // 实际API调用
    const response = await request.post('/auth/login', credentials);

    // 保存token和用户信息
    if (response.access_token) {
      localStorage.setItem('access_token', response.access_token);
      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token);
      }
      if (response.user) {
        setCurrentUser(response.user);
      }
    }

    return response;
  } catch (error) {
    if (USE_MOCK_DATA) {
      // API失败时使用模拟登录（仅用于开发）
      console.warn('API登录失败，使用模拟用户:', error.message);

      // 模拟登录逻辑
      if (credentials.username === 'admin' && credentials.password === 'admin123') {
      const mockUser = {
        id: '1',
        username: 'admin',
        email: 'admin@clawai.com',
        full_name: '系统管理员',
        status: UserStatus.ACTIVE,
        roles: [UserRole.ADMIN],
        permissions: [
          'system:*',
          'security:*',
          'tools:*',
          'reports:*',
          'data:*'
        ],
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-04-06T10:00:00Z',
        last_login: '2026-04-06T10:00:00Z'
      };

      const mockToken = 'mock_jwt_token_admin_' + Date.now();
      localStorage.setItem('access_token', mockToken);
      setCurrentUser(mockUser);

      return {
        access_token: mockToken,
        token_type: 'bearer',
        expires_in: 3600,
        refresh_token: 'mock_refresh_token',
        user: mockUser
      };
    } else if (credentials.username === 'user' && credentials.password === 'user123') {
      const mockUser = {
        id: '2',
        username: 'user',
        email: 'user@clawai.com',
        full_name: '普通用户',
        status: UserStatus.ACTIVE,
        roles: [UserRole.USER],
        permissions: [
          'reports:view',
          'tools:basic',
          'data:read'
        ],
        created_at: '2026-02-01T00:00:00Z',
        updated_at: '2026-04-06T09:00:00Z',
        last_login: '2026-04-06T09:00:00Z'
      };

      const mockToken = 'mock_jwt_token_user_' + Date.now();
      localStorage.setItem('access_token', mockToken);
      setCurrentUser(mockUser);

      return {
        access_token: mockToken,
        token_type: 'bearer',
        expires_in: 3600,
        refresh_token: 'mock_refresh_token',
        user: mockUser
      };
    } else {
      throw new Error('用户名或密码错误');
    }
    } else {
      throw error;
    }
  }
};

/**
 * 用户注册
 * @param {Object} userData - 用户数据
 * @returns {Promise} 注册结果
 */
export const register = async (userData) => {
  try {
    return await request.post('/auth/register', userData);
  } catch (error) {
    if (USE_MOCK_DATA) {
      console.warn('API注册失败，使用模拟注册:', error.message);

      // 模拟注册逻辑
      const mockUser = {
      id: Date.now().toString(),
      username: userData.username,
      email: userData.email,
      full_name: userData.full_name,
      status: UserStatus.ACTIVE,
      roles: [UserRole.USER],
      permissions: [
        'reports:view',
        'tools:basic',
        'data:read'
      ],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_login: null
    };

    return {
      ...mockUser,
      message: '注册成功'
    };
    } else {
      throw error;
    }
  }
};

/**
 * 获取当前用户信息
 * @returns {Promise} 当前用户信息
 */
export const getMe = async () => {
  try {
    return await request.get('/auth/me');
  } catch (error) {
    if (USE_MOCK_DATA) {
      console.warn('API获取用户信息失败，使用本地存储:', error.message);

      // 返回本地存储的用户信息
      const user = getCurrentUser();
      if (user) {
        return user;
      }
    }

    throw new Error('用户未登录');
  }
};

/**
 * 更新当前用户信息
 * @param {Object} userData - 用户数据
 * @returns {Promise} 更新结果
 */
export const updateMe = async (userData) => {
  try {
    return await request.put('/auth/me', userData);
  } catch (error) {
    if (USE_MOCK_DATA) {
      console.warn('API更新用户信息失败，更新本地存储:', error.message);

      // 更新本地存储的用户信息
      const currentUser = getCurrentUser();
      const updatedUser = {
        ...currentUser,
        ...userData,
        updated_at: new Date().toISOString()
      };

      setCurrentUser(updatedUser);

      return updatedUser;
    } else {
      throw error;
    }
  }
};

/**
 * 获取用户列表（需要管理员权限）
 * @param {Object} params - 查询参数
 * @returns {Promise} 用户列表
 */
export const getUsers = async (params = {}) => {
  try {
    // 尝试调用用户管理API
    return await request.get('/auth/users', { params });
  } catch (error) {
    if (USE_MOCK_DATA) {
      console.warn('用户列表API不可用，使用模拟数据:', error.message);

      // 模拟用户数据
      const mockUsers = [
      {
        id: '1',
        username: 'admin',
        email: 'admin@clawai.com',
        full_name: '系统管理员',
        status: UserStatus.ACTIVE,
        roles: [UserRole.ADMIN],
        permissions_count: 25,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-04-06T10:00:00Z',
        last_login: '2026-04-06T10:00:00Z',
        login_count: 127
      },
      {
        id: '2',
        username: 'user',
        email: 'user@clawai.com',
        full_name: '普通用户',
        status: UserStatus.ACTIVE,
        roles: [UserRole.USER],
        permissions_count: 8,
        created_at: '2026-02-01T00:00:00Z',
        updated_at: '2026-04-06T09:00:00Z',
        last_login: '2026-04-06T09:00:00Z',
        login_count: 42
      },
      {
        id: '3',
        username: 'analyst',
        email: 'analyst@clawai.com',
        full_name: '安全分析师',
        status: UserStatus.ACTIVE,
        roles: [UserRole.ANALYST],
        permissions_count: 15,
        created_at: '2026-02-15T00:00:00Z',
        updated_at: '2026-04-05T16:30:00Z',
        last_login: '2026-04-05T16:30:00Z',
        login_count: 63
      },
      {
        id: '4',
        username: 'viewer',
        email: 'viewer@clawai.com',
        full_name: '只读用户',
        status: UserStatus.ACTIVE,
        roles: [UserRole.VIEWER],
        permissions_count: 5,
        created_at: '2026-03-01T00:00:00Z',
        updated_at: '2026-04-04T14:20:00Z',
        last_login: '2026-04-04T14:20:00Z',
        login_count: 18
      },
      {
        id: '5',
        username: 'developer',
        email: 'developer@clawai.com',
        full_name: '开发人员',
        status: UserStatus.ACTIVE,
        roles: [UserRole.DEVELOPER],
        permissions_count: 12,
        created_at: '2026-03-10T00:00:00Z',
        updated_at: '2026-04-03T11:45:00Z',
        last_login: '2026-04-03T11:45:00Z',
        login_count: 31
      }
    ];

    // 应用过滤
    let filteredUsers = [...mockUsers];
    if (params.status) {
      filteredUsers = filteredUsers.filter(user => user.status === params.status);
    }
    if (params.role) {
      filteredUsers = filteredUsers.filter(user => user.roles.includes(params.role));
    }
    if (params.search) {
      const searchLower = params.search.toLowerCase();
      filteredUsers = filteredUsers.filter(user =>
        user.username.toLowerCase().includes(searchLower) ||
        user.email.toLowerCase().includes(searchLower) ||
        user.full_name.toLowerCase().includes(searchLower)
      );
    }

    // 应用分页
    const page = params.page || 1;
    const pageSize = params.pageSize || 20;
    const startIndex = (page - 1) * pageSize;
    const paginatedUsers = filteredUsers.slice(startIndex, startIndex + pageSize);

    return {
      users: paginatedUsers,
      total: filteredUsers.length,
      page,
      page_size: pageSize,
      total_pages: Math.ceil(filteredUsers.length / pageSize)
    };
    } else {
      throw error;
    }
  }
};

/**
 * 获取用户详情
 * @param {string} userId - 用户ID
 * @returns {Promise} 用户详情
 */
export const getUser = async (userId) => {
  try {
    return await request.get(`/auth/users/${userId}`);
  } catch (error) {
    if (USE_MOCK_DATA) {
      console.warn('用户详情API不可用，使用模拟数据:', error.message);

      // 从模拟用户列表中查找
      const mockUsers = await getUsers();
      const user = mockUsers.users.find(u => u.id === userId);

      if (user) {
        return user;
      }
    }

    throw new Error('用户不存在');
  }
};

/**
 * 创建用户（需要管理员权限）
 * @param {Object} userData - 用户数据
 * @returns {Promise} 创建的用户
 */
export const createUser = async (userData) => {
  try {
    return await request.post('/auth/users', userData);
  } catch (error) {
    if (USE_MOCK_DATA) {
      console.warn('创建用户API不可用，使用模拟创建:', error.message);

      // 模拟创建用户
      const newUser = {
      id: Date.now().toString(),
      ...userData,
      status: UserStatus.ACTIVE,
      roles: userData.roles || [UserRole.USER],
      permissions_count: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_login: null,
      login_count: 0
    };

    return newUser;
    } else {
      throw error;
    }
  }
};

/**
 * 更新用户（需要管理员权限）
 * @param {string} userId - 用户ID
 * @param {Object} userData - 用户数据
 * @returns {Promise} 更新结果
 */
export const updateUser = async (userId, userData) => {
  try {
    return await request.put(`/auth/users/${userId}`, userData);
  } catch (error) {
    if (USE_MOCK_DATA) {
      console.warn('更新用户API不可用，使用模拟更新:', error.message);

      // 模拟更新用户
      const existingUser = await getUser(userId);
    const updatedUser = {
      ...existingUser,
      ...userData,
      updated_at: new Date().toISOString()
    };

    return updatedUser;
    } else {
      throw error;
    }
  }
};

/**
 * 删除用户（需要管理员权限）
 * @param {string} userId - 用户ID
 * @returns {Promise} 删除结果
 */
export const deleteUser = async (userId) => {
  try {
    return await request.delete(`/auth/users/${userId}`);
  } catch (error) {
    if (USE_MOCK_DATA) {
      console.warn('删除用户API不可用，使用模拟删除:', error.message);

      // 模拟删除
      return {
        success: true,
        message: `用户 ${userId} 已删除`,
        deleted_at: new Date().toISOString()
      };
    } else {
      throw error;
    }
  }
};

/**
 * 获取权限列表
 * @returns {Promise} 权限列表
 */
export const getPermissions = async () => {
  try {
    return await request.get('/rbac/permissions');
  } catch (error) {
    if (USE_MOCK_DATA) {
      console.warn('权限API不可用，使用模拟权限数据:', error.message);

      // 模拟权限数据
      return [
      // 系统管理权限
      { id: 'system:*', name: '系统完全控制', category: PermissionCategory.SYSTEM, description: '所有系统管理权限' },
      { id: 'system:settings', name: '系统设置', category: PermissionCategory.SYSTEM, description: '管理系统设置' },
      { id: 'system:users', name: '用户管理', category: PermissionCategory.SYSTEM, description: '管理用户账户' },
      { id: 'system:roles', name: '角色管理', category: PermissionCategory.SYSTEM, description: '管理角色和权限' },

      // 安全操作权限
      { id: 'security:*', name: '安全完全控制', category: PermissionCategory.SECURITY, description: '所有安全操作权限' },
      { id: 'security:scan', name: '执行扫描', category: PermissionCategory.SECURITY, description: '执行安全扫描' },
      { id: 'security:attack', name: '执行攻击', category: PermissionCategory.SECURITY, description: '执行攻击测试' },
      { id: 'security:monitor', name: '实时监控', category: PermissionCategory.SECURITY, description: '监控安全状态' },

      // 工具使用权限
      { id: 'tools:*', name: '工具完全控制', category: PermissionCategory.TOOLS, description: '所有工具使用权限' },
      { id: 'tools:basic', name: '基础工具', category: PermissionCategory.TOOLS, description: '使用基础安全工具' },
      { id: 'tools:advanced', name: '高级工具', category: PermissionCategory.TOOLS, description: '使用高级安全工具' },
      { id: 'tools:custom', name: '自定义工具', category: PermissionCategory.TOOLS, description: '使用自定义工具' },

      // 报告管理权限
      { id: 'reports:*', name: '报告完全控制', category: PermissionCategory.REPORTS, description: '所有报告管理权限' },
      { id: 'reports:view', name: '查看报告', category: PermissionCategory.REPORTS, description: '查看安全报告' },
      { id: 'reports:generate', name: '生成报告', category: PermissionCategory.REPORTS, description: '生成安全报告' },
      { id: 'reports:export', name: '导出报告', category: PermissionCategory.REPORTS, description: '导出报告文件' },

      // 数据访问权限
      { id: 'data:*', name: '数据完全控制', category: PermissionCategory.DATA, description: '所有数据访问权限' },
      { id: 'data:read', name: '读取数据', category: PermissionCategory.DATA, description: '读取系统数据' },
      { id: 'data:write', name: '写入数据', category: PermissionCategory.DATA, description: '写入系统数据' },
      { id: 'data:delete', name: '删除数据', category: PermissionCategory.DATA, description: '删除系统数据' }
    ];
    } else {
      throw error;
    }
  }
};

/**
 * 用户登出
 */
export const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('current_user');
};

// 用户服务
const userService = {
  login,
  register,
  getMe,
  updateMe,
  getUsers,
  getUser,
  createUser,
  updateUser,
  deleteUser,
  getPermissions,
  logout,
  UserStatus,
  UserRole,
  PermissionCategory
};

export default userService;