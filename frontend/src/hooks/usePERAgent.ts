/**
 * P-E-R Agent Hook
 * 管理 P-E-R 会话状态和 WebSocket 连接
 * 支持后端 EventBus 桥接的扩展事件类型：
 *   state_changed / message / tool_event / finding / progress
 */

import { useState, useCallback, useRef, useEffect } from 'react';

const _wsBase = (import.meta.env.VITE_WS_URL as string)
  || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//localhost:8000`;
const WS_URL = `${_wsBase}/ws/per-events`;

export type ToolEventStatus = 'start' | 'complete' | 'error';
export type MessageType = 'info' | 'success' | 'error' | 'warning';
export type AgentState = 'idle' | 'running' | 'paused' | 'completed' | 'error';

export interface ToolEvent {
  id: string;
  name: string;
  status: ToolEventStatus;
  args: Record<string, unknown>;
  result?: unknown;
  timestamp: string;
  /** 从 start 到 complete/error 的耗时（ms），仅 complete/error 时有值 */
  durationMs?: number;
}

export interface LogEntry {
  id: string;
  text: string;
  msgType: MessageType;
  timestamp: string;
  /** 来源：eventbus（后端 EventBus）或 per（P-E-R 生成器） */
  source: 'eventbus' | 'per';
}

