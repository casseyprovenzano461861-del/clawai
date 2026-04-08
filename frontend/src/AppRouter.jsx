import React, { useState, Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import {
  Home, Target, Network, Activity, History, FileText,
  Settings, HelpCircle, Shield, Command, Moon, Sun,
  Zap, Menu, X, ChevronDown
} from 'lucide-react';

// 组件懒加载
const ClawAIDashboard = lazy(() => import('./pages/ClawAIDashboard'));
const KnowledgeGraph = lazy(() => import('./components/KnowledgeGraph'));
const RealTimeMonitor = lazy(() => import('./components/RealTimeMonitor'));
const ScanHistory = lazy(() => import('./components/ScanHistory'));
const ReportGenerator = lazy(() => import('./components/ReportGenerator'));
const PluginManager = lazy(() => import('./components/PluginManager'));

// 导入 UX 组件
import ErrorBoundary from './components/ErrorBoundary';
import CommandPalette from './components/CommandPalette';
import { PageLoadingSkeleton } from './components/Skeleton';
import useKeyboardShortcuts from './hooks/useKeyboardShortcuts';

/**
 * 导航配置
 */
const navigation = [
  { name: '仪表板', href: '/', icon: Home },
  { name: '安全扫描', href: '/scan', icon: Target },
  { name: '知识图谱', href: '/knowledge-graph', icon: Network },
  { name: '实时监控', href: '/monitor', icon: Activity },
  { name: '扫描历史', href: '/history', icon: History },
  { name: '报告管理', href: '/reports', icon: FileText },
  { name: '插件管理', href: '/plugins', icon: Zap },
];

/**
 * 导航栏组件
 */
const Navbar = ({ darkMode, setDarkMode, toggleCommandPalette }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const location = useLocation();

  return (
    <nav className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-b sticky top-0 z-40`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo 和主导航 */}
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Shield className={`h-8 w-8 ${darkMode ? 'text-blue-500' : 'text-blue-600'}`} />
              <span className={`ml-2 text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                ClawAI
              </span>
              <span className={`ml-2 text-xs px-2 py-0.5 rounded ${darkMode ? 'bg-blue-600/20 text-blue-400' : 'bg-blue-100 text-blue-600'}`}>
                v2.0
              </span>
            </div>

            {/* 桌面端导航 */}
            <div className="hidden md:ml-6 md:flex md:space-x-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                      isActive
                        ? darkMode
                          ? 'bg-gray-700 text-white'
                          : 'bg-gray-100 text-gray-900'
                        : darkMode
                          ? 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
                          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>

          {/* 右侧操作区 */}
          <div className="flex items-center space-x-2">
            {/* 命令面板按钮 */}
            <button
              onClick={toggleCommandPalette}
              className={`hidden sm:flex items-center px-3 py-1.5 rounded-lg text-sm ${
                darkMode
                  ? 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
              }`}
            >
              <Command className="w-4 h-4 mr-2" />
              <span>命令面板</span>
              <kbd className="ml-2 px-1.5 py-0.5 rounded text-xs bg-gray-600/30">Ctrl+K</kbd>
            </button>

            {/* 主题切换 */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className={`p-2 rounded-lg ${
                darkMode ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-600'
              }`}
              title={darkMode ? '切换到浅色模式' : '切换到深色模式'}
            >
              {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>

            {/* 帮助 */}
            <button
              className={`p-2 rounded-lg ${
                darkMode ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-600'
              }`}
              title="帮助"
            >
              <HelpCircle className="w-5 h-5" />
            </button>

            {/* 设置 */}
            <button
              className={`p-2 rounded-lg ${
                darkMode ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-600'
              }`}
              title="设置"
            >
              <Settings className="w-5 h-5" />
            </button>

            {/* 用户头像 */}
            <div className="relative">
              <button
                onClick={() => setProfileMenuOpen(!profileMenuOpen)}
                className={`flex items-center space-x-2 p-1 rounded-lg ${
                  darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  darkMode ? 'bg-blue-600' : 'bg-blue-500'
                } text-white text-sm font-medium`}>
                  A
                </div>
                <ChevronDown className={`w-4 h-4 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`} />
              </button>

              {/* 用户菜单 */}
              {profileMenuOpen && (
                <div className={`absolute right-0 mt-2 w-48 rounded-lg shadow-lg ${
                  darkMode ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
                }`}>
                  <div className="py-1">
                    <a href="#" className={`block px-4 py-2 text-sm ${darkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-100'}`}>
                      个人设置
                    </a>
                    <a href="#" className={`block px-4 py-2 text-sm ${darkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-100'}`}>
                      API 密钥
                    </a>
                    <hr className={darkMode ? 'border-gray-700' : 'border-gray-200'} />
                    <a href="#" className={`block px-4 py-2 text-sm text-red-500 ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}>
                      退出登录
                    </a>
                  </div>
                </div>
              )}
            </div>

            {/* 移动端菜单按钮 */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className={`md:hidden p-2 rounded-lg ${
                darkMode ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-600'
              }`}
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* 移动端导航菜单 */}
      {mobileMenuOpen && (
        <div className={`md:hidden border-t ${darkMode ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white'}`}>
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center px-3 py-2 rounded-lg text-base font-medium ${
                    isActive
                      ? darkMode
                        ? 'bg-gray-700 text-white'
                        : 'bg-gray-100 text-gray-900'
                      : darkMode
                        ? 'text-gray-300 hover:bg-gray-700'
                        : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  {item.name}
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </nav>
  );
};

/**
 * 主应用组件
 */
function AppWithRouter() {
  const [darkMode, setDarkMode] = useState(true);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  // 全局快捷键
  useKeyboardShortcuts({
    'ctrl+k': () => setCommandPaletteOpen(true),
  });

  // 命令面板导航
  const handleNavigate = (path) => {
    window.location.href = path;
  };

  return (
    <ErrorBoundary>
      <Router>
        <div className={`min-h-screen ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
          {/* 导航栏 */}
          <Navbar
            darkMode={darkMode}
            setDarkMode={setDarkMode}
            toggleCommandPalette={() => setCommandPaletteOpen(true)}
          />

          {/* 命令面板 */}
          <CommandPalette
            isOpen={commandPaletteOpen}
            onClose={() => setCommandPaletteOpen(false)}
            onNavigate={handleNavigate}
            darkMode={darkMode}
          />

          {/* 主内容区 */}
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <ErrorBoundary>
              <Suspense fallback={<PageLoadingSkeleton />}>
                <Routes>
                  <Route path="/" element={<ClawAIDashboard />} />
                  <Route path="/scan" element={<ClawAIDashboard />} />
                  <Route path="/knowledge-graph" element={<KnowledgeGraph />} />
                  <Route path="/monitor" element={<RealTimeMonitor />} />
                  <Route path="/history" element={<ScanHistory darkMode={darkMode} />} />
                  <Route path="/reports" element={<ReportGenerator />} />
                  <Route path="/plugins" element={<PluginManager />} />
                </Routes>
              </Suspense>
            </ErrorBoundary>
          </main>

          {/* 页脚 */}
          <footer className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-t mt-auto`}>
            <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
              <div className="flex flex-col md:flex-row justify-between items-center">
                <div className="text-center md:text-left">
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    ClawAI v2.0.0 - AI驱动的智能安全评估系统
                  </p>
                </div>
                <div className="mt-4 md:mt-0 flex items-center space-x-6">
                  <span className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                    <kbd className="px-1.5 py-0.5 rounded bg-gray-700/30 mr-1">Ctrl</kbd>
                    <kbd className="px-1.5 py-0.5 rounded bg-gray-700/30">K</kbd>
                    {' '}打开命令面板
                  </span>
                </div>
              </div>
            </div>
          </footer>
        </div>
      </Router>
    </ErrorBoundary>
  );
}

export default AppWithRouter;
