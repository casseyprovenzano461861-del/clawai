import React, { useState, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, User, Lock, Mail, Eye, EyeOff, AlertCircle, UserPlus, Terminal, CheckCircle } from 'lucide-react';
import userService from '../services/userService';
import CyberInput from '../components/shared/CyberInput';

// 密码强度计算
const calcStrength = (pwd) => {
  if (!pwd) return { score: 0, label: '', color: '' };
  let score = 0;
  if (pwd.length >= 6)  score++;
  if (pwd.length >= 10) score++;
  if (/[A-Z]/.test(pwd)) score++;
  if (/[0-9]/.test(pwd)) score++;
  if (/[^A-Za-z0-9]/.test(pwd)) score++;
  const levels = [
    { label: '太短',   color: '#ef4444' },
    { label: '弱',     color: '#f97316' },
    { label: '一般',   color: '#f59e0b' },
    { label: '较强',   color: '#22c55e' },
    { label: '强',     color: '#00d4ff' },
    { label: '极强',   color: '#8b5cf6' },
  ];
  return { score, ...levels[Math.min(score, 5)] };
};

// 流动粒子背景（与 Login 保持一致）
const ParticleBg = () => (
  <div className="fixed inset-0 overflow-hidden pointer-events-none">
    <div
      className="absolute inset-0"
      style={{
        background: 'radial-gradient(ellipse at 70% 20%, rgba(139,92,246,0.07) 0%, transparent 50%), radial-gradient(ellipse at 30% 80%, rgba(0,212,255,0.07) 0%, transparent 50%)',
      }}
    />
    <div className="hero-grid absolute inset-0" />
    <div
      className="absolute inset-0 opacity-[0.02]"
      style={{
        backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,212,255,1) 2px, rgba(0,212,255,1) 4px)',
        backgroundSize: '100% 4px',
      }}
    />
  </div>
);

