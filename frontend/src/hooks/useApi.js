/**
 * 统一API钩子
 * 提供React钩子用于API调用，包含加载状态、错误处理和缓存
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../services/api';

/**
 * API钩子配置
 */
const defaultConfig = {
  manual: false,           // 是否手动触发
  initialData: null,       // 初始数据
  refreshInterval: 0,      // 刷新间隔（毫秒）
  cacheTime: 0,            // 缓存时间（毫秒）
  retryCount: 0,           // 重试次数
  retryDelay: 1000,        // 重试延迟（毫秒）
  onSuccess: null,         // 成功回调
  onError: null,           // 错误回调
};

/**
 * 缓存管理器
 */
const cache = new Map();

/**
 * 检查缓存是否有效
 */
function isCacheValid(key, cacheTime) {
  if (!cache.has(key)) return false;
  const { timestamp } = cache.get(key);
  return Date.now() - timestamp < cacheTime;
}

/**
 * 获取缓存数据
 */
function getCache(key) {
  return cache.has(key) ? cache.get(key).data : null;
}

/**
 * 设置缓存数据
 */
function setCache(key, data) {
  cache.set(key, { data, timestamp: Date.now() });
}

/**
 * 清除缓存
 */
function clearCache(key) {
  if (key) {
    cache.delete(key);
  } else {
    cache.clear();
  }
}

/**
 * 主API钩子
 * @param {Function|string} fetcher - API调用函数或端点字符串
 * @param {Object} options - 配置选项
 * @returns {Object} 状态和数据
 */
