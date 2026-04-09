import React from 'react';

/**
 * CyberInput - 统一的赛博朋克风格输入组件
 *
 * 合并自 Login.jsx 和 Register.jsx 的内联 CyberInput 定义。
 * 使用 input-cyber CSS 类（定义在 index.css）。
 *
 * Props:
 *   icon     - Lucide icon 组件（可选）
 *   label    - 标签文本（可选）
 *   required - 是否必填，显示红色 * 标记
 *   error    - 错误提示文本（可选）
 *   children - 右侧插槽（如密码显示/隐藏按钮）
 *   ...props - 传递给 <input> 的其余属性
 */
const CyberInput = ({ icon: Icon, label, required, error, children, ...props }) => (
  <div className={label ? 'mb-4' : ''}>
    {label && (
      <label className="block text-xs font-medium text-cyan-400/70 uppercase tracking-wider mb-1.5">
        {label}{required && <span className="text-neon-pink ml-1">*</span>}
      </label>
    )}
    <div className="relative">
      {Icon && (
        <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyan-500/60 pointer-events-none" />
      )}
      <input
        className={`input-cyber w-full ${Icon ? 'pl-10' : 'pl-4'} ${props.type === 'password' ? 'pr-10' : 'pr-4'} py-2.5 text-sm`}
        {...props}
      />
      {children}
    </div>
    {error && (
      <p className="mt-1 text-xs text-red-400">{error}</p>
    )}
  </div>
);

export default CyberInput;
