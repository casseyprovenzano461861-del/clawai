/**
 * ReportGenerator — 报告管理页
 * 展示所有 P-E-R 扫描历史，支持查看详情、导出 JSON
 * 数据来源：ScanContext.scanHistory（每次 P-E-R 完成自动写入）
 */

import React, { useState } from 'react';
import {
  FileText, Download, Trash2, ChevronRight, ChevronDown,
  AlertTriangle, Shield, Clock, Target, RefreshCw, Info,
} from 'lucide-react';
import GlowCard from './shared/GlowCard';
import SectionHeader from './shared/SectionHeader';
import { useScan } from '../context/ScanContext';
import scanHistoryService from '../services/scanHistoryService';

const SEV_COLOR = {
  critical: '#ef4444',
  high:     '#f97316',
  medium:   '#f59e0b',
  low:      '#3b82f6',
  info:     '#6b7280',
};

const SEV_ORDER = ['critical', 'high', 'medium', 'low', 'info'];

// ─── 单条报告行 ────────────────────────────────────────────────────────────────
const ReportRow = ({ record, onDelete }) => {
  const [open, setOpen] = useState(false);

  const findings  = record.findings || [];
  const tasks     = record.tasks    || [];
  const vulns     = findings.filter(f => f.type !== 'open_ports');
  const ports     = findings
    .filter(f => f.type === 'open_ports')
    .flatMap(f => f.ports || []);

  const topSev = SEV_ORDER.find(s => vulns.some(f => f.severity === s)) || null;

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report_${record.target}_${record.id || Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="border border-gray-800/60 rounded-xl overflow-hidden">
      {/* 摘要行 */}
      <div
        className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-white/5 transition-colors"
        onClick={() => setOpen(o => !o)}
      >
        {open
          ? <ChevronDown size={14} className="text-gray-500 shrink-0" />
          : <ChevronRight size={14} className="text-gray-500 shrink-0" />}

        <Target size={13} className="text-cyan-400 shrink-0" />
        <span className="flex-1 text-sm font-mono text-white truncate">{record.target}</span>

        {/* 严重程度标签 */}
        {topSev && (
          <span
            className="text-[11px] px-2 py-0.5 rounded font-medium"
            style={{ color: SEV_COLOR[topSev], background: SEV_COLOR[topSev] + '22' }}
          >
            {topSev}
          </span>
        )}

        <span className="text-xs text-gray-500 shrink-0">
          漏洞 <span className="text-red-400">{vulns.length}</span>
          {ports.length > 0 && <> · 端口 <span className="text-blue-400">{ports.length}</span></>}
        </span>

        <span className="text-xs text-gray-600 shrink-0">
          {new Date(record.timestamp).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}
        </span>

        {/* 操作按钮 */}
        <button
          onClick={e => { e.stopPropagation(); exportJSON(); }}
          className="p-1 rounded hover:text-cyan-400 hover:bg-cyan-500/10 transition-colors text-gray-600"
          title="导出 JSON"
        >
          <Download size={13} />
        </button>
        <button
          onClick={e => { e.stopPropagation(); onDelete(record.id); }}
          className="p-1 rounded hover:text-red-400 hover:bg-red-500/10 transition-colors text-gray-600"
          title="删除"
        >
          <Trash2 size={13} />
        </button>
      </div>

      {/* 展开详情 */}
      {open && (
        <div className="px-4 pb-4 border-t border-gray-800/40 space-y-4 pt-3">

          {/* 端口列表 */}
          {ports.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-2">开放端口</p>
              <div className="flex flex-wrap gap-1.5">
                {ports.map((p, i) => {
                  const num     = typeof p === 'object' ? p.port    : p;
                  const service = typeof p === 'object' ? p.service : '';
                  return (
                    <span key={`${num}-${i}`} className="text-xs font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      {num}{service ? `/${service}` : ''}
                    </span>
                  );
                })}
              </div>
            </div>
          )}

          {/* 漏洞列表 */}
          {vulns.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-2">漏洞发现</p>
              <div className="space-y-1.5">
                {vulns.map((f, i) => {
                  const sev = f.severity || 'info';
                  return (
                    <div key={i} className="flex items-start gap-2 p-2 rounded-lg" style={{ background: SEV_COLOR[sev] + '11' }}>
                      <div className="w-2 h-2 rounded-full mt-1 shrink-0" style={{ background: SEV_COLOR[sev] }} />
                      <div>
                        <p className="text-xs text-white">{f.title || f.type}</p>
                        {(f.detail || f.description) && (
                          <p className="text-[11px] text-gray-400 mt-0.5">{f.detail || f.description}</p>
                        )}
                      </div>
                      <span className="ml-auto text-[11px]" style={{ color: SEV_COLOR[sev] }}>{sev}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 执行任务 */}
          {tasks.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-2">执行任务 ({tasks.length})</p>
              <div className="flex flex-wrap gap-1.5">
                {tasks.map((t, i) => {
                  const name   = typeof t === 'string' ? t : t.name;
                  const status = typeof t === 'object' ? t.status : 'completed';
                  return (
                    <span key={i} className={`text-xs font-mono px-2 py-0.5 rounded border ${
                      status === 'completed' ? 'text-green-400 border-green-500/20 bg-green-500/10' :
                      status === 'failed'    ? 'text-red-400 border-red-500/20 bg-red-500/10' :
                                              'text-gray-400 border-gray-700/50 bg-gray-800/50'
                    }`}>
                      {name}
                    </span>
                  );
                })}
              </div>
            </div>
          )}

          {/* AI 报告摘要 */}
          {record.report && (
            <div>
              <p className="text-xs text-gray-500 mb-2">AI 分析摘要</p>
              <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">
                {typeof record.report === 'string'
                  ? record.report
                  : record.report.summary || record.report.executive_summary || JSON.stringify(record.report, null, 2)}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── 主组件 ──────────────────────────────────────────────────────────────────
const ReportGenerator = () => {
  const { scanHistory, refreshHistory, clearLastScan } = useScan();

  const handleDelete = (id) => {
    try { scanHistoryService.delete(id); } catch {}
    refreshHistory();
  };

  const perReports = [...scanHistory].sort((a, b) =>
    new Date(b.timestamp) - new Date(a.timestamp)
  );

  const totalVulns = perReports.reduce((n, r) =>
    n + (r.findings || []).filter(f => f.type !== 'open_ports').length, 0
  );

  return (
    <div className="min-h-screen px-4 py-6 max-w-screen-2xl mx-auto space-y-4">

      {/* 页头 */}
      <GlowCard color="cyan" padding="md" className="relative overflow-hidden">
        <div className="scanlines absolute inset-0 pointer-events-none" />
        <div className="relative z-10 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <FileText size={18} className="text-cyan-400" />
            <div>
              <h1 className="text-base font-semibold text-white">报告管理</h1>
              <p className="text-xs text-gray-500">P-E-R 扫描完成后自动生成</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <span className="text-gray-500">报告数 <span className="text-cyan-400 font-mono">{perReports.length}</span></span>
            <span className="text-gray-500">总漏洞 <span className="text-red-400 font-mono">{totalVulns}</span></span>
            <button
              onClick={refreshHistory}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-gray-400 hover:text-cyan-400 hover:bg-cyan-500/10 transition-all border border-gray-700/50"
            >
              <RefreshCw size={12} /> 刷新
            </button>
          </div>
        </div>
      </GlowCard>

      {/* 报告列表 */}
      <GlowCard color="blue" padding="md">
        {perReports.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-4 text-gray-600">
            <Shield size={48} className="opacity-15" />
            <p className="text-sm">暂无报告</p>
            <p className="text-xs text-gray-700">在仪表板发起 P-E-R 扫描，完成后报告自动出现在这里</p>
          </div>
        ) : (
          <div className="space-y-2">
            {perReports.map(record => (
              <ReportRow
                key={record.id || record.timestamp}
                record={record}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </GlowCard>
    </div>
  );
};

export default ReportGenerator;
