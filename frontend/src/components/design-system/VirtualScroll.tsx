import React, { useState, useEffect, useRef, useCallback } from 'react';

export interface VirtualScrollProps<T> {
  items: T[];
  itemHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  overscan?: number;
  className?: string;
  containerHeight?: number | string;
  onScroll?: (scrollTop: number) => void;
  loading?: boolean;
  loadingComponent?: React.ReactNode;
  emptyComponent?: React.ReactNode;
  scrollToIndex?: number;
  onScrollToIndex?: () => void;
}

const VirtualScroll = <T,>({
  items,
  itemHeight,
  renderItem,
  overscan = 5,
  className = '',
  containerHeight = '400px',
  onScroll,
  loading = false,
  loadingComponent,
  emptyComponent,
  scrollToIndex,
  onScrollToIndex,
}: VirtualScrollProps<T>) => {
  const [scrollTop, setScrollTop] = useState(0);
  const [viewportHeight, setViewportHeight] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  // 计算可见项
  const calculateVisibleItems = useCallback(() => {
    if (!containerRef.current) return { startIndex: 0, endIndex: 0 };

    const scrollContainer = containerRef.current;
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      items.length - 1,
      Math.floor((scrollTop + viewportHeight) / itemHeight) + overscan
    );

    return { startIndex, endIndex };
  }, [scrollTop, viewportHeight, itemHeight, items.length, overscan]);

  // 处理滚动
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const newScrollTop = e.currentTarget.scrollTop;
    setScrollTop(newScrollTop);
    onScroll?.(newScrollTop);
  }, [onScroll]);

  // 更新视口高度
  useEffect(() => {
    const updateViewportHeight = () => {
      if (containerRef.current) {
        setViewportHeight(containerRef.current.clientHeight);
      }
    };

    updateViewportHeight();
    window.addEventListener('resize', updateViewportHeight);

    return () => {
      window.removeEventListener('resize', updateViewportHeight);
    };
  }, []);

  // 滚动到指定索引
  useEffect(() => {
    if (scrollToIndex !== undefined && containerRef.current) {
      const scrollPosition = scrollToIndex * itemHeight;
      containerRef.current.scrollTo({
        top: scrollPosition,
        behavior: 'smooth',
      });
      onScrollToIndex?.();
    }
  }, [scrollToIndex, itemHeight, onScrollToIndex]);

  // 计算可见项
  const { startIndex, endIndex } = calculateVisibleItems();
  const visibleItems = items.slice(startIndex, endIndex + 1);

  // 计算内容高度和偏移量
  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  // 默认加载组件
  const defaultLoadingComponent = (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
        <p className="mt-2 text-gray-500">加载中...</p>
      </div>
    </div>
  );

  // 默认空状态组件
  const defaultEmptyComponent = (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="text-gray-400 text-4xl mb-2">📭</div>
        <p className="text-gray-500">暂无数据</p>
      </div>
    </div>
  );

  return (
    <div
      ref={containerRef}
      className={`overflow-auto ${className}`}
      style={{ height: containerHeight }}
      onScroll={handleScroll}
    >
      {/* 内容容器 */}
      <div
        ref={contentRef}
        style={{
          height: totalHeight,
          position: 'relative',
        }}
      >
        {/* 可见项 */}
        <div
          style={{
            position: 'absolute',
            top: offsetY,
            left: 0,
            right: 0,
          }}
        >
          {loading ? (
            loadingComponent || defaultLoadingComponent
          ) : items.length === 0 ? (
            emptyComponent || defaultEmptyComponent
          ) : (
            visibleItems.map((item, index) => {
              const actualIndex = startIndex + index;
              return (
                <div
                  key={actualIndex}
                  style={{
                    height: itemHeight,
                  }}
                >
                  {renderItem(item, actualIndex)}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* 滚动指示器 */}
      {items.length > 0 && (
        <div className="fixed bottom-4 right-4 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-75">
          {startIndex + 1}-{Math.min(endIndex + 1, items.length)} / {items.length}
        </div>
      )}
    </div>
  );
};

// 虚拟列表项组件
export interface VirtualListItemProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  selected?: boolean;
  hoverable?: boolean;
}

export const VirtualListItem: React.FC<VirtualListItemProps> = ({
  children,
  className = '',
  onClick,
  selected = false,
  hoverable = true,
}) => {
  return (
    <div
      className={`
        border-b border-gray-200 dark:border-gray-700
        ${selected ? 'bg-primary-50 dark:bg-primary-900/20' : ''}
        ${hoverable ? 'hover:bg-gray-50 dark:hover:bg-gray-800' : ''}
        ${onClick ? 'cursor-pointer' : ''}
        transition-colors duration-150
        ${className}
      `}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

// 虚拟表格组件
export interface VirtualTableProps<T> extends Omit<VirtualScrollProps<T>, 'renderItem'> {
  columns: Array<{
    key: string;
    title: string;
    width?: string;
    render?: (item: T, index: number) => React.ReactNode;
  }>;
  renderRow?: (item: T, index: number) => React.ReactNode;
  headerSticky?: boolean;
}

export const VirtualTable = <T,>({
  columns,
  renderRow,
  headerSticky = true,
  ...props
}: VirtualTableProps<T>) => {
  const defaultRenderItem = (item: T, index: number) => {
    if (renderRow) {
      return renderRow(item, index);
    }

    return (
      <VirtualListItem>
        <div className="flex">
          {columns.map((column) => (
            <div
              key={column.key}
              className="px-4 py-3"
              style={{ width: column.width || 'auto' }}
            >
              {column.render
                ? column.render(item, index)
                : (item as any)[column.key]}
            </div>
          ))}
        </div>
      </VirtualListItem>
    );
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      {/* 表头 */}
      {headerSticky && (
        <div className="sticky top-0 z-10 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="flex">
            {columns.map((column) => (
              <div
                key={column.key}
                className="px-4 py-3 font-medium text-gray-700 dark:text-gray-300"
                style={{ width: column.width || 'auto' }}
              >
                {column.title}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 虚拟滚动内容 */}
      <VirtualScroll
        {...props}
        renderItem={defaultRenderItem}
      />
    </div>
  );
};

export default VirtualScroll;