/**
 * Reports — 报告管理页（左列表 + 右预览双栏布局）
 * 综合改版：专业渗透测试报告风格 + 可视化仪表板
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  FileText, Target, Download, Trash2, Plus, Eye,
  CheckCircle, XCircle, Clock, Loader, AlertTriangle,
  Shield, ChevronDown, ChevronRight, RefreshCw, Search,
  AlertCircle, Info, Activity, Terminal, Bug, Lock,
  TrendingUp, Zap, Globe, Server, Flag, GitBranch,
} from 'lucide-react';
import { useScan } from '../context/ScanContext';
import scanHistoryService from '../services/scanHistoryService';
import apiClient from '../services/apiClient';

// ─── 常量 ─────────────────────────────────────────────────────────────────────
const SEV_COLOR = {
  critical: '#ef4444',
  high:     '#f97316',
  medium:   '#f59e0b',
  low:      '#3b82f6',
  info:     '#6b7280',
};
const SEV_BG = {
  critical: 'rgba(239,68,68,0.08)',
  high:     'rgba(249,115,22,0.08)',
  medium:   'rgba(245,158,11,0.08)',
  low:      'rgba(59,130,246,0.08)',
  info:     'rgba(107,114,128,0.08)',
};
const SEV_ORDER  = ['critical', 'high', 'medium', 'low', 'info'];
const SEV_LABEL  = { critical: '严重', high: '高危', medium: '中危', low: '低危', info: '信息' };
const SEV_SCORE  = { critical: 9, high: 7, medium: 5, low: 3, info: 1 };

const fmtDate = (iso) => {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  } catch { return String(iso).slice(0, 16); }
};

const fmtDateFull = (iso) => {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch { return String(iso); }
};

// ─── 风险评分计算 ─────────────────────────────────────────────────────────────
const calcRiskScore = (vulns) => {
  if (!vulns.length) return 0;
  const topSev = SEV_ORDER.find(s => vulns.some(f => f.severity === s));
  if (!topSev) return 0;
  const baseScore = SEV_SCORE[topSev] || 0;
  const critCount = vulns.filter(f => f.severity === 'critical').length;
  const highCount = vulns.filter(f => f.severity === 'high').length;
  const bonus = Math.min(critCount * 0.5 + highCount * 0.2, 1.0);
  return Math.min(Math.round((baseScore + bonus) * 10), 100);
};

const riskLevel = (score) => {
  if (score >= 90) return { label: 'CRITICAL', color: '#ef4444' };
  if (score >= 70) return { label: 'HIGH',     color: '#f97316' };
  if (score >= 50) return { label: 'MEDIUM',   color: '#f59e0b' };
  if (score >= 20) return { label: 'LOW',      color: '#3b82f6' };
  return             { label: 'NONE',      color: '#6b7280' };
};

// ─── 生成报告弹窗 ─────────────────────────────────────────────────────────────
const GenerateModal = ({ onClose, onGenerated }) => {
  const [form, setForm] = useState({
    target: '', format: 'html', template: 'standard',
    testerName: '', clientName: '', startDate: '', endDate: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.target.trim()) { setError('请输入目标地址'); return; }
    setLoading(true); setError('');
    try {
      await apiClient.reports.generate({
        title:           `安全评估报告 - ${form.target}`,
        target:          form.target.trim(),
        format:          form.format,
        template:        form.template,
        tester_name:     form.testerName.trim() || undefined,
        client_name:     form.clientName.trim() || undefined,
        test_start_date: form.startDate || undefined,
        test_end_date:   form.endDate   || undefined,
        parameters:      {},
      });
      onGenerated();
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail?.message || err?.message || '生成失败');
    } finally {
      setLoading(false);
    }
  };

  const inputCls = 'w-full bg-[#060910] border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-cyan-500 outline-none transition-colors';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-[#0d1117] border border-cyan-500/30 rounded-2xl p-6 w-full max-w-lg shadow-2xl">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Plus size={15} className="text-cyan-400" /> 生成新报告
        </h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">目标地址 <span className="text-red-400">*</span></label>
            <input value={form.target} onChange={set('target')} placeholder="example.com · 192.168.1.1" className={inputCls} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">导出格式</label>
              <select value={form.format} onChange={set('format')} className={inputCls}>
                <option value="html">HTML（推荐）</option>
                <option value="markdown">Markdown</option>
                <option value="json">JSON</option>
                <option value="pdf">PDF</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">模板</label>
              <select value={form.template} onChange={set('template')} className={inputCls}>
                <option value="standard">标准</option>
                <option value="executive">执行摘要</option>
                <option value="technical">技术详情</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">测试人员</label>
              <input value={form.testerName} onChange={set('testerName')} placeholder="姓名或团队" className={inputCls} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">委托方</label>
              <input value={form.clientName} onChange={set('clientName')} placeholder="客户名称" className={inputCls} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">开始日期</label>
              <input type="date" value={form.startDate} onChange={set('startDate')} className={inputCls} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">结束日期</label>
              <input type="date" value={form.endDate} onChange={set('endDate')} className={inputCls} />
            </div>
          </div>
          {error && <p className="text-xs text-red-400">{error}</p>}
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white border border-gray-700 rounded-lg transition-colors">
              取消
            </button>
            <button type="submit" disabled={loading}
              className="px-4 py-2 text-sm text-white bg-cyan-600 hover:bg-cyan-500 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2">
              {loading && <Loader size={13} className="animate-spin" />}
              {loading ? '生成中...' : '生成'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ─── 严重等级标签 ─────────────────────────────────────────────────────────────
const SevBadge = ({ sev, size = 'sm' }) => {
  const color = SEV_COLOR[sev] || SEV_COLOR.info;
  const label = SEV_LABEL[sev] || sev;
  const px    = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';
  return (
    <span className={`inline-flex items-center rounded font-bold font-mono tracking-wide ${px}`}
      style={{ color, background: color + '1a', border: `1px solid ${color}33` }}>
      {label}
    </span>
  );
};

// ─── SVG 环形风险评分 ─────────────────────────────────────────────────────────
const RiskGauge = ({ score }) => {
  const level  = riskLevel(score);
  const R      = 36;
  const cx     = 44;
  const cy     = 44;
  const stroke = 6;
  const circ   = 2 * Math.PI * R;
  const dash   = (score / 100) * circ;

  return (
    <div className="relative flex items-center justify-center" style={{ width: 88, height: 88 }}>
      <svg width={88} height={88} style={{ transform: 'rotate(-90deg)', position: 'absolute', top: 0, left: 0 }}>
        <circle cx={cx} cy={cy} r={R} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth={stroke} />
        <circle cx={cx} cy={cy} r={R} fill="none" stroke={level.color} strokeWidth={stroke}
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 4px ${level.color}66)`, transition: 'stroke-dasharray 0.6s ease' }} />
      </svg>
      <div className="relative flex flex-col items-center justify-center z-10">
        <span className="text-xl font-black font-mono leading-none" style={{ color: level.color }}>{score}</span>
        <span className="text-[9px] font-bold tracking-widest" style={{ color: level.color + 'cc' }}>{level.label}</span>
      </div>
    </div>
  );
};

// ─── 漏洞分布横条图 ───────────────────────────────────────────────────────────
const VulnDistBar = ({ vulns }) => {
  const counts = SEV_ORDER.filter(s => s !== 'info').map(sev => ({
    sev, label: SEV_LABEL[sev], count: vulns.filter(v => v.severity === sev).length,
    color: SEV_COLOR[sev],
  })).filter(x => x.count > 0);

  if (!counts.length) return null;
  const max = Math.max(...counts.map(x => x.count), 1);

  return (
    <div className="space-y-1.5">
      {counts.map(({ sev, label, count, color }) => (
        <div key={sev} className="flex items-center gap-2">
          <span className="text-[10px] w-8 text-right font-mono shrink-0" style={{ color }}>{label}</span>
          <div className="flex-1 h-1.5 rounded-full" style={{ background: 'rgba(255,255,255,0.05)' }}>
            <div className="h-full rounded-full transition-all duration-700"
              style={{ width: `${(count / max) * 100}%`, background: color, boxShadow: `0 0 6px ${color}66` }} />
          </div>
          <span className="text-[10px] font-mono w-4 shrink-0" style={{ color }}>{count}</span>
        </div>
      ))}
    </div>
  );
};

// ─── 漏洞详情卡片 ─────────────────────────────────────────────────────────────
const VulnCard = ({ finding, idx }) => {
  const [open, setOpen] = useState(idx < 3); // 前3个默认展开
  const sev  = finding.severity || 'info';
  const color = SEV_COLOR[sev];

  const typeIconMap = {
    sql_injection:     <Bug size={12} />,
    xss:               <Zap size={12} />,
    rce:               <Terminal size={12} />,
    lfi:               <FileText size={12} />,
    auth_bypass:       <Lock size={12} />,
    info_disclosure:   <Info size={12} />,
    open_redirect:     <Globe size={12} />,
  };
  const typeIcon = typeIconMap[finding.type] || <AlertCircle size={12} />;

  return (
    <div className="rounded-xl overflow-hidden transition-all"
      style={{ background: SEV_BG[sev], border: `1px solid ${color}28` }}>
      <button
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-white/[0.02] transition-colors"
        onClick={() => setOpen(o => !o)}
      >
        <span style={{ color }} className="shrink-0">{typeIcon}</span>
        <span className="flex-1 text-sm font-medium text-gray-100 truncate">
          {finding.title || finding.type || '未知漏洞'}
        </span>
        <SevBadge sev={sev} />
        {finding.cve && (
          <span className="text-[10px] font-mono text-gray-500 border border-gray-700/50 px-1.5 py-0.5 rounded shrink-0">
            {finding.cve}
          </span>
        )}
        {open
          ? <ChevronDown size={13} className="text-gray-500 shrink-0" />
          : <ChevronRight size={13} className="text-gray-500 shrink-0" />}
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3">
          {(finding.detail || finding.description) && (
            <div>
              <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1">描述</p>
              <p className="text-xs text-gray-300 leading-relaxed">{finding.detail || finding.description}</p>
            </div>
          )}
          {finding.url && (
            <div>
              <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1">影响路径</p>
              <code className="text-[11px] text-cyan-400 bg-black/30 px-2 py-1 rounded block font-mono break-all">{finding.url}</code>
            </div>
          )}
          {finding.payload && (
            <div>
              <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1">Payload</p>
              <code className="text-[11px] text-yellow-400 bg-black/30 px-2 py-1 rounded block font-mono break-all">{finding.payload}</code>
            </div>
          )}
          {finding.recommendation && (
            <div className="flex gap-2 p-2.5 rounded-lg bg-emerald-500/5 border border-emerald-500/15">
              <CheckCircle size={12} className="text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-[11px] font-semibold text-emerald-400 mb-0.5">修复建议</p>
                <p className="text-[11px] text-gray-400 leading-relaxed">{finding.recommendation}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── 端口卡片 ─────────────────────────────────────────────────────────────────
const PortBadge = ({ port }) => {
  const num     = typeof port === 'object' ? port.port     : port;
  const service = typeof port === 'object' ? port.service  : '';
  const state   = typeof port === 'object' ? port.state    : 'open';
  const isOpen  = !state || state === 'open';

  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-mono"
      style={{ background: 'rgba(59,130,246,0.07)', border: '1px solid rgba(59,130,246,0.2)' }}>
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${isOpen ? 'bg-emerald-400' : 'bg-gray-600'}`} />
      <span className="text-blue-300 font-bold">{num}</span>
      {service && <span className="text-gray-500">/ {service}</span>}
    </div>
  );
};

// ─── 任务时间线 ───────────────────────────────────────────────────────────────
const TaskTimeline = ({ tasks }) => {
  return (
    <div className="space-y-1.5">
      {tasks.map((t, i) => {
        const name   = typeof t === 'string' ? t : (t.name || t.type || `任务 ${i + 1}`);
        const status = typeof t === 'object' ? t.status : 'completed';
        const desc   = typeof t === 'object' ? (t.description || t.result) : null;

        const statusConfig = {
          completed: { icon: <CheckCircle size={11} />, color: '#34d399', bg: 'rgba(52,211,153,0.08)' },
          failed:    { icon: <XCircle size={11} />,     color: '#f87171', bg: 'rgba(248,113,113,0.08)' },
          running:   { icon: <Loader size={11} className="animate-spin" />, color: '#facc15', bg: 'rgba(250,204,21,0.08)' },
        }[status] || { icon: <Clock size={11} />, color: '#6b7280', bg: 'rgba(107,114,128,0.08)' };

        return (
          <div key={i} className="flex gap-3 items-start p-2.5 rounded-lg"
            style={{ background: statusConfig.bg, border: `1px solid ${statusConfig.color}22` }}>
            <span className="mt-0.5 shrink-0" style={{ color: statusConfig.color }}>{statusConfig.icon}</span>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-gray-200 font-mono truncate">{name}</p>
              {desc && <p className="text-[11px] text-gray-500 mt-0.5 leading-relaxed line-clamp-2">{String(desc).slice(0, 200)}</p>}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ─── 折叠区块 ─────────────────────────────────────────────────────────────────
const Section = ({ title, icon, count, defaultOpen = true, accent = '#06b6d4', children }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-xl overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.06)' }}>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-2.5 px-4 py-3 text-left transition-colors hover:bg-white/[0.02]"
        style={{ background: 'rgba(255,255,255,0.02)' }}
      >
        <span style={{ color: accent }}>{icon}</span>
        <span className="text-xs font-semibold text-gray-200 tracking-wide">{title}</span>
        {count != null && count > 0 && (
          <span className="ml-1 text-[10px] font-mono px-1.5 py-0.5 rounded"
            style={{ color: accent, background: accent + '1a', border: `1px solid ${accent}33` }}>
            {count}
          </span>
        )}
        <span className="ml-auto text-gray-600">
          {open ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
        </span>
      </button>
      {open && <div className="p-4">{children}</div>}
    </div>
  );
};

// ─── 右侧：扫描历史详情面板（重新设计）────────────────────────────────────────
const ScanDetailPanel = ({ record, onDelete }) => {
  // 兼容新格式（findings[]）和旧格式（attack_chain）
  const rawFindings = record.findings || [];
  const attackChain = record.result?.attack_chain || record.attack_chain || [];

  // 从旧格式 attack_chain 中构建 findings（如果新格式为空）
  const findings = rawFindings.length > 0
    ? rawFindings
    : attackChain.map(step => ({
        type:           step.tool || step.type || 'unknown',
        title:          step.name || step.action || step.tool || '扫描步骤',
        severity:       step.severity || (step.success ? 'medium' : 'info'),
        detail:         step.result || step.description || step.output || '',
        url:            step.target || step.url || '',
        recommendation: step.recommendation || '',
      }));

  const vulns    = findings.filter(f => f.type !== 'open_ports');
  const ports    = findings.filter(f => f.type === 'open_ports').flatMap(f => f.ports || []);
  const tasks    = record.tasks || [];

  // 旧格式 target_analysis 作为 AI 摘要后备
  const aiReport = record.report || record.result?.target_analysis
    || (record.result?.rule_engine_decision ? `决策：${record.result.rule_engine_decision}` : null);

  const score    = useMemo(() => calcRiskScore(vulns), [vulns]);
  const level    = riskLevel(score);

  // 漏洞统计
  const sevCounts = SEV_ORDER.reduce((acc, s) => {
    acc[s] = vulns.filter(f => f.severity === s).length;
    return acc;
  }, {});

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = `scan_${record.target}_${record.id || Date.now()}.json`;
    a.click(); URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">

      {/* ── 顶部 Header ── */}
      <div className="shrink-0 px-6 py-4 border-b" style={{ borderColor: 'rgba(255,255,255,0.07)', background: '#0a0e17' }}>
        <div className="flex items-start justify-between gap-4 mb-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Globe size={14} className="text-cyan-400 shrink-0" />
              <h2 className="text-base font-mono font-bold text-white truncate">{record.target}</h2>
              <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium shrink-0 ${
                record.success ? 'text-emerald-400 bg-emerald-400/10 border border-emerald-400/20'
                               : 'text-red-400 bg-red-400/10 border border-red-400/20'}`}>
                {record.success ? '渗透成功' : record.success === false ? '未突破' : '已分析'}
              </span>
            </div>
            <p className="text-xs text-gray-500 ml-6">{fmtDateFull(record.timestamp)}</p>
          </div>
          <div className="flex gap-2 shrink-0">
            <button onClick={exportJSON}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-400 border border-gray-700/50 rounded-lg hover:text-cyan-400 hover:border-cyan-500/40 hover:bg-cyan-500/5 transition-all">
              <Download size={12} /> JSON
            </button>
            <button onClick={() => onDelete(record.id)}
              className="p-1.5 text-gray-600 hover:text-red-400 hover:bg-red-500/10 rounded-lg border border-transparent hover:border-red-500/20 transition-all">
              <Trash2 size={13} />
            </button>
          </div>
        </div>

        {/* 统计概览行 */}
        <div className="flex items-center gap-0 rounded-xl overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.06)' }}>
          {/* 风险评分 */}
          <div className="flex items-center gap-3 px-4 py-3 shrink-0" style={{ background: 'rgba(255,255,255,0.02)' }}>
            <div className="relative" style={{ width: 88, height: 88 }}>
              <RiskGauge score={score} />
            </div>
            <div>
              <p className="text-[11px] text-gray-500 mb-0.5">综合风险</p>
              <p className="text-lg font-black font-mono" style={{ color: level.color }}>{level.label}</p>
              <p className="text-[10px] text-gray-600">评分 {score}/100</p>
            </div>
          </div>

          {/* 分隔 */}
          <div className="w-px self-stretch" style={{ background: 'rgba(255,255,255,0.06)' }} />

          {/* 漏洞分布 */}
          <div className="flex-1 px-4 py-3">
            <p className="text-[11px] text-gray-500 mb-2">漏洞分布</p>
            {vulns.length > 0 ? (
              <VulnDistBar vulns={vulns} />
            ) : (
              <p className="text-xs text-gray-600">无漏洞发现</p>
            )}
          </div>

          {/* 分隔 */}
          <div className="w-px self-stretch" style={{ background: 'rgba(255,255,255,0.06)' }} />

          {/* 关键数字 */}
          <div className="px-4 py-3 shrink-0 space-y-2">
            {[
              { label: '漏洞', value: vulns.length,  color: vulns.length  ? '#f87171' : '#6b7280' },
              { label: '端口', value: ports.length,  color: ports.length  ? '#60a5fa' : '#6b7280' },
              { label: '任务', value: tasks.length,  color: tasks.length  ? '#a78bfa' : '#6b7280' },
            ].map(({ label, value, color }) => (
              <div key={label} className="flex items-center justify-between gap-4">
                <span className="text-[11px] text-gray-500">{label}</span>
                <span className="text-sm font-black font-mono" style={{ color }}>{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── 内容区（可滚动）── */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3">

        {/* 漏洞发现 */}
        {vulns.length > 0 && (
          <Section title="漏洞发现" icon={<Bug size={14} />} count={vulns.length} defaultOpen accent="#ef4444">
            <div className="space-y-2">
              {vulns.map((f, i) => <VulnCard key={i} finding={f} idx={i} />)}
            </div>
          </Section>
        )}

        {/* 开放端口 */}
        {ports.length > 0 && (
          <Section title="开放端口" icon={<Server size={14} />} count={ports.length} defaultOpen accent="#3b82f6">
            <div className="flex flex-wrap gap-2">
              {ports.map((p, i) => <PortBadge key={i} port={p} />)}
            </div>
          </Section>
        )}

        {/* AI 分析摘要 */}
        {aiReport && (
          <Section title="AI 分析摘要" icon={<Zap size={14} />} defaultOpen accent="#f59e0b">
            <div className="p-3 rounded-lg text-xs text-gray-300 leading-relaxed whitespace-pre-wrap"
              style={{ background: 'rgba(245,158,11,0.04)', border: '1px solid rgba(245,158,11,0.1)' }}>
              {typeof aiReport === 'string'
                ? aiReport
                : aiReport.summary || aiReport.executive_summary || JSON.stringify(aiReport, null, 2)}
            </div>
          </Section>
        )}

        {/* 执行任务 */}
        {tasks.length > 0 && (
          <Section title="执行任务" icon={<GitBranch size={14} />} count={tasks.length} defaultOpen={false} accent="#8b5cf6">
            <TaskTimeline tasks={tasks} />
          </Section>
        )}

        {/* 空状态 */}
        {ports.length === 0 && vulns.length === 0 && tasks.length === 0 && !aiReport && (
          <div className="flex flex-col items-center justify-center py-16 gap-4 text-gray-600">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
              <Shield size={24} className="opacity-30" />
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-500">暂无详细数据</p>
              <p className="text-xs text-gray-700 mt-1">请重新执行扫描以生成报告数据</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ─── 左侧：扫描历史报告行 ─────────────────────────────────────────────────────
const ScanListItem = ({ record, selected, onClick }) => {
  const vulns  = (record.findings || []).filter(f => f.type !== 'open_ports');
  const topSev = SEV_ORDER.find(s => vulns.some(f => f.severity === s));
  const score  = calcRiskScore(vulns);
  const level  = riskLevel(score);

  return (
    <div
      onClick={onClick}
      className={[
        'px-3 py-2.5 cursor-pointer transition-all rounded-lg',
        selected
          ? 'bg-cyan-500/10 border-l-2 border-cyan-400'
          : 'hover:bg-white/[0.04] border-l-2 border-transparent',
      ].join(' ')}
    >
      <div className="flex items-center gap-2.5">
        <div className="w-2 h-2 rounded-full shrink-0" style={{ background: level.color, boxShadow: `0 0 5px ${level.color}66` }} />
        <div className="flex-1 min-w-0">
          <p className="text-xs text-gray-200 font-mono truncate">{record.target}</p>
          <p className="text-[11px] text-gray-600 mt-0.5">{fmtDate(record.timestamp)}</p>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          {topSev && <SevBadge sev={topSev} size="sm" />}
          {vulns.length > 0 && (
            <span className="text-[10px] text-gray-600">{vulns.length} 漏洞</span>
          )}
          {vulns.length === 0 && (
            <span className="text-[10px] text-gray-700">无漏洞</span>
          )}
        </div>
      </div>
    </div>
  );
};

// ─── 左侧：后端报告行 ─────────────────────────────────────────────────────────
const BackendListItem = ({ report, selected, onClick }) => {
  const meta = report.report_metadata || {};
  const statusConfig = {
    completed:  { dot: 'bg-emerald-400', text: 'text-emerald-400' },
    generating: { dot: 'bg-yellow-400 animate-pulse', text: 'text-yellow-400' },
    failed:     { dot: 'bg-red-400', text: 'text-red-400' },
  }[report.status] || { dot: 'bg-gray-600', text: 'text-gray-500' };

  return (
    <div
      onClick={onClick}
      className={[
        'px-3 py-2.5 cursor-pointer transition-all rounded-lg',
        selected
          ? 'bg-purple-500/10 border-l-2 border-purple-400'
          : 'hover:bg-white/[0.04] border-l-2 border-transparent',
      ].join(' ')}
    >
      <div className="flex items-center gap-2.5">
        <span className={`w-2 h-2 rounded-full shrink-0 ${statusConfig.dot}`} />
        <div className="flex-1 min-w-0">
          <p className="text-xs text-gray-200 truncate" title={report.title}>{report.title}</p>
          <p className="text-[11px] text-gray-600 mt-0.5 font-mono truncate">{meta.target || '—'}</p>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <span className="text-[10px] font-mono text-gray-500 border border-gray-700/50 px-1 rounded">
            {(report.format || 'html').toUpperCase()}
          </span>
          {report.finding_count > 0 && (
            <span className="text-[10px] text-red-400">{report.finding_count} 发现</span>
          )}
        </div>
      </div>
    </div>
  );
};

// ─── 右侧：后端报告预览面板 ───────────────────────────────────────────────────
const BackendPreviewPanel = ({ report, onDelete }) => {
  const [html, setHtml]               = useState('');
  const [loadingHtml, setLoadingHtml] = useState(false);
  const [htmlError,   setHtmlError]   = useState('');
  const meta = report.report_metadata || {};

  useEffect(() => {
    if (report.status !== 'completed') return;
    setLoadingHtml(true); setHtmlError(''); setHtml('');
    apiClient.reports.download(report.id, 'html')
      .then(res => setHtml(typeof res.data === 'string' ? res.data : JSON.stringify(res.data, null, 2)))
      .catch(err => setHtmlError(err?.response?.data?.detail?.message || '加载失败'))
      .finally(() => setLoadingHtml(false));
  }, [report.id, report.status]);

  const handleDownload = async (fmt) => {
    try {
      const res  = await apiClient.reports.download(report.id, fmt);
      const ext  = fmt === 'markdown' ? 'md' : fmt;
      const blob = new Blob(
        [typeof res.data === 'string' ? res.data : JSON.stringify(res.data, null, 2)],
        { type: fmt === 'json' ? 'application/json' : 'text/plain' },
      );
      const url = URL.createObjectURL(blob);
      const a   = document.createElement('a');
      a.href = url; a.download = `report_${report.id}.${ext}`;
      a.click(); URL.revokeObjectURL(url);
    } catch {}
  };

  const statusLabel = { completed: '已完成', generating: '生成中', failed: '失败', pending: '等待' };
  const statusColor = { completed: 'text-emerald-400', generating: 'text-yellow-400', failed: 'text-red-400', pending: 'text-gray-500' };

  return (
    <div className="h-full flex flex-col">
      <div className="px-5 py-4 border-b border-gray-800/50 shrink-0" style={{ background: '#0a0e17' }}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-white truncate">{report.title}</h2>
            <div className="flex items-center gap-2 mt-1">
              <span className={`text-xs ${statusColor[report.status] || 'text-gray-500'}`}>
                {statusLabel[report.status] || report.status}
              </span>
              {meta.target && <span className="text-xs text-gray-600 font-mono">{meta.target}</span>}
            </div>
          </div>
          <div className="flex gap-1.5 shrink-0">
            {report.status === 'completed' && (
              <button onClick={() => handleDownload(report.format || 'html')}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-400 border border-gray-700/50 rounded-lg hover:text-cyan-400 hover:border-cyan-500/30 hover:bg-cyan-500/5 transition-all">
                <Download size={12} /> 下载
              </button>
            )}
            <button onClick={() => onDelete(report.id)}
              className="p-1.5 text-gray-600 hover:text-red-400 hover:bg-red-500/10 rounded-lg border border-transparent hover:border-red-500/20 transition-all">
              <Trash2 size={13} />
            </button>
          </div>
        </div>
        <div className="flex gap-3 mt-2 text-xs">
          <span className="text-gray-500">格式 <span className="font-mono text-gray-400">{(report.format || 'html').toUpperCase()}</span></span>
          {report.finding_count > 0 && <span className="text-gray-500">发现 <span className="text-red-400 font-mono">{report.finding_count}</span></span>}
          <span className="text-gray-500 ml-auto">{fmtDate(report.created_at)}</span>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        {report.status === 'generating' && (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-gray-500">
            <Loader size={28} className="animate-spin text-yellow-400" />
            <p className="text-sm">报告生成中，请稍候...</p>
          </div>
        )}
        {report.status === 'failed' && (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-red-400">
            <XCircle size={28} />
            <p className="text-sm">报告生成失败</p>
          </div>
        )}
        {report.status === 'completed' && (
          <>
            {loadingHtml && (
              <div className="flex items-center justify-center h-full text-gray-500">
                <Loader size={20} className="animate-spin mr-2" /> 加载预览中...
              </div>
            )}
            {htmlError && (
              <div className="flex items-center justify-center h-full text-red-400 gap-2 text-sm">
                <AlertTriangle size={16} /> {htmlError}
              </div>
            )}
            {!loadingHtml && !htmlError && html && (
              <iframe srcDoc={html} title={report.title} className="w-full h-full border-0" sandbox="allow-scripts" />
            )}
            {!loadingHtml && !htmlError && !html && (
              <div className="flex flex-col items-center justify-center h-full gap-3 text-gray-600">
                <FileText size={28} className="opacity-30" />
                <p className="text-sm">暂无预览内容</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

// ─── 空占位面板 ───────────────────────────────────────────────────────────────
const EmptyPlaceholder = () => (
  <div className="flex flex-col items-center justify-center h-full gap-5 text-gray-600">
    <div className="relative">
      <div className="w-20 h-20 rounded-2xl flex items-center justify-center"
        style={{ background: 'rgba(6,182,212,0.05)', border: '1px solid rgba(6,182,212,0.15)' }}>
        <Shield size={32} style={{ color: 'rgba(6,182,212,0.3)' }} />
      </div>
      <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-lg flex items-center justify-center"
        style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)' }}>
        <FileText size={12} style={{ color: 'rgba(245,158,11,0.5)' }} />
      </div>
    </div>
    <div className="text-center">
      <p className="text-sm text-gray-400">选择报告以查看详情</p>
      <p className="text-xs text-gray-700 mt-1">左侧列表中选择扫描历史或专业报告</p>
    </div>
  </div>
);

// ─── 主组件 ───────────────────────────────────────────────────────────────────
const Reports = () => {
  const { scanHistory, refreshHistory } = useScan();

  const [backendReports, setBackendReports] = useState([]);
  const [backendLoading, setBackendLoading] = useState(false);
  const [backendError,   setBackendError]   = useState('');
  const [showGenModal,   setShowGenModal]   = useState(false);
  const [selected,       setSelected]       = useState(null);
  const [filter,         setFilter]         = useState('all');
  const [searchQ,        setSearchQ]        = useState('');

  const pollRef = useRef(null);

  const loadBackendReports = useCallback(async () => {
    setBackendLoading(true); setBackendError('');
    try {
      const res = await apiClient.reports.list({ page: 1, page_size: 50 });
      setBackendReports(res.reports || res.data?.reports || []);
    } catch (err) {
      const msg = err?.response?.data?.detail?.message || err?.response?.data?.detail || err?.message || '加载失败';
      setBackendError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setBackendLoading(false);
    }
  }, []);

  useEffect(() => { loadBackendReports(); }, [loadBackendReports]);

  useEffect(() => {
    const hasGenerating = backendReports.some(r => r.status === 'generating');
    if (hasGenerating) {
      pollRef.current = setTimeout(() => loadBackendReports(), 3000);
    }
    return () => clearTimeout(pollRef.current);
  }, [backendReports, loadBackendReports]);

  const handleScanDelete = (id) => {
    try { scanHistoryService.delete(id); } catch {}
    refreshHistory();
    if (selected?.type === 'scan' && selected.data.id === id) setSelected(null);
  };

  const handleBackendDelete = async (id) => {
    try {
      await apiClient.reports.delete(id);
      setBackendReports(prev => prev.filter(r => r.id !== id));
      if (selected?.type === 'backend' && selected.data.id === id) setSelected(null);
    } catch {}
  };

  const perReports = [...scanHistory].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  const q             = searchQ.toLowerCase();
  const filteredScan  = perReports.filter(r => {
    if (q && !r.target.toLowerCase().includes(q)) return false;
    if (filter === 'critical') {
      const vulns = (r.findings || []).filter(f => f.type !== 'open_ports');
      return vulns.some(f => f.severity === 'critical' || f.severity === 'high');
    }
    return true;
  });
  const filteredBackend = backendReports.filter(r => {
    const meta = r.report_metadata || {};
    if (q && !r.title.toLowerCase().includes(q) && !(meta.target || '').toLowerCase().includes(q)) return false;
    if (filter === 'completed') return r.status === 'completed';
    if (filter === 'failed')    return r.status === 'failed';
    return true;
  });

  const totalScan    = perReports.length;
  const totalBackend = backendReports.length;
  const totalVulns   = perReports.reduce((n, r) => n + (r.findings || []).filter(f => f.type !== 'open_ports').length, 0);

  useEffect(() => {
    if (selected?.type === 'backend') {
      const updated = backendReports.find(r => r.id === selected.data.id);
      if (updated && updated !== selected.data) setSelected({ type: 'backend', data: updated });
    }
  }, [backendReports]);

  return (
    <div className="flex h-full min-h-screen" style={{ background: '#060910' }}>

      {/* ── 左侧列表区 ── */}
      <div className="w-[300px] shrink-0 flex flex-col border-r h-full"
        style={{ borderColor: 'rgba(255,255,255,0.07)', background: '#0a0e17' }}>

        {/* 头部 */}
        <div className="px-4 pt-5 pb-3 shrink-0">
          <h1 className="text-sm font-bold text-white flex items-center gap-2 mb-3">
            <Shield size={14} className="text-cyan-400" /> 报告管理
          </h1>
          {/* 统计概览 */}
          <div className="grid grid-cols-3 gap-1.5 mb-3">
            {[
              { label: 'P-E-R', value: totalScan,    color: '#06b6d4' },
              { label: '专业',  value: totalBackend, color: '#a78bfa' },
              { label: '漏洞',  value: totalVulns,   color: '#f87171' },
            ].map(({ label, value, color }) => (
              <div key={label} className="text-center py-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                <p className="text-base font-black font-mono" style={{ color }}>{value}</p>
                <p className="text-[10px] text-gray-600">{label}</p>
              </div>
            ))}
          </div>

          {/* 搜索框 */}
          <div className="relative mb-2">
            <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-600 pointer-events-none" />
            <input type="text" value={searchQ} onChange={e => setSearchQ(e.target.value)}
              placeholder="搜索目标或标题..."
              className="w-full pl-7 pr-3 py-1.5 text-xs bg-black/30 border border-gray-800/60 rounded-lg text-gray-300 placeholder-gray-700 focus:border-gray-600 outline-none" />
          </div>

          {/* 过滤标签 */}
          <div className="flex gap-1 flex-wrap">
            {[['all', '全部'], ['critical', '高危'], ['completed', '已完成'], ['failed', '失败']].map(([k, label]) => (
              <button key={k} onClick={() => setFilter(k)}
                className={[
                  'text-[11px] px-2 py-0.5 rounded-full border transition-all',
                  filter === k
                    ? 'border-cyan-500/50 text-cyan-400 bg-cyan-500/8'
                    : 'border-gray-800/60 text-gray-600 hover:text-gray-400 hover:border-gray-700',
                ].join(' ')}>
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* 列表 */}
        <div className="flex-1 overflow-y-auto px-2 pb-2 space-y-4">

          {filteredScan.length > 0 && (
            <div>
              <div className="flex items-center gap-2 px-2 py-1.5">
                <Activity size={11} className="text-cyan-500/60" />
                <span className="text-[10px] text-gray-600 font-bold uppercase tracking-widest">P-E-R 扫描</span>
                <span className="ml-auto text-[11px] text-gray-700 font-mono">{filteredScan.length}</span>
              </div>
              <div className="space-y-0.5">
                {filteredScan.map(record => (
                  <ScanListItem key={record.id || record.timestamp} record={record}
                    selected={selected?.type === 'scan' && selected.data.id === record.id}
                    onClick={() => setSelected({ type: 'scan', data: record })} />
                ))}
              </div>
            </div>
          )}

          <div>
            <div className="flex items-center gap-2 px-2 py-1.5">
              <FileText size={11} className="text-purple-500/60" />
              <span className="text-[10px] text-gray-600 font-bold uppercase tracking-widest">专业报告</span>
              {backendLoading && <Loader size={10} className="animate-spin text-gray-600 ml-1" />}
              <span className="ml-auto text-[11px] text-gray-700 font-mono">{filteredBackend.length}</span>
            </div>

            {backendError && (
              <div className="mx-2 p-2 rounded-lg bg-yellow-500/5 border border-yellow-500/20 text-[11px] text-yellow-500/80 flex items-center gap-1.5 mb-2">
                <AlertTriangle size={11} /> {backendError}
              </div>
            )}

            <div className="space-y-0.5">
              {filteredBackend.map(report => (
                <BackendListItem key={report.id} report={report}
                  selected={selected?.type === 'backend' && selected.data.id === report.id}
                  onClick={() => setSelected({ type: 'backend', data: report })} />
              ))}
              {!backendLoading && filteredBackend.length === 0 && !backendError && (
                <div className="text-center py-6 text-gray-700 text-xs">暂无专业报告</div>
              )}
            </div>
          </div>

          {filteredScan.length === 0 && filteredBackend.length === 0 && !backendError && !backendLoading && (
            <div className="flex flex-col items-center justify-center py-12 gap-3 text-gray-700">
              <Shield size={24} className="opacity-30" />
              <p className="text-xs">暂无报告数据</p>
            </div>
          )}
        </div>

        {/* 底部操作 */}
        <div className="shrink-0 px-3 py-3 border-t flex gap-2" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
          <button onClick={loadBackendReports}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-500 border border-gray-800/60 rounded-lg hover:text-gray-300 hover:border-gray-700 transition-all">
            <RefreshCw size={11} className={backendLoading ? 'animate-spin' : ''} /> 刷新
          </button>
          <button onClick={() => setShowGenModal(true)}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs text-white bg-cyan-600/80 hover:bg-cyan-600 rounded-lg transition-all">
            <Plus size={11} /> 生成报告
          </button>
        </div>
      </div>

      {/* ── 右侧预览区 ── */}
      <div className="flex-1 min-w-0 h-full overflow-hidden" style={{ background: '#060910' }}>
        {selected?.type === 'scan'    && <ScanDetailPanel record={selected.data} onDelete={handleScanDelete} />}
        {selected?.type === 'backend' && <BackendPreviewPanel report={selected.data} onDelete={handleBackendDelete} />}
        {!selected && <EmptyPlaceholder />}
      </div>

      {showGenModal && (
        <GenerateModal onClose={() => setShowGenModal(false)} onGenerated={() => { loadBackendReports(); }} />
      )}
    </div>
  );
};

export default Reports;
