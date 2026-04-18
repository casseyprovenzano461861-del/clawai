import React, { Suspense, lazy, Component } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';

import AppShell from './components/layout/AppShell';
import { PageLoadingSkeleton } from './components/Skeleton';
import { ScanProvider } from './context/ScanContext';
import { PERAgentProvider } from './context/PERAgentContext';

const Dashboard     = lazy(() => import('./pages/Dashboard'));
const AttackMap     = lazy(() => import('./pages/AttackMap'));
const Reports       = lazy(() => import('./pages/Reports'));
const PluginManager = lazy(() => import('./components/PluginManager'));

const Loader = () => <PageLoadingSkeleton />;

/** 页面级错误边界：显示内联错误，不会跳转路由 */
class PageErrorBoundary extends Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('[PageErrorBoundary]', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-full min-h-[60vh] gap-4 p-8">
          <div className="text-red-400 text-4xl">⚠</div>
          <p className="text-gray-300 font-mono text-sm">页面加载失败</p>
          <p className="text-gray-600 text-xs max-w-md text-center break-all">
            {this.state.error?.message}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-2 px-4 py-2 text-xs rounded-lg border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10 transition-colors"
          >
            重试
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

/** 稳定包装：Suspense + 页面级错误边界，不会触发路由跳转 */
const PageWrapper = ({ children }) => (
  <PageErrorBoundary>
    <Suspense fallback={<Loader />}>
      {children}
    </Suspense>
  </PageErrorBoundary>
);

const AppRouter = () => (
  <Router>
    <ScanProvider>
      <PERAgentProvider>
        <Routes>
          <Route element={<AppShell />}>
            <Route index              element={<PageWrapper><Dashboard /></PageWrapper>} />
            <Route path="/attack-map" element={<PageWrapper><AttackMap /></PageWrapper>} />
            <Route path="/reports"    element={<PageWrapper><Reports /></PageWrapper>} />
            <Route path="/plugins"    element={<PageWrapper><PluginManager /></PageWrapper>} />
          </Route>
          <Route path="/login"    element={<Navigate to="/" replace />} />
          <Route path="/register" element={<Navigate to="/" replace />} />
          <Route path="*"         element={<Navigate to="/" replace />} />
        </Routes>
      </PERAgentProvider>
    </ScanProvider>
  </Router>
);

export default AppRouter;
