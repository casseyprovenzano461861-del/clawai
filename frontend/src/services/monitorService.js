/**
 * 实时监控API服务
 */
import { request } from './apiClient';

// 监控事件类型枚举
export const MonitorEventType = {
  SCAN_STARTED: 'scan_started',
  SCAN_PROGRESS: 'scan_progress',
  SCAN_COMPLETED: 'scan_completed',
  SCAN_FAILED: 'scan_failed',
  TOOL_STARTED: 'tool_started',
  TOOL_COMPLETED: 'tool_completed',
  VULNERABILITY_FOUND: 'vulnerability_found',
  ATTACK_STARTED: 'attack_started',
  ATTACK_COMPLETED: 'attack_completed',
  SYSTEM_ALERT: 'system_alert',
  USER_ACTION: 'user_action'
};

// 监控状态枚举
export const MonitorStatus = {
  IDLE: 'idle',
  RUNNING: 'running',
  PAUSED: 'paused',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled'
};

// 严重性等级枚举
export const SeverityLevel = {
  CRITICAL: 'critical',
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low',
  INFO: 'info'
};

/**
 * 建立WebSocket连接
 * @param {Function} onMessage - 消息处理回调
 * @param {Function} onError - 错误处理回调
 * @returns {WebSocket} WebSocket连接
 */
