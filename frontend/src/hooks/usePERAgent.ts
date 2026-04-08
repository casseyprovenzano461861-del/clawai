/**
 * P-E-R Agent Hook
 * 管理 P-E-R 会话状态和 WebSocket 连接
 */

import { useState, useCallback, useRef, useEffect } from 'react';

const WS_URL = process.env.REACT_APP_WS_URL || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/per-events`;

export const usePERAgent = (options = {}) => {
  const {
    autoConnect = false,
    maxRetries = 3,
    retryDelay = 1000,
    onEvent,
    onError,
    onComplete
  } = options;

  const [status, setStatus] = useState('idle'); // idle, connecting, connected, running, error
  const [phase, setPhase] = useState('idle');
  const [iteration, setIteration] = useState(0);
  const [maxIterations, setMaxIterations] = useState(5);
  const [tasks, setTasks] = useState([]);
  const [findings, setFindings] = useState([]);
  const [budget, setBudget] = useState(null);
  const [report, setReport] = useState(null);
  
  const wsRef = useRef(null);
  const retryCountRef = useRef(0);
  const sessionIdRef = useRef(null);

  // 连接 WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setStatus('connecting');

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('connected');
        retryCountRef.current = 0;
        
        // 发送心跳
        ws.send(JSON.stringify({ action: 'ping' }));
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
        if (status === 'running') {
          setStatus('connected');
        }
        
        // 自动重连
        if (retryCountRef.current < maxRetries) {
          retryCountRef.current++;
          setTimeout(connect, retryDelay * retryCountRef.current);
        }
      };

    } catch (error) {
      console.error('Failed to connect:', error);
      setStatus('error');
      onError?.(error);
    }
  }, [maxRetries, retryDelay, status, onError]);

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
        if (event.findings?.length) {
          setFindings(prev => [...prev, ...event.findings]);
        }
        break;

      case 'reflection':
        // 可以存储反思摘要
        break;

      case 'complete':
        setStatus('connected');
        setPhase('completed');
        setReport(event.report);
        setBudget(event.budget_summary);
        onComplete?.(event);
        break;

      case 'error':
        setStatus('error');
        setPhase('failed');
        onError?.(new Error(event.message));
        break;

      default:
        break;
    }
  }, [onEvent, onComplete, onError]);

  // 启动 P-E-R
  const startPentest = useCallback((target, goal = '', mode = 'full') => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      connect();
      setTimeout(() => startPentest(target, goal, mode), 500);
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

  // 自动连接
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    
    return () => {
      wsRef.current?.close();
    };
  }, [autoConnect, connect]);

  return {
    // 状态
    status,
    phase,
    iteration,
    maxIterations,
    tasks,
    findings,
    budget,
    report,
    
    // 方法
    connect,
    disconnect,
    startPentest,
    stopPentest,
    
    // 工具方法
    isConnected: status === 'connected' || status === 'running',
    isRunning: status === 'running',
    clearFindings: () => setFindings([])
  };
};

export default usePERAgent;
