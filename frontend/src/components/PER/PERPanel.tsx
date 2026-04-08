/**
 * P-E-R 控制台组件
 * 实时显示 Planner-Executor-Reflector 自主渗透测试流程
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  Play, Square, RefreshCw, Target, Brain, Zap, CheckCircle,
  AlertCircle, Clock, Activity, ChevronRight, FileText
} from 'lucide-react';

// 阶段图标和颜色
const PHASE_CONFIG = {
  idle: { icon: Activity, color: 'text-gray-400', bg: 'bg-gray-500' },
  planning: { icon: Brain, color: 'text-blue-400', bg: 'bg-blue-500' },
  executing: { icon: Zap, color: 'text-yellow-400', bg: 'bg-yellow-500' },
  reflecting: { icon: RefreshCw, color: 'text-purple-400', bg: 'bg-purple-500' },
  completed: { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500' },
  failed: { icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-500' },
};

/**
 * 阶段指示器组件
 */
export const PhaseIndicator = ({ current, className = '' }) => {
  const phases = ['planning', 'executing', 'reflecting'];
  const config = PHASE_CONFIG[current] || PHASE_CONFIG.idle;
  const currentIndex = phases.indexOf(current);
  
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {phases.map((phase, index) => {
        const phaseConfig = PHASE_CONFIG[phase];
        const isActive = phase === current;
        const isPast = currentIndex > index;
        
        return (
          <React.Fragment key={phase}>
            <div
              className={`
                flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium
                transition-all duration-300
                ${isActive ? `${phaseConfig.bg} text-white shadow-lg` : ''}
                ${isPast ? 'bg-gray-700 text-gray-300' : ''}
                ${!isActive && !isPast ? 'bg-gray-800 text-gray-500' : ''}
              `}
            >
              <phaseConfig.icon size={14} className={isActive ? 'animate-pulse' : ''} />
              <span className="capitalize">{phase}</span>
            </div>
            {index < phases.length - 1 && (
              <ChevronRight
                size={16}
                className={isPast ? 'text-gray-400' : 'text-gray-600'}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

/**
 * 任务列表组件
 */
export const TaskList = ({ tasks, activeIndex, className = '' }) => {
  if (!tasks || tasks.length === 0) return null;
  
  return (
    <div className={`space-y-2 ${className}`}>
      <h4 className="text-sm font-medium text-gray-400 mb-2">执行计划</h4>
      {tasks.map((task, index) => {
        const isActive = index === activeIndex;
        const statusColor = {
          pending: 'text-gray-500',
          running: 'text-yellow-400',
          completed: 'text-green-400',
          failed: 'text-red-400',
        }[task.status || 'pending'];
        
        return (
          <div
            key={task.id || index}
            className={`
              flex items-center gap-2 p-2 rounded-lg
              transition-all duration-200
              ${isActive ? 'bg-gray-800 border border-blue-500/50' : 'bg-gray-900/50'}
            `}
          >
            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
              isActive ? 'bg-blue-500 text-white' : 'bg-gray-700 text-gray-400'
            }`}>
              {index + 1}
            </span>
            <span className={`flex-1 text-sm ${statusColor}`}>
              {task.name || task}
            </span>
            {task.status === 'running' && (
              <RefreshCw size={14} className="animate-spin text-yellow-400" />
            )}
            {task.status === 'completed' && (
              <CheckCircle size={14} className="text-green-400" />
            )}
            {task.status === 'failed' && (
              <AlertCircle size={14} className="text-red-400" />
            )}
          </div>
        );
      })}
    </div>
  );
};

/**
 * 发现卡片组件
 */
export const FindingCard = ({ finding, className = '' }) => {
  const severityColors = {
    critical: 'border-red-500 bg-red-500/10',
    high: 'border-orange-500 bg-orange-500/10',
    medium: 'border-yellow-500 bg-yellow-500/10',
    low: 'border-blue-500 bg-blue-500/10',
    info: 'border-gray-500 bg-gray-500/10',
  };
  
  const severity = finding.severity || 'info';
  const borderColor = severityColors[severity] || severityColors.info;
  
  return (
    <div className={`p-3 rounded-lg border-l-4 ${borderColor} ${className}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-white">
          {finding.type || finding.title || 'Finding'}
        </span>
        <span className={`text-xs px-2 py-0.5 rounded capitalize ${
          severity === 'critical' ? 'bg-red-500/20 text-red-400' :
          severity === 'high' ? 'bg-orange-500/20 text-orange-400' :
          severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
          'bg-gray-500/20 text-gray-400'
        }`}>
          {severity}
        </span>
      </div>
      {finding.description && (
        <p className="text-xs text-gray-400">{finding.description}</p>
      )}
    </div>
  );
};

/**
 * P-E-R 主控制面板
 */
const PERPanel = ({ 
  onSessionEnd,
  className = '' 
}) => {
  const [target, setTarget] = useState('');
  const [goal, setGoal] = useState('');
  const [mode, setMode] = useState('full');
  const [isRunning, setIsRunning] = useState(false);
  const [phase, setPhase] = useState('idle');
  const [iteration, setIteration] = useState(0);
  const [tasks, setTasks] = useState([]);
  const [activeTaskIndex, setActiveTaskIndex] = useState(-1);
  const [findings, setFindings] = useState([]);
  const [logs, setLogs] = useState([]);
  const [summary, setSummary] = useState(null);
  
  const wsRef = useRef(null);
  const logsEndRef = useRef(null);
  
  // 自动滚动到日志底部
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);
  
  // 添加日志
  const addLog = useCallback((event) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev.slice(-100), { ...event, timestamp }]);
    
    // 更新状态
    switch (event.type) {
      case 'phase':
        setPhase(event.phase);
        break;
      case 'plan':
        setTasks(event.tasks);
        break;
      case 'task_start':
        setActiveTaskIndex(event.index);
        setTasks(prev => prev.map((t, i) => 
          i === event.index ? { ...t, status: 'running' } : t
        ));
        break;
      case 'task_result':
        setTasks(prev => prev.map((t, i) => 
          i === activeTaskIndex ? { ...t, status: event.success ? 'completed' : 'failed' } : t
        ));
        if (event.findings) {
          setFindings(prev => [...prev, ...event.findings]);
        }
        break;
      case 'iteration':
        setIteration(event.num);
        break;
      case 'reflection':
        setSummary(event.summary);
        break;
      case 'complete':
        setIsRunning(false);
        setPhase('completed');
        if (onSessionEnd) {
          onSessionEnd(event);
        }
        break;
      case 'error':
        setIsRunning(false);
        setPhase('failed');
        break;
    }
  }, [activeTaskIndex, onSessionEnd]);
  
  // 连接 WebSocket
  const connectWebSocket = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/per-events`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    
    ws.onopen = () => {
      addLog({ type: 'connected', message: 'WebSocket 连接成功' });
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      addLog(data);
    };
    
    ws.onerror = (error) => {
      addLog({ type: 'error', message: 'WebSocket 连接错误' });
    };
    
    ws.onclose = () => {
      addLog({ type: 'disconnected', message: 'WebSocket 连接关闭' });
    };
  }, [addLog]);
  
  // 启动 P-E-R
  const startPER = useCallback(() => {
    if (!target.trim()) return;
    
    setIsRunning(true);
    setPhase('idle');
    setIteration(0);
    setTasks([]);
    setFindings([]);
    setLogs([]);
    setSummary(null);
    
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      connectWebSocket();
      // 等待连接
      setTimeout(() => {
        wsRef.current?.send(JSON.stringify({
          action: 'start_per',
          target: target.trim(),
          goal: goal.trim() || undefined,
          mode: mode
        }));
      }, 500);
    } else {
      wsRef.current.send(JSON.stringify({
        action: 'start_per',
        target: target.trim(),
        goal: goal.trim() || undefined,
        mode: mode
      }));
    }
  }, [target, goal, mode, connectWebSocket]);
  
  // 停止 P-E-R
  const stopPER = useCallback(() => {
    wsRef.current?.send(JSON.stringify({ action: 'stop_per' }));
    setIsRunning(false);
    setPhase('idle');
  }, []);
  
  return (
    <div className={`bg-gray-900 rounded-xl border border-gray-800 ${className}`}>
      {/* 输入区域 */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex gap-4 mb-4">
          <div className="flex-1">
            <label className="block text-sm text-gray-400 mb-1">目标地址</label>
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="example.com 或 192.168.1.1"
              disabled={isRunning}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
            />
          </div>
          <div className="flex-1">
            <label className="block text-sm text-gray-400 mb-1">测试目标（可选）</label>
            <input
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="对目标进行安全评估"
              disabled={isRunning}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
            />
          </div>
          <div className="w-32">
            <label className="block text-sm text-gray-400 mb-1">模式</label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              disabled={isRunning}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500 disabled:opacity-50"
            >
              <option value="full">完整测试</option>
              <option value="recon">仅侦察</option>
              <option value="vuln">漏洞扫描</option>
            </select>
          </div>
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={startPER}
            disabled={isRunning || !target.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play size={16} />
            开始测试
          </button>
          <button
            onClick={stopPER}
            disabled={!isRunning}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Square size={16} />
            停止
          </button>
        </div>
      </div>
      
      {/* 状态指示器 */}
      <div className="p-4 border-b border-gray-800 flex items-center justify-between">
        <PhaseIndicator current={phase} />
        <div className="flex items-center gap-4 text-sm text-gray-400">
          <span>迭代: {iteration}</span>
          <span>发现: {findings.length}</span>
        </div>
      </div>
      
      {/* 主内容区域 */}
      <div className="grid grid-cols-3 gap-4 p-4">
        {/* 左侧：任务列表 */}
        <div className="col-span-1">
          <TaskList tasks={tasks} activeIndex={activeTaskIndex} />
        </div>
        
        {/* 中间：发现 */}
        <div className="col-span-1 space-y-2 max-h-96 overflow-y-auto">
          <h4 className="text-sm font-medium text-gray-400 mb-2">发现</h4>
          {findings.length === 0 ? (
            <p className="text-sm text-gray-500">暂无发现</p>
          ) : (
            findings.slice(-10).map((finding, index) => (
              <FindingCard key={index} finding={finding} />
            ))
          )}
        </div>
        
        {/* 右侧：日志 */}
        <div className="col-span-1">
          <h4 className="text-sm font-medium text-gray-400 mb-2">执行日志</h4>
          <div className="bg-gray-950 rounded-lg p-3 h-96 overflow-y-auto text-xs font-mono">
            {logs.map((log, index) => (
              <div key={index} className="py-1 border-b border-gray-900/50">
                <span className="text-gray-500">[{log.timestamp}]</span>{' '}
                <span className={`${
                  log.type === 'error' ? 'text-red-400' :
                  log.type === 'task_result' ? (log.success ? 'text-green-400' : 'text-red-400') :
                  'text-gray-300'
                }`}>
                  {log.message || log.type}
                </span>
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        </div>
      </div>
      
      {/* 底部：摘要 */}
      {summary && (
        <div className="p-4 border-t border-gray-800 bg-gray-800/50">
          <h4 className="text-sm font-medium text-gray-400 mb-2">分析摘要</h4>
          <p className="text-sm text-gray-300">{summary}</p>
        </div>
      )}
    </div>
  );
};

export default PERPanel;
