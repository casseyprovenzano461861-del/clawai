/**
 * P-E-R 控制台组件
 * 实时显示 Planner-Executor-Reflector 自主渗透测试流程
 * 已集成 EventBus 桥接事件：进度条、工具时间线、彩色消息日志
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  Play, Square, RefreshCw, Target, Brain, Zap, CheckCircle,
  AlertCircle, Clock, Activity, ChevronRight, FileText,
  Terminal, Info, AlertTriangle, XCircle
} from 'lucide-react';
import usePERAgent, { type ToolEvent, type LogEntry, type MessageType } from '../../hooks/usePERAgent';
import { usePERAgentContext } from '../../context/PERAgentContext';

// 阶段图标和颜色
const PHASE_CONFIG = {
  idle: { icon: Activity, color: 'text-gray-400', bg: 'bg-gray-500' },
  planning: { icon: Brain, color: 'text-blue-400', bg: 'bg-blue-500' },
  executing: { icon: Zap, color: 'text-yellow-400', bg: 'bg-yellow-500' },
  reflecting: { icon: RefreshCw, color: 'text-purple-400', bg: 'bg-purple-500' },
  completed: { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500' },
  failed: { icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-500' },
};

// 消息类型样式
const MSG_TYPE_STYLE: Record<MessageType, string> = {
  info: 'text-gray-300',
  success: 'text-green-400',
  error: 'text-red-400',
  warning: 'text-yellow-400',
};

const MSG_TYPE_ICON: Record<MessageType, React.ElementType> = {
  info: Info,
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
};

/**
 * 阶段指示器组件
 */
export const PhaseIndicator = ({ current, className = '' }) => {
  const phases = ['planning', 'executing', 'reflecting'];
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

  // RCE / CVE Skill 确认漏洞高亮
  const isRCEConfirmed = finding.type === 'cve_skill' && finding.vulnerable;
  const evidence = finding.evidence || finding.output_preview || '';
  
  return (
    <div className={`p-3 rounded-lg border-l-4 ${borderColor} ${className} ${
      isRCEConfirmed ? 'ring-2 ring-red-500/60 shadow-lg shadow-red-500/20' : ''
    }`}>
      <div className="flex items-center justify-between mb-1">
        <span className={`text-sm font-medium ${
          isRCEConfirmed ? 'text-red-300' : 'text-white'
        }`}>
          {isRCEConfirmed && '🔴 '}{finding.type || finding.title || 'Finding'}
          {isRCEConfirmed && ' — RCE 已确认'}
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
      {(finding.description || finding.detail) && (
        <p className="text-xs text-gray-400">{finding.description || finding.detail}</p>
      )}
      {isRCEConfirmed && evidence && (
        <pre className="mt-1.5 text-xs font-mono text-green-400 bg-black/40 rounded p-1.5 overflow-x-auto max-h-24">
          {String(evidence).slice(0, 300)}
        </pre>
      )}
    </div>
  );
};

/**
 * 进度条组件（EventBus PROGRESS 事件驱动）
 */
const ProgressBar = ({ percent, description }: { percent: number; description: string }) => {
  const pct = Math.round(percent * 100);
  return (
    <div className="mb-3">
      <div className="flex justify-between text-xs text-gray-400 mb-1">
        <span className="truncate max-w-xs">{description || '执行中…'}</span>
        <span className="ml-2 shrink-0">{pct}%</span>
      </div>
      <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 rounded-full transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
};

/**
 * 单条工具调用条目（EventBus TOOL 事件驱动）
 */
const ToolEventRow = ({ event }: { event: ToolEvent }) => {
  const isRunning = event.status === 'start';
  const isError = event.status === 'error';
  const isComplete = event.status === 'complete';

  return (
    <div className="flex items-center gap-2 py-1 text-xs border-b border-gray-800/50 last:border-0">
      <Terminal size={12} className="text-gray-500 shrink-0" />
      <span className="text-gray-300 font-mono truncate flex-1">{event.name}</span>
      {isRunning && <RefreshCw size={11} className="animate-spin text-yellow-400 shrink-0" />}
      {isComplete && (
        <>
          <CheckCircle size={11} className="text-green-400 shrink-0" />
          {event.durationMs !== undefined && (
            <span className="text-gray-500 shrink-0">{event.durationMs}ms</span>
          )}
        </>
      )}
      {isError && <XCircle size={11} className="text-red-400 shrink-0" />}
    </div>
  );
};

/**
 * 工具调用时间线（最近 20 条）
 */
const ToolTimeline = ({ events }: { events: ToolEvent[] }) => {
  const visible = events.slice(-20);
  return (
    <div>
      <h4 className="text-sm font-medium text-gray-400 mb-2 flex items-center gap-1.5">
        <Terminal size={13} />
        工具调用
        {events.some(e => e.status === 'start') && (
          <RefreshCw size={11} className="animate-spin text-yellow-400 ml-1" />
        )}
      </h4>
      {visible.length === 0 ? (
        <p className="text-xs text-gray-600">等待工具调用…</p>
      ) : (
        <div className="bg-gray-950 rounded-lg p-2 max-h-48 overflow-y-auto">
          {visible.map(ev => <ToolEventRow key={ev.id} event={ev} />)}
        </div>
      )}
    </div>
  );
};

/**
 * 彩色实时消息日志（EventBus MESSAGE + 原有 per 事件）
 */
const ColoredLog = ({ logs }: { logs: LogEntry[] }) => {
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div>
      <h4 className="text-sm font-medium text-gray-400 mb-2">执行日志</h4>
      <div className="bg-gray-950 rounded-lg p-3 h-64 overflow-y-auto text-xs font-mono">
        {logs.length === 0 && (
          <p className="text-gray-600">等待事件…</p>
        )}
        {logs.map(log => {
          const Icon = MSG_TYPE_ICON[log.msgType] || Info;
          return (
            <div key={log.id} className="flex gap-1.5 py-0.5">
              <span className="text-gray-600 shrink-0">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              <Icon size={11} className={`${MSG_TYPE_STYLE[log.msgType]} shrink-0 mt-0.5`} />
              <span className={MSG_TYPE_STYLE[log.msgType]}>{log.text}</span>
              {log.source === 'eventbus' && (
                <span className="text-gray-700 ml-auto shrink-0">bus</span>
              )}
            </div>
          );
        })}
        <div ref={endRef} />
      </div>
    </div>
  );
};

