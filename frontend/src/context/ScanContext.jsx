/**
 * ScanContext — 全局扫描状态管理
 *
 * 提供跨模块共享的扫描状态：
 *   lastScan       - 最新一次扫描结果
 *   scanHistory    - 扫描历史列表（与 localStorage 同步）
 *   activeTarget   - 当前正在扫描/已选中的目标
 *   scanStatus     - idle | scanning | done | error
 *
 * 提供方法：
 *   startScan(target, mode)  - 触发扫描，更新全局状态
 *   refreshHistory()         - 重新从 localStorage 同步历史
 *   selectScan(record)       - 跨模块选中历史记录
 *   clearLastScan()          - 清除最新扫描（重置视图）
 */

import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import scanHistoryService from '../services/scanHistoryService';
import attackService from '../services/attackService';

// ─── 初始状态 ─────────────────────────────────────────────────────────────────
const initialState = {
  lastScan:     null,    // 最新扫描结果对象
  scanHistory:  [],      // 历史记录数组
  activeTarget: '',      // 当前目标
  scanStatus:   'idle',  // idle | scanning | done | error
  errorMsg:     '',
};

// ─── Reducer ─────────────────────────────────────────────────────────────────
function reducer(state, action) {
  switch (action.type) {
    case 'SCAN_START':
      return { ...state, scanStatus: 'scanning', activeTarget: action.target, errorMsg: '' };

    case 'SCAN_DONE':
      return {
        ...state,
        scanStatus:   'done',
        lastScan:     action.result,
        scanHistory:  [action.record, ...state.scanHistory].slice(0, 50),
      };

    case 'SCAN_ERROR':
      return { ...state, scanStatus: 'error', errorMsg: action.message };

    case 'HISTORY_LOADED':
      return { ...state, scanHistory: action.history };

    case 'SELECT_SCAN':
      return {
        ...state,
        lastScan:     action.record.result || action.record,
        activeTarget: action.record.target || '',
        scanStatus:   'done',
      };

    case 'CLEAR_LAST':
      return { ...state, lastScan: null, scanStatus: 'idle', errorMsg: '' };

    default:
      return state;
  }
}

// ─── Context ─────────────────────────────────────────────────────────────────
const ScanContext = createContext(null);

// ─── Provider ─────────────────────────────────────────────────────────────────
export function ScanProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  // 初始化：从 localStorage 加载历史
  useEffect(() => {
    const history = scanHistoryService.getAll();
    dispatch({ type: 'HISTORY_LOADED', history });
  }, []);

  /** 触发扫描 */
  const startScan = useCallback(async (target, mode = 'full') => {
    if (!target?.trim()) return;
    dispatch({ type: 'SCAN_START', target: target.trim() });
    try {
      // mode 字符串 → options 对象（runAttack 第二参数期望对象）
      const result = await attackService.runAttack(target.trim(), {
        useReal: false,       // 后端 unified_executor 桥接已修复，false = 走规则引擎
        ruleEngineMode: true,
      });
      // 持久化到 localStorage
      const record = scanHistoryService.add({ ...result, target: target.trim() });
      dispatch({ type: 'SCAN_DONE', result, record });
      return result;
    } catch (e) {
      dispatch({ type: 'SCAN_ERROR', message: e.message || '扫描失败' });
      throw e;
    }
  }, []);

  /** 从 localStorage 重新同步历史 */
  const refreshHistory = useCallback(() => {
    const history = scanHistoryService.getAll();
    dispatch({ type: 'HISTORY_LOADED', history });
  }, []);

  /** 跨模块选中历史记录 */
  const selectScan = useCallback((record) => {
    dispatch({ type: 'SELECT_SCAN', record });
  }, []);

  /** 清除最新扫描 */
  const clearLastScan = useCallback(() => {
    dispatch({ type: 'CLEAR_LAST' });
  }, []);

  const value = {
    ...state,
    startScan,
    refreshHistory,
    selectScan,
    clearLastScan,
  };

  return <ScanContext.Provider value={value}>{children}</ScanContext.Provider>;
}

// ─── Hook ─────────────────────────────────────────────────────────────────────
export function useScan() {
  const ctx = useContext(ScanContext);
  if (!ctx) throw new Error('useScan must be used within <ScanProvider>');
  return ctx;
}

export default ScanContext;
