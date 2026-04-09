/**
 * Navbar — 统一顶部导航栏（Cyberpunk 风格）
 */

import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Shield, Home, Target, Network, Activity,
  History, FileText, Zap, Menu, X, User, LogOut,
} from 'lucide-react';

const NAV_ITEMS = [
  { name: '仪表板',   href: '/',                icon: Home },
  { name: '实时监控', href: '/monitor',          icon: Activity },
  { name: '知识图谱', href: '/knowledge-graph',  icon: Network },
  { name: '扫描历史', href: '/history',          icon: History },
  { name: '报告管理', href: '/reports',          icon: FileText },
  { name: '插件管理', href: '/plugins',          icon: Zap },
];

const NavLink = ({ item, active }) => {
  const Icon = item.icon;
  return (
    <Link
      to={item.href}
      className={[
        'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200',
        active
          ? 'text-cyan-400 bg-cyan-500/10 shadow-[0_0_12px_rgba(0,212,255,0.15)]'
          : 'text-gray-400 hover:text-gray-100 hover:bg-white/5',
      ].join(' ')}
    >
      <Icon size={14} />
      <span>{item.name}</span>
    </Link>
  );
};

const Navbar = () => {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (href) =>
    href === '/' ? location.pathname === '/' : location.pathname.startsWith(href);

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 h-14"
      style={{
        background: 'rgba(6, 9, 16, 0.92)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid rgba(0, 212, 255, 0.12)',
        boxShadow: '0 1px 0 rgba(0,212,255,0.06)',
      }}
    >
      <div className="max-w-screen-2xl mx-auto h-full px-4 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 shrink-0 group">
          <div className="relative">
            <Shield
              size={22}
              className="text-cyan-400 group-hover:text-cyan-300 transition-colors"
              style={{ filter: 'drop-shadow(0 0 6px rgba(0,212,255,0.6))' }}
            />
          </div>
          <span
            className="text-base font-bold tracking-tight"
            style={{
              background: 'linear-gradient(90deg, #00d4ff, #8b5cf6)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            ClawAI
          </span>
          <span className="text-[10px] text-gray-600 font-mono mt-0.5 hidden sm:block">v2.0</span>
        </Link>

        {/* 桌面导航 */}
        <div className="hidden md:flex items-center gap-1">
          {NAV_ITEMS.map(item => (
            <NavLink key={item.href} item={item} active={isActive(item.href)} />
          ))}
        </div>

        {/* 右侧操作区 */}
        <div className="flex items-center gap-2">
          {/* 用户菜单（简化版） */}
          <Link
            to="/login"
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-gray-400 hover:text-gray-200 hover:bg-white/5 transition-all"
          >
            <User size={14} />
            <span>账户</span>
          </Link>

          {/* 移动端菜单按钮 */}
          <button
            className="md:hidden p-1.5 text-gray-400 hover:text-cyan-400 transition-colors"
            onClick={() => setMobileOpen(v => !v)}
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* 移动端下拉菜单 */}
      {mobileOpen && (
        <div
          className="md:hidden absolute top-14 left-0 right-0 py-2 px-4 flex flex-col gap-1"
          style={{
            background: 'rgba(6, 9, 16, 0.97)',
            borderBottom: '1px solid rgba(0,212,255,0.12)',
          }}
        >
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.href}
              item={item}
              active={isActive(item.href)}
            />
          ))}
        </div>
      )}
    </nav>
  );
};

export default Navbar;
