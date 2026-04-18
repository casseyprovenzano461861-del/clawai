/**
 * Skeleton — 统一骨架屏组件
 *
 * 用法：
 *   <Skeleton />                    — 单行文本骨架
 *   <Skeleton width="60px" height="60px" rounded="full" />  — 头像骨架
 *   <Skeleton variant="card" />     — 卡片骨架
 *   <SkeletonList count={4} />      — 列表骨架（4行）
 */

import React from 'react';

const ROUNDED = {
  sm:   '4px',
  md:   '6px',
  lg:   '8px',
  xl:   '12px',
  full: '9999px',
};

export const Skeleton = ({
  width = '100%',
  height = '14px',
  rounded = 'md',
  className = '',
  style = {},
}) => (
  <div
    className={`skeleton ${className}`}
    style={{
      width,
      height,
      borderRadius: ROUNDED[rounded] || rounded,
      ...style,
    }}
  />
);

// 卡片骨架
export const SkeletonCard = ({ className = '' }) => (
  <div className={`bg-[#0a0e17]/85 rounded-xl p-4 border border-white/5 ${className}`}>
    <div className="flex items-start justify-between mb-3">
      <div className="flex-1">
        <Skeleton width="40%" height="10px" className="mb-2" />
        <Skeleton width="60%" height="24px" />
      </div>
      <Skeleton width="38px" height="38px" rounded="lg" />
    </div>
    <Skeleton width="30%" height="10px" />
  </div>
);

// 列表项骨架
export const SkeletonListItem = ({ className = '' }) => (
  <div className={`flex items-center gap-3 py-2.5 ${className}`}>
    <Skeleton width="32px" height="32px" rounded="lg" />
    <div className="flex-1">
      <Skeleton width="45%" height="12px" className="mb-1.5" />
      <Skeleton width="70%" height="10px" />
    </div>
    <Skeleton width="50px" height="20px" rounded="full" />
  </div>
);

// 列表骨架（多行）
export const SkeletonList = ({ count = 3, className = '' }) => (
  <div className={`divide-y divide-white/5 ${className}`}>
    {Array.from({ length: count }).map((_, i) => (
      <SkeletonListItem key={i} />
    ))}
  </div>
);

// 文本块骨架
export const SkeletonText = ({ lines = 3, className = '' }) => (
  <div className={`space-y-2 ${className}`}>
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton
        key={i}
        width={i === lines - 1 ? '65%' : '100%'}
        height="12px"
      />
    ))}
  </div>
);

export default Skeleton;
