import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ClawAIDashboard from './pages/ClawAIDashboard';
import DesignSystemDemo from './pages/DesignSystemDemo';
import ImplementationSummary from './pages/ImplementationSummary';
import { Home, Palette, TrendingUp, Shield } from 'lucide-react';

function AppWithRouter() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        {/* 导航栏 */}
        <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <div className="flex-shrink-0 flex items-center">
                  <Shield className="h-8 w-8 text-primary-600" />
                  <span className="ml-2 text-xl font-bold text-gray-900 dark:text-white">
                    ClawAI
                  </span>
                </div>
                <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                  <Link
                    to="/"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 dark:text-white border-b-2 border-transparent hover:border-primary-500"
                  >
                    <Home className="h-4 w-4 mr-1" />
                    仪表板
                  </Link>
                  <Link
                    to="/design-system"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 dark:text-gray-400 border-b-2 border-transparent hover:border-primary-500 hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    <Palette className="h-4 w-4 mr-1" />
                    设计系统
                  </Link>
                  <Link
                    to="/implementation"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 dark:text-gray-400 border-b-2 border-transparent hover:border-primary-500 hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    <TrendingUp className="h-4 w-4 mr-1" />
                    实施进度
                  </Link>
                </div>
              </div>
              <div className="flex items-center">
                <a
                  href="https://github.com/yourusername/clawai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                >
                  GitHub
                </a>
              </div>
            </div>
          </div>
        </nav>

        {/* 主要内容 */}
        <main>
          <Routes>
            <Route path="/" element={<ClawAIDashboard />} />
            <Route path="/design-system" element={<DesignSystemDemo />} />
            <Route path="/implementation" element={<ImplementationSummary />} />
          </Routes>
        </main>

        {/* 页脚 */}
        <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <div className="text-center md:text-left">
                <p className="text-base text-gray-500 dark:text-gray-400">
                  © 2024 ClawAI. 保留所有权利。
                </p>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  版本 1.0.0 · 最后更新: 2024年3月
                </p>
              </div>
              <div className="mt-4 md:mt-0">
                <nav className="flex space-x-6">
                  <Link
                    to="/"
                    className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    首页
                  </Link>
                  <Link
                    to="/design-system"
                    className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    设计系统
                  </Link>
                  <Link
                    to="/implementation"
                    className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    实施进度
                  </Link>
                  <a
                    href="#"
                    className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    联系我们
                  </a>
                </nav>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default AppWithRouter;