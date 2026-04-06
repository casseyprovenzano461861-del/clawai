import React from 'react';
import { ChevronUp, ChevronDown, Filter, MoreVertical } from 'lucide-react';
import { Button } from './Button';

export interface TableColumn<T> {
  key: string;
  title: string;
  width?: string | number;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  render?: (value: any, row: T, index: number) => React.ReactNode;
}

export interface TableProps<T> {
  columns: TableColumn<T>[];
  data: T[];
  loading?: boolean;
  emptyText?: string;
  striped?: boolean;
  hoverable?: boolean;
  bordered?: boolean;
  compact?: boolean;
  onRowClick?: (row: T, index: number) => void;
  onSort?: (key: string, direction: 'asc' | 'desc') => void;
  sortKey?: string;
  sortDirection?: 'asc' | 'desc';
  pagination?: {
    current: number;
    total: number;
    pageSize: number;
    onChange: (page: number) => void;
  };
  selection?: {
    selectedKeys: string[];
    onChange: (selectedKeys: string[]) => void;
    rowKey: string;
  };
  actions?: (row: T) => React.ReactNode;
  className?: string;
}

const Table = <T extends Record<string, any>>({
  columns,
  data,
  loading = false,
  emptyText = '暂无数据',
  striped = true,
  hoverable = true,
  bordered = true,
  compact = false,
  onRowClick,
  onSort,
  sortKey,
  sortDirection,
  pagination,
  selection,
  actions,
  className = '',
}: TableProps<T>) => {
  // 处理排序点击
  const handleSortClick = (column: TableColumn<T>) => {
    if (column.sortable && onSort) {
      const newDirection = sortKey === column.key && sortDirection === 'asc' ? 'desc' : 'asc';
      onSort(column.key, newDirection);
    }
  };

  // 处理行选择
  const handleRowSelect = (row: T) => {
    if (!selection) return;
    
    const key = row[selection.rowKey];
    const isSelected = selection.selectedKeys.includes(key);
    
    const newSelectedKeys = isSelected
      ? selection.selectedKeys.filter(k => k !== key)
      : [...selection.selectedKeys, key];
    
    selection.onChange(newSelectedKeys);
  };

  // 处理全选
  const handleSelectAll = () => {
    if (!selection) return;
    
    const allKeys = data.map(row => row[selection.rowKey]);
    const newSelectedKeys = selection.selectedKeys.length === data.length
      ? []
      : allKeys;
    
    selection.onChange(newSelectedKeys);
  };

  // 渲染单元格内容
  const renderCell = (column: TableColumn<T>, row: T, index: number) => {
    const value = row[column.key];
    
    if (column.render) {
      return column.render(value, row, index);
    }
    
    return value;
  };

  // 表格类名
  const tableClasses = [
    'w-full',
    bordered ? 'border border-gray-200 dark:border-gray-700' : '',
    compact ? 'text-sm' : 'text-base',
    className,
  ].filter(Boolean).join(' ');

  // 行类名
  const getRowClasses = (index: number, row: T) => {
    const isSelected = selection?.selectedKeys.includes(row[selection.rowKey]);
    
    return [
      'transition-colors',
      striped && index % 2 === 1 ? 'bg-gray-50 dark:bg-gray-800/50' : '',
      hoverable ? 'hover:bg-gray-100 dark:hover:bg-gray-700' : '',
      isSelected ? 'bg-primary-50 dark:bg-primary-900/20' : '',
      onRowClick ? 'cursor-pointer' : '',
    ].filter(Boolean).join(' ');
  };

  // 分页组件
  const renderPagination = () => {
    if (!pagination) return null;
    
    const { current, total, pageSize, onChange } = pagination;
    const totalPages = Math.ceil(total / pageSize);
    
    if (totalPages <= 1) return null;
    
    const pages = [];
    const maxVisible = 5;
    
    // 计算显示的页码
    let startPage = Math.max(1, current - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage + 1 < maxVisible) {
      startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    return (
      <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
        <div className="text-sm text-gray-700 dark:text-gray-300">
          共 {total} 条记录，第 {current} / {totalPages} 页
        </div>
        
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onChange(current - 1)}
            disabled={current === 1}
          >
            上一页
          </Button>
          
          {pages.map(page => (
            <Button
              key={page}
              variant={page === current ? 'primary' : 'outline'}
              size="sm"
              onClick={() => onChange(page)}
            >
              {page}
            </Button>
          ))}
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => onChange(current + 1)}
            disabled={current === totalPages}
          >
            下一页
          </Button>
        </div>
      </div>
    );
  };

  return (
    <div className="overflow-hidden rounded-lg">
      <table className={tableClasses}>
        {/* 表头 */}
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            {/* 选择列 */}
            {selection && (
              <th className="px-4 py-3 text-left">
                <input
                  type="checkbox"
                  checked={data.length > 0 && selection.selectedKeys.length === data.length}
                  onChange={handleSelectAll}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
              </th>
            )}
            
            {/* 数据列 */}
            {columns.map(column => (
              <th
                key={column.key}
                className={`
                  px-4 py-3 text-left font-medium text-gray-700 dark:text-gray-300
                  ${column.align === 'center' ? 'text-center' : ''}
                  ${column.align === 'right' ? 'text-right' : ''}
                  ${column.sortable ? 'cursor-pointer select-none' : ''}
                `}
                style={{ width: column.width }}
                onClick={() => handleSortClick(column)}
              >
                <div className={`flex items-center gap-1 ${column.align === 'center' ? 'justify-center' : column.align === 'right' ? 'justify-end' : ''}`}>
                  {column.title}
                  
                  {column.sortable && (
                    <div className="flex flex-col">
                      <ChevronUp
                        className={`h-3 w-3 ${
                          sortKey === column.key && sortDirection === 'asc'
                            ? 'text-primary-600'
                            : 'text-gray-400'
                        }`}
                      />
                      <ChevronDown
                        className={`h-3 w-3 -mt-1 ${
                          sortKey === column.key && sortDirection === 'desc'
                            ? 'text-primary-600'
                            : 'text-gray-400'
                        }`}
                      />
                    </div>
                  )}
                </div>
              </th>
            ))}
            
            {/* 操作列 */}
            {actions && (
              <th className="px-4 py-3 text-right">
                <MoreVertical className="h-4 w-4 text-gray-400" />
              </th>
            )}
          </tr>
        </thead>
        
        {/* 表格内容 */}
        <tbody>
          {loading ? (
            <tr>
              <td
                colSpan={columns.length + (selection ? 1 : 0) + (actions ? 1 : 0)}
                className="px-4 py-8 text-center"
              >
                <div className="flex flex-col items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                  <p className="mt-2 text-gray-500">加载中...</p>
                </div>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length + (selection ? 1 : 0) + (actions ? 1 : 0)}
                className="px-4 py-8 text-center text-gray-500"
              >
                {emptyText}
              </td>
            </tr>
          ) : (
            data.map((row, index) => (
              <tr
                key={index}
                className={getRowClasses(index, row)}
                onClick={() => onRowClick?.(row, index)}
              >
                {/* 选择单元格 */}
                {selection && (
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selection.selectedKeys.includes(row[selection.rowKey])}
                      onChange={() => handleRowSelect(row)}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      onClick={(e) => e.stopPropagation()}
                    />
                  </td>
                )}
                
                {/* 数据单元格 */}
                {columns.map(column => (
                  <td
                    key={`${index}-${column.key}`}
                    className={`
                      px-4 py-3 border-t border-gray-200 dark:border-gray-700
                      ${column.align === 'center' ? 'text-center' : ''}
                      ${column.align === 'right' ? 'text-right' : ''}
                    `}
                  >
                    {renderCell(column, row, index)}
                  </td>
                ))}
                
                {/* 操作单元格 */}
                {actions && (
                  <td className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 text-right">
                    <div onClick={(e) => e.stopPropagation()}>
                      {actions(row)}
                    </div>
                  </td>
                )}
              </tr>
            ))
          )}
        </tbody>
      </table>
      
      {/* 分页 */}
      {renderPagination()}
    </div>
  );
};

export default Table;