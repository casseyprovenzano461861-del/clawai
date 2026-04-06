// 设计系统工具函数

/**
 * 合并CSS类名
 */
export function cn(...classes: (string | boolean | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}

/**
 * 生成唯一ID
 */
export function generateId(prefix = 'id'): string {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * 格式化数字
 */
export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
}

/**
 * 格式化日期
 */
export function formatDate(date: Date | string, format: 'short' | 'medium' | 'long' = 'medium'): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  
  const formats = {
    short: {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    },
    medium: {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    },
    long: {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long',
    },
  };
  
  return d.toLocaleDateString('zh-CN', formats[format]);
}

/**
 * 格式化时间
 */
export function formatTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 截断文本
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return `${text.substring(0, maxLength)}...`;
}

/**
 * 获取颜色变体
 */
export function getColorVariant(color: string, variant: number): string {
  const colorMap: Record<string, Record<number, string>> = {
    primary: {
      50: 'bg-primary-50',
      100: 'bg-primary-100',
      200: 'bg-primary-200',
      300: 'bg-primary-300',
      400: 'bg-primary-400',
      500: 'bg-primary-500',
      600: 'bg-primary-600',
      700: 'bg-primary-700',
      800: 'bg-primary-800',
      900: 'bg-primary-900',
    },
    gray: {
      50: 'bg-gray-50',
      100: 'bg-gray-100',
      200: 'bg-gray-200',
      300: 'bg-gray-300',
      400: 'bg-gray-400',
      500: 'bg-gray-500',
      600: 'bg-gray-600',
      700: 'bg-gray-700',
      800: 'bg-gray-800',
      900: 'bg-gray-900',
    },
    success: {
      50: 'bg-success-50',
      100: 'bg-success-100',
      200: 'bg-success-200',
      300: 'bg-success-300',
      400: 'bg-success-400',
      500: 'bg-success-500',
      600: 'bg-success-600',
      700: 'bg-success-700',
      800: 'bg-success-800',
      900: 'bg-success-900',
    },
    warning: {
      50: 'bg-warning-50',
      100: 'bg-warning-100',
      200: 'bg-warning-200',
      300: 'bg-warning-300',
      400: 'bg-warning-400',
      500: 'bg-warning-500',
      600: 'bg-warning-600',
      700: 'bg-warning-700',
      800: 'bg-warning-800',
      900: 'bg-warning-900',
    },
    error: {
      50: 'bg-error-50',
      100: 'bg-error-100',
      200: 'bg-error-200',
      300: 'bg-error-300',
      400: 'bg-error-400',
      500: 'bg-error-500',
      600: 'bg-error-600',
      700: 'bg-error-700',
      800: 'bg-error-800',
      900: 'bg-error-900',
    },
  };
  
  return colorMap[color]?.[variant] || '';
}

/**
 * 获取文本颜色
 */
export function getTextColor(color: string, variant: number): string {
  const colorMap: Record<string, Record<number, string>> = {
    primary: {
      50: 'text-primary-50',
      100: 'text-primary-100',
      200: 'text-primary-200',
      300: 'text-primary-300',
      400: 'text-primary-400',
      500: 'text-primary-500',
      600: 'text-primary-600',
      700: 'text-primary-700',
      800: 'text-primary-800',
      900: 'text-primary-900',
    },
    gray: {
      50: 'text-gray-50',
      100: 'text-gray-100',
      200: 'text-gray-200',
      300: 'text-gray-300',
      400: 'text-gray-400',
      500: 'text-gray-500',
      600: 'text-gray-600',
      700: 'text-gray-700',
      800: 'text-gray-800',
      900: 'text-gray-900',
    },
    success: {
      50: 'text-success-50',
      100: 'text-success-100',
      200: 'text-success-200',
      300: 'text-success-300',
      400: 'text-success-400',
      500: 'text-success-500',
      600: 'text-success-600',
      700: 'text-success-700',
      800: 'text-success-800',
      900: 'text-success-900',
    },
    warning: {
      50: 'text-warning-50',
      100: 'text-warning-100',
      200: 'text-warning-200',
      300: 'text-warning-300',
      400: 'text-warning-400',
      500: 'text-warning-500',
      600: 'text-warning-600',
      700: 'text-warning-700',
      800: 'text-warning-800',
      900: 'text-warning-900',
    },
    error: {
      50: 'text-error-50',
      100: 'text-error-100',
      200: 'text-error-200',
      300: 'text-error-300',
      400: 'text-error-400',
      500: 'text-error-500',
      600: 'text-error-600',
      700: 'text-error-700',
      800: 'text-error-800',
      900: 'text-error-900',
    },
  };
  
  return colorMap[color]?.[variant] || '';
}

/**
 * 获取边框颜色
 */
export function getBorderColor(color: string, variant: number): string {
  const colorMap: Record<string, Record<number, string>> = {
    primary: {
      50: 'border-primary-50',
      100: 'border-primary-100',
      200: 'border-primary-200',
      300: 'border-primary-300',
      400: 'border-primary-400',
      500: 'border-primary-500',
      600: 'border-primary-600',
      700: 'border-primary-700',
      800: 'border-primary-800',
      900: 'border-primary-900',
    },
    gray: {
      50: 'border-gray-50',
      100: 'border-gray-100',
      200: 'border-gray-200',
      300: 'border-gray-300',
      400: 'border-gray-400',
      500: 'border-gray-500',
      600: 'border-gray-600',
      700: 'border-gray-700',
      800: 'border-gray-800',
      900: 'border-gray-900',
    },
    success: {
      50: 'border-success-50',
      100: 'border-success-100',
      200: 'border-success-200',
      300: 'border-success-300',
      400: 'border-success-400',
      500: 'border-success-500',
      600: 'border-success-600',
      700: 'border-success-700',
      800: 'border-success-800',
      900: 'border-success-900',
    },
    warning: {
      50: 'border-warning-50',
      100: 'border-warning-100',
      200: 'border-warning-200',
      300: 'border-warning-300',
      400: 'border-warning-400',
      500: 'border-warning-500',
      600: 'border-warning-600',
      700: 'border-warning-700',
      800: 'border-warning-800',
      900: 'border-warning-900',
    },
    error: {
      50: 'border-error-50',
      100: 'border-error-100',
      200: 'border-error-200',
      300: 'border-error-300',
      400: 'border-error-400',
      500: 'border-error-500',
      600: 'border-error-600',
      700: 'border-error-700',
      800: 'border-error-800',
      900: 'border-error-900',
    },
  };
  
  return colorMap[color]?.[variant] || '';
}

/**
 * 验证邮箱格式
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * 验证URL格式
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * 防抖函数
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * 节流函数
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * 深拷贝对象
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * 获取对象嵌套属性值
 */
export function getNestedValue(obj: any, path: string, defaultValue?: any): any {
  const keys = path.split('.');
  let result = obj;
  
  for (const key of keys) {
    if (result && typeof result === 'object' && key in result) {
      result = result[key];
    } else {
      return defaultValue;
    }
  }
  
  return result;
}

/**
 * 设置对象嵌套属性值
 */
export function setNestedValue(obj: any, path: string, value: any): void {
  const keys = path.split('.');
  let current = obj;
  
  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i];
    if (!(key in current) || typeof current[key] !== 'object') {
      current[key] = {};
    }
    current = current[key];
  }
  
  current[keys[keys.length - 1]] = value;
}