/**
 * ToastContext — 全局轻量通知系统
 *
 * 使用：
 *   const { toast } = useToast();
 *   toast.error('请求失败');
 *   toast.success('操作成功');
 *   toast.warn('注意：...');
 *   toast.info('提示信息');
 */

import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';

const ToastContext = createContext(null);

const ICONS = {
  success: { Icon: CheckCircle, color: '#22c55e', bg: 'rgba(34,197,94,0.12)',  border: 'rgba(34,197,94,0.3)' },
  error:   { Icon: XCircle,     color: '#ef4444', bg: 'rgba(239,68,68,0.12)',  border: 'rgba(239,68,68,0.3)' },
  warn:    { Icon: AlertTriangle,color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.3)' },
  info:    { Icon: Info,         color: '#3b82f6', bg: 'rgba(59,130,246,0.12)', border: 'rgba(59,130,246,0.3)' },
};

const ToastItem = ({ id, type, message, onDismiss }) => {
  const { Icon, color, bg, border } = ICONS[type] || ICONS.info;
  return (
    <div
      className="flex items-start gap-3 px-4 py-3 rounded-xl shadow-lg max-w-sm w-full pointer-events-auto"
      style={{
        background: bg,
        border: `1px solid ${border}`,
        backdropFilter: 'blur(12px)',
        animation: 'slide-in-right 0.25s ease both',
      }}
    >
      <Icon size={16} style={{ color, flexShrink: 0, marginTop: 1 }} />
      <p className="flex-1 text-sm text-gray-200 leading-snug">{message}</p>
      <button
        onClick={() => onDismiss(id)}
        className="shrink-0 text-gray-500 hover:text-gray-300 transition-colors"
      >
        <X size={13} />
      </button>
    </div>
  );
};

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);
  const timerRefs = useRef({});

  const dismiss = useCallback((id) => {
    clearTimeout(timerRefs.current[id]);
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const show = useCallback((type, message, duration = 4000) => {
    const id = `toast_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    setToasts(prev => [...prev.slice(-4), { id, type, message }]); // 最多同时显示 5 条
    timerRefs.current[id] = setTimeout(() => dismiss(id), duration);
    return id;
  }, [dismiss]);

  const toast = {
    success: (msg, d) => show('success', msg, d),
    error:   (msg, d) => show('error',   msg, d),
    warn:    (msg, d) => show('warn',    msg, d),
    info:    (msg, d) => show('info',    msg, d),
  };

  // 挂载到 window 供 apiClient 等非 React 模块使用（事件总线模式）
  React.useEffect(() => {
    window.__clawai_toast = toast;
    return () => { delete window.__clawai_toast; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show]);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      {/* Toast 容器 */}
      <div
        className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none"
        aria-live="polite"
      >
        {toasts.map(t => (
          <ToastItem key={t.id} {...t} onDismiss={dismiss} />
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within <ToastProvider>');
  return ctx;
};

export default ToastContext;
