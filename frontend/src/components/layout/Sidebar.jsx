/**
 * Sidebar — 左侧边栏导航（Grafana 风格 + Cyberpunk）
 * 支持展开/折叠，激活态高亮，连接状态指示
 */

import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Globe,
  FileText,
  Puzzle,
  ChevronLeft,
  ChevronRight,
  Shield,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { useWebSocket } from '../../context/WebSocketContext';

const NAV_ITEMS = [
  { name: '仪表板',   href: '/',            icon: LayoutDashboard },
  { name: '攻击地图', href: '/attack-map',  icon: Globe },
  { name: '报告管理', href: '/reports',     icon: FileText },
  { name: '插件商城', href: '/plugins',     icon: Puzzle },
];

const NavItem = ({ item, active, collapsed }) => {
  const Icon = item.icon;
  return (
    <Link
      to={item.href}
      title={collapsed ? item.name : undefined}
      className={[
        'relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium',
        'transition-all duration-200 group overflow-hidden',
        active
          ? 'text-cyan-400'
          : 'text-gray-500 hover:text-gray-200 hover:bg-white/5',
      ].join(' ')}
      style={
        active
          ? {
              background: 'rgba(0,212,255,0.08)',
              boxShadow: 'inset 0 0 20px rgba(0,212,255,0.04)',
            }
          : {}
      }
    >
      {/* 激活态左侧竖条 */}
      {active && (
        <span
          className="absolute left-0 top-1 bottom-1 w-[3px] rounded-r-full"
          style={{
            background: 'linear-gradient(180deg, #00d4ff, #8b5cf6)',
            boxShadow: '0 0 8px rgba(0,212,255,0.8)',
          }}
        />
      )}

      <Icon
        size={17}
        className={[
          'shrink-0 transition-all duration-200',
          active
            ? 'text-cyan-400'
            : 'text-gray-500 group-hover:text-gray-300',
        ].join(' ')}
        style={active ? { filter: 'drop-shadow(0 0 5px rgba(0,212,255,0.7))' } : {}}
      />

      {!collapsed && (
        <span className="truncate">{item.name}</span>
      )}
    </Link>
  );
};

const Sidebar = () => {
  const location = useLocation();
  const { connected: wsConnected } = useWebSocket();

  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem('sidebar_collapsed') === 'true';
    } catch {
      return false;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('sidebar_collapsed', String(collapsed));
    } catch {}
  }, [collapsed]);

  const isActive = (href) =>
    href === '/' ? location.pathname === '/' : location.pathname.startsWith(href);

  return (
    <aside
      className="flex flex-col h-screen shrink-0 border-r transition-[width] duration-250 ease-in-out"
      style={{
        width: collapsed ? 64 : 220,
        background: 'rgba(6,9,16,0.98)',
        borderColor: 'rgba(255,255,255,0.06)',
      }}
    >
      {/* Logo 区 */}
      <div
        className="flex items-center h-14 px-3 shrink-0 border-b"
        style={{ borderColor: 'rgba(255,255,255,0.06)' }}
      >
        <Link to="/" className="flex items-center gap-2.5 min-w-0">
          <Shield
            size={22}
            className="text-cyan-400 shrink-0"
            style={{
              filter: 'drop-shadow(0 0 6px rgba(0,212,255,0.6))',
              animation: 'neon-pulse 3s ease-in-out infinite',
            }}
          />
          {!collapsed && (
            <span
              className="font-bold text-base tracking-tight truncate shimmer-text"
            >
              ClawAI
            </span>
          )}
        </Link>
      </div>

      {/* 导航项 */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden px-2 py-3 space-y-1">
        {NAV_ITEMS.map((item) => (
          <NavItem
            key={item.href}
            item={item}
            active={isActive(item.href)}
            collapsed={collapsed}
          />
        ))}
      </nav>

      {/* 底部：连接状态 + 折叠按钮 */}
      <div
        className="shrink-0 border-t px-3 py-3 flex items-center"
        style={{ borderColor: 'rgba(255,255,255,0.06)' }}
      >
        {/* 连接状态 */}
        <div
          className="flex items-center gap-2 flex-1 min-w-0"
          title={wsConnected ? '后端已连接' : '后端未连接'}
        >
          {wsConnected ? (
            <>
              <span
                className="w-2 h-2 rounded-full bg-emerald-400 shrink-0"
                style={{
                  boxShadow: '0 0 6px rgba(34,197,94,0.8)',
                  animation: 'neon-pulse 2s ease-in-out infinite',
                }}
              />
              {!collapsed && (
                <span className="text-xs text-emerald-400/70 font-mono truncate">
                  LIVE
                </span>
              )}
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-red-500 shrink-0" />
              {!collapsed && (
                <span className="text-xs text-red-400/60 font-mono truncate">
                  OFF
                </span>
              )}
            </>
          )}
        </div>

        {/* 折叠按钮 */}
        <button
          onClick={() => setCollapsed((v) => !v)}
          className="ml-auto p-1 rounded-md text-gray-600 hover:text-gray-300 hover:bg-white/6 transition-all duration-150"
          title={collapsed ? '展开侧边栏' : '折叠侧边栏'}
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
