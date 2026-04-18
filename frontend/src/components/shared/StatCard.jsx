/**
 * StatCard — 统一统计卡片（增强版）
 * 新增：icon 发光、counter 入场动画、trend 箭头、loading 骨架屏
 *
 * 用法：
 *   <StatCard icon={Shield} label="总扫描数" value={42} />
 *   <StatCard icon={AlertTriangle} label="高危漏洞" value={7} color="red" trend="+2" />
 */

import React, { useEffect, useRef, useState } from 'react';
import GlowCard from './GlowCard';

const COLOR_TEXT = {
  cyan:   'text-cyan-400',
  blue:   'text-blue-400',
  purple: 'text-purple-400',
  green:  'text-emerald-400',
  red:    'text-red-400',
  yellow: 'text-yellow-400',
  pink:   'text-pink-400',
};

const COLOR_BG = {
  cyan:   'bg-cyan-500/10',
  blue:   'bg-blue-500/10',
  purple: 'bg-purple-500/10',
  green:  'bg-emerald-500/10',
  red:    'bg-red-500/10',
  yellow: 'bg-yellow-500/10',
  pink:   'bg-pink-500/10',
};

const COLOR_GLOW = {
  cyan:   '0,212,255',
  blue:   '59,130,246',
  purple: '139,92,246',
  green:  '16,185,129',
  red:    '239,68,68',
  yellow: '245,158,11',
  pink:   '236,72,153',
};

// 数字计数动画 hook
function useCountUp(target, duration = 800) {
  const [display, setDisplay] = useState(0);
  const prevTarget = useRef(0);

  useEffect(() => {
    if (typeof target !== 'number') { setDisplay(target); return; }
    const start = prevTarget.current;
    const diff = target - start;
    if (diff === 0) return;
    const startTime = performance.now();
    const tick = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out-cubic
      setDisplay(Math.round(start + diff * eased));
      if (progress < 1) requestAnimationFrame(tick);
      else prevTarget.current = target;
    };
    requestAnimationFrame(tick);
  }, [target, duration]);

  return typeof target === 'number' ? display : target;
}

const StatCard = ({
  icon: Icon,
  label,
  value,
  unit = '',
  color = 'cyan',
  trend,
  loading = false,
  className = '',
  animate = '',
}) => {
  const textCls = COLOR_TEXT[color] || COLOR_TEXT.cyan;
  const bgCls   = COLOR_BG[color]   || COLOR_BG.cyan;
  const glowRgb = COLOR_GLOW[color] || COLOR_GLOW.cyan;
  const displayVal = useCountUp(typeof value === 'number' ? value : 0);
  const finalDisplay = typeof value === 'number' ? displayVal : value;

  return (
    <GlowCard color={color} padding="md" className={className} animate={animate}>
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1.5 font-medium">{label}</p>
          {loading ? (
            <div className="skeleton h-7 w-20 rounded mb-1" />
          ) : (
            <p className={`text-2xl font-bold ${textCls} leading-none animate-counter tabular-nums`}>
              {finalDisplay}
              {unit && <span className="text-sm font-normal text-gray-400 ml-1">{unit}</span>}
            </p>
          )}
          {trend && !loading && (
            <p className={`text-xs mt-1.5 flex items-center gap-0.5 ${trend.startsWith('+') ? 'text-emerald-400' : 'text-red-400'}`}>
              <span>{trend.startsWith('+') ? '▲' : '▼'}</span>
              <span>{trend.replace(/^[+-]/, '')} 较上次</span>
            </p>
          )}
        </div>
        {Icon && (
          <div
            className={`p-2.5 rounded-lg ${bgCls} ml-3 shrink-0`}
            style={{ boxShadow: `0 0 12px rgba(${glowRgb},0.25)` }}
          >
            <Icon size={18} className={textCls} />
          </div>
        )}
      </div>
    </GlowCard>
  );
};

export default StatCard;
