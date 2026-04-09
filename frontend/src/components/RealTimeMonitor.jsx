import React, { useState, useEffect, useRef } from 'react';
import {
  Activity, Clock, Play, Pause, RefreshCw, Download,
  BarChart3, TrendingUp, Zap, CheckCircle, AlertCircle,
  Server, Network, Cpu, Database, Globe, Shield,
  ChevronRight, ChevronDown, Maximize2, Minimize2,
  MessageSquare, FileText, Users, Settings
} from 'lucide-react';

// 导入设计系统组件
import Card from './design-system/Card';
import Button from './design-system/Button';
import Badge from './design-system/Badge';
import Alert from './design-system/Alert';
import { useScan } from '../context/ScanContext';

// 导入监控服务
import monitorService, {
  MonitorEventType,
  MonitorStatus,
  SeverityLevel
} from '../services/monitorService';

const RealTimeMonitor = () => {
  const { activeTarget, scanStatus } = useScan();
  const [isConnected, setIsConnected] = useState(false);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [executionTime, setExecutionTime] = useState(0);
  const [logEntries, setLogEntries] = useState([]);
  const [activeScans, setActiveScans] = useState([]);
  const [systemMetrics, setSystemMetrics] = useState({});
  const [expandedLogs, setExpandedLogs] = useState(false);
  const [fullScreen, setFullScreen] = useState(false);
  
  const timerRef = useRef(null);
  const wsRef = useRef(null);
  const logContainerRef = useRef(null);

  // 模拟扫描步骤
  const scanSteps = [
    { id: 1, name: '目标验证', description: '验证目标可达性和格式', duration: 2, tool: 'validator' },
    { id: 2, name: '端口扫描', description: '扫描开放端口和服务', duration: 8, tool: 'nmap' },
    { id: 3, name: '服务识别', description: '识别运行的服务和版本', duration: 5, tool: 'whatweb' },
    { id: 4, name: '漏洞扫描', description: '扫描已知漏洞', duration: 12, tool: 'nuclei' },
    { id: 5, name: '结果分析', description: '分析扫描结果和风险评估', duration: 6, tool: 'analyzer' },
    { id: 6, name: '报告生成', description: '生成安全评估报告', duration: 4, tool: 'reporter' }
  ];

  // 获取监控数据
  const fetchMonitorData = async () => {
    try {
      // 并行获取数据
      const [stats, activeScansData, recentEvents, systemResources] = await Promise.all([
        monitorService.getMonitorStats(),
        monitorService.getActiveScans(),
        monitorService.getRecentEvents(10),
        monitorService.getSystemResources()
      ]);

      // 更新系统指标
      setSystemMetrics({
        cpuUsage: stats.system_load || systemResources?.current?.cpu || 0,
        memoryUsage: stats.memory_usage || systemResources?.current?.memory || 0,
        diskUsage: stats.disk_usage || systemResources?.current?.disk || 0,
        activeConnections: stats.active_scans || 0,
        networkIn: systemResources?.current?.network_in || 0,
        networkOut: systemResources?.current?.network_out || 0,
        errorRate: 0.5 // 暂时模拟
      });

      // 更新活动扫描
      setActiveScans(activeScansData.map(scan => ({
        id: scan.id,
        target: scan.target,
        progress: scan.progress,
        status: scan.status,
        startTime: formatTime(scan.started_at),
        estimatedEnd: formatTime(scan.estimated_completion)
      })));

      // 更新日志
      setLogEntries(recentEvents.map(event => ({
        id: event.id,
        timestamp: formatTime(event.timestamp, true),
        level: mapSeverityToLevel(event.severity),
        message: event.message,
        source: event.type
      })));
    } catch (error) {
      console.error('获取监控数据失败:', error);
      // 降级方案：使用模拟数据
      setSystemMetrics({
        cpuUsage: 45,
        memoryUsage: 62,
        diskUsage: 78,
        activeConnections: 3,
        networkIn: 1250,
        networkOut: 850,
        errorRate: 0.5
      });
      setActiveScans([
        { id: 'scan-001', target: '192.168.1.100', progress: 65, status: 'running', startTime: '11:30:15', estimatedEnd: '11:42:30' },
        { id: 'scan-002', target: 'example.com', progress: 30, status: 'running', startTime: '11:35:20', estimatedEnd: '11:50:45' },
        { id: 'scan-003', target: 'test.local', progress: 100, status: 'completed', startTime: '11:20:10', estimatedEnd: '11:32:05' }
      ]);
      setLogEntries([
        { id: 1, timestamp: '11:40:15', level: 'info', message: 'WebSocket连接已建立', source: 'connection' },
        { id: 2, timestamp: '11:40:20', level: 'info', message: '开始扫描目标: 192.168.1.100', source: 'scanner' },
        { id: 3, timestamp: '11:40:25', level: 'warning', message: '检测到防火墙，调整扫描策略', source: 'nmap' },
        { id: 4, timestamp: '11:40:30', level: 'info', message: '发现开放端口: 80, 443, 22', source: 'nmap' },
        { id: 5, timestamp: '11:40:35', level: 'success', message: '服务识别完成: Apache 2.4', source: 'whatweb' },
        { id: 6, timestamp: '11:40:40', level: 'error', message: '连接超时，重试中...', source: 'nuclei' },
        { id: 7, timestamp: '11:40:45', level: 'info', message: '重试成功，继续漏洞扫描', source: 'nuclei' }
      ]);
    }
  };

  // 辅助函数：解析网络流量字符串
  const parseNetworkTraffic = (traffic) => {
    const match = traffic.match(/^([\d.]+)\s*(B|KB|MB|GB)$/);
    if (match) {
      const value = parseFloat(match[1]);
      const unit = match[2];
      return { value, unit };
    }
    return { value: 0, unit: 'B' };
  };

  // 辅助函数：格式化时间
  const formatTime = (timestamp, includeSeconds = false) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    if (includeSeconds) {
      const seconds = date.getSeconds().toString().padStart(2, '0');
      return `${hours}:${minutes}:${seconds}`;
    }
    return `${hours}:${minutes}`;
  };

  // 辅助函数：将严重性映射到日志级别
  const mapSeverityToLevel = (severity) => {
    switch (severity) {
      case SeverityLevel.CRITICAL:
      case SeverityLevel.HIGH:
        return 'error';
      case SeverityLevel.MEDIUM:
        return 'warning';
      case SeverityLevel.LOW:
        return 'info';
      default:
        return 'info';
    }
  };

  useEffect(() => {
    // 初始化数据
    fetchMonitorData();

    // 建立WebSocket连接
    const ws = monitorService.connectWebSocket(
      (data) => {
        // 处理实时消息
        handleWebSocketMessage(data);
      },
      (error) => {
        console.error('WebSocket连接错误:', error);
        setIsConnected(false);
      }
    );
    wsRef.current = ws;

    // 添加连接状态监听
    if (ws) {
      ws.addEventListener('open', () => {
        console.log('WebSocket连接已建立');
        setIsConnected(true);
      });
      ws.addEventListener('close', () => {
        console.log('WebSocket连接已关闭');
        setIsConnected(false);
      });
    }

    // 设置定时刷新数据
    const refreshInterval = setInterval(() => {
      fetchMonitorData();
    }, 5000); // 每5秒刷新一次

    // 清理定时器和WebSocket连接
    return () => {
      clearInterval(refreshInterval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // 滚动到最新日志
  useEffect(() => {
    if (logContainerRef.current && expandedLogs) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logEntries, expandedLogs]);

  // 处理WebSocket消息
  const handleWebSocketMessage = (data) => {
    console.log('收到WebSocket消息:', data);

    // 根据消息类型处理
    switch (data.type) {
      case MonitorEventType.SCAN_STARTED:
      case MonitorEventType.SCAN_PROGRESS:
      case MonitorEventType.SCAN_COMPLETED:
        // 更新扫描进度
        if (data.details?.progress !== undefined) {
          setScanProgress(data.details.progress);
        }
        if (data.details?.scan_id) {
          // 更新活动扫描列表
          fetchMonitorData(); // 刷新数据
        }
        break;

      case MonitorEventType.VULNERABILITY_FOUND:
      case MonitorEventType.TOOL_STARTED:
      case MonitorEventType.TOOL_COMPLETED:
      case MonitorEventType.ATTACK_STARTED:
      case MonitorEventType.ATTACK_COMPLETED:
      case MonitorEventType.SYSTEM_ALERT:
      case MonitorEventType.USER_ACTION:
        // 添加新日志
        const newLog = {
          id: `ws_${Date.now()}`,
          timestamp: formatTime(data.timestamp || new Date().toISOString(), true),
          level: mapSeverityToLevel(data.severity || SeverityLevel.INFO),
          message: data.message || '收到监控事件',
          source: data.type
        };
        setLogEntries(prev => [...prev.slice(-20), newLog]); // 保持最近20条日志
        break;
    }

    // 实时更新系统指标（如果消息中包含）
    if (data.metrics) {
      setSystemMetrics(prev => ({
        ...prev,
        ...data.metrics
      }));
    }
  };

  const startMonitoring = () => {
    if (!isConnected) {
      alert('请先建立WebSocket连接');
      return;
    }
    setIsMonitoring(true);
    setScanProgress(0);
    setExecutionTime(0);
    setCurrentStep(scanSteps[0].name);
    
    // 添加开始日志
    const startLog = {
      id: logEntries.length + 1,
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      level: 'info',
      message: '开始实时监控扫描进度',
      source: 'monitor'
    };
    setLogEntries(prev => [...prev, startLog]);
  };

  const stopMonitoring = () => {
    setIsMonitoring(false);
    
    // 添加停止日志
    const stopLog = {
      id: logEntries.length + 1,
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      level: 'info',
      message: '停止实时监控',
      source: 'monitor'
    };
    setLogEntries(prev => [...prev, stopLog]);
  };

  const resetMonitoring = () => {
    setIsMonitoring(false);
    setScanProgress(0);
    setExecutionTime(0);
    setCurrentStep('');
    setLogEntries([]);
    // 重新获取数据
    fetchMonitorData();
  };

  const exportLogs = () => {
    const logText = logEntries.map(log => 
      `[${log.timestamp}] [${log.level.toUpperCase()}] [${log.source}] ${log.message}`
    ).join('\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `clawai-monitor-logs-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getLogLevelColor = (level) => {
    switch (level) {
      case 'error': return 'text-red-500 bg-red-500/100/10';
      case 'warning': return 'text-yellow-500 bg-yellow-500/100/10';
      case 'success': return 'text-green-500 bg-green-500/100/10';
      case 'info': 
      default: return 'text-blue-500 bg-blue-500/100/10';
    }
  };

  const getLogLevelIcon = (level) => {
    switch (level) {
      case 'error': return <AlertCircle className="w-4 h-4" />;
      case 'warning': return <AlertCircle className="w-4 h-4" />;
      case 'success': return <CheckCircle className="w-4 h-4" />;
      case 'info': 
      default: return <MessageSquare className="w-4 h-4" />;
    }
  };

  const MetricCard = ({ icon: Icon, title, value, unit, color = 'blue', change }) => {
    const colorClasses = {
      blue: 'text-blue-500',
      green: 'text-green-500',
      red: 'text-red-500',
      purple: 'text-purple-500',
      orange: 'text-orange-500'
    };

    return (
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div className={`p-2 rounded-lg ${colorClasses[color]}/10`}>
            <Icon className={`w-5 h-5 ${colorClasses[color]}`} />
          </div>
          {change && (
            <Badge variant={change > 0 ? 'danger' : 'success'} size="sm">
              {change > 0 ? '+' : ''}{change}%
            </Badge>
          )}
        </div>
        <div className="text-2xl font-bold mb-1">{value}{unit}</div>
        <div className="text-sm opacity-70">{title}</div>
      </Card>
    );
  };

  const ProgressStep = ({ step, index, isActive, isCompleted }) => {
    return (
      <div className="flex items-center">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
          isCompleted ? 'bg-green-500/100 text-white' :
          isActive ? 'bg-blue-500/100 text-white' :
          'bg-[#111827] text-gray-400'
        }`}>
          {isCompleted ? <CheckCircle className="w-5 h-5" /> : step.id}
        </div>
        <div className="ml-4">
          <div className={`font-medium ${isActive ? 'text-blue-400' : 'text-gray-400'}`}>
            {step.name}
          </div>
          <div className="text-sm opacity-70">{step.description}</div>
          <div className="text-xs opacity-50 mt-1">工具: {step.tool} | 预计: {step.duration}s</div>
        </div>
      </div>
    );
  };

  return (
    <div className={`${fullScreen ? 'fixed inset-0 z-50 bg-[#060910]' : ''}`}>
      <div className={`${fullScreen ? 'h-screen overflow-auto' : ''}`}>

        {/* ScanContext 状态横幅 */}
        {activeTarget && (
          <div className={`mb-4 px-4 py-2.5 rounded-xl flex items-center gap-3 text-sm font-mono border ${
            scanStatus === 'scanning'
              ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300'
              : scanStatus === 'done'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : scanStatus === 'error'
              ? 'bg-red-500/10 border-red-500/30 text-red-300'
              : 'bg-white/5 border-white/10 text-gray-400'
          }`}>
            <span className={`w-2 h-2 rounded-full shrink-0 ${
              scanStatus === 'scanning' ? 'bg-cyan-400 animate-pulse' :
              scanStatus === 'done' ? 'bg-emerald-400' :
              scanStatus === 'error' ? 'bg-red-400' : 'bg-gray-600'
            }`} />
            <span className="flex-1 truncate">
              {scanStatus === 'scanning' ? `正在扫描: ${activeTarget}` :
               scanStatus === 'done'     ? `最近扫描: ${activeTarget}` :
               scanStatus === 'error'    ? `扫描失败: ${activeTarget}` :
               `目标: ${activeTarget}`}
            </span>
          </div>
        )}
        {/* 控制栏 */}
        <Card className="mb-6">
          <div className="flex flex-col md:flex-row items-center justify-between p-4">
            <div className="flex items-center space-x-4 mb-4 md:mb-0">
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2 ${isConnected ? 'bg-green-500/100' : 'bg-red-500/100'}`}></div>
                <span className="text-sm">
                  {isConnected ? 'WebSocket已连接' : '连接中...'}
                </span>
              </div>
              
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2 ${isMonitoring ? 'bg-green-500/100 animate-pulse' : 'bg-[#111827]0'}`}></div>
                <span className="text-sm">
                  {isMonitoring ? '监控进行中' : '监控已停止'}
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant={isMonitoring ? 'danger' : 'primary'}
                onClick={isMonitoring ? stopMonitoring : startMonitoring}
                disabled={!isConnected}
                className="flex items-center"
              >
                {isMonitoring ? (
                  <>
                    <Pause className="w-4 h-4 mr-2" />
                    停止监控
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    开始监控
                  </>
                )}
              </Button>

              <Button
                variant="outline"
                onClick={resetMonitoring}
                className="flex items-center"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                重置
              </Button>

              <Button
                variant="ghost"
                onClick={exportLogs}
                className="flex items-center"
              >
                <Download className="w-4 h-4 mr-2" />
                导出日志
              </Button>

              <Button
                variant="ghost"
                onClick={() => setFullScreen(!fullScreen)}
                className="flex items-center"
              >
                {fullScreen ? (
                  <Minimize2 className="w-4 h-4" />
                ) : (
                  <Maximize2 className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧：进度监控和步骤 */}
          <div className="lg:col-span-2 space-y-6">
            {/* 进度条 */}
            <Card>
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <Activity className="w-6 h-6 text-blue-400 mr-2" />
                  <h2 className="text-xl font-semibold">扫描进度监控</h2>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-sm">
                    <span className="opacity-70">当前步骤: </span>
                    <span className="font-medium text-blue-400">{currentStep || '等待开始'}</span>
                  </div>
                  <div className="text-sm">
                    <span className="opacity-70">执行时间: </span>
                    <span className="font-medium">{executionTime}s</span>
                  </div>
                </div>
              </div>

              {/* 进度条 */}
              <div className="mb-6">
                <div className="flex justify-between text-sm mb-2">
                  <span>进度</span>
                  <span className="font-bold">{scanProgress}%</span>
                </div>
                <div className="w-full h-4 bg-[#111827] rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-blue-500 to-green-500 transition-all duration-300"
                    style={{ width: `${scanProgress}%` }}
                  ></div>
                </div>
              </div>

              {/* 扫描步骤 */}
              <div className="space-y-4">
                <h3 className="font-semibold mb-2">扫描步骤</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {scanSteps.map((step, index) => {
                    const stepProgress = (index + 1) / scanSteps.length * 100;
                    const isActive = scanProgress >= (index / scanSteps.length * 100) && scanProgress < stepProgress;
                    const isCompleted = scanProgress >= stepProgress;
                    
                    return (
                      <ProgressStep
                        key={step.id}
                        step={step}
                        index={index}
                        isActive={isActive}
                        isCompleted={isCompleted}
                      />
                    );
                  })}
                </div>
              </div>
            </Card>

            {/* 活动扫描 */}
            <Card>
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <Zap className="w-6 h-6 text-yellow-400 mr-2" />
                  <h2 className="text-xl font-semibold">活动扫描</h2>
                </div>
                <Badge variant="info" size="sm">
                  {activeScans.filter(s => s.status === 'running').length} 个进行中
                </Badge>
              </div>

              <div className="space-y-4">
                {activeScans.map((scan) => (
                  <div key={scan.id} className="p-4 rounded-lg bg-[#0a0e17]/60">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center">
                        <div className={`w-3 h-3 rounded-full mr-2 ${
                          scan.status === 'running' ? 'bg-green-500/100 animate-pulse' :
                          scan.status === 'completed' ? 'bg-blue-500/100' : 'bg-[#111827]0'
                        }`}></div>
                        <div>
                          <div className="font-medium">{scan.target}</div>
                          <div className="text-sm opacity-70">ID: {scan.id}</div>
                        </div>
                      </div>
                      <Badge variant={scan.status === 'running' ? 'success' : 'info'} size="sm">
                        {scan.status === 'running' ? '进行中' : '已完成'}
                      </Badge>
                    </div>

                    <div className="mb-2">
                      <div className="flex justify-between text-sm mb-1">
                        <span>进度</span>
                        <span className="font-bold">{scan.progress}%</span>
                      </div>
                      <div className="w-full h-2 bg-[#111827] rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${
                            scan.status === 'running' ? 'bg-gradient-to-r from-yellow-500 to-green-500' : 'bg-blue-500/100'
                          }`}
                          style={{ width: `${scan.progress}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="opacity-70">开始时间: </span>
                        <span>{scan.startTime}</span>
                      </div>
                      <div>
                        <span className="opacity-70">预计结束: </span>
                        <span>{scan.estimatedEnd}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* 实时日志 */}
            <Card>
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <FileText className="w-6 h-6 text-purple-400 mr-2" />
                  <h2 className="text-xl font-semibold">实时日志</h2>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setExpandedLogs(!expandedLogs)}
                    className="flex items-center"
                  >
                    {expandedLogs ? (
                      <>
                        <ChevronDown className="w-4 h-4 mr-1" />
                        收起
                      </>
                    ) : (
                      <>
                        <ChevronRight className="w-4 h-4 mr-1" />
                        展开
                      </>
                    )}
                  </Button>
                  <Badge variant="info" size="sm">
                    {logEntries.length} 条
                  </Badge>
                </div>
              </div>

              <div 
                ref={logContainerRef}
                className={`overflow-y-auto transition-all duration-300 ${
                  expandedLogs ? 'max-h-96' : 'max-h-48'
                }`}
              >
                <div className="space-y-2">
                  {logEntries.map((log) => (
                    <div
                      key={log.id}
                      className={`p-3 rounded-lg flex items-start ${getLogLevelColor(log.level)}`}
                    >
                      <div className="mr-3 mt-0.5">
                        {getLogLevelIcon(log.level)}
                      </div>
                      <div className="flex-1">
                        <div className="flex justify-between mb-1">
                          <span className="font-medium text-sm">[{log.source}]</span>
                          <span className="text-xs opacity-70">{log.timestamp}</span>
                        </div>
                        <div className="text-sm">{log.message}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {!expandedLogs && logEntries.length > 3 && (
                <div className="mt-4 text-center text-sm opacity-70">
                  还有 {logEntries.length - 3} 条日志未显示，点击展开查看全部
                </div>
              )}
            </Card>
          </div>

          {/* 右侧：系统指标 */}
          <div className="space-y-6">
            {/* 系统指标 */}
            <Card>
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <BarChart3 className="w-6 h-6 text-green-400 mr-2" />
                  <h2 className="text-xl font-semibold">系统指标</h2>
                </div>
                <Badge variant="success" size="sm">
                  实时更新
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <MetricCard
                  icon={Cpu}
                  title="CPU使用率"
                  value={systemMetrics.cpuUsage?.toFixed(1) || '0.0'}
                  unit="%"
                  color="red"
                  change={2.5}
                />
                <MetricCard
                  icon={Database}
                  title="内存使用"
                  value={systemMetrics.memoryUsage?.toFixed(1) || '0.0'}
                  unit="%"
                  color="purple"
                  change={1.2}
                />
                <MetricCard
                  icon={Network}
                  title="网络流入"
                  value={(systemMetrics.networkIn / 1000).toFixed(1)}
                  unit=" KB/s"
                  color="blue"
                  change={-0.8}
                />
                <MetricCard
                  icon={Network}
                  title="网络流出"
                  value={(systemMetrics.networkOut / 1000).toFixed(1)}
                  unit=" KB/s"
                  color="green"
                  change={1.5}
                />
                <MetricCard
                  icon={Server}
                  title="磁盘使用"
                  value={systemMetrics.diskUsage?.toFixed(1) || '0.0'}
                  unit="%"
                  color="orange"
                  change={0.3}
                />
                <MetricCard
                  icon={Users}
                  title="活动连接"
                  value={systemMetrics.activeConnections || 0}
                  unit=" 个"
                  color="blue"
                />
              </div>
            </Card>

            {/* 性能图表 */}
            <Card>
              <div className="flex items-center mb-6">
                <TrendingUp className="w-6 h-6 text-blue-400 mr-2" />
                <h2 className="text-xl font-semibold">性能趋势</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>CPU使用率趋势</span>
                    <span className="font-medium">{systemMetrics.cpuUsage?.toFixed(1) || '0.0'}%</span>
                  </div>
                  <div className="w-full h-2 bg-[#111827] rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-red-500 to-orange-500"
                      style={{ width: `${systemMetrics.cpuUsage || 0}%` }}
                    ></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>内存使用趋势</span>
                    <span className="font-medium">{systemMetrics.memoryUsage?.toFixed(1) || '0.0'}%</span>
                  </div>
                  <div className="w-full h-2 bg-[#111827] rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                      style={{ width: `${systemMetrics.memoryUsage || 0}%` }}
                    ></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>网络流量趋势</span>
                    <span className="font-medium">
                      {(systemMetrics.networkIn / 1000).toFixed(1)} / {(systemMetrics.networkOut / 1000).toFixed(1)} KB/s
                    </span>
                  </div>
                  <div className="w-full h-4 bg-[#111827] rounded-full overflow-hidden flex">
                    <div 
                      className="h-full bg-blue-500/100"
                      style={{ width: `${Math.min(100, (systemMetrics.networkIn / 2000) * 100)}%` }}
                    ></div>
                    <div 
                      className="h-full bg-green-500/100"
                      style={{ width: `${Math.min(100, (systemMetrics.networkOut / 2000) * 100)}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-xs mt-1">
                    <span className="text-blue-400">流入</span>
                    <span className="text-green-400">流出</span>
                  </div>
                </div>
              </div>
            </Card>

            {/* 连接状态 */}
            <Card>
              <div className="flex items-center mb-6">
                <Globe className="w-6 h-6 text-blue-400 mr-2" />
                <h2 className="text-xl font-semibold">连接状态</h2>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg bg-[#0a0e17]/60">
                  <div className="flex items-center">
                    <div className={`w-2 h-2 rounded-full mr-3 ${
                      isConnected ? 'bg-green-500/100' : 'bg-red-500/100'
                    }`}></div>
                    <div>
                      <div className="font-medium">WebSocket连接</div>
                      <div className="text-sm opacity-70">实时数据推送</div>
                    </div>
                  </div>
                  <Badge variant={isConnected ? 'success' : 'danger'} size="sm">
                    {isConnected ? '已连接' : '未连接'}
                  </Badge>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-[#0a0e17]/60">
                  <div className="flex items-center">
                    <div className="w-2 h-2 rounded-full bg-green-500/100 mr-3"></div>
                    <div>
                      <div className="font-medium">API服务</div>
                      <div className="text-sm opacity-70">REST接口服务</div>
                    </div>
                  </div>
                  <Badge variant="success" size="sm">正常</Badge>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-[#0a0e17]/60">
                  <div className="flex items-center">
                    <div className="w-2 h-2 rounded-full bg-green-500/100 mr-3"></div>
                    <div>
                      <div className="font-medium">数据库</div>
                      <div className="text-sm opacity-70">扫描结果存储</div>
                    </div>
                  </div>
                  <Badge variant="success" size="sm">正常</Badge>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-[#0a0e17]/60">
                  <div className="flex items-center">
                    <div className={`w-2 h-2 rounded-full mr-3 ${
                      systemMetrics.errorRate < 1 ? 'bg-green-500/100' : 'bg-yellow-500/100'
                    }`}></div>
                    <div>
                      <div className="font-medium">错误率</div>
                      <div className="text-sm opacity-70">最近1小时</div>
                    </div>
                  </div>
                  <Badge variant={systemMetrics.errorRate < 1 ? 'success' : 'warning'} size="sm">
                    {systemMetrics.errorRate?.toFixed(2) || '0.00'}%
                  </Badge>
                </div>
              </div>
            </Card>

            {/* 快速操作 */}
            <Card>
              <div className="flex items-center mb-6">
                <Settings className="w-6 h-6 text-gray-400 mr-2" />
                <h2 className="text-xl font-semibold">监控设置</h2>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">自动刷新</span>
                  <div className="relative inline-block w-12 h-6">
                    <input type="checkbox" className="sr-only" defaultChecked />
                    <div className="block bg-[#111827] w-12 h-6 rounded-full"></div>
                    <div className="dot absolute left-1 top-1 bg-[#0a0e17] w-4 h-4 rounded-full transition"></div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm">声音提醒</span>
                  <div className="relative inline-block w-12 h-6">
                    <input type="checkbox" className="sr-only" />
                    <div className="block bg-[#111827] w-12 h-6 rounded-full"></div>
                    <div className="dot absolute left-1 top-1 bg-[#0a0e17] w-4 h-4 rounded-full transition"></div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm">日志保留</span>
                  <select className="bg-[#0a0e17] border border-white/10 rounded px-2 py-1 text-sm">
                    <option>7天</option>
                    <option>30天</option>
                    <option>90天</option>
                  </select>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm">更新频率</span>
                  <select className="bg-[#0a0e17] border border-white/10 rounded px-2 py-1 text-sm">
                    <option>实时 (500ms)</option>
                    <option>快速 (1s)</option>
                    <option>标准 (5s)</option>
                    <option>慢速 (10s)</option>
                  </select>
                </div>

                <Button variant="outline" fullWidth className="mt-4">
                  <Settings className="w-4 h-4 mr-2" />
                  高级设置
                </Button>
              </div>
            </Card>
          </div>
        </div>

        {/* 状态栏 */}
        <div className="mt-6">
          <Card>
            <div className="flex flex-col md:flex-row items-center justify-between p-4">
              <div className="flex items-center space-x-4 mb-2 md:mb-0">
                <div className="flex items-center">
                  <Shield className="w-4 h-4 text-green-500 mr-2" />
                  <span className="text-sm">监控系统状态: </span>
                  <span className="text-sm font-medium ml-1 text-green-500">正常</span>
                </div>
                <div className="flex items-center">
                  <Clock className="w-4 h-4 text-blue-500 mr-2" />
                  <span className="text-sm">最后更新: </span>
                  <span className="text-sm font-medium ml-1">
                    {new Date().toLocaleTimeString('zh-CN', { hour12: false })}
                  </span>
                </div>
                <div className="flex items-center">
                  <Activity className="w-4 h-4 text-yellow-500 mr-2" />
                  <span className="text-sm">活动扫描: </span>
                  <span className="text-sm font-medium ml-1">
                    {activeScans.filter(s => s.status === 'running').length} 个
                  </span>
                </div>
              </div>

              <div className="text-sm opacity-70">
                数据更新间隔: 500ms | 日志条目: {logEntries.length} | 系统负载: {systemMetrics.cpuUsage?.toFixed(1) || '0.0'}%
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default RealTimeMonitor;
