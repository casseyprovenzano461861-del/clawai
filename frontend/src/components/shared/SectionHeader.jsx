/**
 * SectionHeader — 统一区块标题组件
 *
 * 用法：
 *   <SectionHeader title="活动代理" icon={Activity} />
 *   <SectionHeader title="漏洞发现" icon={Bug} count={7} action={<button>清除</button>} />
 */

import React from 'react';

const SectionHeader = ({
  title,
  icon: Icon,
  count,
  action,
  className = '',
}) => (
  <div className={`flex items-center justify-between mb-3 ${className}`}>
    <div className="flex items-center gap-2">
      {Icon && <Icon size={15} className="text-cyan-400 shrink-0" />}
      <h3 className="text-sm font-semibold text-gray-200 uppercase tracking-wide">{title}</h3>
      {count !== undefined && (
        <span className="text-xs px-1.5 py-0.5 rounded bg-cyan-500/15 text-cyan-400 font-mono">
          {count}
        </span>
      )}
    </div>
    {action && <div className="shrink-0">{action}</div>}
  </div>
);

export default SectionHeader;
