import React, { useState, useEffect } from 'react';
import { Sun, Moon } from 'lucide-react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeToggleProps {
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({
  showLabel = false,
  size = 'md',
}) => {
  const [theme, setTheme] = useState<Theme>('system');
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light');

  // 初始化主题
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as Theme | null;
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme) {
      setTheme(savedTheme);
      applyTheme(savedTheme);
    } else {
      setTheme('system');
      applyTheme('system');
    }
    
    // 监听系统主题变化
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      if (theme === 'system') {
        applyTheme('system');
      }
    };
    
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // 应用主题
  const applyTheme = (selectedTheme: Theme) => {
    let themeToApply: 'light' | 'dark';
    
    if (selectedTheme === 'system') {
      const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      themeToApply = systemPrefersDark ? 'dark' : 'light';
    } else {
      themeToApply = selectedTheme;
    }
    
    // 更新DOM
    if (themeToApply === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    
    setResolvedTheme(themeToApply);
    localStorage.setItem('theme', selectedTheme);
  };

  // 切换主题
  const toggleTheme = () => {
    const themes: Theme[] = ['light', 'dark', 'system'];
    const currentIndex = themes.indexOf(theme);
    const nextIndex = (currentIndex + 1) % themes.length;
    const nextTheme = themes[nextIndex];
    
    setTheme(nextTheme);
    applyTheme(nextTheme);
  };

  // 直接设置主题
  const setThemeDirectly = (selectedTheme: Theme) => {
    setTheme(selectedTheme);
    applyTheme(selectedTheme);
  };

  // 大小样式
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12',
  };

  // 图标大小
  const iconSizes = {
    sm: 16,
    md: 20,
    lg: 24,
  };

  // 获取当前主题标签
  const getThemeLabel = () => {
    switch (theme) {
      case 'light':
        return '浅色模式';
      case 'dark':
        return '深色模式';
      case 'system':
        return '跟随系统';
      default:
        return '主题';
    }
  };

  return (
    <div className="flex items-center gap-2">
      {showLabel && (
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {getThemeLabel()}
        </span>
      )}
      
      <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-full p-1">
        <button
          onClick={() => setThemeDirectly('light')}
          className={`flex items-center justify-center rounded-full p-2 transition-colors ${
            theme === 'light'
              ? 'bg-white text-gray-900 shadow'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
          }`}
          aria-label="浅色模式"
          title="浅色模式"
        >
          <Sun size={iconSizes[size]} />
        </button>
        
        <button
          onClick={() => setThemeDirectly('dark')}
          className={`flex items-center justify-center rounded-full p-2 transition-colors ${
            theme === 'dark'
              ? 'bg-gray-800 text-white shadow'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
          }`}
          aria-label="深色模式"
          title="深色模式"
        >
          <Moon size={iconSizes[size]} />
        </button>
        
        <button
          onClick={() => setThemeDirectly('system')}
          className={`flex items-center justify-center rounded-full p-2 transition-colors ${
            theme === 'system'
              ? 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400 shadow'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
          }`}
          aria-label="跟随系统"
          title="跟随系统"
        >
          <svg
            className={sizeClasses[size]}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
        </button>
      </div>
      
      {/* 主题状态指示器 */}
      <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
        <div className={`w-2 h-2 rounded-full ${
          resolvedTheme === 'dark' ? 'bg-gray-800' : 'bg-gray-300'
        }`} />
        <span>{resolvedTheme === 'dark' ? '深色' : '浅色'}</span>
      </div>
    </div>
  );
};

export default ThemeToggle;