import React from 'react';
import { cn } from '../utils/cn';

/**
 * 基础骨架组件
 */
export const Skeleton = ({
  className,
  variant = 'rectangular',
  width,
  height,
  rounded = 'md',
  animate = true,
  ...props
}) => {
  const roundedStyles = {
    none: 'rounded-none',
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    full: 'rounded-full'
  };

  const variantStyles = {
    rectangular: '',
    circular: 'rounded-full',
    text: 'rounded h-4'
  };

  return (
    <div
      className={cn(
        'bg-gray-700/50',
        roundedStyles[rounded],
        variantStyles[variant],
        animate && 'animate-pulse',
        className
      )}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height
      }}
      {...props}
    />
  );
};

/**
 * 文本骨架
 */
export const TextSkeleton = ({ lines = 3, className, lineClassName }) => {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          className={cn(
            'h-4',
            i === lines - 1 && 'w-2/3',
            lineClassName
          )}
        />
      ))}
    </div>
  );
};

/**
 * 头像骨架
 */
export const AvatarSkeleton = ({ size = 'md', className }) => {
  const sizes = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  return (
    <Skeleton
      variant="circular"
      className={cn(sizes[size], className)}
    />
  );
};

/**
 * 卡片骨架
 */
export const CardSkeleton = ({ className, showHeader = true, lines = 3 }) => {
  return (
    <div className={cn('bg-gray-800 rounded-xl p-6 space-y-4', className)}>
      {showHeader && (
        <div className="flex items-center justify-between">
          <Skeleton className="h-6 w-1/3" />
          <Skeleton className="h-6 w-16" />
        </div>
      )}
      <TextSkeleton lines={lines} />
    </div>
  );
};

/**
 * 列表项骨架
 */
export const ListItemSkeleton = ({ showAvatar = true, className }) => {
  return (
    <div className={cn('flex items-center space-x-4 p-4', className)}>
      {showAvatar && <AvatarSkeleton />}
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
      <Skeleton className="h-8 w-20 rounded-lg" />
    </div>
  );
};

/**
 * 表格骨架
 */
export const TableSkeleton = ({ rows = 5, columns = 4, className }) => {
  return (
    <div className={cn('overflow-hidden rounded-lg', className)}>
      {/* 表头 */}
      <div className="bg-gray-800 p-4 flex space-x-4">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      {/* 表体 */}
      <div className="divide-y divide-gray-700">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="p-4 flex space-x-4 bg-gray-900/50">
            {Array.from({ length: columns }).map((_, colIndex) => (
              <Skeleton
                key={colIndex}
                className={cn(
                  'h-4 flex-1',
                  colIndex === 0 && 'w-1/4'
                )}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * 扫描结果骨架
 */
export const ScanResultSkeleton = ({ className }) => {
  return (
    <div className={cn('bg-gray-800 rounded-2xl p-8 space-y-6', className)}>
      {/* 标题区域 */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-10 w-10 rounded-full" />
      </div>

      {/* 攻击链 */}
      <div className="space-y-4">
        <Skeleton className="h-6 w-32" />
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="p-4 rounded-lg border-l-4 border-gray-700 bg-gray-700/50"
            >
              <div className="flex justify-between items-start">
                <div className="space-y-2 flex-1">
                  <div className="flex items-center space-x-3">
                    <Skeleton className="h-6 w-20 rounded" />
                    <Skeleton className="h-4 w-32" />
                  </div>
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                </div>
                <div className="text-right space-y-2">
                  <Skeleton className="h-4 w-12" />
                  <Skeleton className="h-4 w-16" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 规则引擎决策 */}
      <div className="p-4 rounded-lg bg-gradient-to-r from-gray-700/30 to-gray-800/30">
        <Skeleton className="h-5 w-32 mb-4" />
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Skeleton className="h-4 w-20 mb-2" />
            <Skeleton className="h-6 w-24" />
          </div>
          <div>
            <Skeleton className="h-4 w-20 mb-2" />
            <Skeleton className="h-6 w-16" />
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * 工具列表骨架
 */
export const ToolListSkeleton = ({ count = 6, className }) => {
  return (
    <div className={cn('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4', className)}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="p-4 rounded-lg bg-gray-800 border border-gray-700">
          <div className="flex justify-between items-start mb-3">
            <div className="space-y-2 flex-1">
              <Skeleton className="h-5 w-24" />
              <Skeleton className="h-3 w-full" />
            </div>
            <Skeleton className="h-6 w-16 rounded" />
          </div>
          <div className="flex space-x-2">
            <Skeleton className="h-5 w-20 rounded" />
            <Skeleton className="h-5 w-16 rounded" />
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * 知识图谱骨架
 */
export const KnowledgeGraphSkeleton = ({ className }) => {
  return (
    <div className={cn('relative', className)}>
      {/* 左侧面板 */}
      <div className="absolute left-0 top-0 w-64 h-full bg-gray-800 rounded-l-lg p-4 space-y-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <div className="grid grid-cols-2 gap-2">
          <Skeleton className="h-10 rounded-lg" />
          <Skeleton className="h-10 rounded-lg" />
        </div>
        <div className="space-y-2 pt-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-full" />
        </div>
      </div>

      {/* 主图区域 */}
      <div className="ml-64 h-96 bg-gray-900 rounded-r-lg flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center space-x-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="w-12 h-12 rounded-full bg-gray-700 animate-pulse"
                style={{ animationDelay: `${i * 200}ms` }}
              />
            ))}
          </div>
          <Skeleton className="h-4 w-32 mx-auto" />
        </div>
      </div>
    </div>
  );
};

/**
 * 仪表板骨架
 */
export const DashboardSkeleton = ({ className }) => {
  return (
    <div className={cn('space-y-8', className)}>
      {/* 状态卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {Array.from({ length: 3 }).map((_, i) => (
          <CardSkeleton key={i} lines={1} />
        ))}
      </div>

      {/* 主扫描区域 */}
      <div className="bg-gray-800 rounded-2xl p-8 space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-64" />
          </div>
          <Skeleton className="h-10 w-10 rounded-full" />
        </div>

        <div className="flex space-x-4">
          <Skeleton className="flex-1 h-12 rounded-lg" />
          <Skeleton className="h-12 w-32 rounded-lg" />
        </div>

        <Skeleton className="h-24 w-full rounded-lg" />
      </div>

      {/* 工具列表 */}
      <div className="space-y-4">
        <Skeleton className="h-8 w-32" />
        <ToolListSkeleton count={6} />
      </div>
    </div>
  );
};

/**
 * 页面加载骨架
 */
export const PageLoadingSkeleton = ({ message = '加载中...' }) => {
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="text-center space-y-4">
        <div className="relative w-16 h-16 mx-auto">
          <div className="absolute inset-0 rounded-full border-4 border-gray-700"></div>
          <div className="absolute inset-0 rounded-full border-4 border-blue-500 border-t-transparent animate-spin"></div>
        </div>
        <p className="text-gray-400">{message}</p>
      </div>
    </div>
  );
};

export default Skeleton;
