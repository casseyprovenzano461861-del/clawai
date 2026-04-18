/**
 * Dashboard — ClawAI 主仪表板（侧边栏版重构）
 *
 * 布局：顶部输入栏 + 下方两列（左固定统计 / 右 Tab 内容）
 * 配色：GitHub Dark 风格统一卡片，减少过度发光
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useScan } from '../context/ScanContext';
import { usePERAgentContext } from '../context/PERAgentContext';
import {
  Target, Play, Shield, Activity, AlertTriangle,
  CheckCircle, Cpu, Bug, Terminal, History, Search,
  Crosshair, ChevronRight, Clock, RefreshCw, BarChart3,
} from 'lucide-react';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
} from 'recharts';

import GlowCard      from '../components/shared/GlowCard';
import StatCard      from '../components/shared/StatCard';
import SectionHeader from '../components/shared/SectionHeader';
import PERPanel      from '../components/PER/PERPanel';
import ScanHistory   from '../components/ScanHistory';
import DiscoverPanel from '../components/discover/DiscoverPanel';

// ─── 常量 ─────────────────────────────────────────────────────────────────────
const SEV_COLOR = {
  critical: '#ef4444',
  high:     '#f97316',
  medium:   '#f59e0b',
  low:      '#3b82f6',
  info:     '#6b7280',
};
const SEV_LABEL = {
  critical: '严重', high: '高危', medium: '中危', low: '低危', info: '信息',
};
const TABS = [
  { id: 'overview', label: '概览',       icon: BarChart3 },
  { id: 'per',      label: 'P-E-R',      icon: Terminal },
  { id: 'history',  label: '扫描历史',   icon: History },
  { id: 'discover', label: '靶机发现',   icon: Search },
];

// ─── 子组件 ───────────────────────────────────────────────────────────────────

const AgentCard = ({ agent }) => {
  const progress = agent.progress !== undefined ? Math.round(agent.progress * 100) : null;
  return (
    <div className="flex items-center gap-3 py-2.5 px-3 rounded-lg bg-[#161b22] border border-white/[0.06]">
      <span
        className="w-2 h-2 rounded-full shrink-0"
        style={{
          background: agent.status === 'running' ? '#00d4ff' : agent.status === 'completed' ? '#22c55e' : '#ef4444',
          boxShadow: agent.status === 'running' ? '0 0 6px rgba(0,212,255,0.8)' : 'none',
          animation: agent.status === 'running' ? 'neon-pulse 1.5s ease-in-out infinite' : 'none',
        }}
      />
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-200 truncate font-mono">{agent.target || agent.name}</p>
        {agent.phase && <p className="text-[11px] text-cyan-500/70 mt-0.5">{agent.phase}</p>}
      </div>
      {progress !== null && (
        <div className="flex flex-col items-end gap-1 shrink-0">
          <span className="text-[11px] text-gray-400 font-mono tabular-nums">{progress}%</span>
          <div className="w-16 h-1 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{ width: `${progress}%`, background: 'linear-gradient(90deg,#00d4ff,#3b82f6)', transition: 'width 0.4s ease' }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

const TimelineItem = ({ item, index }) => {
  const iconMap = {
    scan:    <div className="w-5 h-5 rounded-full bg-cyan-500/15 flex items-center justify-center shrink-0"><Cpu size={10} className="text-cyan-400" /></div>,
    finding: <div className="w-5 h-5 rounded-full bg-red-500/15 flex items-center justify-center shrink-0"><Bug size={10} className="text-red-400" /></div>,
    success: <div className="w-5 h-5 rounded-full bg-emerald-500/15 flex items-center justify-center shrink-0"><CheckCircle size={10} className="text-emerald-400" /></div>,
    error:   <div className="w-5 h-5 rounded-full bg-yellow-500/15 flex items-center justify-center shrink-0"><AlertTriangle size={10} className="text-yellow-400" /></div>,
  };
  return (
    <div
      className="flex items-start gap-3 py-2.5 border-b border-gray-800/40 last:border-0"
      style={{ animationDelay: `${index * 40}ms` }}
    >
      {iconMap[item.type] || <div className="w-5 h-5 rounded-full bg-gray-700/40 flex items-center justify-center shrink-0"><Activity size={10} className="text-gray-500" /></div>}
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-300">{item.message}</p>
        {item.target && <p className="text-[11px] text-gray-600 font-mono mt-0.5 truncate">{item.target}</p>}
      </div>
      <span className="text-[10px] text-gray-600 shrink-0 tabular-nums font-mono">{item.time}</span>
    </div>
  );
};

const DonutCenter = ({ cx, cy, total }) => (
  <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central">
    <tspan x={cx} dy="-0.3em" fontSize="22" fontWeight="700" fill="#e2e8f0">{total}</tspan>
    <tspan x={cx} dy="1.4em" fontSize="10" fill="#6b7280">漏洞</tspan>
  </text>
);

const FindingsPieChart = ({ data, total }) => {
  if (!data || data.every(d => d.value === 0)) {
    return (
      <div className="flex flex-col items-center justify-center h-32 gap-2">
        <Bug size={24} className="text-gray-700" />
        <p className="text-xs text-gray-600">暂无漏洞数据</p>
      </div>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={144}>
      <PieChart>
        <Pie data={data} cx="50%" cy="50%" innerRadius={40} outerRadius={62} paddingAngle={2}
          dataKey="value" startAngle={90} endAngle={-270}>
          {data.map((entry, i) => (
            <Cell key={i} fill={SEV_COLOR[entry.name] || '#6b7280'} stroke="transparent" />
          ))}
        </Pie>
        <DonutCenter cx="50%" cy="50%" total={total} />
        <Tooltip
          contentStyle={{ background: '#0d1117', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
          formatter={(val, name) => [val, SEV_LABEL[name] || name]}
        />
      </PieChart>
    </ResponsiveContainer>
  );
};

const SeverityBars = ({ findings, total }) => (
  <div className="space-y-1.5 mt-2">
    {Object.entries(findings).filter(([, v]) => v > 0).map(([key, val]) => (
      <div key={key} className="flex items-center gap-2">
        <span className="text-[11px] text-gray-500 w-9 text-right shrink-0">{SEV_LABEL[key]}</span>
        <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: total > 0 ? `${(val / total) * 100}%` : '0%', background: SEV_COLOR[key] }}
          />
        </div>
        <span className="text-[11px] font-mono tabular-nums text-gray-400 w-5 shrink-0">{val}</span>
      </div>
    ))}
  </div>
);

const ScanRow = ({ item, index }) => {
  const totalFindings = item.findings?.length ||
    (item.vulnerabilities ? Object.values(item.vulnerabilities).reduce((a, b) => a + (b || 0), 0) : 0);
  return (
    <div
      className="flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-white/[0.03] transition-colors"
      style={{ animationDelay: `${index * 40}ms` }}
    >
      <Crosshair size={11} className="text-gray-700 shrink-0" />
      <span className="text-xs text-gray-300 font-mono flex-1 truncate">{item.target}</span>
      {totalFindings > 0 && (
        <span className="text-[11px] px-1.5 py-0.5 rounded badge-red shrink-0">{totalFindings}</span>
      )}
      <span className={`text-[11px] px-2 py-0.5 rounded-full shrink-0 ${
        item.success ? 'badge-green' : item.success === false ? 'badge-red' : 'bg-gray-800/60 text-gray-500'
      }`}>
        {item.success ? '完成' : item.success === false ? '失败' : '—'}
      </span>
    </div>
  );
};

const EmptyGuide = () => (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <div className="w-14 h-14 rounded-xl flex items-center justify-center mb-4 bg-cyan-500/8 border border-cyan-500/20">
      <Target size={26} className="text-cyan-400" style={{ filter: 'drop-shadow(0 0 8px rgba(0,212,255,0.5))' }} />
    </div>
    <h3 className="text-sm font-semibold text-gray-200 mb-1.5">准备开始渗透测试</h3>
    <p className="text-xs text-gray-500 max-w-xs leading-relaxed">在上方输入框填入目标地址，AI 将自动规划并执行完整的渗透测试流程</p>
    <div className="flex flex-col gap-1.5 text-xs text-gray-600 mt-4">
      {['支持 IP / 域名 / CIDR', '自动调用 30+ 安全工具', '实时生成渗透报告'].map(t => (
        <div key={t} className="flex items-center gap-2">
          <CheckCircle size={11} className="text-emerald-600" />
          <span>{t}</span>
        </div>
      ))}
    </div>
  </div>
);

// ─── 主组件 ───────────────────────────────────────────────────────────────────
const Dashboard = () => {
  const { scanHistory } = useScan();
  const { isRunning, tasks, findings: perFindings, phase, status: wsStatus, iteration, maxIterations } = usePERAgentContext();

  const [target,       setTarget]       = useState('');
  const [scanMode,     setScanMode]     = useState('full');
  const [loading,      setLoading]      = useState(false);
  const [perAutoStart, setPerAutoStart] = useState(false);
  const [activeTab,    setActiveTab]    = useState('overview');
  const [activeAgents, setActiveAgents] = useState([]);
  const [activity,     setActivity]     = useState([]);
  const [stats,        setStats]        = useState({ total: 0, running: 0, completed: 0, findings: 0 });
  const [findings,     setFindings]     = useState({ critical: 0, high: 0, medium: 0, low: 0, info: 0 });

  const connected = wsStatus === 'connected' || wsStatus === 'running' || wsStatus === 'completed';

  useEffect(() => {
    const fc = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
    let completed = 0;
    scanHistory.forEach(s => {
      if (s.success) completed++;
      (s.findings || []).forEach(f => {
        if (f.type === 'open_ports') return;
        const sev = f.severity || 'info';
        if (fc[sev] !== undefined) fc[sev]++;
      });
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
      completed,
      findings: Object.values(fc).reduce((a, b) => a + b, 0),
    }));
  }, [scanHistory]);

  useEffect(() => {
    const currentTarget = sessionStorage.getItem('per_current_target') || '';
    if (isRunning && currentTarget) {
      setActiveAgents([{
        target: currentTarget,
        status: 'running',
        progress: tasks.length > 0
          ? tasks.filter(t => t.status === 'completed').length / tasks.length
          : undefined,
        phase,
      }]);
      setStats(prev => ({ ...prev, running: 1 }));
    } else if (!isRunning) {
      setActiveAgents([]);
      setStats(prev => ({ ...prev, running: 0 }));
    }
  }, [isRunning, tasks, phase]);

  const handleSessionEnd = useCallback((ev) => {
    const resolvedTarget = ev?.target || target || sessionStorage.getItem('per_current_target') || '';
    setActivity(prev => [{ type: 'success', message: `P-E-R 完成: ${resolvedTarget}`, time: new Date().toLocaleTimeString() }, ...prev.slice(0, 49)]);
    // 扫描完成后重置 autoStart，防止 re-render 重新触发扫描覆盖报告
    setPerAutoStart(false);
  }, [target]);

  const handleScan = useCallback((overrideTarget) => {
    const t = (overrideTarget ?? target).trim();
    if (!t) { document.querySelector('.scan-target-input')?.focus(); return; }
    if (loading) return;
    setLoading(true);
    setActivity(prev => [{ type: 'scan', message: `启动扫描: ${t}`, target: t, time: new Date().toLocaleTimeString() }, ...prev.slice(0, 49)]);
    sessionStorage.setItem('per_current_target', t);
    sessionStorage.setItem('per_scan_mode', scanMode);
    setPerAutoStart(false);
    setTimeout(() => {
      setActiveTab('per');
      setPerAutoStart(true);
      setLoading(false);
    }, 50);
  }, [target, scanMode, loading]);

  const pieData = useMemo(
    () => Object.entries(findings).filter(([, v]) => v > 0).map(([name, value]) => ({ name, value })),
    [findings],
  );
  const totalFindings = useMemo(() => Object.values(findings).reduce((a, b) => a + b, 0), [findings]);

  // ── render ──
  return (
    <div className="flex flex-col h-full min-h-screen p-5 gap-5 max-w-screen-2xl mx-auto">

      {/* ── 顶部扫描输入条 ── */}
      <div
        className="rounded-xl p-px"
        style={{ background: 'linear-gradient(135deg, rgba(0,212,255,0.25), rgba(139,92,246,0.15), rgba(0,212,255,0.08))' }}
      >
        <div className="rounded-xl bg-[#0d1117] px-4 py-3.5">
          <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
            <div className="flex-1 relative">
              <Target size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-cyan-500/40 pointer-events-none" />
              <input
                type="text"
                value={target}
                onChange={e => setTarget(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleScan()}
                placeholder="输入目标 · example.com · 192.168.1.1 · 10.0.0.0/24"
                disabled={loading}
                className="input-cyber w-full pl-9 pr-4 text-sm h-9 scan-target-input"
                autoFocus
              />
            </div>
            <select
              value={scanMode}
              onChange={e => setScanMode(e.target.value)}
              disabled={loading}
              className="input-cyber text-sm h-9 w-full sm:w-36 shrink-0"
            >
              <option value="full">完整测试</option>
              <option value="recon">仅侦察</option>
              <option value="vuln">漏洞扫描</option>
            </select>
            <button
              onClick={() => handleScan()}
              disabled={loading}
              className={`btn-cyber flex items-center justify-center gap-2 whitespace-nowrap text-sm h-9 px-5 shrink-0 ${!target.trim() ? 'opacity-50' : ''}`}
            >
              {loading
                ? <><RefreshCw size={13} className="animate-spin" />扫描中</>
                : <><Play size={13} />开始扫描</>
              }
            </button>
          </div>

          {/* 状态行 */}
          <div className="flex items-center justify-between mt-2.5 text-[11px]">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5">
                <span
                  className="w-1.5 h-1.5 rounded-full"
                  style={{ background: connected ? '#22c55e' : '#4b5563', boxShadow: connected ? '0 0 5px rgba(34,197,94,0.7)' : 'none' }}
                />
                <span className={connected ? 'text-emerald-400' : 'text-gray-600'}>
                  {connected ? '后端已连接' : '后端未连接'}
                </span>
              </div>
              {isRunning && (
                <div className="flex items-center gap-1.5 text-yellow-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
                  迭代 {iteration}/{maxIterations} · {phase}
                  {perFindings.length > 0 && <span className="text-red-400 ml-1">{perFindings.length} 发现</span>}
                </div>
              )}
            </div>
            {scanHistory.length > 0 && (
              <button
                onClick={() => setTarget(scanHistory[0].target)}
                className="flex items-center gap-1 text-gray-600 hover:text-gray-400 transition-colors"
                title="填入最近目标"
              >
                <History size={10} />
                <span className="font-mono truncate max-w-[120px]">{scanHistory[0].target}</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ── 主体双列 ── */}
      <div className="flex flex-1 gap-5 min-h-0 lg:flex-row flex-col">

        {/* ── 左列（统计区，固定宽度） ── */}
        <div className="lg:w-[280px] xl:w-[300px] shrink-0 flex flex-col gap-4">

          {/* 统计卡片 */}
          <div className="grid grid-cols-2 gap-3">
            <StatCard icon={Shield}        label="总扫描"   value={stats.total}     color="cyan"  animate="animate-slide-up-delay-1" />
            <StatCard icon={Activity}      label="运行中"   value={stats.running}   color="blue"  animate="animate-slide-up-delay-1" />
            <StatCard icon={CheckCircle}   label="已完成"   value={stats.completed} color="green" animate="animate-slide-up-delay-2" />
            <StatCard icon={AlertTriangle} label="漏洞总数" value={stats.findings}  color="red"   animate="animate-slide-up-delay-2" />
          </div>

          {/* 活动代理 */}
          <div
            className="rounded-xl border p-4"
            style={{ background: '#0d1117', borderColor: 'rgba(255,255,255,0.07)' }}
          >
            <SectionHeader title="活动代理" icon={Cpu} count={activeAgents.length} />
            {activeAgents.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-6 gap-2">
                <Cpu size={20} className="text-gray-700" />
                <p className="text-xs text-gray-600">暂无运行代理</p>
              </div>
            ) : (
              <div className="space-y-2 mt-3">
                {activeAgents.map((a, i) => <AgentCard key={i} agent={a} />)}
              </div>
            )}
          </div>

          {/* 漏洞分布 */}
          <div
            className="rounded-xl border p-4"
            style={{ background: '#0d1117', borderColor: 'rgba(255,255,255,0.07)' }}
          >
            <SectionHeader title="漏洞分布" icon={Bug} count={totalFindings > 0 ? totalFindings : undefined} />
            <FindingsPieChart data={pieData} total={totalFindings} />
            {totalFindings > 0 && <SeverityBars findings={findings} total={totalFindings} />}
          </div>
        </div>

        {/* ── 右列（Tab 区，flex-1） ── */}
        <div className="flex-1 min-w-0 flex flex-col gap-3">

          {/* Tab 导航 */}
          <div
            className="flex gap-1 p-1 rounded-xl shrink-0"
            style={{ background: '#0d1117', border: '1px solid rgba(255,255,255,0.07)' }}
          >
            {TABS.map(tab => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={[
                    'relative flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium',
                    'transition-all duration-200',
                    active
                      ? 'text-cyan-400 bg-cyan-500/10'
                      : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.04]',
                  ].join(' ')}
                >
                  <Icon size={13} className={active ? 'drop-shadow-[0_0_4px_rgba(0,212,255,0.8)]' : ''} />
                  <span className="hidden sm:inline">{tab.label}</span>
                  {active && (
                    <span
                      className="absolute bottom-0 left-3 right-3 h-px rounded-full"
                      style={{ background: 'linear-gradient(90deg,transparent,#00d4ff,transparent)' }}
                    />
                  )}
                </button>
              );
            })}
          </div>

          {/* Tab 内容 */}
          <div className="flex-1 min-h-0">

            {activeTab === 'overview' && (
              <div className="space-y-4 animate-fade-in">
                {activity.length === 0 && scanHistory.length === 0 ? (
                  <div className="rounded-xl border p-4" style={{ background: '#0d1117', borderColor: 'rgba(255,255,255,0.07)' }}>
                    <EmptyGuide />
                  </div>
                ) : (
                  <>
                    {activity.length > 0 && (
                      <div className="rounded-xl border p-4" style={{ background: '#0d1117', borderColor: 'rgba(255,255,255,0.07)' }}>
                        <SectionHeader title="最近活动" icon={Clock} count={activity.length} />
                        <div className="mt-2 max-h-52 overflow-y-auto pr-1">
                          {activity.slice(0, 20).map((item, i) => <TimelineItem key={i} item={item} index={i} />)}
                        </div>
                      </div>
                    )}
                    <div className="rounded-xl border p-4" style={{ background: '#0d1117', borderColor: 'rgba(255,255,255,0.07)' }}>
                      <SectionHeader
                        title="最近扫描"
                        icon={History}
                        count={scanHistory.length}
                        action={
                          scanHistory.length > 5 && (
                            <button onClick={() => setActiveTab('history')} className="flex items-center gap-1 text-xs text-cyan-500 hover:text-cyan-300 transition-colors">
                              查看全部 <ChevronRight size={11} />
                            </button>
                          )
                        }
                      />
                      <div className="mt-2 space-y-0.5">
                        {scanHistory.slice(0, 6).map((item, i) => <ScanRow key={item.id || i} item={item} index={i} />)}
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}

            {activeTab === 'per' && (
              <div className="animate-fade-in">
                <PERPanel
                  initialTarget={target}
                  initialMode={scanMode}
                  autoStart={perAutoStart}
                  onSessionEnd={handleSessionEnd}
                />
              </div>
            )}

            {activeTab === 'history' && (
              <div className="animate-fade-in">
                <ScanHistory />
              </div>
            )}

            {activeTab === 'discover' && (
              <div className="animate-fade-in rounded-xl border p-4" style={{ background: '#0d1117', borderColor: 'rgba(255,255,255,0.07)' }}>
                <SectionHeader title="靶机发现" icon={Search} />
                <div className="mt-4">
                  <DiscoverPanel onStartScan={(ip) => { setTarget(ip); handleScan(ip); }} />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