export function useApi(fetcher, options = {}) {
  const config = { ...defaultConfig, ...options };
  const [data, setData] = useState(config.initialData);
  const [loading, setLoading] = useState(!config.manual);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, loading, success, error

  const fetchRef = useRef();
  const abortControllerRef = useRef();
  const cacheKey = typeof fetcher === 'string' ? fetcher : null;

  // 创建实际的fetch函数
  const fetchData = useCallback(async (fetchOptions = {}) => {
    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // 创建新的AbortController
    abortControllerRef.current = new AbortController();

    // 检查缓存
    if (cacheKey && config.cacheTime > 0 && isCacheValid(cacheKey, config.cacheTime)) {
      const cachedData = getCache(cacheKey);
      setData(cachedData);
      setStatus('success');
      if (config.onSuccess) config.onSuccess(cachedData);
      return cachedData;
    }

    setLoading(true);
    setError(null);
    setStatus('loading');

    let retryCount = 0;
    let lastError = null;

    while (retryCount <= config.retryCount) {
      try {
        // 执行API调用
        let result;
        if (typeof fetcher === 'function') {
          result = await fetcher({
            signal: abortControllerRef.current.signal,
            ...fetchOptions,
          });
        } else if (typeof fetcher === 'string') {
          // 如果是字符串，使用api.get方法
          result = await api.get(fetcher, {
            signal: abortControllerRef.current.signal,
            ...fetchOptions,
          });
        } else {
          throw new Error('无效的fetcher参数');
        }

        // 更新状态
        setData(result);
        setLoading(false);
        setStatus('success');

        // 缓存数据
        if (cacheKey && config.cacheTime > 0) {
          setCache(cacheKey, result);
        }

        // 成功回调
        if (config.onSuccess) config.onSuccess(result);

        return result;
      } catch (err) {
        lastError = err;

        // 如果是取消请求，不重试
        if (err.name === 'AbortError') {
          break;
        }

        // 检查是否达到重试次数
        if (retryCount >= config.retryCount) {
          break;
        }

        // 等待重试延迟
        await new Promise(resolve => setTimeout(resolve, config.retryDelay));
        retryCount++;
      }
    }

    // 所有重试都失败
    setError(lastError);
    setLoading(false);
    setStatus('error');

    // 错误回调
    if (config.onError) config.onError(lastError);

    throw lastError;
  }, [fetcher, config, cacheKey]);

  // 保存fetch函数引用
  fetchRef.current = fetchData;

  // 自动获取数据（如果不是手动模式）
  useEffect(() => {
    if (!config.manual) {
      fetchData();
    }

    // 设置刷新间隔
    let intervalId = null;
    if (config.refreshInterval > 0) {
      intervalId = setInterval(() => {
        fetchData();
      }, config.refreshInterval);
    }

    // 清理函数
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [config.manual, config.refreshInterval, fetchData]);

  // 手动触发函数
  const trigger = useCallback((options) => fetchData(options), [fetchData]);

  // 重新获取数据（忽略缓存）
  const refetch = useCallback((options) => {
    if (cacheKey) {
      clearCache(cacheKey);
    }
    return fetchData(options);
  }, [fetchData, cacheKey]);

  // 重置状态
  const reset = useCallback(() => {
    setData(config.initialData);
    setLoading(!config.manual);
    setError(null);
    setStatus('idle');
  }, [config.initialData, config.manual]);

  return {
    data,
    loading,
    error,
    status,
    trigger,
    refetch,
    reset,
    isIdle: status === 'idle',
    isLoading: status === 'loading',
    isSuccess: status === 'success',
    isError: status === 'error',
  };
}

/**
 * 便捷钩子：使用API对象的方法
 */
export function useApiMethod(method, ...args) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(async (...executeArgs) => {
    setLoading(true);
    setError(null);
    try {
      const result = await method(...executeArgs);
      setData(result);
      return result;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [method]);

  // 如果提供了参数，自动执行
  useEffect(() => {
    if (args.length > 0) {
      execute(...args);
    }
  }, [execute, args]);

  return { data, loading, error, execute };
}

/**
 * 认证钩子
 */
export function useAuth() {
  const login = useApiMethod(api.auth.login);
  const register = useApiMethod(api.auth.register);
  const logout = useApiMethod(api.auth.logout);
  const getCurrentUser = useApiMethod(api.auth.getCurrentUser);

  return {
    login: login.execute,
    register: register.execute,
    logout: logout.execute,
    getCurrentUser: getCurrentUser.execute,
    loginState: login,
    registerState: register,
    logoutState: logout,
    currentUserState: getCurrentUser,
  };
}

/**
 * 用户管理钩子
 */
export function useUsers() {
  const list = useApiMethod(api.users.list);
  const get = useApiMethod(api.users.get);
  const create = useApiMethod(api.users.create);
  const update = useApiMethod(api.users.update);
  const remove = useApiMethod(api.users.delete);

  return {
    list: list.execute,
    get: get.execute,
    create: create.execute,
    update: update.execute,
    remove: remove.execute,
    listState: list,
    getState: get,
    createState: create,
    updateState: update,
    removeState: remove,
  };
}

/**
 * 知识图谱钩子
 */
export function useKnowledgeGraph() {
  const getGraph = useApi(api.knowledgeGraph.getGraph);
  const getStats = useApi(api.knowledgeGraph.getStats);
  const search = useApiMethod(api.knowledgeGraph.search);
  const getNodeDetails = useApiMethod(api.knowledgeGraph.getNodeDetails);
  const getEdgeDetails = useApiMethod(api.knowledgeGraph.getEdgeDetails);

  return {
    graph: getGraph,
    stats: getStats,
    search: search.execute,
    getNodeDetails: getNodeDetails.execute,
    getEdgeDetails: getEdgeDetails.execute,
    searchState: search,
    nodeDetailsState: getNodeDetails,
    edgeDetailsState: getEdgeDetails,
  };
}

/**
 * 报告管理钩子
 */
export function useReports() {
  const list = useApi(api.reports.list);
  const generate = useApiMethod(api.reports.generate);
  const download = useApiMethod(api.reports.download);
  const remove = useApiMethod(api.reports.delete);

  return {
    list,
    generate: generate.execute,
    download: download.execute,
    remove: remove.execute,
    generateState: generate,
    downloadState: download,
    removeState: remove,
  };
}

/**
 * 实时数据钩子（WebSocket）
 */
export function useRealtime(endpoint, options = {}) {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const wsRef = useRef();

  useEffect(() => {
    const wsUrl = endpoint.startsWith('ws') ? endpoint : `ws://localhost:8000${endpoint}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnected(true);
      setError(null);
      if (options.onConnect) options.onConnect();
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        setData(message);
        if (options.onMessage) options.onMessage(message);
      } catch (err) {
        console.error('WebSocket消息解析失败:', err);
      }
    };

    ws.onerror = (err) => {
      setError(err);
      if (options.onError) options.onError(err);
    };

    ws.onclose = () => {
      setConnected(false);
      if (options.onDisconnect) options.onDisconnect();
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [endpoint, options]);

  const send = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }
  }, []);

  return { data, connected, error, send, disconnect };
}

// 导出缓存工具
export { clearCache };

// 默认导出主钩子
export default useApi;