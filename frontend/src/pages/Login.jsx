import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, User, Lock, Eye, EyeOff, AlertCircle } from 'lucide-react';
import userService from '../services/userService';
import CyberInput from '../components/shared/CyberInput';

const Login = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [showPwd, setShowPwd] = useState(false);
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = e => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async e => {
    e.preventDefault();
    if (!formData.username || !formData.password) { setError('请输入用户名和密码'); return; }
    setLoading(true);
    try {
      const result = await userService.login(formData);
      // userService.login() 内部已处理 token 存储，无需重复写入 localStorage
      if (result.access_token) {
        navigate('/');
      }
    } catch (err) {
      setError(err.message || '登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(0,212,255,0.06) 0%, #060910 60%)' }}
    >
      <div className="w-full max-w-sm animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-8">
          <div
            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4"
            style={{ background: 'rgba(0,212,255,0.08)', border: '1px solid rgba(0,212,255,0.25)', boxShadow: '0 0 24px rgba(0,212,255,0.15)' }}
          >
            <Shield size={28} style={{ color: '#00d4ff', filter: 'drop-shadow(0 0 8px rgba(0,212,255,0.7))' }} />
          </div>
          <h1 className="text-2xl font-bold text-neon">ClawAI</h1>
          <p className="text-sm text-gray-500 mt-1">AI 驱动的智能安全评估系统</p>
        </div>

        {/* 卡片 */}
        <div className="card-cyber p-7">
          <h2 className="text-base font-semibold text-gray-200 mb-5">登录账户</h2>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/25 flex items-center gap-2 text-red-400 text-xs">
              <AlertCircle size={14} className="shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1.5">用户名</label>
              <CyberInput icon={User} name="username" value={formData.username} onChange={handleChange} placeholder="输入用户名" autoComplete="username" />
            </div>

            <div>
              <label className="block text-xs text-gray-500 mb-1.5">密码</label>
              <CyberInput
                icon={Lock}
                type={showPwd ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="输入密码"
                autoComplete="current-password"
              >
                <button type="button" onClick={() => setShowPwd(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-300 transition-colors">
                  {showPwd ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </CyberInput>
            </div>

            <button type="submit" disabled={loading} className="btn-cyber w-full mt-2 text-sm">
              {loading ? '登录中…' : '登录'}
            </button>
          </form>

          <p className="mt-5 text-center text-xs text-gray-600">
            还没有账号？{' '}
            <Link to="/register" className="text-cyan-400 hover:text-cyan-300 transition-colors">注册</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
