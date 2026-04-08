import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  Target, Play, Brain, Shield, Zap, CheckCircle, AlertCircle,
  Cpu, Network, Lock, RefreshCw, Activity, Search, Settings,
  BarChart3, Clock, AlertTriangle, History, Command, Keyboard,
  Moon, Sun, ChevronRight, X, Download, Trash2, WifiOff,
  FileText, Bug, FlaskConical, Terminal, ArrowRight, ChevronDown, Plus, Globe
} from 'lucide-react';
import {
  PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer
} from 'recharts';

// 导入新组件
import { 
  Skeleton, 
  ScanResultSkeleton, 
  ToolListSkeleton, 
  CardSkeleton 
} from '../components/Skeleton';
import ScanHistory from '../components/ScanHistory';
import ToolManager from '../components/ToolManager';
import ManualScanner from '../components/ManualScanner';
import scanHistoryService from '../services/scanHistoryService';
import useKeyboardShortcuts from '../hooks/useKeyboardShortcuts';
import api, { setAuthToken } from '../services/api';
import i18n from '../i18n';

const t = i18n.t;

/**
 * ClawAI 主仪表板 - 集成所有新功能
 */
const ClawAIDashboard = () => {
  // 状态
  const [target, setTarget] = useState('');
  const [loading, setLoading] = useState(false);
  const [attackData, setAttackData] = useState(null);
  const [error, setError] = useState(null);
  const [tools, setTools] = useState([]);
  const [health, setHealth] = useState(null);
  const [darkMode, setDarkMode] = useState(true);
  const [toolsLoading, setToolsLoading] = useState(true);
  
  // 扫描历史状态
  const [showHistory, setShowHistory] = useState(false);
  const [recentScans, setRecentScans] = useState([]);

  // 快捷键提示状态
  const [showShortcutHint, setShowShortcutHint] = useState(false);
  
  // 工具管理状态
  const [showToolManager, setShowToolManager] = useState(false);
  
  // 自主扫描状态
  const [showManualScanner, setShowManualScanner] = useState(false);
  
  // 活动馈送状态
  const [activityFeed, setActivityFeed] = useState([]);
  
  // 实时代理状态
  const [activeAgents, setActiveAgents] = useState([]);
  
  // 连接状态
  const [connectionLost, setConnectionLost] = useState(false);
  
  // 刷新状态
  const [refreshing, setRefreshing] = useState(false);
  
  // 活动过滤器
  const [activityFilter, setActivityFilter] = useState('all');
  
  // 连续错误计数
  const consecutiveErrorsRef = useRef(0);
  const prevFindingsCountRef = useRef(-1);
  const prevRunningCountRef = useRef(-1);
  
  // 通知状态
  const [toasts, setToasts] = useState([]);
  let _toastId = 0;

  // 相对时间函数
  function relativeTime(ts) {
    const diff = Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  }

  // 通知系统
  const addToast = useCallback((message, severity = 'info') => {
    const id = ++_toastId;
    setToasts(prev => [...prev.slice(-4), { id, message, severity }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 5000);
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  // 饼图组件
  function DonutChart({ data }) {
    const filtered = data.filter(d => d.value > 0);
    if (filtered.length === 0) return <p className="text-gray-400 text-center py-8 text-sm">No data yet</p>;
    const total = filtered.reduce((s, d) => s + d.value, 0);

    return (
      <div className="flex items-center gap-4">
        <ResponsiveContainer width={140} height={140}>
          <PieChart>
            <Pie
              data={filtered}
              dataKey="value"
              cx="50%"
              cy="50%"
              innerRadius={38}
              outerRadius={62}
              paddingAngle={2}
              strokeWidth={0}
            >
              {filtered.map((d, i) => (
                <Cell key={i} fill={d.color} />
              ))}
            </Pie>
            <RechartsTooltip
              contentStyle={{ background: '#1a1a2e', border: '1px solid #2a2a3e', borderRadius: 8, fontSize: 12 }}
              itemStyle={{ color: '#e2e8f0' }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="flex flex-col gap-1.5">
          {filtered.map(d => (
            <div key={d.name} className="flex items-center gap-2 text-sm">
              <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: d.color }} />
              <span className="text-gray-300 whitespace-nowrap">{d.name}</span>
              <span className="text-white font-semibold ml-auto tabular-nums">{d.value}</span>
              <span className="text-gray-500 text-xs w-10 text-right">{((d.value / total) * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // 实时代理卡片
  function ActiveAgentCard({ agent }) {
    return (
      <div className="flex items-center gap-4 p-3 bg-gray-700/60 rounded-lg hover:bg-gray-700 transition-colors group">
        {/* 脉冲指示器 */}
        <div className="relative flex-shrink-0">
          <div className={`w-3 h-3 rounded-full ${agent.status === 'running' ? 'bg-green-500' : 'bg-yellow-500'}`} />
          {agent.status === 'running' && (
            <div className="absolute inset-0 w-3 h-3 rounded-full bg-green-500 animate-ping opacity-40" />
          )}
        </div>

        {/* 信息 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-white truncate max-w-[180px] sm:max-w-[300px]">
              {agent.target}
            </span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-600 text-gray-300 uppercase hidden sm:inline">
              {agent.mode.replace('_', ' ')}
            </span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <div className="flex-1 h-1.5 bg-gray-600 rounded-full overflow-hidden max-w-[200px]">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${agent.progress}%`,
                  background: 'linear-gradient(90deg, #22c55e, #16a34a)',
                }}
              />
            </div>
            <span className="text-xs text-gray-400 tabular-nums w-8">{agent.progress}%</span>
            <span className="text-xs text-gray-500 hidden sm:inline">{agent.phase}</span>
          </div>
        </div>

        {/* 发现 + 箭头 */}
        <div className="flex items-center gap-2">
          {agent.findings_count > 0 && (
            <div className="flex items-center gap-1">
              <Bug className="w-3 h-3 text-red-400" />
              <span className="text-xs text-red-400 font-medium tabular-nums">{agent.findings_count}</span>
            </div>
          )}
          <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-gray-400 transition-colors" />
        </div>
      </div>
    );
  }

  // 获取工具列表
  const fetchTools = async () => {
    setToolsLoading(true);
    try {
      const response = await api.get('/api/v1/tools');
      setTools(response.tools || []);
    } catch (err) {
      console.error('获取工具列表失败:', err);
      // 使用模拟数据
      setTools([
        { name: 'nmap', description: '网络扫描工具', category: 'reconnaissance', status: 'available', required: true },
        { name: 'sqlmap', description: 'SQL注入检测工具', category: 'exploitation', status: 'available', required: true },
        { name: 'nikto', description: 'Web服务器扫描工具', category: 'scanning', status: 'available', required: false },
        { name: 'dirsearch', description: 'Web路径扫描工具', category: 'scanning', status: 'available', required: false },
        { name: 'nuclei', description: '基于模板的漏洞扫描工具', category: 'scanning', status: 'available', required: false },
        { name: 'wafw00f', description: 'WAF检测工具', category: 'scanning', status: 'available', required: false },
      ]);
    } finally {
      setToolsLoading(false);
    }
  };

  // 数据获取函数
  const fetchData = useCallback(async () => {
    try {
      // 并行获取所有数据
      const [toolsData, healthData, historyData] = await Promise.all([
        api.get('/api/v1/tools').catch(() => ({ tools: [] })),
        api.get('/health').catch(() => ({ status: 'degraded' })),
        Promise.resolve(scanHistoryService.getAll())
      ]);

      // 更新状态
      setTools(toolsData.tools || []);
      setHealth(healthData);
      setRecentScans(historyData.slice(0, 5));

      // 模拟活动馈送数据
        setActivityFeed([
          {
            type: 'scan',
            action: 'started',
            title: '开始扫描 example.com',
            description: '完整的AI驱动安全评估',
            timestamp: new Date().toISOString(),
            link: '#',
            status: 'running'
          },
          {
            type: 'vulnerability',
            action: 'discovered',
            title: '发现SQL注入漏洞',
            description: '登录表单中的严重漏洞',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            link: '#',
            severity: 'critical'
          },
          {
            type: 'agent_task',
            action: 'completed',
            title: 'Nmap扫描完成',
            description: '端口扫描成功完成',
            timestamp: new Date(Date.now() - 7200000).toISOString(),
            link: '#',
            status: 'completed'
          }
        ]);

      // 模拟实时代理数据
      setActiveAgents([
        {
          agent_id: '1',
          target: 'example.com',
          status: 'running',
          progress: 45,
          phase: '扫描中',
          scan_id: 'scan_123',
          started_at: new Date(Date.now() - 1800000).toISOString(),
          findings_count: 2,
          mode: 'full_scan'
        },
        {
          agent_id: '2',
          target: 'test.local',
          status: 'running',
          progress: 78,
          phase: '利用中',
          scan_id: 'scan_456',
          started_at: new Date(Date.now() - 3600000).toISOString(),
          findings_count: 5,
          mode: 'auto_pentest'
        }
      ]);

      // 连接恢复
      if (consecutiveErrorsRef.current >= 3) {
        setConnectionLost(false);
        addToast('Connection restored', 'success');
      }
      consecutiveErrorsRef.current = 0;
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      consecutiveErrorsRef.current++;
      if (consecutiveErrorsRef.current >= 3) setConnectionLost(true);
    }
  }, [addToast]);

  // 加载最近扫描历史
  const loadRecentScans = () => {
    const history = scanHistoryService.getAll();
    setRecentScans(history.slice(0, 5));
  };

  // 执行扫描
  const executeScan = async () => {
    if (!target.trim()) {
      setError('请输入目标IP或域名');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/attack', {
        target: target.trim(),
        use_real: false,
        rule_engine_mode: true
      });

      setAttackData(response);
      
      // 保存到扫描历史
      scanHistoryService.add(response);
      loadRecentScans();
      
      // 添加通知
      addToast(`Scan started for ${target.trim()}`, 'info');
      
    } catch (err) {
      setError(err.message);
      addToast(`Scan failed: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // 执行PentestGPT扫描
  const executePentestGPT = async (instruction = 'Web application security testing') => {
    if (!target.trim()) {
      setError('请输入目标IP或域名');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await api.post('/api/v1/pentest/gpt/start', {
        target: target.trim(),
        instruction 
      });

      if (!data.success) {
        throw new Error(data.message || '启动PentestGPT扫描失败');
      }

      // 添加通知
      addToast(`PentestGPT扫描已启动: ${target.trim()}`, 'success');
      
    } catch (err) {
      setError(err.message);
      addToast(`PentestGPT扫描失败: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // 刷新数据
  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  }, [fetchData]);

  // 加载历史扫描结果
  const handleLoadHistory = (result) => {
    setAttackData(result);
    setShowHistory(false);
  };

  // 清除当前结果
  const clearResult = () => {
    setAttackData(null);
    setError(null);
  };

  // 导出结果
  const exportResult = () => {
    if (!attackData) return;
    const data = JSON.stringify(attackData, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `clawai-scan-${attackData.target}-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // 键盘快捷键
  useKeyboardShortcuts({
    'ctrl+enter': executeScan,
    'escape': () => {
      if (showHistory) setShowHistory(false);
      if (showShortcutHint) setShowShortcutHint(false);
    },
    'ctrl+h': () => setShowHistory(true),
    'ctrl+k': () => setShowShortcutHint(true),
  });

  // 自动登录
  const autoLogin = async () => {
    try {
      const response = await api.auth.login({ username: 'admin', password: 'admin123' });
      if (response.access_token) {
        setAuthToken(response.access_token);
        console.log('自动登录成功');
      }
    } catch (err) {
      console.error('自动登录失败:', err);
    }
  };

  // 初始化加载
  useEffect(() => {
    autoLogin();
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // 严重性颜色映射
  const severityColors = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-yellow-500',
    low: 'bg-blue-500',
    info: 'bg-gray-500'
  };

  // 图表颜色
  const SEVERITY_CHART_COLORS = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#eab308',
    low: '#3b82f6',
    info: '#6b7280',
  };

  const STATUS_CHART_COLORS = {
    running: '#22c55e',
    completed: '#6366f1',
    stopped: '#eab308',
    failed: '#ef4444',
    pending: '#6b7280',
    paused: '#f59e0b',
  };

  // 派生数据
  const severityChartData = useMemo(() => [
    { name: 'Critical', value: 2, color: SEVERITY_CHART_COLORS.critical },
    { name: 'High', value: 5, color: SEVERITY_CHART_COLORS.high },
    { name: 'Medium', value: 8, color: SEVERITY_CHART_COLORS.medium },
    { name: 'Low', value: 12, color: SEVERITY_CHART_COLORS.low },
    { name: 'Info', value: 20, color: SEVERITY_CHART_COLORS.info },
  ], []);

  const scanChartData = useMemo(() => [
    { name: 'Running', value: 2, color: STATUS_CHART_COLORS.running },
    { name: 'Completed', value: 15, color: STATUS_CHART_COLORS.completed },
    { name: 'Stopped', value: 1, color: STATUS_CHART_COLORS.stopped },
    { name: 'Failed', value: 0, color: STATUS_CHART_COLORS.failed },
    { name: 'Pending', value: 0, color: STATUS_CHART_COLORS.pending },
  ], []);

  const filteredActivity = useMemo(() => {
    if (activityFilter === 'all') return activityFeed;
    return activityFeed.filter(a => a.type === activityFilter);
  }, [activityFeed, activityFilter]);

  const statCards = useMemo(() => [
    { label: '总扫描数', value: 18, icon: Activity, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
    { label: '运行中', value: 2, icon: Play, color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20' },
    { label: '已完成', value: 15, icon: CheckCircle, color: 'text-indigo-400', bg: 'bg-indigo-500/10', border: 'border-indigo-500/20' },
    { label: '总漏洞数', value: 27, icon: Bug, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
    { label: '严重', value: 2, icon: AlertTriangle, color: 'text-red-500', bg: 'bg-red-600/10', border: 'border-red-600/20' },
    { label: '高危', value: 5, icon: Shield, color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20' },
  ], []);

  return (
    <div className={`min-h-screen ${darkMode ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-900'}`}>
      {/* 动画样式 */}
      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(-8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes countUp {
          from { opacity: 0; transform: translateY(6px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {/* 通知系统 */}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
        {toasts.map(t => (
          <div
            key={t.id}
            className={`bg-gray-800 border-l-4 ${t.severity === 'info' ? 'border-blue-500' : t.severity === 'success' ? 'border-green-500' : t.severity === 'warning' ? 'border-yellow-500' : 'border-red-500'} rounded-lg px-4 py-3 shadow-xl flex items-start gap-3`}
            style={{ animation: 'fadeSlideIn 0.3s ease-out' }}
          >
            <span className="text-sm text-gray-200 flex-1">{t.message}</span>
            <button onClick={() => dismissToast(t.id)} className="text-gray-500 hover:text-white">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>

      {/* 连接丢失横幅 */}
      {connectionLost && (
        <div
          className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg px-4 py-2.5 flex items-center gap-3"
          style={{ animation: 'fadeSlideIn 0.3s ease-out' }}
        >
          <WifiOff className="w-4 h-4 text-yellow-400 flex-shrink-0" />
          <span className="text-sm text-yellow-300">Connection issues detected. Retrying...</span>
        </div>
      )}

      {/* 快捷键提示 */}
      {showShortcutHint && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center" onClick={() => setShowShortcutHint(false)}>
          <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-xl p-6 max-w-md w-full mx-4`}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold flex items-center">
                <Keyboard className="w-5 h-5 mr-2" />
                键盘快捷键
              </h3>
              <button onClick={() => setShowShortcutHint(false)} className="p-1 rounded hover:bg-gray-700">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="opacity-70">开始扫描</span>
                <kbd className="px-2 py-1 rounded bg-gray-700 text-sm">Ctrl + Enter</kbd>
              </div>
              <div className="flex justify-between items-center">
                <span className="opacity-70">打开历史</span>
                <kbd className="px-2 py-1 rounded bg-gray-700 text-sm">Ctrl + H</kbd>
              </div>
              <div className="flex justify-between items-center">
                <span className="opacity-70">显示快捷键</span>
                <kbd className="px-2 py-1 rounded bg-gray-700 text-sm">Ctrl + K</kbd>
              </div>
              <div className="flex justify-between items-center">
                <span className="opacity-70">关闭弹窗</span>
                <kbd className="px-2 py-1 rounded bg-gray-700 text-sm">Esc</kbd>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 扫描历史侧边栏 */}
      {showHistory && (
        <div className="fixed inset-0 z-40 flex">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowHistory(false)} />
          <div className={`relative ml-auto w-full max-w-md ${darkMode ? 'bg-gray-800' : 'bg-white'} h-full overflow-auto shadow-xl`}>
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
              <h3 className="text-lg font-bold flex items-center">
                <History className="w-5 h-5 mr-2" />
                扫描历史
              </h3>
              <button onClick={() => setShowHistory(false)} className="p-1 rounded hover:bg-gray-700">
                <X className="w-5 h-5" />
              </button>
            </div>
            <ScanHistory 
              onLoadScan={handleLoadHistory} 
              darkMode={darkMode} 
            />
          </div>
        </div>
      )}

      {/* 工具管理侧边栏 */}
      {showToolManager && (
        <div className="fixed inset-0 z-40 flex">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowToolManager(false)} />
          <div className={`relative ml-auto w-full max-w-3xl ${darkMode ? 'bg-gray-800' : 'bg-white'} h-full overflow-auto shadow-xl`}>
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
              <h3 className="text-lg font-bold flex items-center">
                <Command className="w-5 h-5 mr-2" />
                工具管理
              </h3>
              <button onClick={() => setShowToolManager(false)} className="p-1 rounded hover:bg-gray-700">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4">
              <ToolManager />
            </div>
          </div>
        </div>
      )}

      {/* 自主扫描侧边栏 */}
      {showManualScanner && (
        <div className="fixed inset-0 z-40 flex">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowManualScanner(false)} />
          <div className={`relative ml-auto w-full max-w-3xl ${darkMode ? 'bg-gray-800' : 'bg-white'} h-full overflow-auto shadow-xl`}>
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
              <h3 className="text-lg font-bold flex items-center">
                <Terminal className="w-5 h-5 mr-2" />
                自主扫描
              </h3>
              <button onClick={() => setShowManualScanner(false)} className="p-1 rounded hover:bg-gray-700">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4">
              <ManualScanner />
            </div>
          </div>
        </div>
      )}

      {/* 导航栏 */}
      <header className={`${darkMode ? 'bg-gray-800' : 'bg-white'} border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-purple-500" />
              <span className="ml-2 text-xl font-bold">ClawAI</span>
              <span className="ml-2 text-sm opacity-70">智能安全评估系统</span>
            </div>
            <div className="flex items-center space-x-2">
              {/* 快捷键提示按钮 */}
              <button 
                onClick={() => setShowShortcutHint(true)}
                className={`p-2 rounded-lg ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
                title="快捷键"
              >
                <Keyboard className="h-5 w-5" />
              </button>
              
              {/* 工具管理按钮 */}
              <button 
                onClick={() => setShowToolManager(true)}
                className={`p-2 rounded-lg ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
                title="工具管理"
              >
                <Command className="h-5 w-5" />
              </button>
              
              {/* 自主扫描按钮 */}
              <button 
                onClick={() => setShowManualScanner(true)}
                className={`p-2 rounded-lg ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
                title="自主扫描"
              >
                <Terminal className="h-5 w-5" />
              </button>
              
              {/* 历史记录按钮 */}
              <button 
                onClick={() => setShowHistory(true)}
                className={`p-2 rounded-lg ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'} relative`}
                title="扫描历史"
              >
                <History className="h-5 w-5" />
                {recentScans.length > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-blue-500 rounded-full text-xs flex items-center justify-center">
                    {recentScans.length}
                  </span>
                )}
              </button>
              
              {/* 主题切换 */}
              <button 
                onClick={() => setDarkMode(!darkMode)}
                className={`p-2 rounded-lg ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
                title={darkMode ? '切换浅色模式' : '切换深色模式'}
              >
                {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </button>
              
              {/* 刷新按钮 */}
              <button 
                onClick={handleRefresh}
                className={`p-2 rounded-lg ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
                title="刷新数据"
              >
                <RefreshCw className={`h-5 w-5 ${refreshing ? 'animate-spin' : ''}`} />
              </button>
              
              {/* 设置 */}
              <button className={`p-2 rounded-lg ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`} title="设置">
                <Settings className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* 标题和快速操作 */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h2 className="text-2xl font-bold text-white flex items-center gap-2">
              <Zap className="w-6 h-6 text-purple-500" />
              ClawAI 仪表盘
            </h2>
            <p className="text-gray-400 mt-1">AI驱动的智能安全评估系统</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleRefresh}
              className="p-2 rounded-lg bg-gray-700 border border-gray-600 hover:border-gray-500 text-gray-400 hover:text-white transition-all"
              title="刷新"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => setShowHistory(true)}
              className="px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold hover:opacity-90 flex items-center"
            >
              <Plus className="w-5 h-5 mr-2" />
              新建扫描
            </button>
          </div>
        </div>

        {/* 快速操作 */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {([
            { label: '自动渗透测试', icon: Zap, to: '#', color: 'text-green-400', bg: 'bg-green-500/10 hover:bg-green-500/20', border: 'border-green-500/20 hover:border-green-500/40', desc: '三流AI测试' },
            { label: '完整安全测试', icon: Shield, to: '#', color: 'text-red-400', bg: 'bg-red-500/10 hover:bg-red-500/20', border: 'border-red-500/20 hover:border-red-500/40', desc: '100种漏洞类型' },
            { label: '漏洞实验室', icon: FlaskConical, to: '#', color: 'text-purple-400', bg: 'bg-purple-500/10 hover:bg-purple-500/20', border: 'border-purple-500/20 hover:border-purple-500/40', desc: '按类型挑战' },
            { label: '终端', icon: Terminal, to: '#', color: 'text-cyan-400', bg: 'bg-cyan-500/10 hover:bg-cyan-500/20', border: 'border-cyan-500/20 hover:border-cyan-500/40', desc: 'AI聊天与命令' },
          ]).map((action, index) => (
            <div
              key={index}
              className={`p-4 rounded-xl border ${action.border} ${action.bg} transition-all cursor-pointer group`}
            >
              <action.icon className={`w-6 h-6 ${action.color} mb-2`} />
              <p className="font-semibold text-white text-sm group-hover:translate-x-0.5 transition-transform">
                {action.label}
              </p>
              <p className="text-xs text-gray-400 mt-0.5">{action.desc}</p>
            </div>
          ))}
        </div>

        {/* 统计卡片 */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {statCards.map((stat, idx) => (
            <div
              key={stat.label}
              className={`bg-gray-800 rounded-xl border ${stat.border} p-4 hover:scale-[1.02] transition-all cursor-default`}
              style={{ animation: `fadeSlideIn 0.3s ease-out ${idx * 0.05}s both` }}
            >
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${stat.bg}`}>
                  <stat.icon className={`w-5 h-5 ${stat.color}`} />
                </div>
                <div>
                  <p
                    className="text-xl font-bold text-white tabular-nums"
                    style={{ animation: 'countUp 0.5s ease-out' }}
                  >
                    {stat.value}
                  </p>
                  <p className="text-[11px] text-gray-400 whitespace-nowrap">{stat.label}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 实时代理 */}
        {activeAgents.length > 0 && (
          <div className="bg-gray-800 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <span className="flex items-center gap-2">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500" />
                </span>
                实时代理 ({activeAgents.length}/5)
              </span>
              <button className="text-sm text-blue-500 hover:text-blue-400 flex items-center gap-1">
                管理 <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="space-y-2">
              {activeAgents.map(agent => (
                <ActiveAgentCard key={agent.agent_id} agent={agent} />
              ))}
            </div>
          </div>
        )}

        {/* 图表行 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gray-800 rounded-2xl p-6 shadow-xl">
            <h3 className="text-lg font-semibold mb-4">漏洞严重程度</h3>
            <DonutChart data={severityChartData} />
          </div>
          <div className="bg-gray-800 rounded-2xl p-6 shadow-xl">
            <h3 className="text-lg font-semibold mb-4">扫描状态</h3>
            <DonutChart data={scanChartData} />
          </div>
        </div>

        {/* 最近扫描 + 发现 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 最近扫描 */}
          <div className="bg-gray-800 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">最近扫描</h3>
              <button 
                onClick={() => setShowHistory(true)}
                className="text-sm text-blue-500 hover:text-blue-400 flex items-center gap-1"
              >
                查看全部 <ArrowRight className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-2">
              {recentScans.length === 0 ? (
                <div className="text-center py-8">
                  <Globe className="w-10 h-10 text-gray-600 mx-auto mb-2" />
                  <p className="text-gray-400 text-sm">暂无扫描记录</p>
                  <button 
                    onClick={() => setShowHistory(true)}
                    className="text-blue-500 text-sm hover:underline mt-1 inline-block"
                  >
                    开始你的第一次扫描
                  </button>
                </div>
              ) : (
                recentScans.map((scan, index) => (
                  <div
                    key={scan.id}
                    onClick={() => handleLoadHistory(scan.result)}
                    className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors group cursor-pointer"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-white truncate group-hover:text-blue-400 transition-colors">
                        {scan.target}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-gray-500">{relativeTime(scan.timestamp)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-2">
                      <span className="text-xs text-gray-400 tabular-nums">
                        {scan.vulnerabilities?.total || 0} 个漏洞
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* 主扫描区域 */}
          <div className="bg-gray-800 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">AI驱动扫描</h3>
              <div className="flex items-center gap-2">
                <div className="px-3 py-1 rounded-full text-xs font-semibold flex items-center bg-purple-900/50 text-purple-300">
                  <Brain className="w-4 h-4 mr-1" />
                  AI引擎已启用
                </div>
              </div>
            </div>

            {/* 目标输入 */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">目标地址</label>
                <div className="flex space-x-4">
                  <input
                    type="text"
                    value={target}
                    onChange={(e) => setTarget(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && e.ctrlKey && executeScan()}
                    placeholder="例如: example.com 或 192.168.1.1"
                    className="flex-1 px-4 py-3 rounded-lg bg-gray-700 border-gray-600 border focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                  <div className="flex flex-col sm:flex-row gap-2">
                    <button
                      onClick={executeScan}
                      disabled={loading}
                      className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold hover:opacity-90 disabled:opacity-50 flex items-center justify-center"
                    >
                      {loading ? (
                        <>
                          <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
                          扫描中...
                        </>
                      ) : (
                        <>
                          <Play className="h-5 w-5 mr-2" />
                          开始扫描
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => executePentestGPT()}
                      disabled={loading}
                      className="flex-1 px-4 py-3 bg-gradient-to-r from-green-600 to-teal-600 text-white rounded-lg font-semibold hover:opacity-90 disabled:opacity-50 flex items-center justify-center"
                    >
                      {loading ? (
                        <>
                          <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
                          PentestGPT...
                        </>
                      ) : (
                        <>
                          <Brain className="h-5 w-5 mr-2" />
                          PentestGPT
                        </>
                      )}
                    </button>
                  </div>
                </div>
                {error && (
                  <div className="mt-3 p-3 bg-red-900/30 border border-red-700 rounded-lg">
                    <div className="flex items-center">
                      <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
                      <span className="text-red-300">{error}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* 安全警告 */}
              <div className="p-4 bg-yellow-900/20 border border-yellow-700 rounded-lg">
                <div className="flex items-start">
                  <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2 mt-0.5" />
                  <div>
                    <p className="font-medium text-yellow-300">安全警告</p>
                    <p className="text-sm opacity-80 mt-1">
                      仅扫描您有权测试的网站或系统。未授权扫描可能是非法的。
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 活动馈送 */}
        <div className="bg-gray-800 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">活动馈送</h3>
            <div className="flex items-center gap-1 flex-wrap">
              {(['all', 'scan', 'vulnerability', 'agent_task', 'report']).map(f => (
                <button
                  key={f}
                  onClick={() => setActivityFilter(f)}
                  className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                    activityFilter === f
                      ? 'bg-blue-500/20 text-blue-400'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700'
                  }`}
                >
                  {f === 'all' ? '全部'
                    : f === 'agent_task' ? '任务'
                    : f === 'vulnerability' ? '漏洞'
                    : f === 'scan' ? '扫描'
                    : '报告'}
                </button>
              ))}
            </div>
          </div>
          <div className="space-y-1.5 max-h-[400px] overflow-auto">
            {filteredActivity.length === 0 ? (
              <p className="text-gray-400 text-center py-8 text-sm">暂无活动</p>
            ) : (
              filteredActivity.map((activity, idx) => {
                return (
                  <div
                    key={`${activity.type}-${activity.timestamp}-${idx}`}
                    className="flex items-start gap-3 p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors group cursor-pointer"
                    style={{ animation: `fadeSlideIn 0.2s ease-out ${Math.min(idx * 0.03, 0.3)}s both` }}
                  >
                    {/* 图标 */}
                    <div className={`mt-0.5 p-1.5 rounded-lg flex-shrink-0 ${
                      activity.type === 'scan' ? 'bg-blue-500/20 text-blue-400' :
                      activity.type === 'vulnerability' ? 'bg-red-500/20 text-red-400' :
                      activity.type === 'agent_task' ? 'bg-purple-500/20 text-purple-400' :
                      'bg-green-500/20 text-green-400'
                    }`}>
                      {activity.type === 'scan' ? <Shield className="w-3.5 h-3.5" /> :
                       activity.type === 'vulnerability' ? <AlertTriangle className="w-3.5 h-3.5" /> :
                       activity.type === 'agent_task' ? <Cpu className="w-3.5 h-3.5" /> :
                       <FileText className="w-3.5 h-3.5" />}
                    </div>

                    {/* 内容 */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-gray-500 uppercase font-medium">
                          {activity.type === 'scan' ? '扫描' : 
                           activity.type === 'vulnerability' ? '漏洞' : 
                           activity.type === 'agent_task' ? '任务' : '报告'}
                        </span>
                        <span className="text-[10px] text-gray-600">{activity.action === 'started' ? '开始' : 
                           activity.action === 'discovered' ? '发现' : 
                           activity.action === 'completed' ? '完成' : activity.action}</span>
                      </div>
                      <p className="font-medium text-white text-sm truncate group-hover:text-blue-400 transition-colors">
                        {activity.title}
                      </p>
                      {activity.description && (
                        <p className="text-xs text-gray-400 truncate">{activity.description}</p>
                      )}
                    </div>

                    {/* 元数据 */}
                    <div className="flex flex-col items-end gap-1 flex-shrink-0">
                      {activity.severity && (
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                          activity.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                          activity.severity === 'high' ? 'bg-orange-500/20 text-orange-400' :
                          activity.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                          activity.severity === 'low' ? 'bg-blue-500/20 text-blue-400' :
                          'bg-gray-500/20 text-gray-400'
                        }`}>
                          {activity.severity === 'critical' ? '严重' :
                           activity.severity === 'high' ? '高危' :
                           activity.severity === 'medium' ? '中危' :
                           activity.severity === 'low' ? '低危' :
                           '信息'}
                        </span>
                      )}
                      {activity.status && !activity.severity && (
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                          activity.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                          activity.status === 'running' ? 'bg-blue-500/20 text-blue-400' :
                          activity.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                          activity.status === 'stopped' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-gray-700 text-gray-300'
                        }`}>
                          {activity.status === 'completed' ? '已完成' :
                           activity.status === 'running' ? '运行中' :
                           activity.status === 'failed' ? '失败' :
                           activity.status === 'stopped' ? '已停止' :
                           activity.status}
                        </span>
                      )}
                      <span className="text-[10px] text-gray-500">{relativeTime(activity.timestamp)}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* 扫描结果 */}
        {loading ? (
          <ScanResultSkeleton className="mb-8" />
        ) : attackData ? (
          <div className="bg-gray-800 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-bold">扫描结果</h2>
                <p className="text-gray-400 mt-1">
                  目标: <span className="font-mono">{attackData.target}</span> • 时间: {attackData.execution_time}
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={exportResult}
                  className="p-2 rounded-lg hover:bg-gray-700"
                  title="导出结果"
                >
                  <Download className="h-5 w-5" />
                </button>
                <button
                  onClick={clearResult}
                  className="p-2 rounded-lg hover:bg-gray-700"
                  title="清除结果"
                >
                  <Trash2 className="h-5 w-5" />
                </button>
                <CheckCircle className="h-10 w-10 text-green-500" />
              </div>
            </div>

            {/* 攻击链 */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">攻击链 ({attackData.attack_chain?.length || 0} 步)</h3>
              <div className="space-y-3">
                {attackData.attack_chain?.map((step, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg border-l-4 ${step.highlight ? 'border-red-500 bg-red-900/10' : 'border-blue-500'} bg-gray-700/50`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center">
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${severityColors[step.severity] || 'bg-gray-500'}`}>
                            {step.severity?.toUpperCase()}
                          </span>
                          <span className="ml-3 font-medium">Step {step.step}: {step.title}</span>
                        </div>
                        <p className="mt-2 opacity-80">{step.description}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-sm opacity-70">{step.duration}</div>
                        <div className={`text-sm mt-1 ${step.success ? 'text-green-500' : 'text-red-500'}`}>
                          {step.success ? '✅ 成功' : '❌ 失败'}
                        </div>
                      </div>
                    </div>
                    <div className="mt-2 text-sm opacity-70 flex items-center">
                      <Cpu className="h-4 w-4 mr-1" />
                      Tool: {step.tool}
                    </div>
                  </div>
                ))}
              </div>

              {/* 规则引擎决策 */}
              {attackData.rule_engine_decision && (
                <div className="mt-6 p-4 rounded-lg bg-gradient-to-r from-purple-900/20 to-blue-900/20 border border-purple-700/30">
                  <h4 className="font-semibold mb-2">规则引擎决策</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm opacity-70">选择路径</p>
                      <p className="font-mono">{attackData.rule_engine_decision.selected_path_type}</p>
                    </div>
                    <div>
                      <p className="text-sm opacity-70">置信度</p>
                      <p className="font-mono">{(attackData.rule_engine_decision.confidence * 100).toFixed(1)}%</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : null}
      </main>

      <footer className={`bg-gray-800 border-t border-gray-700 mt-8`}>
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex flex-col sm:flex-row justify-between items-center">
            <div className="text-sm text-gray-400">
              ClawAI v2.0.0 • AI驱动的智能安全评估系统
            </div>
            <div className="flex items-center space-x-4 mt-2 sm:mt-0">
              <span className="text-xs text-gray-500">
                <kbd className="px-1.5 py-0.5 rounded bg-gray-700/50">Ctrl+K</kbd> 快捷键
              </span>
              <span className="text-xs text-gray-500">
                <kbd className="px-1.5 py-0.5 rounded bg-gray-700/50">Ctrl+H</kbd> 历史
              </span>
              <button
                onClick={handleRefresh}
                className="p-2 rounded-lg hover:bg-gray-700"
              >
                <RefreshCw className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default ClawAIDashboard;
