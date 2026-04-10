/**
 * ScanTerminal — 实时终端风格扫描页面
 *
 * 布局：
 *   顶部：目标输入 + 模式选择 + 开始/停止 + 进度条
 *   左栏 (60%)：仿终端滚动输出
 *   右栏 (40%)：发现列表 + FLAG 高亮
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Terminal, Play, Square, Target, AlertTriangle,
         CheckCircle, Zap, Shield, Flag } from 'lucide-react';
import { usePERAgent } from '../hooks/usePERAgent';
import GlowCard from '../components/shared/GlowCard';
import { api } from '../services/apiClient';

// ─── 颜色常量（Cyberpunk 风格）────────────────────────────────────────────────
const C = {
  green:  '#00ff41',
  red:    '#ff3c3c',
  amber:  '#ffbf00',
  cyan:   '#00cfff',
  dim:    '#4a7a4a',
  bg:     '#060910',
  bgCard: '#0a0e17',
};

// ─── 扫描模式配置 ─────────────────────────────────────────────────────────────
const PROFILES = [
  { id: 'quick',    label: '快速扫描',  desc: '3轮：nmap + curl' },
  { id: 'standard', label: '标准扫描',  desc: '5轮：nmap + curl + dirsearch' },
  { id: 'deep',     label: '深度扫描',  desc: '10轮：全工具链' },
];

// ─── 终端日志行组件 ────────────────────────────────────────────────────────────
const TerminalLine = ({ entry }) => {
  const { text, msgType, timestamp, source } = entry;

  // 工具执行行：特殊样式
  const isTool = source === 'tool';
  const isFlag = text.includes('FLAG') || text.includes('flag{') || text.includes('HTB{');

  const color = isFlag
    ? C.red
    : isTool
    ? C.cyan
    : msgType === 'error'
    ? C.red
    : msgType === 'success'
    ? C.green
    : msgType === 'warning'
    ? C.amber
    : C.green;

  const time = timestamp
    ? new Date(timestamp).toLocaleTimeString('zh-CN', { hour12: false })
    : '';

  return (
    <div
      className="flex gap-2 font-mono text-xs leading-relaxed py-0.5"
      style={{ color, ...(isFlag ? { fontWeight: 700, fontSize: '0.8rem' } : {}) }}
    >
      <span style={{ color: C.dim, flexShrink: 0 }}>{time}</span>
      <span style={{ color: C.dim, flexShrink: 0 }}>
        {isTool ? '▶' : isFlag ? '⚑' : '·'}
      </span>
      <span className="break-all whitespace-pre-wrap">{text}</span>
    </div>
  );
};

// ─── 发现卡片 ─────────────────────────────────────────────────────────────────
const FindingCard = ({ finding }) => {
  const { title, severity, detail } = finding;
  const sevColor = {
    critical: C.red,
    high: C.red,
    medium: C.amber,
    low: C.cyan,
    info: C.dim,
  }[severity?.toLowerCase()] || C.dim;

  return (
    <div
      className="border rounded p-2 mb-2 text-xs font-mono"
      style={{ borderColor: sevColor + '55', background: sevColor + '11' }}
    >
      <div className="flex items-center gap-1.5 mb-0.5" style={{ color: sevColor }}>
        <AlertTriangle size={11} />
        <span className="font-bold uppercase">{severity || 'info'}</span>
        <span style={{ color: C.green }}>{title}</span>
      </div>
      {detail && (
        <div style={{ color: '#aaa' }} className="ml-4 truncate">{detail}</div>
      )}
    </div>
  );
};

// ─── Flag 横幅 ────────────────────────────────────────────────────────────────
const FlagBanner = ({ flags }) => {
  if (!flags || flags.length === 0) return null;
  return (
    <div
      className="border-2 rounded-lg p-4 mb-4 text-center animate-pulse"
      style={{ borderColor: C.red, background: C.red + '22' }}
    >
      <div className="flex items-center justify-center gap-2 mb-2" style={{ color: C.red }}>
        <Flag size={20} />
        <span className="font-bold text-lg font-mono tracking-widest">FLAG CAPTURED</span>
        <Flag size={20} />
      </div>
      {flags.map((f, i) => (
        <div key={i} className="font-mono text-sm font-bold" style={{ color: '#fff' }}>
          {f}
        </div>
      ))}
    </div>
  );
};

// ─── 进度条 ───────────────────────────────────────────────────────────────────
const ProgressBar = ({ value, label }) => (
  <div className="w-full">
    <div className="flex justify-between text-xs font-mono mb-1" style={{ color: C.dim }}>
      <span>{label || '扫描进度'}</span>
      <span>{Math.round(value * 100)}%</span>
    </div>
    <div className="w-full rounded-full h-1.5" style={{ background: '#1a2a1a' }}>
      <div
        className="h-1.5 rounded-full transition-all duration-500"
        style={{ width: `${value * 100}%`, background: C.green }}
      />
    </div>
  </div>
);

// ─── 主页面 ───────────────────────────────────────────────────────────────────
export default function ScanTerminal() {
  const [target, setTarget]   = useState('');
  const [profile, setProfile] = useState('standard');
  const [scanId, setScanId]   = useState(null);
  const [flags, setFlags]     = useState([]);
  const [termLines, setTermLines] = useState([]);
  const termRef = useRef(null);

  const {
    status, progress, currentTask,
    toolEvents, logs, findings,
    connect, disconnect,
  } = usePERAgent({
    autoConnect: true,
    onEvent: (evt) => {
      // FLAG_FOUND 事件：收集 flag
      if (evt.type === 'flag_found' || (evt.scan_event === 'flag_found')) {
        const newFlags = evt.flags || (evt.flag ? [evt.flag] : []);
        if (newFlags.length) setFlags(prev => [...new Set([...prev, ...newFlags])]);
      }
    },
  });

  // 将 logs 和 toolEvents 合并成终端行
  useEffect(() => {
    const lines = [];

    // 来自 EventBus 的 message 日志
    for (const log of logs) {
      lines.push({
        id: log.id,
        text: log.text,
        msgType: log.msgType,
        timestamp: log.timestamp,
        source: 'eventbus',
      });
    }

    // 工具事件 → 命令输出行
    for (const tool of toolEvents) {
      if (tool.status === 'start') {
        const cmd = tool.args?.command || tool.args?.cmd || '';
        lines.push({
          id: tool.id + '-start',
          text: `[${tool.name}] ${cmd}`,
          msgType: 'info',
          timestamp: tool.timestamp,
          source: 'tool',
        });
      } else if (tool.status === 'complete' && tool.result) {
        const preview = String(tool.result).slice(0, 200).replace(/\n/g, ' ');
        lines.push({
          id: tool.id + '-result',
          text: `  → ${preview}`,
          msgType: 'success',
          timestamp: tool.timestamp,
          source: 'eventbus',
        });
      }
    }

    // 按 timestamp 排序
    lines.sort((a, b) => new Date(a.timestamp || 0).getTime() - new Date(b.timestamp || 0).getTime());
    setTermLines(lines);
  }, [logs, toolEvents]);

  // 自动滚动终端到底部
  useEffect(() => {
    if (termRef.current) {
      termRef.current.scrollTop = termRef.current.scrollHeight;
    }
  }, [termLines]);

  // 从 findings 中提取 Flag
  useEffect(() => {
    const flagFindings = findings.filter(
      f => f.title?.toLowerCase().includes('flag') || f.detail?.includes('flag{')
    );
    if (flagFindings.length) {
      const extracted = flagFindings.flatMap(f => {
        const m = (f.detail || '').match(/(flag\{[^}]+\}|HTB\{[^}]+\}|THM\{[^}]+\}|[a-f0-9]{32})/gi);
        return m || [];
      });
      if (extracted.length) setFlags(prev => [...new Set([...prev, ...extracted])]);
    }
  }, [findings]);

  const isRunning = status === 'running';

  const handleStart = useCallback(async () => {
    if (!target.trim()) return;
    setFlags([]);
    setTermLines([]);

    try {
      // baseURL 已含 /api/v1，不要重复加前缀
      const res = await api.post('/scan/start', {
        target: target.trim(),
        profile,
      });
      setScanId(res?.scan_id || res?.data?.scan_id || null);
      // 添加初始日志行
      setTermLines([{
        id: 'start',
        text: `扫描启动 → ${target.trim()} [${profile}]`,
        msgType: 'info',
        timestamp: new Date().toISOString(),
        source: 'eventbus',
      }]);
    } catch (err) {
      setTermLines([{
        id: 'err',
        text: `启动失败: ${err?.response?.data?.detail || err.message}`,
        msgType: 'error',
        timestamp: new Date().toISOString(),
        source: 'eventbus',
      }]);
    }
  }, [target, profile]);

  const handleStop = useCallback(async () => {
    if (scanId) {
      try { await api.delete(`/scan/${scanId}`); } catch (_) {}
      setScanId(null);
    }
  }, [scanId]);

  return (
    <div className="min-h-screen p-4 font-mono" style={{ background: C.bg }}>
      {/* ── 标题 ── */}
      <div className="flex items-center gap-3 mb-5">
        <Terminal size={22} style={{ color: C.green }} />
        <h1 className="text-xl font-bold tracking-wider" style={{ color: C.green }}>
          CLAWAI SCAN TERMINAL
        </h1>
        <div className="flex-1 h-px" style={{ background: C.green + '33' }} />
        <span
          className="text-xs px-2 py-0.5 rounded border font-mono"
          style={{
            color: isRunning ? C.green : C.dim,
            borderColor: isRunning ? C.green : C.dim,
            animation: isRunning ? 'pulse 1.5s infinite' : 'none',
          }}
        >
          {isRunning ? '● SCANNING' : status === 'connected' ? '○ READY' : '◌ ' + status.toUpperCase()}
        </span>
      </div>

      {/* ── 控制栏 ── */}
      <GlowCard color="green" className="mb-4 p-3">
        <div className="flex flex-wrap gap-3 items-end">
          {/* 目标输入 */}
          <div className="flex-1 min-w-48">
            <label className="text-xs mb-1 block" style={{ color: C.dim }}>TARGET</label>
            <div className="flex items-center gap-2 border rounded px-2 py-1.5" style={{ borderColor: C.green + '55', background: '#0a140a' }}>
              <Target size={14} style={{ color: C.dim }} />
              <input
                type="text"
                className="flex-1 bg-transparent text-sm outline-none"
                style={{ color: C.green }}
                placeholder="http://target.com"
                value={target}
                onChange={e => setTarget(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !isRunning && handleStart()}
                disabled={isRunning}
              />
            </div>
          </div>

          {/* 扫描模式 */}
          <div>
            <label className="text-xs mb-1 block" style={{ color: C.dim }}>PROFILE</label>
            <select
              className="border rounded px-2 py-1.5 text-sm outline-none"
              style={{ borderColor: C.green + '55', background: '#0a140a', color: C.green }}
              value={profile}
              onChange={e => setProfile(e.target.value)}
              disabled={isRunning}
            >
              {PROFILES.map(p => (
                <option key={p.id} value={p.id}>{p.label} — {p.desc}</option>
              ))}
            </select>
          </div>

          {/* 开始/停止 */}
          {!isRunning ? (
            <button
              onClick={handleStart}
              disabled={!target.trim() || status === 'connecting'}
              className="flex items-center gap-2 px-4 py-1.5 rounded border text-sm transition-all hover:opacity-80 disabled:opacity-40"
              style={{ borderColor: C.green, color: C.green, background: C.green + '22' }}
            >
              <Play size={14} />
              START SCAN
            </button>
          ) : (
            <button
              onClick={handleStop}
              className="flex items-center gap-2 px-4 py-1.5 rounded border text-sm transition-all hover:opacity-80"
              style={{ borderColor: C.red, color: C.red, background: C.red + '22' }}
            >
              <Square size={14} />
              STOP
            </button>
          )}
        </div>

        {/* 进度条 */}
        {(isRunning || progress > 0) && (
          <div className="mt-3">
            <ProgressBar value={progress} label={currentTask || '扫描进度'} />
          </div>
        )}
      </GlowCard>

      {/* ── 主内容区 ── */}
      <div className="flex gap-4" style={{ height: 'calc(100vh - 220px)', minHeight: 400 }}>

        {/* 左栏：终端输出 */}
        <GlowCard color="green" className="flex-[3] flex flex-col overflow-hidden p-0">
          <div
            className="flex items-center gap-2 px-3 py-2 border-b text-xs"
            style={{ borderColor: C.green + '33', color: C.dim }}
          >
            <Terminal size={12} />
            <span>TERMINAL OUTPUT</span>
            <span className="ml-auto">{termLines.length} lines</span>
          </div>
          <div
            ref={termRef}
            className="flex-1 overflow-y-auto px-3 py-2 space-y-0"
            style={{ background: '#050a05' }}
          >
            {termLines.length === 0 ? (
              <div className="text-center py-12" style={{ color: C.dim }}>
                <Terminal size={32} className="mx-auto mb-3 opacity-30" />
                <p className="text-sm">输入目标地址并点击 START SCAN</p>
              </div>
            ) : (
              termLines.map(line => <TerminalLine key={line.id} entry={line} />)
            )}
            {/* 光标 */}
            {isRunning && (
              <div className="flex items-center gap-1 mt-1 text-xs" style={{ color: C.green }}>
                <span>▶</span>
                <span className="animate-pulse">_</span>
              </div>
            )}
          </div>
        </GlowCard>

        {/* 右栏：发现 + Flag */}
        <div className="flex-[2] flex flex-col gap-3 overflow-hidden">
          {/* Flag 横幅 */}
          <FlagBanner flags={flags} />

          {/* 发现列表 */}
          <GlowCard color="red" className="flex-1 flex flex-col overflow-hidden p-0">
            <div
              className="flex items-center gap-2 px-3 py-2 border-b text-xs"
              style={{ borderColor: C.red + '33', color: C.dim }}
            >
              <Shield size={12} />
              <span>FINDINGS</span>
              <span
                className="ml-auto font-bold"
                style={{ color: findings.length > 0 ? C.red : C.dim }}
              >
                {findings.length}
              </span>
            </div>
            <div className="flex-1 overflow-y-auto p-3">
              {findings.length === 0 ? (
                <div className="text-center py-8" style={{ color: C.dim }}>
                  <Shield size={28} className="mx-auto mb-2 opacity-20" />
                  <p className="text-xs">暂无发现</p>
                </div>
              ) : (
                findings.map((f, i) => <FindingCard key={i} finding={f} />)
              )}
            </div>
          </GlowCard>

          {/* 工具时间线（最近5条） */}
          <GlowCard color="blue" className="flex-none p-3">
            <div className="text-xs mb-2" style={{ color: C.dim }}>TOOL TIMELINE</div>
            {toolEvents.length === 0 ? (
              <p className="text-xs" style={{ color: C.dim }}>等待工具执行...</p>
            ) : (
              toolEvents.slice(-5).map(t => (
                <div key={t.id} className="flex items-center gap-2 text-xs py-0.5">
                  <Zap size={10} style={{ color: t.status === 'complete' ? C.green : t.status === 'error' ? C.red : C.amber }} />
                  <span style={{ color: C.cyan }} className="w-20 truncate">{t.name}</span>
                  <span style={{ color: C.dim }}>
                    {t.status === 'complete' && t.durationMs ? `${t.durationMs}ms` : t.status}
                  </span>
                </div>
              ))
            )}
          </GlowCard>
        </div>
      </div>
    </div>
  );
}
