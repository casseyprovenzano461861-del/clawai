/**
 * AppRouter — 路由配置
 */

import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import AppShell from './components/layout/AppShell';
import ErrorBoundary from './components/ErrorBoundary';
import { PageLoadingSkeleton } from './components/Skeleton';
import { ScanProvider } from './context/ScanContext';
import { PERAgentProvider } from './context/PERAgentContext';

const Dashboard    = lazy(() => import('./pages/Dashboard'));
const AttackMap    = lazy(() => import('./pages/AttackMap'));
const ReportGenerator = lazy(() => import('./components/ReportGenerator'));
const PluginManager   = lazy(() => import('./components/PluginManager'));
const Login        = lazy(() => import('./pages/Login'));
const Register     = lazy(() => import('./pages/Register'));

const Loader = () => <PageLoadingSkeleton />;

const isAuthenticated = () => !!localStorage.getItem('access_token');

const ProtectedRoute = ({ children }) => {
  if (!isAuthenticated()) return <Navigate to="/login" replace />;
  return children;
};

const wrap = (Component) => (
  <Suspense fallback={<Loader />}>
    <ProtectedRoute><Component /></ProtectedRoute>
  </Suspense>
);

const AppRouter = () => (
  <Router>
    <ScanProvider>
      <PERAgentProvider>
        <ErrorBoundary>
          <Routes>
            <Route path="/login"    element={<Suspense fallback={<Loader />}><Login /></Suspense>} />
            <Route path="/register" element={<Suspense fallback={<Loader />}><Register /></Suspense>} />

            <Route element={<AppShell />}>
              <Route index          element={wrap(Dashboard)} />
              <Route path="/attack-map" element={wrap(AttackMap)} />
              <Route path="/reports"    element={wrap(ReportGenerator)} />
              <Route path="/plugins"    element={wrap(PluginManager)} />
            </Route>
          </Routes>
        </ErrorBoundary>
      </PERAgentProvider>
    </ScanProvider>
  </Router>
);

export default AppRouter;
