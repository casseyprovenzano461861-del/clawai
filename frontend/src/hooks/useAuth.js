/**
 * useAuth — 向后兼容的认证 Hook
 *
 * 直接代理到 AuthContext，确保全应用只有一个认证状态实例。
 * 旧代码无需修改导入路径，行为一致。
 */
export { useAuthContext as useAuth } from '../context/AuthContext';
export { useAuthContext as default } from '../context/AuthContext';
