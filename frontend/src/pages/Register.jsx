import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, User, Lock, Mail, Eye, EyeOff, AlertCircle, UserPlus } from 'lucide-react';
import userService from '../services/userService';

const CyberInput = ({ icon: Icon, label, required, error, children, ...props }) => (
  <div className="mb-4">
    {label && (
      <label className="block text-xs font-medium text-cyan-400/70 uppercase tracking-wider mb-1.5">
        {label}{required && <span className="text-neon-pink ml-1">*</span>}
      </label>
    )}
    <div className="relative">
      {Icon && (
        <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyan-500/60 pointer-events-none" />
      )}
      <input
        className={`input-cyber w-full ${Icon ? 'pl-10' : 'pl-4'} ${props.type === 'password' ? 'pr-10' : 'pr-4'} py-2.5`}
        {...props}
      />
      {children}
    </div>
  </div>
);

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    confirmPassword: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!formData.username || !formData.email || !formData.password) {
      setError('请填写所有必填字段');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('两次输入的密码不一致');
      return;
    }

    if (formData.password.length < 6) {
      setError('密码长度不能少于6个字符');
      return;
    }

    setLoading(true);
    try {
      await userService.register({
        username: formData.username,
        email: formData.email,
        full_name: formData.full_name || formData.username,
        password: formData.password
      });
      navigate('/login');
    } catch (err) {
      setError(err.message || '注册失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4 py-8"
      style={{
        background: 'radial-gradient(ellipse at 50% 0%, rgba(0,212,255,0.08) 0%, rgba(139,92,246,0.05) 40%, #060910 70%)',
        backgroundColor: '#060910',
      }}
    >
      {/* Scanlines overlay */}
      <div
        className="fixed inset-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,212,255,0.5) 2px, rgba(0,212,255,0.5) 4px)',
          backgroundSize: '100% 4px',
        }}
      />

      <div className="w-full max-w-md relative z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <div
            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4"
            style={{
              background: 'linear-gradient(135deg, rgba(0,212,255,0.15), rgba(139,92,246,0.15))',
              border: '1px solid rgba(0,212,255,0.3)',
              boxShadow: '0 0 20px rgba(0,212,255,0.2), inset 0 0 20px rgba(0,212,255,0.05)',
            }}
          >
            <Shield className="w-8 h-8" style={{ color: '#00d4ff' }} />
          </div>
          <h1
            className="text-3xl font-bold"
            style={{
              background: 'linear-gradient(135deg, #00d4ff, #8b5cf6)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            ClawAI
          </h1>
          <p className="text-gray-500 mt-1 text-sm">创建账号，开始渗透测试之旅</p>
        </div>

        {/* Register Card */}
        <div
          className="rounded-xl p-8"
          style={{
            background: 'rgba(10,14,23,0.85)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(0,212,255,0.15)',
            boxShadow: '0 0 40px rgba(0,212,255,0.05), 0 20px 60px rgba(0,0,0,0.5)',
          }}
        >
          <div className="flex items-center gap-2 mb-6">
            <UserPlus className="w-5 h-5" style={{ color: '#00d4ff' }} />
            <h2 className="text-lg font-semibold text-white">注册新账号</h2>
          </div>

          {error && (
            <div
              className="mb-5 p-3 rounded-lg flex items-center gap-2 text-sm"
              style={{
                background: 'rgba(239,68,68,0.08)',
                border: '1px solid rgba(239,68,68,0.25)',
                color: '#f87171',
              }}
            >
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <CyberInput
              icon={User}
              label="用户名"
              required
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="输入用户名"
              autoComplete="username"
            />

            <CyberInput
              icon={Mail}
              label="邮箱"
              required
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="输入邮箱地址"
              autoComplete="email"
            />

            <CyberInput
              icon={User}
              label="姓名"
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              placeholder="输入姓名（可选）"
            />

            <CyberInput
              icon={Lock}
              label="密码"
              required
              type={showPassword ? 'text' : 'password'}
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="至少6个字符"
              autoComplete="new-password"
            >
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-cyan-400 transition-colors"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </CyberInput>

            <CyberInput
              icon={Lock}
              label="确认密码"
              required
              type={showPassword ? 'text' : 'password'}
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="再次输入密码"
              autoComplete="new-password"
              style={{ marginBottom: '1.5rem' }}
            />

            <button
              type="submit"
              disabled={loading}
              className="btn-cyber w-full py-2.5 font-medium mt-2"
              style={loading ? { opacity: 0.6, cursor: 'not-allowed' } : {}}
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

          <div className="mt-6 text-center text-sm text-gray-500">
            已有账号？{' '}
            <Link
              to="/login"
              className="font-medium transition-colors"
              style={{ color: '#00d4ff' }}
              onMouseEnter={e => (e.target.style.color = '#8b5cf6')}
              onMouseLeave={e => (e.target.style.color = '#00d4ff')}
            >
              立即登录
            </Link>
          </div>
        </div>

        {/* Bottom hint */}
        <p className="text-center text-xs text-gray-600 mt-6">
          仅用于授权范围内的安全测试 · ClawAI {new Date().getFullYear()}
        </p>
      </div>
    </div>
  );
};

export default Register;
