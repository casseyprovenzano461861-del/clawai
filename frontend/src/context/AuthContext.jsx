/**
 * AuthContext — 全局认证状态
 *
 * 将 useAuth 的网络请求提升到根层，确保整个应用只发一次 /auth/me，
 * ProtectedRoute / PublicRoute 直接消费同一份状态，不再各自触发验证。
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api, clearAuthTokens } from '../services/apiClient';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [isAuth,  setIsAuth]  = useState(false);
  const [loading, setLoading] = useState(true);
  const [user,    setUser]    = useState(null);

  const validate = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setIsAuth(false);
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api.auth.getCurrentUser();
      setUser(me);
      setIsAuth(true);
    } catch {
      clearAuthTokens();
      setIsAuth(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { validate(); }, [validate]);

  const logout = useCallback(async () => {
    try { await api.auth.logout(); } catch { /* 后端登出失败不影响前端清理 */ }
    clearAuthTokens();
    localStorage.removeItem('current_user');
    setIsAuth(false);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ isAuth, loading, user, revalidate: validate, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuthContext = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuthContext must be used within <AuthProvider>');
  return ctx;
};

export default AuthContext;