/**
 * P-E-R 主控制面板
 */
const PERPanel = ({ 
  onSessionEnd,
  initialTarget = '',
  initialMode = 'full',
  autoStart = false,
  className = '' 
}) => {
  const [target, setTarget] = useState(initialTarget);
  const [goal, setGoal] = useState('');
  const [mode, setMode] = useState(initialMode);
  const [activeTaskIndex, setActiveTaskIndex] = useState(-1);
  const [summary, setSummary] = useState<string | null>(null);

  // 从全局 Context 读取，页面切换不丢失数据
  const {
    status,
    phase,
    iteration,
    tasks,
    findings,
    report,
    // EventBus 桥接
    progress,
    currentTask,
    toolEvents,
    logs,
    // 方法
    startPentest,
    stopPentest,
    isRunning,
    isCompleted,
  } = usePERAgentContext();

  // 监听 report 变化（完成时）：通知父组件（保存已由 PERAgentContext 统一处理）
  // tasks 变化时同步激活索引
  useEffect(() => {
    const runningIdx = tasks.findIndex(t => t.status === 'running');
    setActiveTaskIndex(runningIdx);
  }, [tasks]);

  // 监听 report 变化（完成时）：通知父组件（保存已由 PERAgentContext 统一处理）
  // 用 ref 存 onSessionEnd，避免父组件每次 re-render 重建函数引用导致重复触发
  const onSessionEndRef = useRef(onSessionEnd);
  useEffect(() => { onSessionEndRef.current = onSessionEnd; }, [onSessionEnd]);
  const reportNotifiedRef = useRef<unknown>(null);
  useEffect(() => {
    if (!report) return;
    // 同一份报告只通知一次，防止父组件 re-render 重复触发
    if (reportNotifiedRef.current === report) return;
    reportNotifiedRef.current = report;
    if (onSessionEndRef.current) onSessionEndRef.current({ type: 'complete', report });
  }, [report]);

  const handleStart = useCallback(() => {
    if (!target.trim()) return;
    setSummary(null);
    setActiveTaskIndex(-1);
    startPentest(target.trim(), goal.trim(), mode);
  }, [target, goal, mode, startPentest]);

  // 当外部传入新目标或模式时同步到本地 state
  useEffect(() => {
    if (initialTarget && initialTarget !== target) {
      setTarget(initialTarget);
    }
  }, [initialTarget]);

  useEffect(() => {
    if (initialMode && initialMode !== mode) {
      setMode(initialMode);
    }
  }, [initialMode]);

  // autoStart：外部触发扫描，直接调用 startPentest（内部会处理连接等待）
  const autoStartFiredRef = useRef(false);
  // 记录当前 autoStart 对应的目标，用于折叠逻辑判断
  const autoStartTargetRef = useRef('');

  // 记录上次 autoStart 触发时的目标，只有目标真正改变时才重置 fired 标记
  const prevAutoStartTargetRef = useRef('');
  useEffect(() => {
    if (autoStart && initialTarget) {
      // 目标变了才允许重新触发，已完成的同一目标不重置
      if (!isCompleted && initialTarget !== prevAutoStartTargetRef.current) {
        autoStartFiredRef.current = false;
        prevAutoStartTargetRef.current = initialTarget;
      }
      autoStartTargetRef.current = initialTarget;
    }
  }, [autoStart, initialTarget, isCompleted]);

  useEffect(() => {
    // 已完成状态下不触发新扫描，防止报告被覆盖
    if (autoStart && initialTarget && !autoStartFiredRef.current && !isCompleted) {
      autoStartFiredRef.current = true;
      setSummary(null);
      setActiveTaskIndex(-1);
      // 如果当前正在运行，先停止再重新开始
      if (isRunning) stopPentest();
      // 使用 initialMode（Dashboard 传入的模式），而非内部 mode state
      startPentest(initialTarget.trim(), '', initialMode || mode);
    }
  }, [autoStart, initialTarget, isCompleted, startPentest, stopPentest, initialMode, mode]);

  // 折叠逻辑：autoStart 触发且（运行中 或 已完成）时折叠，显示紧凑目标行
  const isAutoRunning = autoStart && (isRunning || isCompleted) && autoStartTargetRef.current === initialTarget;

  // 报告区展开：扫描完成时自动滚动到报告
  const reportRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (report) {
      setTimeout(() => reportRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 200);
    }
  }, [report]);

  return (
    <div className={`bg-gray-900 rounded-xl border border-gray-800 ${className}`}>
      {/* 输入区域：autoStart 且目标匹配时折叠，只保留目标显示和停止按钮 */}
      {isAutoRunning ? (
        <div className="p-3 border-b border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Target size={13} className={isCompleted ? "text-green-400" : "text-cyan-400"} />
            <span className="font-mono text-cyan-300">{target}</span>
            <span className="text-gray-600">·</span>
            <span className="capitalize">{mode}</span>
            {isCompleted && <span className="text-xs px-2 py-0.5 rounded-full bg-green-500/20 text-green-400">已完成</span>}
          </div>
          {isRunning ? (
            <button
              onClick={stopPentest}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm transition-colors"
            >
              <Square size={13} />
              停止
            </button>
          ) : (
            <button
              onClick={() => startPentest(target.trim(), goal.trim(), mode)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors"
            >
              <Play size={13} />
              重新扫描
            </button>
          )}
        </div>
      ) : (
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
            onClick={handleStart}
            disabled={isRunning || !target.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play size={16} />
            开始测试
          </button>
          <button
            onClick={stopPentest}
            disabled={!isRunning}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Square size={16} />
            停止
          </button>
        </div>
      </div>
      )}
      
      {/* 完成横幅 */}
      {isCompleted && (
        <div className="px-4 py-2.5 bg-green-500/10 border-b border-green-500/30 flex items-center gap-2">
          <CheckCircle size={14} className="text-green-400 shrink-0" />
          <span className="text-sm text-green-300 font-medium">扫描完成</span>
          <span className="text-xs text-green-500/70 ml-1">共 {iteration} 次迭代 · 发现 {findings.length} 项</span>
          <button
            onClick={() => startPentest(target.trim(), goal.trim(), mode)}
            className="ml-auto text-xs px-3 py-1 rounded bg-green-500/20 hover:bg-green-500/30 text-green-300 transition-colors"
          >
            重新扫描
          </button>
        </div>
      )}

      {/* 状态指示器 + 进度条 */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center justify-between mb-3">
          <PhaseIndicator current={phase} />
          <div className="flex items-center gap-4 text-sm text-gray-400">
            <span>迭代: {iteration}</span>
            <span>发现: {findings.length}</span>
            <span className={`capitalize ${
              status === 'running' ? 'text-yellow-400' :
              status === 'completed' ? 'text-green-400' :
              status === 'connected' ? 'text-green-400' :
              status === 'error' ? 'text-red-400' : 'text-gray-500'
            }`}>
              {status === 'completed' ? '已完成' : status}
            </span>
          </div>
        </div>
        {/* 进度条（执行中显示；完成时显示满格） */}
        {(isRunning || isCompleted) && (
          <ProgressBar percent={isCompleted ? 1 : progress} description={isCompleted ? '扫描已完成' : currentTask} />
        )}
      </div>
      
      {/* 主内容区域 */}
      <div className="grid grid-cols-3 gap-4 p-4">
        {/* 左侧：任务列表 */}
        <div className="col-span-1">
          <TaskList tasks={tasks} activeIndex={activeTaskIndex} />
          {/* 工具时间线（任务列表下方） */}
          <div className="mt-4">
            <ToolTimeline events={toolEvents} />
          </div>
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
        
        {/* 右侧：彩色日志 */}
        <div className="col-span-1">
          <ColoredLog logs={logs} />
        </div>
      </div>
      
      {/* 底部：摘要 / 报告 */}
      {(summary || report) && (
        <div ref={reportRef} className="p-4 border-t border-gray-800 bg-gray-800/50">
          <h4 className="text-sm font-medium text-gray-400 mb-2 flex items-center gap-1.5">
            <FileText size={13} />
            {report ? '最终报告' : '分析摘要'}
            {report && <span className="ml-2 text-xs px-2 py-0.5 rounded bg-green-500/20 text-green-400">扫描完成</span>}
          </h4>
          <p className="text-sm text-gray-300 whitespace-pre-wrap">
            {report || summary}
          </p>
        </div>
      )}
    </div>
  );
};

export default PERPanel;
