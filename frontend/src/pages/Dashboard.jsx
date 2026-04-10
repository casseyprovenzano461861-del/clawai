/**
 * Dashboard — ClawAI 主仪表板（Cyberpunk 重建版）
 *
 * 布局：
 *   顶部全宽扫描输入条
 *   左列（1/3）：统计卡片 + 活动代理列表
 *   右列（2/3）：tabs → 概览 / P-E-R 控制台 / 扫描历史
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useScan } from '../context/ScanContext';
import {
  Target, Play, Square, Shield, Activity, AlertTriangle,
  CheckCircle, Cpu, Zap, Clock, RefreshCw, ChevronRight,
  BarChart3, Bug, Terminal, History, Wifi, WifiOff,
} from 'lucide-react';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
} from 'recharts';

import GlowCard    from '../components/shared/GlowCard';
import StatCard    from '../components/shared/StatCard';
import SectionHeader from '../components/shared/SectionHeader';
import PERPanel    from '../components/PER/PERPanel';
import ScanHistory from '../components/ScanHistory';
import { api }     from '../services/apiClient';
import attackService from '../services/attackService';

// ─── 严重程度颜色 ────────────────────────────────────────────────────────────
const SEV_COLOR = {
  critical: '#ef4444',
  high:     '#f97316',
  medium:   '#f59e0b',
  low:      '#3b82f6',
  info:     '#6b7280',
};

// ─── 标签页配置 ───────────────────────────────────────────────────────────────
const TABS = [
  { id: 'overview', label: '概览',      icon: BarChart3 },
  { id: 'per',      label: 'P-E-R 控制台', icon: Terminal },
  { id: 'history',  label: '扫描历史',  icon: History },
];

// ─── 活动代理卡片 ─────────────────────────────────────────────────────────────
const AgentCard = ({ agent }) => {
  const statusColor = {
    running:   'text-cyan-400',
    completed: 'text-emerald-400',
    error:     'text-red-400',
    idle:      'text-gray-500',
  }[agent.status] || 'text-gray-500';

  return (
    <GlowCard color="blue" padding="sm" className="flex items-center gap-3">
      <div className={`w-2 h-2 rounded-full shrink-0 ${
        agent.status === 'running' ? 'bg-cyan-400 animate-pulse' :
        agent.status === 'completed' ? 'bg-emerald-400' : 'bg-red-400'
      }`} />
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-200 truncate font-mono">{agent.target || agent.name}</p>
        <p className={`text-[11px] ${statusColor}`}>{agent.status}</p>
      </div>
      {agent.progress !== undefined && (
        <div className="text-xs text-gray-500 font-mono shrink-0">
          {Math.round(agent.progress * 100)}%
        </div>
      )}
    </GlowCard>
  );
};

// ─── 活动时间线条目 ───────────────────────────────────────────────────────────
const TimelineItem = ({ item }) => {
  const icon = {
    scan:    <Cpu size={12} className="text-cyan-400" />,
    finding: <Bug size={12} className="text-red-400" />,
    success: <CheckCircle size={12} className="text-emerald-400" />,
    error:   <AlertTriangle size={12} className="text-yellow-400" />,
  }[item.type] || <Activity size={12} className="text-gray-500" />;

  return (
    <div className="flex items-start gap-2.5 py-1.5 border-b border-gray-800/50 last:border-0">
      <div className="shrink-0 mt-0.5">{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-300 truncate">{item.message}</p>
        {item.target && (
          <p className="text-[11px] text-gray-600 font-mono">{item.target}</p>
        )}
      </div>
      <span className="text-[10px] text-gray-600 shrink-0 tabular-nums">
        {item.time || ''}
      </span>
    </div>
  );
};

// ─── 漏洞饼图 ─────────────────────────────────────────────────────────────────
const FindingsPieChart = ({ data }) => {
  if (!data || data.every(d => d.value === 0)) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-600 text-sm">
        暂无漏洞数据
      </div>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={160}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={45}
          outerRadius={70}
          paddingAngle={3}
          dataKey="value"
        >
          {data.map((entry, i) => (
            <Cell key={i} fill={SEV_COLOR[entry.name] || '#6b7280'} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: '#0a0e17', border: '1px solid rgba(0,212,255,0.2)', borderRadius: 8 }}
          labelStyle={{ color: '#e2e8f0' }}
          itemStyle={{ color: '#9ca3af' }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
};

// ─── 主组件 ───────────────────────────────────────────────────────────────────
const Dashboard = () => {
  const { startScan, scanHistory, scanStatus } = useScan();

  const [target,       setTarget]       = useState('');
  const [scanMode,     setScanMode]     = useState('full');
  const [loading,      setLoading]      = useState(false);
  const [perAutoStart, setPerAutoStart] = useState(false);
  const [connected,    setConnected]    = useState(false);
  const [activeTab,    setActiveTab]    = useState('overview');
  const [activeAgents, setActiveAgents] = useState([]);
  const [activity,     setActivity]     = useState([]);
  const [stats,        setStats]        = useState({
    total: 0, running: 0, completed: 0, findings: 0,
  });
  const [findings,     setFindings]     = useState({
    critical: 0, high: 0, medium: 0, low: 0, info: 0,
  });

  const pollRef = useRef(null);

  // ── 拉取后端数据 ────────────────────────────────────────────────────────────
  const fetchData = useCallback(async () => {
    try {
      const [healthRes, scansRes] = await Promise.allSettled([
        api.health.check(),
        api.scans?.list?.({ limit: 5 }),
      ]);

      if (healthRes.status === 'fulfilled') setConnected(true);

      if (scansRes.status === 'fulfilled' && scansRes.value?.data) {
        const scans = scansRes.value.data;
        const running   = scans.filter(s => s.status === 'running').length;
        const completed = scans.filter(s => s.status === 'completed').length;
        setStats(prev => ({ ...prev, total: scans.length, running, completed }));
        setActiveAgents(scans.filter(s => s.status === 'running').slice(0, 5).map(s => ({
          target: s.target, status: s.status, progress: s.progress,
        })));
      }
    } catch {
      setConnected(false);
    }
  }, []);

  // ── 本地扫描历史（从 ScanContext 同步）──────────────────────────────────────
  useEffect(() => {
    // 从历史统计发现分布
    const fc = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
    scanHistory.forEach(s => {
      if (s.vulnerabilities) {
        Object.entries(s.vulnerabilities).forEach(([k, v]) => {
          if (fc[k] !== undefined) fc[k] += (v || 0);
        });
      }
    });
    setFindings(fc);
    setStats(prev => ({
      ...prev,
      total: scanHistory.length,
      findings: Object.values(fc).reduce((a, b) => a + b, 0),
    }));
  }, [scanHistory]);

  // ── 轮询后端 ────────────────────────────────────────────────────────────────
  useEffect(() => {
    fetchData();
    pollRef.current = setInterval(fetchData, 10_000);
    return () => clearInterval(pollRef.current);
  }, [fetchData]);

  // ── 快速扫描（通过 ScanContext 驱动）──────────────────────────────────────
  const handleScan = useCallback(async () => {
    if (!target.trim() || loading) return;
    setLoading(true);
    setPerAutoStart(false); // 先重置，确保 effect 能触发
    setActiveTab('per');   // 自动切到 P-E-R 控制台
    setActivity(prev => [{
      type: 'scan',
      message: `启动扫描: ${target.trim()}`,
      target: target.trim(),
      time: new Date().toLocaleTimeString(),
    }, ...prev.slice(0, 49)]);
    try {
      setPerAutoStart(true); // 触发 PERPanel 自动启动
      await startScan(target.trim(), scanMode);
      setActivity(prev => [{
        type: 'success',
        message: `扫描完成: ${target.trim()}`,
        target: target.trim(),
        time: new Date().toLocaleTimeString(),
      }, ...prev.slice(0, 49)]);
    } catch (e) {
      setActivity(prev => [{
        type: 'error',
        message: `扫描失败: ${e.message}`,
        time: new Date().toLocaleTimeString(),
      }, ...prev.slice(0, 49)]);
    } finally {
      setLoading(false);
      setPerAutoStart(false);
    }
  }, [target, scanMode, loading, startScan]);

  const pieData = Object.entries(findings)
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name, value }));

  // ── 渲染 ────────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen px-4 py-6 max-w-screen-2xl mx-auto space-y-6">

      {/* ── 顶部扫描输入条 ── */}
      <GlowCard color="cyan" padding="md" className="relative overflow-hidden">
        {/* 扫描线装饰 */}
        <div className="scanlines absolute inset-0 pointer-events-none" />

        <div className="relative z-10 flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
          {/* 目标输入 */}
          <div className="flex-1 relative">
            <Target size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
            <input
              type="text"
              value={target}
              onChange={e => setTarget(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleScan()}
              placeholder="输入目标地址 · example.com · 192.168.1.0/24"
              disabled={loading}
              className="input-cyber w-full pl-9 pr-4 text-sm"
            />
          </div>

          {/* 模式选择 */}
          <select
            value={scanMode}
            onChange={e => setScanMode(e.target.value)}
            disabled={loading}
            className="input-cyber text-sm w-full sm:w-36"
          >
            <option value="full">完整测试</option>
            <option value="recon">仅侦察</option>
            <option value="vuln">漏洞扫描</option>
          </select>

          {/* 扫描按钮 */}
          <button
            onClick={handleScan}
            disabled={loading || scanStatus === 'scanning' || !target.trim()}
            className="btn-cyber flex items-center justify-center gap-2 whitespace-nowrap text-sm"
          >
            {(loading || scanStatus === 'scanning') ? (
              <><RefreshCw size={14} className="animate-spin" /> 扫描中</>
            ) : (
              <><Play size={14} /> 开始扫描</>
            )}
          </button>
        </div>

        {/* 连接状态指示 */}
        <div className="relative z-10 flex items-center gap-1.5 mt-2.5">
          {connected ? (
            <><Wifi size={11} className="text-emerald-400" /><span className="text-[11px] text-emerald-400">后端已连接</span></>
          ) : (
            <><WifiOff size={11} className="text-gray-600" /><span className="text-[11px] text-gray-600">后端未连接</span></>
          )}
        </div>
      </GlowCard>

      {/* ── 主体区域 ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* ── 左列 ── */}
        <div className="lg:col-span-1 space-y-4">

          {/* 统计卡片组 */}
          <div className="grid grid-cols-2 gap-3">
            <StatCard icon={Shield}        label="总扫描"   value={stats.total}     color="cyan" />
            <StatCard icon={Activity}      label="运行中"   value={stats.running}   color="blue" />
            <StatCard icon={CheckCircle}   label="已完成"   value={stats.completed} color="green" />
            <StatCard icon={AlertTriangle} label="漏洞总数" value={stats.findings}  color="red" />
          </div>

          {/* 活动代理 */}
          <GlowCard color="blue" padding="md">
            <SectionHeader
              title="活动代理"
              icon={Cpu}
              count={activeAgents.length}
            />
            {activeAgents.length === 0 ? (
              <p className="text-xs text-gray-600 text-center py-4">暂无运行中的代理</p>
            ) : (
              <div className="space-y-2">
                {activeAgents.map((a, i) => <AgentCard key={i} agent={a} />)}
              </div>
            )}
          </GlowCard>

          {/* 漏洞分布图（仅概览 tab 时显示） */}
          <GlowCard color="red" padding="md">
            <SectionHeader title="漏洞分布" icon={Bug} />
            <FindingsPieChart data={pieData} />
            {/* 图例 */}
            <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
              {Object.entries(findings).map(([name, val]) => (
                <div key={name} className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full" style={{ background: SEV_COLOR[name] }} />
                  <span className="text-[11px] text-gray-500 capitalize">{name}</span>
                  <span className="text-[11px] text-gray-400 font-mono">{val}</span>
                </div>
              ))}
            </div>
          </GlowCard>
        </div>

        {/* ── 右列（tabs） ── */}
        <div className="lg:col-span-2 flex flex-col gap-4">

          {/* Tab 导航 */}
          <div
            className="flex gap-1 p-1 rounded-xl"
            style={{ background: 'rgba(10,14,23,0.8)', border: '1px solid rgba(0,212,255,0.1)' }}
          >
            {TABS.map(tab => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={[
                    'flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                    active
                      ? 'bg-cyan-500/15 text-cyan-400 shadow-[0_0_12px_rgba(0,212,255,0.12)]'
                      : 'text-gray-500 hover:text-gray-300 hover:bg-white/4',
                  ].join(' ')}
                >
                  <Icon size={14} />
                  <span className="hidden sm:inline">{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Tab 内容 */}
          <div className="flex-1">

            {/* 概览 */}
            {activeTab === 'overview' && (
              <div className="space-y-4 animate-fade-in">
                {/* 最近活动时间线 */}
                <GlowCard color="cyan" padding="md">
                  <SectionHeader title="最近活动" icon={Clock} count={activity.length} />
                  {activity.length === 0 ? (
                    <div className="text-center py-8">
                      <Activity size={32} className="text-gray-700 mx-auto mb-3" />
                      <p className="text-sm text-gray-600">输入目标并开始扫描</p>
                      <p className="text-xs text-gray-700 mt-1">实时事件将显示在这里</p>
                    </div>
                  ) : (
                    <div className="space-y-0 max-h-72 overflow-y-auto">
                      {activity.map((item, i) => <TimelineItem key={i} item={item} />)}
                    </div>
                  )}
                </GlowCard>

                {/* 最近扫描列表 */}
                <GlowCard color="blue" padding="md">
                  <SectionHeader
                    title="最近扫描"
                    icon={History}
                    count={scanHistory.slice(0,5).length}
                    action={
                      scanHistory.length > 0 && (
                        <button
                          onClick={() => setActiveTab('history')}
                          className="flex items-center gap-1 text-xs text-cyan-500 hover:text-cyan-300 transition-colors"
                        >
                          查看全部 <ChevronRight size={12} />
                        </button>
                      )
                    }
                  />
                  {scanHistory.length === 0 ? (
                    <p className="text-xs text-gray-600 text-center py-4">暂无扫描历史</p>
                  ) : (
                    <div className="space-y-2">
                      {scanHistory.slice(0, 5).map((item, i) => (
                        <div
                          key={item.id || i}
                          className="flex items-center justify-between py-1.5 border-b border-gray-800/40 last:border-0"
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <Target size={12} className="text-gray-600 shrink-0" />
                            <span className="text-xs text-gray-300 font-mono truncate">{item.target}</span>
                          </div>
                          <span className={`text-[11px] px-2 py-0.5 rounded-full shrink-0 ml-2 ${
                            item.success ? 'bg-emerald-500/15 text-emerald-400' :
                            item.success === false ? 'bg-red-500/15 text-red-400' :
                            'bg-gray-700/40 text-gray-500'
                          }`}>
                            {item.success ? 'completed' : item.success === false ? 'error' : 'unknown'}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </GlowCard>
              </div>
            )}

            {/* P-E-R 控制台 */}
            {activeTab === 'per' && (
              <div className="animate-fade-in">
                <PERPanel
                  initialTarget={target}
                  autoStart={perAutoStart}
                  onSessionEnd={ev => {
                    setActivity(prev => [{
                      type: 'success',
                      message: `P-E-R 完成: ${ev.target || target}`,
                      time: new Date().toLocaleTimeString(),
                    }, ...prev.slice(0, 49)]);
                  }}
                />
              </div>
            )}

            {/* 扫描历史 */}
            {activeTab === 'history' && (
              <div className="animate-fade-in">
                <ScanHistory />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
