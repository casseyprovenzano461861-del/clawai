/**
 * GlowCard — Cyberpunk 风格发光卡片容器
 *
 * 用法：
 *   <GlowCard>内容</GlowCard>
 *   <GlowCard active>激活发光状态</GlowCard>
 *   <GlowCard color="purple" padding="lg">自定义颜色</GlowCard>
 */

import React from 'react';

const COLOR_MAP = {
  cyan:   'rgba(0,212,255',
  blue:   'rgba(59,130,246',
  purple: 'rgba(139,92,246',
  pink:   'rgba(236,72,153',
  green:  'rgba(16,185,129',
  red:    'rgba(239,68,68',
};

const PADDING_MAP = {
  none: '',
  sm:   'p-3',
  md:   'p-4',
  lg:   'p-6',
};

const GlowCard = ({
  children,
  className = '',
  active = false,
  color = 'cyan',
  padding = 'md',
  onClick,
  as: Tag = 'div',
}) => {
  const rgb = COLOR_MAP[color] || COLOR_MAP.cyan;
  const borderOpacity  = active ? '0.55' : '0.18';
  const shadowOpacity  = active ? '0.25' : '0.00';
  const hoverStyle = {
    '--glow-rgb': rgb,
  };

  return (
    <Tag
      onClick={onClick}
      className={[
        'relative rounded-xl transition-all duration-300',
        'bg-[#0a0e17]/85 backdrop-blur-sm',
        PADDING_MAP[padding] || PADDING_MAP.md,
        onClick ? 'cursor-pointer' : '',
        className,
      ].join(' ')}
      style={{
        border: `1px solid ${rgb},${borderOpacity})`,
        boxShadow: active
          ? `0 0 28px ${rgb},${shadowOpacity}), inset 0 0 12px ${rgb},0.04)`
          : 'none',
        ...hoverStyle,
      }}
      onMouseEnter={e => {
        if (active) return;
        e.currentTarget.style.border = `1px solid ${rgb},0.45)`;
        e.currentTarget.style.boxShadow = `0 0 18px ${rgb},0.10)`;
      }}
      onMouseLeave={e => {
        if (active) return;
        e.currentTarget.style.border = `1px solid ${rgb},0.18)`;
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      {children}
    </Tag>
  );
};

export default GlowCard;
