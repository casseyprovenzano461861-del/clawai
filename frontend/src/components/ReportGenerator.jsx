/**
 * ReportGenerator — 报告管理页
 * Tab 1: P-E-R 扫描历史（前端 scanHistory）
 * Tab 2: 后端报告（/api/v1/reports，含生成/预览/下载）
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  FileText, Download, Trash2, ChevronRight, ChevronDown,
  Shield, RefreshCw, Target, Plus, Eye, ExternalLink,
  CheckCircle, XCircle, Clock, Loader, AlertTriangle,
} from 'lucide-react';
import GlowCard from './shared/GlowCard';
import SectionHeader from './shared/SectionHeader';
import { useScan } from '../context/ScanContext';
import scanHistoryService from '../services/scanHistoryService';
import apiClient from '../services/apiClient';

const SEV_COLOR = {
  critical: '#ef4444',
  high:     '#f97316',
  medium:   '#f59e0b',
  low:      '#3b82f6',
  info:     '#6b7280',
};
const SEV_ORDER = ['critical', 'high', 'medium', 'low', 'info'];

// ─── 工具函数 ─────────────────────────────────────────────────────────────────

const fmtDate = (iso) => {
  if (!iso) return '-';
  try {
    return new Date(iso).toLocaleString('zh-CN', {
      month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
    });
  } catch { return iso.slice(0, 16); }
};

// ─── P-E-R 历史单行 ───────────────────────────────────────────────────────────

const ScanReportRow = ({ record, onDelete }) => {
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
    a.download = `scan_${record.target}_${record.id || Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="border border-gray-800/60 rounded-xl overflow-hidden">
      <div
        className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-white/5 transition-colors"
        onClick={() => setOpen(o => !o)}
      >
        {open ? <ChevronDown size={14} className="text-gray-500 shrink-0" /> : <ChevronRight size={14} className="text-gray-500 shrink-0" />}
        <Target size={13} className="text-cyan-400 shrink-0" />
        <span className="flex-1 text-sm font-mono text-white truncate">{record.target}</span>
        {topSev && (
          <span className="text-[11px] px-2 py-0.5 rounded font-medium"
            style={{ color: SEV_COLOR[topSev], background: SEV_COLOR[topSev] + '22' }}>
            {topSev}
          </span>
        )}
        <span className="text-xs text-gray-500 shrink-0">
          漏洞 <span className="text-red-400">{vulns.length}</span>
          {ports.length > 0 && <> · 端口 <span className="text-blue-400">{ports.length}</span></>}
        </span>
        <span className="text-xs text-gray-600 shrink-0">{fmtDate(record.timestamp)}</span>
        <button onClick={e => { e.stopPropagation(); exportJSON(); }}
          className="p-1 rounded hover:text-cyan-400 hover:bg-cyan-500/10 transition-colors text-gray-600" title="导出 JSON">
          <Download size={13} />
        </button>
        <button onClick={e => { e.stopPropagation(); onDelete(record.id); }}
          className="p-1 rounded hover:text-red-400 hover:bg-red-500/10 transition-colors text-gray-600" title="删除">
          <Trash2 size={13} />
        </button>
      </div>

      {open && (
        <div className="px-4 pb-4 border-t border-gray-800/40 space-y-4 pt-3">
          {ports.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-2">开放端口</p>
              <div className="flex flex-wrap gap-1.5">
                {ports.map((p, i) => {
                  const num = typeof p === 'object' ? p.port : p;
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
                        {(f.detail || f.description) && <p className="text-[11px] text-gray-400 mt-0.5">{f.detail || f.description}</p>}
                      </div>
                      <span className="ml-auto text-[11px]" style={{ color: SEV_COLOR[sev] }}>{sev}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {tasks.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-2">执行任务 ({tasks.length})</p>
              <div className="flex flex-wrap gap-1.5">
                {tasks.map((t, i) => {
                  const name = typeof t === 'string' ? t : t.name;
                  const status = typeof t === 'object' ? t.status : 'completed';
                  return (
                    <span key={i} className={`text-xs font-mono px-2 py-0.5 rounded border ${
                      status === 'completed' ? 'text-green-400 border-green-500/20 bg-green-500/10' :
                      status === 'failed'    ? 'text-red-400 border-red-500/20 bg-red-500/10' :
                                              'text-gray-400 border-gray-700/50 bg-gray-800/50'}`}>
                      {name}
                    </span>
                  );
                })}
              </div>
            </div>
          )}

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

// ─── 报告状态图标 ─────────────────────────────────────────────────────────────

const StatusBadge = ({ status }) => {
  if (status === 'completed') return <CheckCircle size={13} className="text-green-400" />;
  if (status === 'failed')    return <XCircle size={13} className="text-red-400" />;
  if (status === 'generating') return <Loader size={13} className="text-yellow-400 animate-spin" />;
  return <Clock size={13} className="text-gray-500" />;
};

// ─── 生成报告弹窗 ─────────────────────────────────────────────────────────────

const GenerateModal = ({ onClose, onGenerated }) => {
  const [target, setTarget] = useState('');
  const [format, setFormat] = useState('html');
  const [template, setTemplate] = useState('standard');
  const [testerName, setTesterName] = useState('');
  const [clientName, setClientName] = useState('');
  const [testStartDate, setTestStartDate] = useState('');
  const [testEndDate, setTestEndDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!target.trim()) { setError('请输入目标地址'); return; }
    setLoading(true);
    setError('');
    try {
      await apiClient.reports.generate({
        title: `安全评估报告 - ${target}`,
        target: target.trim(),
        format,
        template,
        tester_name: testerName.trim() || undefined,
        client_name: clientName.trim() || undefined,
        test_start_date: testStartDate || undefined,
        test_end_date: testEndDate || undefined,
        parameters: {},
      });
      onGenerated();
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail?.message || err.message || '生成失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#0e1626] border border-cyan-500/30 rounded-2xl p-6 w-full max-w-lg shadow-2xl">
        <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
          <Plus size={16} className="text-cyan-400" /> 生成新报告
        </h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">目标地址 <span className="text-red-400">*</span></label>
            <input
              type="text"
              value={target}
              onChange={e => setTarget(e.target.value)}
              placeholder="example.com 或 192.168.1.1"
              className="w-full bg-[#060910] border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-cyan-500 outline-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">导出格式</label>
              <select value={format} onChange={e => setFormat(e.target.value)}
                className="w-full bg-[#060910] border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500 outline-none">
                <option value="html">HTML（推荐）</option>
                <option value="markdown">Markdown</option>
                <option value="json">JSON 原始数据</option>
                <option value="pdf">PDF（需 weasyprint）</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">模板</label>
              <select value={template} onChange={e => setTemplate(e.target.value)}
                className="w-full bg-[#060910] border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500 outline-none">
                <option value="standard">标准</option>
                <option value="executive">执行摘要</option>
                <option value="technical">技术详情</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">测试人员</label>
              <input value={testerName} onChange={e => setTesterName(e.target.value)}
                placeholder="姓名或团队"
                className="w-full bg-[#060910] border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-cyan-500 outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">委托方 / 客户</label>
              <input value={clientName} onChange={e => setClientName(e.target.value)}
                placeholder="客户名称"
                className="w-full bg-[#060910] border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-cyan-500 outline-none"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">测试开始日期</label>
              <input type="date" value={testStartDate} onChange={e => setTestStartDate(e.target.value)}
                className="w-full bg-[#060910] border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500 outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">测试结束日期</label>
              <input type="date" value={testEndDate} onChange={e => setTestEndDate(e.target.value)}
                className="w-full bg-[#060910] border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500 outline-none"
              />
            </div>
          </div>
          {error && <p className="text-xs text-red-400">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white border border-gray-700 rounded-lg transition-colors">
              取消
            </button>
            <button type="submit" disabled={loading}
              className="px-4 py-2 text-sm text-white bg-cyan-600 hover:bg-cyan-500 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2">
              {loading && <Loader size={13} className="animate-spin" />}
              {loading ? '生成中...' : '生成报告'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ─── 报告预览弹窗 ─────────────────────────────────────────────────────────────

const PreviewModal = ({ reportId, title, onClose }) => {
  const [html, setHtml] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const iframeRef = useRef(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await apiClient.reports.download(reportId, 'html');
        // axios 返回的 html 文本
        setHtml(typeof res.data === 'string' ? res.data : JSON.stringify(res.data, null, 2));
      } catch (err) {
        setError(err?.response?.data?.detail?.message || '加载报告失败');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [reportId]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-[#0e1626] border border-cyan-500/30 rounded-2xl w-full max-w-5xl h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800/60 shrink-0">
          <span className="text-sm font-semibold text-white truncate">{title}</span>
          <div className="flex gap-2">
            <a
              href={`/api/v1/reports/${reportId}/download?format=html`}
              download={`report_${reportId}.html`}
              target="_blank" rel="noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-cyan-400 border border-cyan-500/30 rounded-lg hover:bg-cyan-500/10 transition-colors"
            >
              <Download size={12} /> 下载 HTML
            </a>
            <button onClick={onClose} className="px-3 py-1.5 text-xs text-gray-400 border border-gray-700/50 rounded-lg hover:text-white transition-colors">
              关闭
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-hidden">
          {loading && (
            <div className="flex items-center justify-center h-full text-gray-500">
              <Loader size={24} className="animate-spin mr-2" /> 加载中...
            </div>
          )}
          {error && (
            <div className="flex items-center justify-center h-full text-red-400 gap-2">
              <AlertTriangle size={16} /> {error}
            </div>
          )}
          {!loading && !error && (
            <iframe
              ref={iframeRef}
              srcDoc={html}
              title={title}
              className="w-full h-full border-0"
              sandbox="allow-scripts"
            />
          )}
        </div>
      </div>
    </div>
  );
};

// ─── 后端报告行 ───────────────────────────────────────────────────────────────

const BackendReportRow = ({ report, onDelete, onPreview }) => {
  const meta = report.report_metadata || {};
  const target = meta.target || '—';

  const handleDownload = async (fmt) => {
    try {
      const res = await apiClient.reports.download(report.id, fmt);
      const ext = fmt === 'markdown' ? 'md' : fmt;
      const blob = new Blob(
        [typeof res.data === 'string' ? res.data : JSON.stringify(res.data, null, 2)],
        { type: fmt === 'json' ? 'application/json' : 'text/plain' }
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${report.id}.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('下载失败:', err);
    }
  };

  return (
    <div className="flex items-center gap-3 px-4 py-3 border border-gray-800/60 rounded-xl hover:bg-white/5 transition-colors">
      <StatusBadge status={report.status} />

      <Target size={13} className="text-purple-400 shrink-0" />
      <span className="font-mono text-sm text-white flex-1 truncate" title={report.title}>{report.title}</span>

      <span className="text-xs text-gray-600 shrink-0 hidden sm:block">{target}</span>

      <span className="text-[11px] px-2 py-0.5 rounded border border-gray-700/50 text-gray-400 font-mono shrink-0">
        {(report.format || 'html').toUpperCase()}
      </span>

      {report.finding_count > 0 && (
        <span className="text-xs shrink-0">
          漏洞 <span className="text-red-400 font-mono">{report.finding_count}</span>
        </span>
      )}

      <span className="text-xs text-gray-600 shrink-0">{fmtDate(report.created_at)}</span>

      {/* 操作按钮 */}
      <div className="flex gap-1 shrink-0">
        {report.status === 'completed' && (
          <>
            <button
              onClick={() => onPreview(report)}
              className="p-1.5 rounded hover:text-cyan-400 hover:bg-cyan-500/10 transition-colors text-gray-600"
              title="预览"
            >
              <Eye size={13} />
            </button>
            <button
              onClick={() => handleDownload(report.format || 'html')}
              className="p-1.5 rounded hover:text-green-400 hover:bg-green-500/10 transition-colors text-gray-600"
              title="下载"
            >
              <Download size={13} />
            </button>
          </>
        )}
        <button
          onClick={() => onDelete(report.id)}
          className="p-1.5 rounded hover:text-red-400 hover:bg-red-500/10 transition-colors text-gray-600"
          title="删除"
        >
          <Trash2 size={13} />
        </button>
      </div>
    </div>
  );
};

