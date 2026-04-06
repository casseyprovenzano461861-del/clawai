import React, { forwardRef } from 'react';
import { LucideIcon } from 'lucide-react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  icon?: LucideIcon;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      icon: Icon,
      iconPosition = 'left',
      fullWidth = true,
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    // 基础样式类
    const baseClasses = 'block rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed';
    
    // 错误状态样式
    const errorClasses = error ? 'border-error-500 focus:border-error-500 focus:ring-error-500' : '';
    
    // 图标样式
    const iconClasses = Icon ? (iconPosition === 'left' ? 'pl-10' : 'pr-10') : '';
    
    // 宽度样式
    const widthClass = fullWidth ? 'w-full' : '';
    
    // 组合输入框样式
    const inputClasses = [
      baseClasses,
      errorClasses,
      iconClasses,
      widthClass,
      className,
    ].filter(Boolean).join(' ');
    
    return (
      <div className={fullWidth ? 'w-full' : ''}>
        {label && (
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {label}
            {props.required && <span className="text-error-500 ml-1">*</span>}
          </label>
        )}
        
        <div className="relative">
          {Icon && iconPosition === 'left' && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Icon className="h-5 w-5 text-gray-400" />
            </div>
          )}
          
          <input
            ref={ref}
            className={inputClasses}
            disabled={disabled}
            aria-invalid={!!error}
            aria-describedby={error ? `${props.id}-error` : helperText ? `${props.id}-helper` : undefined}
            {...props}
          />
          
          {Icon && iconPosition === 'right' && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <Icon className="h-5 w-5 text-gray-400" />
            </div>
          )}
        </div>
        
        {error && (
          <p id={`${props.id}-error`} className="mt-1 text-sm text-error-600">
            {error}
          </p>
        )}
        
        {helperText && !error && (
          <p id={`${props.id}-helper`} className="mt-1 text-sm text-gray-500">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;