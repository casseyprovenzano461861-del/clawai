import React from 'react';
import { LucideIcon } from 'lucide-react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md' | 'lg';
  icon?: LucideIcon;
  iconPosition?: 'left' | 'right';
  rounded?: 'sm' | 'md' | 'lg' | 'full';
}

const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon: Icon,
  iconPosition = 'left',
  rounded = 'full',
  className = '',
  ...props
}) => {
  // 基础样式类
  const baseClasses = 'inline-flex items-center font-medium';
  
  // 变体样式
  const variantClasses = {
    primary: 'bg-primary-100 text-primary-800',
    secondary: 'bg-gray-100 text-gray-800',
    success: 'bg-success-100 text-success-800',
    warning: 'bg-warning-100 text-warning-800',
    error: 'bg-error-100 text-error-800',
    info: 'bg-blue-100 text-blue-800',
  };
  
  // 大小样式
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-base',
  };
  
  // 圆角样式
  const roundedClasses = {
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    full: 'rounded-full',
  };
  
  // 组合所有样式
  const badgeClasses = [
    baseClasses,
    variantClasses[variant],
    sizeClasses[size],
    roundedClasses[rounded],
    className,
  ].filter(Boolean).join(' ');
  
  return (
    <span className={badgeClasses} {...props}>
      {Icon && iconPosition === 'left' && (
        <Icon className="mr-1 h-3 w-3" />
      )}
      {children}
      {Icon && iconPosition === 'right' && (
        <Icon className="ml-1 h-3 w-3" />
      )}
    </span>
  );
};

export default Badge;