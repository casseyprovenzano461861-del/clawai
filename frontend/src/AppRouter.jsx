/**
 * AppRouter — 路由配置（精简版，布局由 AppShell 承担）
 */

import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import AppShell from './components/layout/AppShell';
import ErrorBoundary from './components/ErrorBoundary';
import { PageLoadingSkeleton } from './components/Skeleton';
import { ScanProvider } from './context/ScanContext';

// 懒加载页面
const Dashboard     = lazy(() => import('./pages/Dashboard'));
const Monitor       = lazy(() => import('./components/RealTimeMonitor'));
const KnowledgeGraph = lazy(() => import('./components/KnowledgeGraph'));
const ScanHistory   = lazy(() => import('./components/ScanHistory'));
const ReportGenerator = lazy(() => import('./components/ReportGenerator'));
const PluginManager = lazy(() => import('./components/PluginManager'));
const Login         = lazy(() => import('./pages/Login'));
const Register      = lazy(() => import('./pages/Register'));

const Loader = () => <PageLoadingSkeleton />;

/**
 * 认证守卫：未登录用户重定向到 /login
 */
const isAuthenticated = () => {
  const token = localStorage.getItem('access_token');
  return !!token;
};

const ProtectedRoute = ({ children }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

const AppRouter = () => (
  <Router>
    <ScanProvider>
      <ErrorBoundary>
        <Routes>
          {/* 认证页面（无 AppShell 包裹） */}
          <Route path="/login"    element={<Suspense fallback={<Loader />}><Login /></Suspense>} />
          <Route path="/register" element={<Suspense fallback={<Loader />}><Register /></Suspense>} />

          {/* 带 AppShell 的主应用路由（需认证） */}
          <Route element={<AppShell />}>
            <Route index element={<Suspense fallback={<Loader />}><ProtectedRoute><Dashboard /></ProtectedRoute></Suspense>} />
            <Route path="/scan"            element={<Suspense fallback={<Loader />}><ProtectedRoute><Dashboard /></ProtectedRoute></Suspense>} />
            <Route path="/monitor"         element={<Suspense fallback={<Loader />}><ProtectedRoute><Monitor /></ProtectedRoute></Suspense>} />
            <Route path="/knowledge-graph" element={<Suspense fallback={<Loader />}><ProtectedRoute><KnowledgeGraph /></ProtectedRoute></Suspense>} />
            <Route path="/history"         element={<Suspense fallback={<Loader />}><ProtectedRoute><ScanHistory /></ProtectedRoute></Suspense>} />
            <Route path="/reports"         element={<Suspense fallback={<Loader />}><ProtectedRoute><ReportGenerator /></ProtectedRoute></Suspense>} />
            <Route path="/plugins"         element={<Suspense fallback={<Loader />}><ProtectedRoute><PluginManager /></ProtectedRoute></Suspense>} />
          </Route>
        </Routes>
      </ErrorBoundary>
    </ScanProvider>
  </Router>
);

export default AppRouter;