export const usePERAgent = (options = {}) => {
  const {
    autoConnect = false,
    maxRetries = 3,
    retryDelay = 1000,
    onEvent,
    onError,
    onComplete
  } = options as any;

  const [status, setStatus] = useState('idle'); // idle, connecting, connected, running, error
  const [phase, setPhase] = useState('idle');
  const [iteration, setIteration] = useState(0);
  const [maxIterations, setMaxIterations] = useState(5);
  const [tasks, setTasks] = useState([]);
  const [findings, setFindings] = useState([]);
  const [budget, setBudget] = useState(null);
  const [report, setReport] = useState(null);

  // --- EventBus 桥接新增状态 ---
  const [agentState, setAgentState] = useState<AgentState>('idle');
  const [currentTask, setCurrentTask] = useState<string>('');
  const [progress, setProgress] = useState<number>(0);
  const [toolEvents, setToolEvents] = useState<ToolEvent[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const wsRef = useRef(null);
  const retryCountRef = useRef(0);
  const sessionIdRef = useRef(null);
  const connectRef = useRef<() => void>(() => {}); // 存最新 connect，供 onclose 递归调用
  /** 等待连接后自动发送的 pending 请求 */
  const pendingStartRef = useRef<{ target: string; goal: string; mode: string } | null>(null);
  /** tool_event start 时间戳，key = tool name */
  const toolStartRef = useRef<Record<string, number>>({});
  const logCounterRef = useRef(0);

  const _nextId = (prefix: string) => `${prefix}-${Date.now()}-${++logCounterRef.current}`;

  // 连接 WebSocket
  const connect = useCallback(() => {
    // 已连接或正在连接中，不重复创建
    const rs = wsRef.current?.readyState;
    if (rs === WebSocket.OPEN || rs === WebSocket.CONNECTING) return;

    setStatus('connecting');

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('connected');
        retryCountRef.current = 0;
        ws.send(JSON.stringify({ action: 'ping' }));
        // 如果有等待中的扫描请求，立即发送
        if (pendingStartRef.current) {
          const { target, goal, mode } = pendingStartRef.current;
          pendingStartRef.current = null;
          setStatus('running');
          setPhase('idle');
          setIteration(0);
          ws.send(JSON.stringify({ action: 'start_per', target, goal: goal || undefined, mode }));
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleEvent(data);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStatus('error');
        onError?.(error);
      };

      ws.onclose = () => {
        setStatus(prev => prev === 'running' ? 'connected' : prev);

        // 有限次重连，后端未启动时不无限循环
        if (retryCountRef.current < maxRetries) {
          retryCountRef.current++;
          const delay = retryDelay * retryCountRef.current;
          setTimeout(() => {
            // 只在还没有活跃连接时才重连
            const cur = wsRef.current?.readyState;
            if (cur !== WebSocket.OPEN && cur !== WebSocket.CONNECTING) {
              connectRef.current();
            }
          }, delay);
        }
      };

    } catch (error) {
      console.error('Failed to connect:', error);
      setStatus('error');
      onError?.(error);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [maxRetries, retryDelay, onError]); // 去掉 status 依赖，避免每次状态变化重建 connect

  // 始终保持 connectRef 指向最新版本
  useEffect(() => { connectRef.current = connect; }, [connect]);

  // 处理事件
  const handleEvent = useCallback((event) => {
    onEvent?.(event);

    switch (event.type) {
      case 'connected':
        break;
        
      case 'start':
        sessionIdRef.current = Date.now().toString();
        setFindings([]);
        setReport(null);
        setToolEvents([]);
        setLogs([]);
        setProgress(0);
        setCurrentTask('');
        break;

      case 'iteration':
        setIteration(event.num);
        setMaxIterations(event.max);
        break;

      case 'phase':
        setPhase(event.phase);
        break;

      case 'plan':
        setTasks(event.tasks.map((name, i) => ({
          id: i,
          name,
          status: 'pending'
        })));
        break;

      case 'task_start':
        setTasks(prev => prev.map((t, i) => 
          i === event.index ? { ...t, status: 'running' } : t
        ));
        break;

      case 'task_result':
        setTasks(prev => prev.map((t, i) => 
          t.name === event.task ? { ...t, status: event.success ? 'completed' : 'failed' } : t
        ));
        // task_result 里的 findings 也合并进去
        if (event.findings?.length) {
          setFindings(prev => [...prev, ...event.findings]);
        }
        break;

      case 'reflection':
        break;

      case 'complete':
        setStatus('connected');
        setPhase('completed');
        setAgentState('completed');
        setProgress(1);
        setReport(event.report);
        setBudget(event.budget_summary);
        onComplete?.(event);
        break;

      case 'error':
        setStatus('error');
        setPhase('failed');
        setAgentState('error');
        onError?.(new Error(event.message));
        break;

      // --- EventBus 桥接事件 ---

      case 'state_changed': {
        const s = event.state as AgentState;
        setAgentState(s);
        if (event.task) setCurrentTask(event.task);
        // 同步 running/paused 到 status
        if (s === 'running') setStatus('running');
        else if (s === 'idle' || s === 'paused') {
          setStatus(prev => (prev === 'running' ? 'connected' : prev));
        }
        setLogs(prev => [...prev.slice(-199), {
          id: _nextId('log'),
          text: event.details || `状态变更: ${s}`,
          msgType: s === 'error' ? 'error' : 'info',
          timestamp: event.timestamp || new Date().toISOString(),
          source: 'eventbus',
        }]);
        break;
      }

      case 'message':
        setLogs(prev => [...prev.slice(-199), {
          id: _nextId('log'),
          text: event.text || '',
          msgType: (event.msg_type as MessageType) || 'info',
          timestamp: event.timestamp || new Date().toISOString(),
          source: 'eventbus',
        }]);
        break;

      case 'tool_event': {
        const ts = event.timestamp || new Date().toISOString();
        if (event.status === 'start') {
          toolStartRef.current[event.name] = Date.now();
          setToolEvents(prev => [...prev.slice(-49), {
            id: _nextId('tool'),
            name: event.name,
            status: 'start',
            args: event.args || {},
            result: null,
            timestamp: ts,
          }]);
        } else {
          const startTime = toolStartRef.current[event.name];
          const durationMs = startTime ? Date.now() - startTime : undefined;
          delete toolStartRef.current[event.name];
          setToolEvents(prev => {
            // 找到最后一个同名 start 条目，更新其状态
            const idx = [...prev].reverse().findIndex(t => t.name === event.name && t.status === 'start');
            if (idx === -1) return prev;
            const realIdx = prev.length - 1 - idx;
            const updated = [...prev];
            updated[realIdx] = {
              ...updated[realIdx],
              status: event.status as ToolEventStatus,
              result: event.result,
              durationMs,
            };
            return updated;
          });
        }
        break;
      }

      case 'finding': {
        // 合并进 findings，支持带/不带 title 的格式
        // 后端 findings 格式：{ type, ports, ... } 或 { type, title, severity, detail }
        const { type: _evType, timestamp: _ts, ...findingData } = event;
        setFindings(prev => {
          // 去重：同类型且关键字段相同则跳过
          const ftype = findingData.type || '';
          const duplicate = prev.some(f => {
            if (f.type !== ftype) return false;
            if (ftype === 'open_ports') return JSON.stringify(f.ports) === JSON.stringify(findingData.ports);
            return f.title === findingData.title && f.detail === findingData.detail;
          });
          if (duplicate) return prev;
          return [...prev, findingData];
        });
        break;
      }

      case 'progress':
        setProgress(Math.min(1, Math.max(0, event.percent ?? 0)));
        if (event.description) setCurrentTask(event.description);
        break;

      default:
        break;
    }
  }, [onEvent, onComplete, onError]);

  // 启动 P-E-R
  const startPentest = useCallback((target, goal = '', mode = 'full') => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      // 存储请求，等连接建立后在 onopen 里自动发送
      pendingStartRef.current = { target, goal, mode };
      connect();
      return;
    }

    setStatus('running');
    setPhase('idle');
    setIteration(0);
    wsRef.current.send(JSON.stringify({
      action: 'start_per',
      target,
      goal: goal || undefined,
      mode
    }));
  }, [connect]);

  // 停止 P-E-R
  const stopPentest = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'stop_per' }));
    }
    setStatus('connected');
    setPhase('idle');
  }, []);

  // 断开连接
  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setStatus('idle');
  }, []);

  // 自动连接 — 只在挂载时执行一次，不把 connect 放依赖数组
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    return () => {
      // 卸载时关闭，清空 ref 避免悬空引用
      wsRef.current?.close();
      wsRef.current = null;
    };
  // connect 用 ref 方式规避，只在 autoConnect 变化时重跑
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoConnect]);

  return {
    // 原有状态
    status,
    phase,
    iteration,
    maxIterations,
    tasks,
    findings,
    budget,
    report,
    
    // EventBus 桥接新增状态
    agentState,
    currentTask,
    progress,
    toolEvents,
    logs,
    
    // 方法
    connect,
    disconnect,
    startPentest,
    stopPentest,
    
    // 工具方法
    isConnected: status === 'connected' || status === 'running',
    isRunning: status === 'running',
    clearFindings: () => setFindings([]),
    clearLogs: () => setLogs([]),
  };
};

export default usePERAgent;