// ─── 主组件 ───────────────────────────────────────────────────────────────────

const ReportGenerator = () => {
  const { scanHistory, refreshHistory } = useScan();
  const [activeTab, setActiveTab] = useState('scan'); // 'scan' | 'backend'
  const [backendReports, setBackendReports] = useState([]);
  const [backendLoading, setBackendLoading] = useState(false);
  const [backendError, setBackendError] = useState('');
  const [showGenModal, setShowGenModal] = useState(false);
  const [previewReport, setPreviewReport] = useState(null);
  // 轮询刷新（生成中时每 3s 刷新一次）
  const pollRef = useRef(null);

  const loadBackendReports = async () => {
    setBackendLoading(true);
    setBackendError('');
    try {
      const res = await apiClient.reports.list({ page: 1, page_size: 50 });
      // apiClient 已自动解包 .data，直接访问 res.reports
      setBackendReports(res.reports || res.data?.reports || []);
    } catch (err) {
      const msg = err?.response?.data?.detail?.message
        || err?.response?.data?.detail
        || err?.message
        || '加载失败，请检查后端连接';
      setBackendError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setBackendLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'backend') {
      loadBackendReports();
    }
  }, [activeTab]);

  // 轮询：若有生成中的报告，3s 刷新一次
  useEffect(() => {
    const hasGenerating = backendReports.some(r => r.status === 'generating');
    if (hasGenerating && activeTab === 'backend') {
      pollRef.current = setTimeout(() => loadBackendReports(), 3000);
    }
    return () => clearTimeout(pollRef.current);
  }, [backendReports, activeTab]);

  const handleScanDelete = (id) => {
    try { scanHistoryService.delete(id); } catch {}
    refreshHistory();
  };

  const handleBackendDelete = async (id) => {
    try {
      await apiClient.reports.delete(id);
      setBackendReports(prev => prev.filter(r => r.id !== id));
    } catch (err) {
      console.error('删除失败:', err);
    }
  };

  const perReports = [...scanHistory].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  const totalVulns = perReports.reduce((n, r) => n + (r.findings || []).filter(f => f.type !== 'open_ports').length, 0);
  const backendCompleted = backendReports.filter(r => r.status === 'completed').length;
  const backendTotal = backendReports.length;

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
              <p className="text-xs text-gray-500">扫描报告生成 · 查看 · 导出</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <span className="text-gray-500">P-E-R 报告 <span className="text-cyan-400 font-mono">{perReports.length}</span></span>
            <span className="text-gray-500">总漏洞 <span className="text-red-400 font-mono">{totalVulns}</span></span>
            <span className="text-gray-500">后端报告 <span className="text-purple-400 font-mono">{backendCompleted}/{backendTotal}</span></span>
          </div>
        </div>
      </GlowCard>

      {/* Tab 切换 */}
      <div className="flex gap-2">
        <button
          onClick={() => setActiveTab('scan')}
          className={`px-4 py-2 text-sm rounded-lg border transition-all ${
            activeTab === 'scan'
              ? 'border-cyan-500/50 text-cyan-400 bg-cyan-500/10'
              : 'border-gray-700/50 text-gray-500 hover:text-gray-300'
          }`}
        >
          P-E-R 扫描历史
          {perReports.length > 0 && (
            <span className="ml-2 text-xs font-mono bg-gray-800 px-1.5 py-0.5 rounded">{perReports.length}</span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('backend')}
          className={`px-4 py-2 text-sm rounded-lg border transition-all flex items-center gap-2 ${
            activeTab === 'backend'
              ? 'border-purple-500/50 text-purple-400 bg-purple-500/10'
              : 'border-gray-700/50 text-gray-500 hover:text-gray-300'
          }`}
        >
          专业报告
          {backendTotal > 0 && (
            <span className="text-xs font-mono bg-gray-800 px-1.5 py-0.5 rounded">{backendTotal}</span>
          )}
        </button>
      </div>

      {/* ── Tab 1: P-E-R 扫描历史 ── */}
      {activeTab === 'scan' && (
        <GlowCard color="blue" padding="md">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-gray-400">P-E-R 框架自动扫描结果</span>
            <button onClick={refreshHistory}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-gray-400 hover:text-cyan-400 hover:bg-cyan-500/10 transition-all border border-gray-700/50 text-xs">
              <RefreshCw size={12} /> 刷新
            </button>
          </div>
          {perReports.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 gap-4 text-gray-600">
              <Shield size={48} className="opacity-15" />
              <p className="text-sm">暂无记录</p>
              <p className="text-xs text-gray-700">在仪表板发起 P-E-R 扫描，完成后报告自动出现在这里</p>
            </div>
          ) : (
            <div className="space-y-2">
              {perReports.map(record => (
                <ScanReportRow key={record.id || record.timestamp} record={record} onDelete={handleScanDelete} />
              ))}
            </div>
          )}
        </GlowCard>
      )}

      {/* ── Tab 2: 后端报告 ── */}
      {activeTab === 'backend' && (
        <GlowCard color="purple" padding="md">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-gray-400">专业渗透测试报告（含 CVSS 评分、修复建议）</span>
            <div className="flex gap-2">
              <button onClick={loadBackendReports}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-gray-400 hover:text-purple-400 hover:bg-purple-500/10 transition-all border border-gray-700/50 text-xs">
                <RefreshCw size={12} className={backendLoading ? 'animate-spin' : ''} /> 刷新
              </button>
              <button onClick={() => setShowGenModal(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white bg-purple-600 hover:bg-purple-500 transition-all text-xs">
                <Plus size={12} /> 生成报告
              </button>
            </div>
          </div>

          {backendError && (
            <div className="flex items-center gap-2 text-yellow-400 text-xs mb-3 p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
              <AlertTriangle size={14} /> {backendError}
            </div>
          )}

          {backendLoading && backendReports.length === 0 ? (
            <div className="flex items-center justify-center py-12 gap-2 text-gray-500">
              <Loader size={20} className="animate-spin" /> 加载中...
            </div>
          ) : backendReports.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 gap-4 text-gray-600">
              <FileText size={48} className="opacity-15" />
              <p className="text-sm">暂无专业报告</p>
              <button onClick={() => setShowGenModal(true)}
                className="flex items-center gap-2 px-4 py-2 text-xs text-purple-400 border border-purple-500/30 rounded-lg hover:bg-purple-500/10 transition-colors">
                <Plus size={12} /> 生成第一份报告
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              {backendReports.map(report => (
                <BackendReportRow
                  key={report.id}
                  report={report}
                  onDelete={handleBackendDelete}
                  onPreview={setPreviewReport}
                />
              ))}
            </div>
          )}
        </GlowCard>
      )}

      {/* 弹窗 */}
      {showGenModal && (
        <GenerateModal
          onClose={() => setShowGenModal(false)}
          onGenerated={() => { loadBackendReports(); setActiveTab('backend'); }}
        />
      )}
      {previewReport && (
        <PreviewModal
          reportId={previewReport.id}
          title={previewReport.title}
          onClose={() => setPreviewReport(null)}
        />
      )}
    </div>
  );
};

export default ReportGenerator;