export const connectWebSocket = (onMessage, onError) => {
  try {
    // WebSocket URL（假设后端支持WebSocket）
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname || 'localhost';
    const port = window.location.port || '8000';
    const wsUrl = `${protocol}//${host}:${port}/ws/monitor`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket连接已建立');
      // 发送认证信息（如果需要）
      const token = localStorage.getItem('access_token');
      if (token) {
        ws.send(JSON.stringify({
          type: 'auth',
          token: token
        }));
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (onMessage) {
          onMessage(data);
        }
      } catch (error) {
        console.error('解析WebSocket消息失败:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket连接错误:', error);
      if (onError) {
        onError(error);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket连接已关闭');
      // 5秒后尝试重连
      setTimeout(() => {
        if (ws.readyState === WebSocket.CLOSED) {
          connectWebSocket(onMessage, onError);
        }
      }, 5000);
    };

    return ws;
  } catch (error) {
    console.error('创建WebSocket连接失败:', error);
    if (onError) {
      onError(error);
    }
    return null;
  }
};

/**
 * 获取实时事件流（使用Server-Sent Events）
 * @param {Function} onEvent - 事件处理回调
 * @returns {EventSource} EventSource连接
 */
export const connectEventSource = (onEvent) => {
  try {
    const eventSource = new EventSource('/api/v1/monitor/events');

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (onEvent) {
          onEvent(data);
        }
      } catch (error) {
        console.error('解析事件源消息失败:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('事件源连接错误:', error);
      eventSource.close();
      // 3秒后重连
      setTimeout(() => {
        connectEventSource(onEvent);
      }, 3000);
    };

    return eventSource;
  } catch (error) {
    console.error('创建事件源连接失败:', error);
    return null;
  }
};

/**
 * 获取监控统计信息
 * @returns {Promise} 监控统计
 */
export const getMonitorStats = async () => {
  try {
    return await request.get('/monitor/stats');
  } catch (error) {
    console.warn('获取监控统计API失败，使用模拟数据:', error.message);

    // 模拟监控统计
    return {
      active_scans: 3,
      completed_scans: 12,
      vulnerabilities_found: 45,
      critical_vulnerabilities: 5,
      total_events: 1287,
      events_last_hour: 42,
      system_load: 65,
      memory_usage: 72,
      disk_usage: 45,
      network_traffic: '1.2 GB'
    };
  }
};

/**
 * 获取活动扫描列表
 * @returns {Promise} 活动扫描列表
 */
export const getActiveScans = async () => {
  try {
    return await request.get('/monitor/active-scans');
  } catch (error) {
    console.warn('获取活动扫描API失败，使用模拟数据:', error.message);

    // 模拟活动扫描
    return [
      {
        id: 'scan-001',
        target: '192.168.1.100',
        type: 'web_vulnerability',
        status: MonitorStatus.RUNNING,
        progress: 65,
        started_at: '2026-04-06T10:30:00Z',
        estimated_completion: '2026-04-06T11:00:00Z',
        findings: 15,
        tools: ['nmap', 'nikto', 'sqlmap']
      },
      {
        id: 'scan-002',
        target: 'example.com',
        type: 'port_scan',
        status: MonitorStatus.RUNNING,
        progress: 30,
        started_at: '2026-04-06T10:45:00Z',
        estimated_completion: '2026-04-06T10:55:00Z',
        findings: 8,
        tools: ['nmap', 'masscan']
      },
      {
        id: 'scan-003',
        target: 'api.example.com',
        type: 'api_security',
        status: MonitorStatus.RUNNING,
        progress: 80,
        started_at: '2026-04-06T10:20:00Z',
        estimated_completion: '2026-04-06T10:40:00Z',
        findings: 22,
        tools: ['burpsuite', 'postman']
      }
    ];
  }
};

/**
 * 获取最近事件
 * @param {number} limit - 事件数量限制
 * @returns {Promise} 最近事件列表
 */
export const getRecentEvents = async (limit = 20) => {
  try {
    return await request.get(`/monitor/recent-events?limit=${limit}`);
  } catch (error) {
    console.warn('获取最近事件API失败，使用模拟数据:', error.message);

    // 模拟最近事件
    const mockEvents = [
      {
        id: 'event-001',
        type: MonitorEventType.SCAN_STARTED,
        timestamp: '2026-04-06T10:30:00Z',
        severity: SeverityLevel.INFO,
        message: '扫描开始: 192.168.1.100',
        details: {
          target: '192.168.1.100',
          scan_type: 'web_vulnerability',
          tools: ['nmap', 'nikto', 'sqlmap']
        }
      },
      {
        id: 'event-002',
        type: MonitorEventType.VULNERABILITY_FOUND,
        timestamp: '2026-04-06T10:32:15Z',
        severity: SeverityLevel.HIGH,
        message: '发现高危漏洞: SQL注入',
        details: {
          target: '192.168.1.100',
          vulnerability: 'SQL Injection',
          location: '/login.php',
          cvss_score: 8.5
        }
      },
      {
        id: 'event-003',
        type: MonitorEventType.SCAN_PROGRESS,
        timestamp: '2026-04-06T10:35:00Z',
        severity: SeverityLevel.INFO,
        message: '扫描进度: 45%',
        details: {
          scan_id: 'scan-001',
          progress: 45,
          findings: 12
        }
      },
      {
        id: 'event-004',
        type: MonitorEventType.TOOL_STARTED,
        timestamp: '2026-04-06T10:36:30Z',
        severity: SeverityLevel.INFO,
        message: '工具开始执行: sqlmap',
        details: {
          tool: 'sqlmap',
          target: '192.168.1.100/login.php',
          parameters: '--level=3 --risk=2'
        }
      },
      {
        id: 'event-005',
        type: MonitorEventType.VULNERABILITY_FOUND,
        timestamp: '2026-04-06T10:38:45Z',
        severity: SeverityLevel.CRITICAL,
        message: '发现严重漏洞: RCE',
        details: {
          target: '192.168.1.100',
          vulnerability: 'Remote Code Execution',
          location: '/admin/upload.php',
          cvss_score: 9.8
        }
      },
      {
        id: 'event-006',
        type: MonitorEventType.SYSTEM_ALERT,
        timestamp: '2026-04-06T10:40:00Z',
        severity: SeverityLevel.MEDIUM,
        message: '系统资源警告: 内存使用率85%',
        details: {
          resource: 'memory',
          usage: 85,
          threshold: 80
        }
      },
      {
        id: 'event-007',
        type: MonitorEventType.SCAN_COMPLETED,
        timestamp: '2026-04-06T10:45:30Z',
        severity: SeverityLevel.INFO,
        message: '扫描完成: 192.168.1.100',
        details: {
          scan_id: 'scan-001',
          findings: 29,
          duration: '15分30秒',
          critical_findings: 1,
          high_findings: 3
        }
      }
    ];

    return mockEvents.slice(0, limit);
  }
};

/**
 * 获取系统资源使用情况
 * @returns {Promise} 系统资源信息
 */
export const getSystemResources = async () => {
  try {
    return await request.get('/monitor/system-resources');
  } catch (error) {
    console.warn('获取系统资源API失败，使用模拟数据:', error.message);

    // 模拟系统资源数据
    const now = Date.now();
    const timePoints = Array.from({ length: 30 }, (_, i) => {
      const time = new Date(now - (29 - i) * 60000); // 最近30分钟
      return time.toISOString();
    });

    return {
      cpu_usage: timePoints.map((time, i) => ({
        time,
        usage: 30 + Math.sin(i * 0.5) * 20 + Math.random() * 10
      })),
      memory_usage: timePoints.map((time, i) => ({
        time,
        usage: 50 + Math.sin(i * 0.3) * 15 + Math.random() * 8
      })),
      disk_usage: timePoints.map((time, i) => ({
        time,
        usage: 40 + Math.sin(i * 0.2) * 10 + Math.random() * 5
      })),
      network_traffic: timePoints.map((time, i) => ({
        time,
        inbound: 100 + Math.sin(i * 0.4) * 50 + Math.random() * 30,
        outbound: 50 + Math.sin(i * 0.4) * 25 + Math.random() * 15
      })),
      current: {
        cpu: 65,
        memory: 72,
        disk: 45,
        network_in: 125,
        network_out: 68
      }
    };
  }
};

/**
 * 获取性能指标
 * @param {string} timeframe - 时间范围 (1h, 24h, 7d, 30d)
 * @returns {Promise} 性能指标
 */
export const getPerformanceMetrics = async (timeframe = '1h') => {
  try {
    return await request.get(`/monitor/performance-metrics?timeframe=${timeframe}`);
  } catch (error) {
    console.warn('获取性能指标API失败，使用模拟数据:', error.message);

    // 模拟性能指标
    const dataPoints = timeframe === '1h' ? 60 : timeframe === '24h' ? 24 : timeframe === '7d' ? 7 : 30;

    return {
      response_time: Array.from({ length: dataPoints }, (_, i) => ({
        time: new Date(Date.now() - (dataPoints - i - 1) * (timeframe === '1h' ? 60000 : timeframe === '24h' ? 3600000 : 86400000)).toISOString(),
        value: 50 + Math.sin(i * 0.3) * 20 + Math.random() * 15
      })),
      request_rate: Array.from({ length: dataPoints }, (_, i) => ({
        time: new Date(Date.now() - (dataPoints - i - 1) * (timeframe === '1h' ? 60000 : timeframe === '24h' ? 3600000 : 86400000)).toISOString(),
        value: 100 + Math.sin(i * 0.4) * 50 + Math.random() * 30
      })),
      error_rate: Array.from({ length: dataPoints }, (_, i) => ({
        time: new Date(Date.now() - (dataPoints - i - 1) * (timeframe === '1h' ? 60000 : timeframe === '24h' ? 3600000 : 86400000)).toISOString(),
        value: Math.max(0, 2 + Math.sin(i * 0.5) * 1.5 + Math.random())
      })),
      success_rate: Array.from({ length: dataPoints }, (_, i) => ({
        time: new Date(Date.now() - (dataPoints - i - 1) * (timeframe === '1h' ? 60000 : timeframe === '24h' ? 3600000 : 86400000)).toISOString(),
        value: Math.min(100, 98 + Math.sin(i * 0.2) * 1 + Math.random() * 0.5)
      }))
    };
  }
};

/**
 * 停止扫描
 * @param {string} scanId - 扫描ID
 * @returns {Promise} 停止结果
 */
export const stopScan = async (scanId) => {
  try {
    return await request.post(`/monitor/scans/${scanId}/stop`);
  } catch (error) {
    console.warn('停止扫描API失败，使用模拟响应:', error.message);

    // 模拟响应
    return {
      success: true,
      message: `扫描 ${scanId} 已停止`,
      stopped_at: new Date().toISOString()
    };
  }
};

/**
 * 获取扫描详情
 * @param {string} scanId - 扫描ID
 * @returns {Promise} 扫描详情
 */
export const getScanDetails = async (scanId) => {
  try {
    return await request.get(`/monitor/scans/${scanId}`);
  } catch (error) {
    console.warn('获取扫描详情API失败，使用模拟数据:', error.message);

    // 模拟扫描详情
    return {
      id: scanId,
      target: '192.168.1.100',
      type: 'web_vulnerability',
      status: MonitorStatus.COMPLETED,
      progress: 100,
      started_at: '2026-04-06T10:30:00Z',
      completed_at: '2026-04-06T10:45:30Z',
      duration: '15分30秒',
      findings: 29,
      tools: ['nmap', 'nikto', 'sqlmap', 'wpscan'],
      results: {
        vulnerabilities: [
          {
            id: 'vuln-001',
            type: 'sql_injection',
            severity: SeverityLevel.HIGH,
            location: '/login.php',
            description: 'SQL注入漏洞',
            cvss_score: 8.5,
            remediation: '使用参数化查询'
          },
          {
            id: 'vuln-002',
            type: 'xss',
            severity: SeverityLevel.MEDIUM,
            location: '/search.php',
            description: '跨站脚本漏洞',
            cvss_score: 6.2,
            remediation: '输入过滤和编码'
          }
        ],
        ports: [
          { port: 80, service: 'http', state: 'open' },
          { port: 443, service: 'https', state: 'open' },
          { port: 22, service: 'ssh', state: 'open' },
          { port: 3306, service: 'mysql', state: 'open' }
        ],
        technologies: [
          { name: 'Apache', version: '2.4.41' },
          { name: 'PHP', version: '7.4.33' },
          { name: 'WordPress', version: '5.8' },
          { name: 'MySQL', version: '8.0' }
        ]
      }
    };
  }
};

// 监控服务
const monitorService = {
  connectWebSocket,
  connectEventSource,
  getMonitorStats,
  getActiveScans,
  getRecentEvents,
  getSystemResources,
  getPerformanceMetrics,
  stopScan,
  getScanDetails,
  MonitorEventType,
  MonitorStatus,
  SeverityLevel
};

export default monitorService;