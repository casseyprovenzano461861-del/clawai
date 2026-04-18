/**
 * GlowCard — Cyberpunk 风格发光卡片容器
 *
 * 用法：
 *   <GlowCard>内容</GlowCard>
 *   <GlowCard active>激活发光状态</GlowCard>
 *   <GlowCard color="purple" padding="lg">自定义颜色</GlowCard>
 *   <GlowCard variant="glass">毛玻璃模式</GlowCard>
 */

import React, { useState } from 'react';

const COLOR_MAP = {
  cyan:   { rgb: '0,212,255'  },
  blue:   { rgb: '59,130,246' },
  purple: { rgb: '139,92,246' },
  pink:   { rgb: '236,72,153' },
  green:  { rgb: '16,185,129' },
  red:    { rgb: '239,68,68'  },
  yellow: { rgb: '245,158,11' },
};

const PADDING_MAP = {
  none: '',
  sm:   'p-3',
  md:   'p-4',
  lg:   'p-6',
  xl:   'p-8',
};

const GlowCard = ({
  children,
  className = '',
  active = false,
  color = 'cyan',
  padding = 'md',
  variant = 'default',  // 'default' | 'glass' | 'solid'
  onClick,
  as: Tag = 'div',
  animate = '',         // 动画类名，如 'animate-slide-up'
}) => {
  const [hovered, setHovered] = useState(false);
  const c = COLOR_MAP[color] || COLOR_MAP.cyan;

  const isActive = active || hovered;
  const borderOpacity = isActive ? '0.5' : '0.15';
  const shadowStr = isActive
    ? `0 0 24px rgba(${c.rgb},0.2), 0 8px 32px rgba(${c.rgb},0.12), inset 0 0 12px rgba(${c.rgb},0.04)`
    : '0 2px 8px rgba(0,0,0,0.3)';

  const bgClass = variant === 'glass'
    ? 'bg-[#060910]/60 backdrop-blur-xl'
    : variant === 'solid'
    ? 'bg-[#0d1220]'
    : 'bg-[#0a0e17]/85 backdrop-blur-sm';

  return (
    <Tag
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={[
        'relative rounded-xl',
        bgClass,
        PADDING_MAP[padding] || PADDING_MAP.md,
        onClick ? 'cursor-pointer' : '',
        animate,
        className,
      ].join(' ')}
      style={{
        border: `1px solid rgba(${c.rgb},${borderOpacity})`,
        boxShadow: shadowStr,
        transition: 'border-color 0.25s ease, box-shadow 0.25s ease, transform 0.2s ease',
        transform: hovered && onClick ? 'translateY(-2px)' : 'translateY(0)',
      }}
    >
      {children}
    </Tag>
  );
};

export default GlowCard;
