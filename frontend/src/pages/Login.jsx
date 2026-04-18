import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, User, Lock, Eye, EyeOff, AlertCircle, Terminal, Zap } from 'lucide-react';
import userService from '../services/userService';
import CyberInput from '../components/shared/CyberInput';
import { useAuthContext } from '../context/AuthContext';

// 快速登录账号列表（仅测试用）
const QUICK_ACCOUNTS = [
  { label: 'Admin', username: 'admin', password: 'admin123', color: '#00d4ff' },
  { label: 'User',  username: 'user',  password: 'user123',  color: '#8b5cf6' },
];

// 流动粒子背景
const ParticleBg = () => {
  const dots = Array.from({ length: 30 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 2 + 1,
    dur: Math.random() * 8 + 4,
    delay: Math.random() * 4,
  }));

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {/* 渐变背景 */}
      <div
        className="absolute inset-0"
        style={{
          background: 'radial-gradient(ellipse at 30% 20%, rgba(0,212,255,0.07) 0%, transparent 50%), radial-gradient(ellipse at 70% 80%, rgba(139,92,246,0.07) 0%, transparent 50%)',
        }}
      />
      {/* 点阵背景 */}
      <div className="hero-grid absolute inset-0" />
      {/* 扫描线 */}
      <div
        className="absolute inset-0 opacity-[0.025]"
        style={{
          backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,212,255,1) 2px, rgba(0,212,255,1) 4px)',
          backgroundSize: '100% 4px',
        }}
      />
      {/* 浮动粒子 */}
      <svg className="absolute inset-0 w-full h-full">
        {dots.map(d => (
          <circle key={d.id} cx={`${d.x}%`} cy={`${d.y}%`} r={d.size} fill="rgba(0,212,255,0.3)">
            <animate
              attributeName="opacity"
              values="0;0.6;0"
              dur={`${d.dur}s`}
              begin={`${d.delay}s`}
              repeatCount="indefinite"
            />
            <animate
              attributeName="cy"
              values={`${d.y}%;${d.y - 5}%;${d.y}%`}
              dur={`${d.dur * 1.5}s`}
              begin={`${d.delay}s`}
              repeatCount="indefinite"
            />
          </circle>
        ))}
      </svg>
    </div>
  );
};

