import React from 'react';
import { AlertCircle, CheckCircle, Info, XCircle, X } from 'lucide-react';

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  dismissible?: boolean;
  onDismiss?: () => void;
}

const Alert: React.FC<AlertProps> = ({
  children,
  variant = 'info',
  title,
  dismissible = false,
  onDismiss,
  className = '',
  ...props
}) => {
  // 基础样式类
  const baseClasses = 'rounded-lg p-4';
  
  // 变体样式
  const variantConfig = {
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-800',
      icon: Info,
    },
    success: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-800',
      icon: CheckCircle,
    },
    warning: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      text: 'text-yellow-800',
      icon: AlertCircle,
    },
    error: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-800',
      icon: XCircle,
    },
  };
  
  const config = variantConfig[variant];
  const Icon = config.icon;
  
  // 组合所有样式
  const alertClasses = [
    baseClasses,
    config.bg,
    config.text,
    'border',
    config.border,
    className,
  ].filter(Boolean).join(' ');
  
  return (
    <div className={alertClasses} role="alert" {...props}>
      <div className="flex">
        <div className="flex-shrink-0">
          <Icon className={`h-5 w-5 ${config.text}`} />
        </div>
        
        <div className="ml-3 flex-1">
          {title && (
            <h3 className="text-sm font-medium">{title}</h3>
          )}
          
          <div className={`text-sm ${title ? 'mt-2' : ''}`}>
            {children}
          </div>
        </div>
        
        {dismissible && (
          <div className="ml-auto pl-3">
            <button
              type="button"
              className={`inline-flex rounded-md ${config.bg} ${config.text} hover:${config.bg.replace('50', '100')} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-${config.bg.replace('bg-', '')} focus:ring-${config.text.replace('text-', '')}`}
              onClick={onDismiss}
              aria-label="Dismiss"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Alert;