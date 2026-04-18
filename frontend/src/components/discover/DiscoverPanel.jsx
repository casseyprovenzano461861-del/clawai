/**
 * DiscoverPanel — 靶机发现面板
 * 通过 WebSocket 实时展示局域网靶机发现进度和评分结果
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Search, Wifi, Target, Play, Square, RefreshCw,
  ChevronRight, Shield, AlertCircle, CheckCircle,
  Info, AlertTriangle, Crosshair, Network, Zap,
  Star, Globe
} from 'lucide-react';
import apiClient from '../../services/apiClient';

// ─── 工具函数 ─────────────────────────────────────────────────────────────────

// 提取 ws://host:port，去掉 VITE_WS_URL 中可能携带的路径
const WS_BASE = (() => {
  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
  try { return new URL(wsUrl).origin.replace(/^http/, 'ws'); } catch { return 'ws://localhost:8000'; }
})();

function getScoreColor(score) {
  if (score >= 60) return 'text-red-400';
  if (score >= 35) return 'text-yellow-400';
  if (score >= 15) return 'text-cyan-400';
  return 'text-gray-400';
}

function getScoreBadge(score) {
  if (score >= 60) return { label: '高价值', color: 'bg-red-900/60 text-red-300 border-red-700' };
  if (score >= 35) return { label: '推荐', color: 'bg-yellow-900/60 text-yellow-300 border-yellow-700' };
  if (score >= 15) return { label: '候选', color: 'bg-cyan-900/60 text-cyan-300 border-cyan-700' };
  return { label: '普通', color: 'bg-gray-800 text-gray-400 border-gray-700' };
}

function getLevelIcon(score) {
  if (score >= 60) return '🎯';
  if (score >= 35) return '🔴';
  if (score >= 15) return '🟡';
  return '⚪';
}

const LOG_STYLE = {
  info: 'text-gray-400',
  success: 'text-green-400',
  warning: 'text-yellow-400',
  error: 'text-red-400',
};

const LOG_ICON = {
  info: Info,
  success: CheckCircle,
  warning: AlertTriangle,
  error: AlertCircle,
};

// ─── 子组件：日志条目 ─────────────────────────────────────────────────────────

function LogEntry({ entry }) {
  const Icon = LOG_ICON[entry.level] || Info;
  return (
    <div className={`flex items-start gap-2 text-xs ${LOG_STYLE[entry.level] || 'text-gray-400'} font-mono`}>
      <Icon size={12} className="mt-0.5 shrink-0" />
      <span>{entry.message}</span>
    </div>
  );
}

// ─── 子组件：主机结果卡片 ─────────────────────────────────────────────────────

function HostCard({ host, rank, onScan }) {
  const [expanded, setExpanded] = useState(false);
  const badge = getScoreBadge(host.score);

  return (
    <div className="border border-gray-700/60 rounded-lg bg-[#0d1117] hover:border-cyan-800/60 transition-colors">
      {/* 主行 */}
      <div
        className="flex items-center gap-3 px-4 py-3 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        {/* 排名 */}
        <span className="text-lg w-6 text-center shrink-0">{getLevelIcon(host.score)}</span>

        {/* IP */}
        <div className="font-mono text-sm font-semibold text-white w-36 shrink-0">
          {host.ip}
        </div>

        {/* 评分 */}
        <div className={`text-sm font-bold w-12 shrink-0 ${getScoreColor(host.score)}`}>
          {host.score}分
        </div>

        {/* 标签 */}
        <span className={`text-xs px-2 py-0.5 rounded border ${badge.color} shrink-0`}>
          {badge.label}
        </span>

        {/* 端口摘要 */}
        <div className="flex flex-wrap gap-1 flex-1 min-w-0">
          {host.open_ports.slice(0, 6).map((p) => (
            <span
              key={p.port}
              className="text-xs bg-gray-800 border border-gray-700 rounded px-1.5 py-0.5 text-gray-300 font-mono"
            >
              {p.port}{p.service ? `/${p.service}` : ''}
            </span>
          ))}
          {host.open_ports.length > 6 && (
            <span className="text-xs text-gray-500">+{host.open_ports.length - 6}</span>
          )}
          {host.open_ports.length === 0 && (
            <span className="text-xs text-gray-600 italic">无开放端口</span>
          )}
        </div>

        {/* 操作按钮 */}
        <button
          onClick={(e) => { e.stopPropagation(); onScan(host.ip); }}
          className="shrink-0 flex items-center gap-1.5 text-xs bg-cyan-900/50 hover:bg-cyan-800/70 text-cyan-300 border border-cyan-800 rounded px-3 py-1.5 transition-colors"
        >
          <Target size={12} />
          扫描
        </button>

        <ChevronRight
          size={14}
          className={`text-gray-600 shrink-0 transition-transform ${expanded ? 'rotate-90' : ''}`}
        />
      </div>

      {/* 展开详情 */}
      {expanded && (
        <div className="px-4 pb-3 border-t border-gray-800 pt-3 space-y-2">
          {host.os_hint && (
            <div className="text-xs text-gray-400">
              <span className="text-gray-500">系统：</span>{host.os_hint}
            </div>
          )}
          {host.matched_rules.length > 0 && (
            <div>
              <div className="text-xs text-gray-500 mb-1">命中规则：</div>
              <div className="space-y-1">
                {host.matched_rules.map((rule, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className="text-green-500">+</span>
                    <span className="text-gray-300">{rule}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {host.banner && (
            <div>
              <div className="text-xs text-gray-500 mb-1">Banner：</div>
              <pre className="text-xs text-gray-400 font-mono bg-gray-900 rounded p-2 overflow-x-auto whitespace-pre-wrap">
                {host.banner.slice(0, 200)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── 子组件：进度条 ──────────────────────────────────────────────────────────

function StepProgress({ currentStep, totalSteps, subCurrent, subTotal, message }) {
  const steps = ['检测网段', '主机探测', '指纹评分'];
  return (
    <div className="space-y-3">
      {/* 步骤指示器 */}
      <div className="flex items-center gap-2">
        {steps.map((label, i) => {
          const stepNum = i + 1;
          const isActive = stepNum === currentStep;
          const isDone = stepNum < currentStep;
          return (
            <React.Fragment key={label}>
              <div className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full transition-all ${
                isActive ? 'bg-cyan-900/60 text-cyan-300 border border-cyan-700' :
                isDone ? 'bg-green-900/40 text-green-400 border border-green-800' :
                'bg-gray-800 text-gray-600 border border-gray-700'
              }`}>
                {isDone ? <CheckCircle size={11} /> : isActive ? <Zap size={11} className="animate-pulse" /> : null}
                {label}
              </div>
              {i < steps.length - 1 && (
                <ChevronRight size={12} className={isDone ? 'text-green-600' : 'text-gray-700'} />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* 当前消息 */}
      {message && (
        <div className="text-xs text-cyan-400 font-mono flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          {message}
        </div>
      )}

      {/* 子进度条 */}
      {subTotal > 0 && (
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-gray-500">
            <span>{subCurrent}/{subTotal}</span>
            <span>{Math.round((subCurrent / subTotal) * 100)}%</span>
          </div>
          <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-cyan-500 rounded-full transition-all duration-300"
              style={{ width: `${(subCurrent / subTotal) * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// ─── 主组件 ──────────────────────────────────────────────────────────────────

export default function DiscoverPanel({ onStartScan }) {
  const [networks, setNetworks] = useState([]);       // 本机网段列表
  const [selectedNetwork, setSelectedNetwork] = useState('');
  const [quickMode, setQuickMode] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState('idle');       // idle | running | completed | error
  const [logs, setLogs] = useState([]);
  const [hosts, setHosts] = useState([]);             // 最终评分结果（有序）
  const [liveHosts, setLiveHosts] = useState([]);     // 实时发现的存活 IP
  const [progress, setProgress] = useState({ step: 0, total: 3, subCurrent: 0, subTotal: 0, message: '' });
  const [aliveCount, setAliveCount] = useState(0);
  const wsRef = useRef(null);
  const logsEndRef = useRef(null);

  // 拉取本机网段
  useEffect(() => {
    apiClient.get('/discover/networks', { timeout: 4000 })
      .then((res) => {
        const nets = res.data?.networks || [];
        setNetworks(nets);
      })
      .catch(() => {
        // 后端不可达时给一个常用默认网段
        setNetworks([
          { cidr: '192.168.1.0/24',  skippable: false },
          { cidr: '192.168.23.0/24', skippable: false },
          { cidr: '10.0.0.0/24',     skippable: false },
        ]);
      });
  }, []);

  // 日志自动滚动
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const addLog = useCallback((message, level = 'info') => {
    setLogs((prev) => [...prev.slice(-200), { message, level, ts: Date.now() }]);
  }, []);

  const connectWS = useCallback((tid) => {
    if (wsRef.current) wsRef.current.close();

    const wsUrl = `${WS_BASE}/api/v1/discover/ws/${tid}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      let msg;
      try { msg = JSON.parse(e.data); } catch { return; }

      const { type, data } = msg;

      if (type === 'log') {
        addLog(data.message, data.level || 'info');
      } else if (type === 'progress') {
        setProgress({
          step: data.step || 0,
          total: data.total || 3,
          subCurrent: data.sub_current || 0,
          subTotal: data.sub_total || 0,
          message: data.message || '',
        });
      } else if (type === 'host_found') {
        setLiveHosts((prev) => [...prev, data.ip]);
      } else if (type === 'host_result') {
        // 实时追加评分结果
        setHosts((prev) => {
          const filtered = prev.filter((h) => h.ip !== data.ip);
          return [...filtered, data].sort((a, b) => b.score - a.score);
        });
      } else if (type === 'completed') {
        setAliveCount(data.alive_count || 0);
        if (data.results?.length > 0) {
          setHosts(data.results);
        }
        setStatus('completed');
        addLog(`发现完成：${data.alive_count} 台存活，${data.results?.length || 0} 台评分`, 'success');
      } else if (type === 'error') {
        setStatus('error');
        addLog(`错误：${data.message}`, 'error');
      }
    };

    ws.onerror = () => addLog('WebSocket 连接错误', 'error');
    ws.onclose = () => {
      if (status === 'running') addLog('连接断开', 'warning');
    };
  }, [addLog, status]);

  // ── 前端模拟扫描（后端不可达时降级使用）──────────────────────────────────────
  const runSimulation = useCallback(() => {
    const cidr = selectedNetwork || '192.168.1.0/24';
    const base = cidr.split('.').slice(0, 3).join('.');

    // 随机生成 3~6 台"发现"的靶机 IP
    const candidateOffsets = [1, 100, 105, 110, 128, 200, 220, 254];
    const picked = candidateOffsets
      .sort(() => Math.random() - 0.5)
      .slice(0, Math.floor(Math.random() * 3) + 3);
    const ips = picked.map(o => `${base}.${o}`);

    // 模拟靶机数据
    const mockHosts = [
      { ip: ips[0], score: 72, os_hint: 'Linux Ubuntu 20.04', open_ports: [{port:22,service:'ssh'},{port:80,service:'http'},{port:8080,service:'http-proxy'}], matched_rules:['SSH开放','Web服务','非标准端口'], banner:'' },
      { ip: ips[1], score: 48, os_hint: 'Linux Debian', open_ports: [{port:21,service:'ftp'},{port:22,service:'ssh'},{port:3306,service:'mysql'}], matched_rules:['FTP匿名','数据库暴露'], banner:'' },
      { ip: ips[2], score: 31, os_hint: 'Windows Server 2019', open_ports: [{port:135,service:'msrpc'},{port:445,service:'smb'},{port:3389,service:'rdp'}], matched_rules:['SMB开放','RDP可达'], banner:'' },
    ];
    if (ips[3]) mockHosts.push({ ip: ips[3], score: 18, os_hint: 'Unknown', open_ports: [{port:80,service:'http'}], matched_rules:['Web服务'], banner:'' });
    if (ips[4]) mockHosts.push({ ip: ips[4], score: 9,  os_hint: 'Linux', open_ports: [], matched_rules:[], banner:'' });
    mockHosts.sort((a, b) => b.score - a.score);

    let step = 0;
    const totalIPs = 254;

    // Step 1: 检测网段
    setTimeout(() => {
      setProgress({ step: 1, total: 3, subCurrent: 0, subTotal: 0, message: `检测本机网段...` });
      addLog(`检测到网段: ${cidr}`, 'info');
    }, 300);

    setTimeout(() => {
      addLog(`网关: ${base}.1  掩码: 255.255.255.0`, 'info');
      setProgress({ step: 1, total: 3, subCurrent: 0, subTotal: totalIPs, message: '开始主机探活 (ICMP)...' });
    }, 900);

    // Step 2: 主机探活
    setTimeout(() => {
      setProgress(p => ({ ...p, step: 2, message: 'Ping 扫描中...' }));
    }, 1200);

    // 模拟逐步发现存活主机
    ips.forEach((ip, idx) => {
      setTimeout(() => {
        setLiveHosts(prev => [...prev, ip]);
        addLog(`发现存活主机: ${ip}`, 'success');
        setProgress(p => ({
          ...p,
          subCurrent: Math.min(Math.round((idx + 1) / ips.length * totalIPs), totalIPs),
          subTotal: totalIPs,
          message: `探活中... 已发现 ${idx + 1} 台`,
        }));
      }, 1500 + idx * 600);
    });

    const afterPing = 1500 + ips.length * 600 + 200;

    // Step 3: 指纹评分
    setTimeout(() => {
      addLog(`存活主机 ${ips.length} 台，开始端口扫描与指纹识别...`, 'info');
      setProgress({ step: 3, total: 3, subCurrent: 0, subTotal: ips.length, message: '端口扫描 & 指纹评分...' });
    }, afterPing);

    mockHosts.forEach((host, idx) => {
      setTimeout(() => {
        setHosts(prev => {
          const filtered = prev.filter(h => h.ip !== host.ip);
          return [...filtered, host].sort((a, b) => b.score - a.score);
        });
        addLog(`${host.ip} → 评分 ${host.score}分 | 开放端口 ${host.open_ports.length} 个`, 'info');
        setProgress(p => ({ ...p, subCurrent: idx + 1 }));
      }, afterPing + 400 + idx * 700);
    });

    // 完成
    const finishTime = afterPing + 400 + mockHosts.length * 700 + 300;
    setTimeout(() => {
      setAliveCount(ips.length);
      setStatus('completed');
      addLog(`✓ 发现完成：${ips.length} 台存活，${mockHosts.length} 台已评分`, 'success');
      addLog(`Top靶机: ${mockHosts[0].ip}（评分 ${mockHosts[0].score}）`, 'success');
    }, finishTime);

  }, [selectedNetwork, addLog]);

  const handleStart = useCallback(async () => {
    setStatus('running');
    setLogs([]);
    setHosts([]);
    setLiveHosts([]);
    setAliveCount(0);
    setProgress({ step: 0, total: 3, subCurrent: 0, subTotal: 0, message: '' });

    try {
      const payload = { quick: quickMode };
      if (selectedNetwork) payload.network = selectedNetwork;

      const res = await apiClient.post('/discover/start', payload, { timeout: 5000 });
      const { task_id } = res.data;
      setTaskId(task_id);
      addLog(`任务已启动 (id: ${task_id})`, 'info');
      connectWS(task_id);
    } catch (err) {
      // 后端不可达时，降级为前端模拟模式
      addLog('后端未连接，进入模拟发现模式...', 'warning');
      runSimulation();
    }
  }, [selectedNetwork, quickMode, addLog, connectWS, runSimulation]);

  const handleStop = useCallback(() => {
    wsRef.current?.close();
    setStatus('idle');
    addLog('已手动停止', 'warning');
  }, [addLog]);

  const handleScanHost = useCallback((ip) => {
    onStartScan?.(ip);
  }, [onStartScan]);

  const isRunning = status === 'running';

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* ── 控制栏 ─────────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-3">
        {/* 网段选择 */}
        <div className="flex items-center gap-2 flex-1 min-w-48">
          <Network size={14} className="text-cyan-500 shrink-0" />
          <select
            className="flex-1 bg-[#0d1117] border border-gray-700 rounded px-3 py-1.5 text-sm text-gray-300 focus:border-cyan-600 focus:outline-none"
            value={selectedNetwork}
            onChange={(e) => setSelectedNetwork(e.target.value)}
            disabled={isRunning}
          >
            <option value="">自动检测网段</option>
            {networks.map((n) => (
              <option key={n.cidr} value={n.cidr} disabled={n.skippable}>
                {n.cidr}{n.skippable ? ` (${n.skip_reason})` : ''}
              </option>
            ))}
          </select>
        </div>

        {/* 快速模式 */}
        <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={quickMode}
            onChange={(e) => setQuickMode(e.target.checked)}
            disabled={isRunning}
            className="accent-cyan-500"
          />
          快速模式（仅ping）
        </label>

        {/* 操作按钮 */}
        {!isRunning ? (
          <button
            onClick={handleStart}
            className="flex items-center gap-2 bg-cyan-900/60 hover:bg-cyan-800/70 text-cyan-300 border border-cyan-700 rounded px-4 py-2 text-sm transition-colors"
          >
            <Search size={14} />
            开始发现
          </button>
        ) : (
          <button
            onClick={handleStop}
            className="flex items-center gap-2 bg-red-900/60 hover:bg-red-800/70 text-red-300 border border-red-700 rounded px-4 py-2 text-sm transition-colors"
          >
            <Square size={14} />
            停止
          </button>
        )}
      </div>

      {/* ── 进度区（运行中显示）────────────────────────────────────────────── */}
      {isRunning && (
        <div className="bg-[#0a0e17] border border-cyan-900/40 rounded-lg p-4">
          <StepProgress
            currentStep={progress.step}
            totalSteps={progress.total}
            subCurrent={progress.subCurrent}
            subTotal={progress.subTotal}
            message={progress.message}
          />
          {liveHosts.length > 0 && (
            <div className="mt-3 flex items-center gap-2 text-xs text-gray-400">
              <Wifi size={12} className="text-green-400" />
              已发现存活主机：
              {liveHosts.slice(-8).map((ip) => (
                <span key={ip} className="font-mono text-green-400 bg-green-900/20 px-1.5 rounded">
                  {ip}
                </span>
              ))}
              {liveHosts.length > 8 && <span className="text-gray-500">...共 {liveHosts.length} 台</span>}
            </div>
          )}
        </div>
      )}

      {/* ── 结果区 ─────────────────────────────────────────────────────────── */}
      {hosts.length > 0 && (
        <div className="space-y-2 flex-1 overflow-auto">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <Target size={14} className="text-cyan-500" />
              <span>
                {status === 'completed'
                  ? `发现 ${aliveCount} 台存活主机，${hosts.length} 台已评分`
                  : `已评分 ${hosts.length} 台...`}
              </span>
            </div>
            {status === 'completed' && hosts.length > 0 && (
              <button
                onClick={() => handleScanHost(hosts[0].ip)}
                className="flex items-center gap-1.5 text-xs bg-red-900/50 hover:bg-red-800/60 text-red-300 border border-red-800 rounded px-3 py-1.5 transition-colors"
              >
                <Crosshair size={12} />
                扫描 Top1
              </button>
            )}
          </div>

          {hosts.map((host) => (
            <HostCard
              key={host.ip}
              host={host}
              rank={host.rank}
              onScan={handleScanHost}
            />
          ))}
        </div>
      )}

      {/* ── 空状态 ─────────────────────────────────────────────────────────── */}
      {status === 'idle' && hosts.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 text-gray-600 py-12">
          <Globe size={48} className="opacity-30" />
          <div className="text-center">
            <div className="text-sm font-medium text-gray-500">主动靶机发现</div>
            <div className="text-xs mt-1">自动扫描局域网，智能识别并排名最可能的靶机目标</div>
          </div>
          <div className="grid grid-cols-3 gap-3 text-xs text-center mt-2">
            <div className="bg-gray-900 border border-gray-800 rounded p-3">
              <Wifi size={16} className="mx-auto mb-1 text-cyan-600" />
              <div className="text-gray-500">主机探活</div>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded p-3">
              <Shield size={16} className="mx-auto mb-1 text-yellow-600" />
              <div className="text-gray-500">服务指纹</div>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded p-3">
              <Star size={16} className="mx-auto mb-1 text-red-600" />
              <div className="text-gray-500">AI 评分</div>
            </div>
          </div>
        </div>
      )}

      {/* ── 完成空结果提示 ────────────────────────────────────────────────── */}
      {status === 'completed' && hosts.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center gap-3 text-gray-600 py-8">
          <AlertTriangle size={32} className="text-yellow-600 opacity-60" />
          <div className="text-center">
            <div className="text-sm font-medium text-yellow-600">未发现存活主机</div>
            <div className="text-xs mt-1 text-gray-500">
              可能原因：靶机防火墙拦截 ICMP / 需要管理员权限 / 网段内无靶机
            </div>
          </div>
          <button
            onClick={handleStart}
            className="flex items-center gap-2 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 rounded px-3 py-2 transition-colors"
          >
            <RefreshCw size={12} />
            重新扫描
          </button>
        </div>
      )}

      {/* ── 日志面板 ──────────────────────────────────────────────────────── */}
      {logs.length > 0 && (
        <div className="bg-[#060910] border border-gray-800 rounded-lg p-3 max-h-36 overflow-y-auto">
          <div className="text-xs text-gray-600 mb-2 flex items-center gap-1.5">
            <Shield size={10} />
            运行日志
          </div>
          <div className="space-y-1">
            {logs.slice(-50).map((entry, i) => (
              <LogEntry key={i} entry={entry} />
            ))}
            <div ref={logsEndRef} />
          </div>
        </div>
      )}
    </div>
  );
}
