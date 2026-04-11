/**
 * PERAgentContext — 全局 P-E-R Agent 状态
 * 在 App 根层级维护唯一 WebSocket 连接，所有页面切换不丢失数据
 * report 产生时自动保存到 ScanContext（报告管理）
 */

import React, { createContext, useContext, useEffect, useRef } from 'react';
import { usePERAgent } from '../hooks/usePERAgent';
import { useScan } from './ScanContext';

type PERAgentContextType = ReturnType<typeof usePERAgent>;

const PERAgentContext = createContext<PERAgentContextType | null>(null);

// 内部组件：可以访问 ScanContext
const PERAgentProviderInner: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const agent = usePERAgent({ autoConnect: true });
  const { savePERReport } = useScan();

  // 用 ref 避免 savePERReport 变化触发重复保存
  const saveRef = useRef(savePERReport);
  useEffect(() => { saveRef.current = savePERReport; }, [savePERReport]);

  // report 一旦出现（扫描完成），立即保存到报告管理，无论当前在哪个页面
  const savedReportRef = useRef<unknown>(null);
  useEffect(() => {
    if (!agent.report) return;
    // 防止同一份 report 重复保存
    if (agent.report === savedReportRef.current) return;
    savedReportRef.current = agent.report;

    const target = sessionStorage.getItem('per_current_target') || '未知目标';
    saveRef.current(target, agent.findings, agent.report, agent.tasks);
  }, [agent.report]);

  return (
    <PERAgentContext.Provider value={agent}>
      {children}
    </PERAgentContext.Provider>
  );
};

export const PERAgentProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <PERAgentProviderInner>{children}</PERAgentProviderInner>
);

export const usePERAgentContext = (): PERAgentContextType => {
  const ctx = useContext(PERAgentContext);
  if (!ctx) throw new Error('usePERAgentContext must be used within PERAgentProvider');
  return ctx;
};

export default PERAgentContext;
