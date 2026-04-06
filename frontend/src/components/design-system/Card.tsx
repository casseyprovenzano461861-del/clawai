import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'flat' | 'ghost';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hoverable?: boolean;
  bordered?: boolean;
}

const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  padding = 'md',
  hoverable = false,
  bordered = true,
  className = '',
  ...props
}) => {
  // 基础样式类
  const baseClasses = 'rounded-lg transition-all duration-200';
  
  // 变体样式
  const variantClasses = {
    default: 'bg-white dark:bg-gray-800',
    elevated: 'bg-white dark:bg-gray-800 shadow-lg',
    flat: 'bg-transparent',
    ghost: 'bg-transparent border-transparent',
  };
  
  // 内边距样式
  const paddingClasses = {
    none: 'p-0',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };
  
  // 边框样式
  const borderClass = bordered ? 'border border-gray-200 dark:border-gray-700' : '';
  
  // 悬停效果
  const hoverClass = hoverable ? 'hover:shadow-md hover:-translate-y-1' : '';
  
  // 组合所有样式
  const cardClasses = [
    baseClasses,
    variantClasses[variant],
    paddingClasses[padding],
    borderClass,
    hoverClass,
    className,
  ].filter(Boolean).join(' ');
  
  return (
    <div className={cardClasses} {...props}>
      {children}
    </div>
  );
};

// 卡片标题组件
export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
}

export const CardTitle: React.FC<CardTitleProps> = ({
  children,
  as: Component = 'h3',
  className = '',
  ...props
}) => {
  return (
    <Component
      className={`text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2 ${className}`}
      {...props}
    >
      {children}
    </Component>
  );
};

// 卡片内容组件
export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {}

export const CardContent: React.FC<CardContentProps> = ({
  children,
  className = '',
  ...props
}) => {
  return (
    <div className={`text-gray-600 dark:text-gray-400 ${className}`} {...props}>
      {children}
    </div>
  );
};

// 卡片页脚组件
export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  align?: 'left' | 'center' | 'right';
}

export const CardFooter: React.FC<CardFooterProps> = ({
  children,
  align = 'left',
  className = '',
  ...props
}) => {
  const alignClasses = {
    left: 'justify-start',
    center: 'justify-center',
    right: 'justify-end',
  };
  
  return (
    <div
      className={`flex items-center ${alignClasses[align]} mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
export { Card };