/**
 * StatCard — 统一统计卡片
 * 替代三处分散的 StatCard / MetricCard 实现
 *
 * 用法：
 *   <StatCard icon={Shield} label="总扫描数" value={42} />
 *   <StatCard icon={AlertTriangle} label="高危漏洞" value={7} color="red" trend="+2" />
 */

import React from 'react';
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

const StatCard = ({
  icon: Icon,
  label,
  value,
  unit = '',
  color = 'cyan',
  trend,
  loading = false,
  className = '',
}) => {
  const textCls = COLOR_TEXT[color] || COLOR_TEXT.cyan;
  const bgCls   = COLOR_BG[color]   || COLOR_BG.cyan;

  return (
    <GlowCard color={color} padding="md" className={className}>
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1.5">{label}</p>
          {loading ? (
            <div className="h-7 w-16 bg-gray-800 rounded animate-pulse" />
          ) : (
            <p className={`text-2xl font-bold ${textCls} leading-none`}>
              {value}
              {unit && <span className="text-sm font-normal text-gray-400 ml-1">{unit}</span>}
            </p>
          )}
          {trend && !loading && (
            <p className={`text-xs mt-1.5 ${trend.startsWith('+') ? 'text-emerald-400' : 'text-red-400'}`}>
              {trend} 较上次
            </p>
          )}
        </div>
        {Icon && (
          <div className={`p-2.5 rounded-lg ${bgCls} ml-3 shrink-0`}>
            <Icon size={18} className={textCls} />
          </div>
        )}
      </div>
    </GlowCard>
  );
};

export default StatCard;