const Login = () => {
  const navigate = useNavigate();
  const { revalidate } = useAuthContext();
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [showPwd, setShowPwd]   = useState(false);
  const [error, setError]       = useState('');
  const [shake, setShake]       = useState(false);
  const [loading, setLoading]   = useState(false);
  const [focused, setFocused]   = useState('');

  const handleChange = e => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const triggerShake = () => {
    setShake(true);
    setTimeout(() => setShake(false), 500);
  };

  const handleQuickLogin = async (account) => {
    setLoading(true);
    setError('');
    try {
      const result = await userService.login({ username: account.username, password: account.password });
      if (result.access_token) {
        await revalidate();
        navigate('/');
      }
    } catch (err) {
      setError(err.message || '快速登录失败');
      triggerShake();
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async e => {
    e.preventDefault();
    if (!formData.username || !formData.password) {
      setError('请输入用户名和密码');
      triggerShake();
      return;
    }
    setLoading(true);
    try {
      const result = await userService.login(formData);
      if (result.access_token) {
        await revalidate();
        navigate('/');
      }
    } catch (err) {
      setError(err.message || '登录失败，请检查用户名和密码');
      triggerShake();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
      <ParticleBg />

      <div className="w-full max-w-sm relative z-10 animate-scale-in">
        {/* Logo */}
        <div className="text-center mb-8">
          <div
            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4 animate-neon-pulse"
            style={{
              background: 'rgba(0,212,255,0.08)',
              border: '1px solid rgba(0,212,255,0.3)',
            }}
          >
            <Shield size={30} style={{ color: '#00d4ff', filter: 'drop-shadow(0 0 10px rgba(0,212,255,0.8))' }} />
          </div>
          <h1 className="text-2xl font-bold shimmer-text mb-1">ClawAI</h1>
          <p className="text-xs text-gray-600 font-mono tracking-widest uppercase">Intelligent Pentest System</p>
        </div>

        {/* 卡片 */}
        <div
          className={shake ? 'animate-shake' : ''}
          style={{
            background: 'rgba(8,12,20,0.9)',
            backdropFilter: 'blur(24px)',
            border: '1px solid rgba(0,212,255,0.15)',
            borderRadius: '16px',
            boxShadow: '0 0 60px rgba(0,212,255,0.06), 0 24px 48px rgba(0,0,0,0.6)',
            padding: '28px',
          }}
        >
          {/* 顶部渐变线 */}
          <div
            className="absolute top-0 left-0 right-0 h-px rounded-t-2xl"
            style={{ background: 'linear-gradient(90deg, transparent, rgba(0,212,255,0.5), transparent)' }}
          />

          <div className="flex items-center gap-2 mb-5">
            <Terminal size={15} className="text-cyan-400" />
            <h2 className="text-sm font-semibold text-gray-200 tracking-wide">用户登录</h2>
          </div>

          {error && (
            <div
              className="mb-4 p-2.5 rounded-lg flex items-center gap-2 text-xs animate-shake"
              style={{
                background: 'rgba(239,68,68,0.08)',
                border: '1px solid rgba(239,68,68,0.25)',
                color: '#f87171',
              }}
            >
              <AlertCircle size={13} className="shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[11px] text-gray-600 mb-1.5 uppercase tracking-wider font-medium">用户名</label>
              <CyberInput
                icon={User}
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="输入用户名"
                autoComplete="username"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-[11px] text-gray-600 uppercase tracking-wider font-medium">密码</label>
              </div>
              <CyberInput
                icon={Lock}
                type={showPwd ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="输入密码"
                autoComplete="current-password"
              >
                <button
                  type="button"
                  onClick={() => setShowPwd(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-300 transition-colors"
                >
                  {showPwd ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </CyberInput>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-cyber w-full text-sm h-10 mt-1"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  验证中...
                </span>
              ) : '登 录'}
            </button>
          </form>

          <hr className="divider-cyber mt-5 mb-4" />

          {/* 快速登录 */}
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2.5">
              <Zap size={11} className="text-yellow-400" />
              <span className="text-[10px] text-gray-600 uppercase tracking-widest font-medium">快速测试登录</span>
            </div>
            <div className="flex gap-2">
              {QUICK_ACCOUNTS.map(acc => (
                <button
                  key={acc.username}
                  type="button"
                  disabled={loading}
                  onClick={() => handleQuickLogin(acc)}
                  className="flex-1 text-xs h-8 rounded-lg font-mono transition-all duration-200 disabled:opacity-40"
                  style={{
                    background: `rgba(${acc.color === '#00d4ff' ? '0,212,255' : '139,92,246'},0.07)`,
                    border: `1px solid ${acc.color}33`,
                    color: acc.color,
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = `rgba(${acc.color === '#00d4ff' ? '0,212,255' : '139,92,246'},0.15)`}
                  onMouseLeave={e => e.currentTarget.style.background = `rgba(${acc.color === '#00d4ff' ? '0,212,255' : '139,92,246'},0.07)`}
                >
                  {acc.label}
                </button>
              ))}
            </div>
          </div>

          <hr className="divider-cyber" />

          <p className="text-center text-xs text-gray-600">
            还没有账号？{' '}
            <Link to="/register" className="text-cyan-400 hover:text-cyan-300 transition-colors font-medium">
              立即注册
            </Link>
          </p>
        </div>

        <p className="text-center text-[11px] text-gray-700 mt-5 font-mono">
          仅用于授权范围内的安全测试 · {new Date().getFullYear()}
        </p>
      </div>
    </div>
  );
};

export default Login;
