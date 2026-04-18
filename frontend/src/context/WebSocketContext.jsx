/**
 * WebSocketContext — 全局 WebSocket 连接状态
 * 连接到后端 /ws/events，监听系统事件，并向子组件暴露连接状态
 */
import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';

const WS_URL = (() => {
  // 从当前页面 host 动态推导，不受端口变化影响
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${proto}://${window.location.host}/ws/per-events`;
})();

// WebSocketContext 连接到通用 /ws/per-events 端点，但不带 token 参数
// token 验证已通过后端 accept 时跳过（端点为公开 WS）

const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 15000]; // 指数退避

const WebSocketContext = createContext({
  connected: false,
  lastEvent: null,
  send: () => {},
});

export const useWebSocket = () => useContext(WebSocketContext);

export const WebSocketProvider = ({ children }) => {
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState(null);
  const wsRef        = useRef(null);
  const attemptRef   = useRef(0);
  const mountedRef   = useRef(true);
  const timerRef     = useRef(null);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    // 后端 /ws/per-events 为公开端点，无需 token 验证，直接连接
    const url = WS_URL;
    let ws;
    try {
      ws = new WebSocket(url);
    } catch {
      scheduleReconnect();
      return;
    }
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) { ws.close(); return; }
      attemptRef.current = 0;
      setConnected(true);
      localStorage.setItem('ws_connected', 'true');
    };

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        setLastEvent(data);
      } catch { /* ignore malformed */ }
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setConnected(false);
      localStorage.setItem('ws_connected', 'false');
      scheduleReconnect();
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  const scheduleReconnect = useCallback(() => {
    const delay = RECONNECT_DELAYS[Math.min(attemptRef.current, RECONNECT_DELAYS.length - 1)];
    attemptRef.current += 1;
    timerRef.current = setTimeout(connect, delay);
  }, [connect]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      clearTimeout(timerRef.current);
      wsRef.current?.close();
      localStorage.setItem('ws_connected', 'false');
    };
  }, [connect]);

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }, []);

  return (
    <WebSocketContext.Provider value={{ connected, lastEvent, send }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export default WebSocketContext;
