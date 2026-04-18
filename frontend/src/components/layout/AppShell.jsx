/**
 * AppShell — 整体布局容器（侧边栏版本）
 * 左侧固定 Sidebar + 右侧内容区自适应滚动
 */

import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

const AppShell = () => (
  <div className="flex h-screen overflow-hidden" style={{ background: '#060910' }}>
    <Sidebar />
    <main className="flex-1 overflow-y-auto overflow-x-hidden">
      <Outlet />
    </main>
  </div>
);

export default AppShell;
