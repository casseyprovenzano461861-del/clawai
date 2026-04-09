/**
 * AppShell — 整体布局容器
 * 提供固定 Navbar + 内容区滚动区域
 */

import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';

const AppShell = () => (
  <div className="min-h-screen" style={{ background: '#060910' }}>
    <Navbar />
    {/* 内容区：顶部留出 Navbar 高度 (56px = h-14) */}
    <main className="pt-14 min-h-[calc(100vh-3.5rem)]">
      <Outlet />
    </main>
  </div>
);

export default AppShell;