// 密码强度条
const StrengthBar = ({ password }) => {
  const s = useMemo(() => calcStrength(password), [password]);
  if (!password) return null;
  return (
    <div className="mt-2">
      <div className="flex gap-1 mb-1">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="flex-1 h-1 rounded-full transition-all duration-300"
            style={{
              background: i < s.score ? s.color : 'rgba(255,255,255,0.06)',
              boxShadow: i < s.score ? `0 0 4px ${s.color}66` : 'none',
            }}
          />
        ))}
      </div>
      <p className="text-[11px]" style={{ color: s.color }}>{s.label}</p>
    </div>
  );
};

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '', email: '', full_name: '', password: '', confirmPassword: '',
  });
  const [showPwd, setShowPwd]   = useState(false);
  const [error, setError]       = useState('');
  const [shake, setShake]       = useState(false);
  const [loading, setLoading]   = useState(false);

  const handleChange = e => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const triggerShake = () => {
    setShake(true);
    setTimeout(() => setShake(false), 500);
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setError('');
    if (!formData.username || !formData.email || !formData.password) {
      setError('请填写所有必填字段'); triggerShake(); return;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('两次输入的密码不一致'); triggerShake(); return;
    }
    if (formData.password.length < 6) {
      setError('密码长度不能少于 6 个字符'); triggerShake(); return;
    }
    setLoading(true);
    try {
      await userService.register({
        username: formData.username,
        email: formData.email,
        full_name: formData.full_name || formData.username,
        password: formData.password,
      });
      navigate('/login');
    } catch (err) {
      setError(err.message || '注册失败，请稍后重试');
      triggerShake();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8 relative overflow-hidden">
      <ParticleBg />

      <div className="w-full max-w-md relative z-10 animate-scale-in">
        {/* Logo */}
        <div className="text-center mb-7">
          <div
            className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-3 animate-neon-pulse"
            style={{
              background: 'linear-gradient(135deg, rgba(0,212,255,0.1), rgba(139,92,246,0.1))',
              border: '1px solid rgba(0,212,255,0.25)',
            }}
          >
            <Shield size={26} style={{ color: '#00d4ff', filter: 'drop-shadow(0 0 8px rgba(0,212,255,0.8))' }} />
          </div>
          <h1 className="text-2xl font-bold shimmer-text mb-1">ClawAI</h1>
          <p className="text-xs text-gray-600 font-mono tracking-widest uppercase">Intelligent Pentest System</p>
        </div>

        {/* 卡片 */}
        <div
          className={`relative ${shake ? 'animate-shake' : ''}`}
          style={{
            background: 'rgba(8,12,20,0.9)',
            backdropFilter: 'blur(24px)',
            border: '1px solid rgba(0,212,255,0.13)',
            borderRadius: '16px',
            boxShadow: '0 0 60px rgba(139,92,246,0.05), 0 24px 48px rgba(0,0,0,0.6)',
            padding: '28px',
          }}
        >
          {/* 顶部渐变线 */}
          <div
            className="absolute top-0 left-0 right-0 h-px rounded-t-2xl"
            style={{ background: 'linear-gradient(90deg, transparent, rgba(139,92,246,0.5), rgba(0,212,255,0.5), transparent)' }}
          />

          <div className="flex items-center gap-2 mb-5">
            <UserPlus size={14} className="text-cyan-400" />
            <h2 className="text-sm font-semibold text-gray-200 tracking-wide">创建账号</h2>
          </div>

          {error && (
            <div
              className="mb-4 p-2.5 rounded-lg flex items-center gap-2 text-xs"
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

          <form onSubmit={handleSubmit} className="space-y-3.5">
            <div>
              <label className="block text-[11px] text-gray-600 mb-1.5 uppercase tracking-wider font-medium">
                用户名 <span className="text-red-500">*</span>
              </label>
              <CyberInput icon={User} name="username" value={formData.username} onChange={handleChange} placeholder="输入用户名" autoComplete="username" />
            </div>

            <div>
              <label className="block text-[11px] text-gray-600 mb-1.5 uppercase tracking-wider font-medium">
                邮箱 <span className="text-red-500">*</span>
              </label>
              <CyberInput icon={Mail} type="email" name="email" value={formData.email} onChange={handleChange} placeholder="输入邮箱地址" autoComplete="email" />
            </div>

            <div>
              <label className="block text-[11px] text-gray-600 mb-1.5 uppercase tracking-wider font-medium">姓名</label>
              <CyberInput icon={User} name="full_name" value={formData.full_name} onChange={handleChange} placeholder="输入姓名（可选）" />
            </div>

            <div>
              <label className="block text-[11px] text-gray-600 mb-1.5 uppercase tracking-wider font-medium">
                密码 <span className="text-red-500">*</span>
              </label>
              <CyberInput
                icon={Lock}
                type={showPwd ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="至少 6 个字符"
                autoComplete="new-password"
              >
                <button type="button" onClick={() => setShowPwd(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-300 transition-colors">
                  {showPwd ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </CyberInput>
              <StrengthBar password={formData.password} />
            </div>

            <div>
              <label className="block text-[11px] text-gray-600 mb-1.5 uppercase tracking-wider font-medium">
                确认密码 <span className="text-red-500">*</span>
              </label>
              <CyberInput
                icon={Lock}
                type={showPwd ? 'text' : 'password'}
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="再次输入密码"
                autoComplete="new-password"
              />
              {formData.confirmPassword && formData.password === formData.confirmPassword && (
                <div className="flex items-center gap-1 mt-1.5 text-emerald-400 text-[11px]">
                  <CheckCircle size={11} /> 密码一致
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-cyber w-full text-sm h-10 mt-2"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  注册中...
                </span>
              ) : '创建账号'}
            </button>
          </form>

          <hr className="divider-cyber mt-5" />
          <p className="text-center text-xs text-gray-600">
            已有账号？{' '}
            <Link to="/login" className="text-cyan-400 hover:text-cyan-300 transition-colors font-medium">
              立即登录
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

export default Register;
