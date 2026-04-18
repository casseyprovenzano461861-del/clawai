/**
 * Navbar — 统一顶部导航栏（Cyberpunk 风格）
 */

import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, Home, FileText, Zap, Menu, X, Network } from 'lucide-react';
import { useWebSocket } from '../../context/WebSocketContext';

const NAV_ITEMS = [
  { name: '仪表板',   href: '/',          icon: Home },
  { name: '攻击地图', href: '/attack-map', icon: Network },
  { name: '报告管理', href: '/reports',   icon: FileText },
  { name: '插件商城', href: '/plugins',   icon: Zap },
];

const NavLink = ({ item, active, onClick }) => {
  const Icon = item.icon;
  return (
    <Link
      to={item.href}
      onClick={onClick}
      className={[
        'relative flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium',
        'transition-all duration-200',
        active
          ? 'text-cyan-400 bg-cyan-500/10'
          : 'text-gray-400 hover:text-gray-100 hover:bg-white/5',
      ].join(' ')}
      style={active ? { boxShadow: '0 0 14px rgba(0,212,255,0.12)' } : {}}
    >
      <Icon size={14} className={active ? 'drop-shadow-[0_0_4px_rgba(0,212,255,0.8)]' : ''} />
      <span>{item.name}</span>
      {active && (
        <span
          className="absolute bottom-0 left-2 right-2 h-px rounded-full"
          style={{
            background: 'linear-gradient(90deg, transparent, #00d4ff, transparent)',
            boxShadow: '0 0 6px rgba(0,212,255,0.8)',
          }}
        />
      )}
    </Link>
  );
};

const ConnectionStatus = ({ connected }) => (
  <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/3">
    {connected ? (
      <>
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" style={{ boxShadow: '0 0 6px rgba(34,197,94,0.8)', animation: 'neon-pulse 2s ease-in-out infinite' }} />
        <span className="text-xs text-emerald-400/80 font-mono">LIVE</span>
      </>
    ) : (
      <>
        <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
        <span className="text-xs text-red-400/70 font-mono">OFF</span>
      </>
    )}
  </div>
);

const Navbar = () => {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { connected: wsConnected } = useWebSocket();

  const isActive = (href) =>
    href === '/' ? location.pathname === '/' : location.pathname.startsWith(href);

  return (
    <>
      <div
        className="fixed top-0 left-0 right-0 z-[51] h-px"
        style={{
          background: 'linear-gradient(90deg, #00d4ff 0%, #8b5cf6 40%, #ec4899 70%, #00d4ff 100%)',
          opacity: 0.8,
        }}
      />

      <nav
        className="fixed top-px left-0 right-0 z-50 h-14"
        style={{
          background: 'rgba(6, 9, 16, 0.94)',
          backdropFilter: 'blur(20px) saturate(1.3)',
          borderBottom: '1px solid rgba(0, 212, 255, 0.1)',
          boxShadow: '0 4px 24px rgba(0,0,0,0.4), 0 1px 0 rgba(0,212,255,0.05)',
        }}
      >
        <div className="max-w-screen-2xl mx-auto h-full px-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 shrink-0 group">
            <Shield
              size={22}
              className="text-cyan-400 group-hover:text-cyan-300 transition-colors duration-300"
              style={{ filter: 'drop-shadow(0 0 6px rgba(0,212,255,0.6))', animation: 'neon-pulse 3s ease-in-out infinite' }}
            />
            <span className="text-base font-bold tracking-tight shimmer-text">ClawAI</span>
            <span className="text-[10px] text-gray-600 font-mono mt-0.5 hidden sm:block border border-gray-800 px-1 rounded">v2.0</span>
          </Link>

          <div className="hidden md:flex items-center gap-0.5">
            {NAV_ITEMS.map(item => (
              <NavLink key={item.href} item={item} active={isActive(item.href)} />
            ))}
          </div>

          <div className="flex items-center gap-2">
            <ConnectionStatus connected={wsConnected} />
            <button
              className="md:hidden p-1.5 text-gray-400 hover:text-cyan-400 transition-colors rounded-lg hover:bg-white/5"
              onClick={() => setMobileOpen(v => !v)}
            >
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        {mobileOpen && (
          <div
            className="md:hidden absolute top-14 left-0 right-0 py-3 px-4 flex flex-col gap-1 animate-slide-down"
            style={{
              background: 'rgba(6, 9, 16, 0.98)',
              borderBottom: '1px solid rgba(0,212,255,0.12)',
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            }}
          >
            {NAV_ITEMS.map(item => (
              <NavLink
                key={item.href}
                item={item}
                active={isActive(item.href)}
                onClick={() => setMobileOpen(false)}
              />
            ))}
          </div>
        )}
      </nav>
    </>
  );
};

export default Navbar;
