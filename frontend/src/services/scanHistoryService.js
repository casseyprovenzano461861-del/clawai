/**
 * 扫描历史管理服务
 * 使用 localStorage 存储扫描历史记录
 */

const STORAGE_KEY = 'clawai_scan_history';
const MAX_HISTORY = 50;

/**
 * 扫描历史服务
 */
const scanHistoryService = {
  /**
   * 获取所有历史记录
   * @returns {Array} 历史记录数组
   */
  getAll() {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('读取扫描历史失败:', error);
      return [];
    }
  },

  /**
   * 添加扫描记录
   * @param {Object} scan - 扫描结果
   * @returns {Object} 添加的记录
   */
  add(scan) {
    const history = this.getAll();
    
    const newRecord = {
      id: `scan_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      target: scan.target,
      executionTime: scan.execution_time,
      executionMode: scan.execution_mode,
      success: scan.success,
      attackChainLength: scan.attack_chain?.length || 0,
      vulnerabilities: {
        critical: scan.attack_chain?.filter(s => s.severity === 'critical')?.length || 0,
        high: scan.attack_chain?.filter(s => s.severity === 'high')?.length || 0,
        medium: scan.attack_chain?.filter(s => s.severity === 'medium')?.length || 0,
        low: scan.attack_chain?.filter(s => s.severity === 'low')?.length || 0
      },
      // 存储完整结果（压缩版本）
      result: {
        target: scan.target,
        execution_time: scan.execution_time,
        execution_mode: scan.execution_mode,
        success: scan.success,
        attack_chain: scan.attack_chain?.slice(0, 20), // 最多保留20个步骤
        target_analysis: scan.target_analysis,
        rule_engine_decision: scan.rule_engine_decision
      }
    };

    // 添加到开头
    history.unshift(newRecord);

    // 限制数量
    const trimmedHistory = history.slice(0, MAX_HISTORY);

    // 保存
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmedHistory));
    } catch (error) {
      console.error('保存扫描历史失败:', error);
      // 如果存储失败，尝试删除旧记录
      if (error.name === 'QuotaExceededError') {
        const reducedHistory = trimmedHistory.slice(0, MAX_HISTORY / 2);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(reducedHistory));
      }
    }

    return newRecord;
  },

  /**
   * 获取单个记录
   * @param {string} id - 记录ID
   * @returns {Object|null} 扫描记录
   */
  getById(id) {
    const history = this.getAll();
    return history.find(item => item.id === id) || null;
  },

  /**
   * 删除单个记录
   * @param {string} id - 记录ID
   * @returns {boolean} 是否删除成功
   */
  delete(id) {
    const history = this.getAll();
    const filtered = history.filter(item => item.id !== id);
    
    if (filtered.length === history.length) {
      return false;
    }

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
      return true;
    } catch (error) {
      console.error('删除扫描历史失败:', error);
      return false;
    }
  },

  /**
   * 清空所有历史
   * @returns {boolean} 是否清空成功
   */
  clear() {
    try {
      localStorage.removeItem(STORAGE_KEY);
      return true;
    } catch (error) {
      console.error('清空扫描历史失败:', error);
      return false;
    }
  },

  /**
   * 获取统计信息
   * @returns {Object} 统计信息
   */
  getStats() {
    const history = this.getAll();
    
    const stats = {
      total: history.length,
      successful: history.filter(h => h.success).length,
      failed: history.filter(h => !h.success).length,
      uniqueTargets: new Set(history.map(h => h.target)).size,
      totalVulnerabilities: {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0
      },
      recentTargets: []
    };

    // 统计漏洞
    history.forEach(h => {
      if (h.vulnerabilities) {
        stats.totalVulnerabilities.critical += h.vulnerabilities.critical || 0;
        stats.totalVulnerabilities.high += h.vulnerabilities.high || 0;
        stats.totalVulnerabilities.medium += h.vulnerabilities.medium || 0;
        stats.totalVulnerabilities.low += h.vulnerabilities.low || 0;
      }
    });

    // 获取最近目标
    const targetMap = new Map();
    history.forEach(h => {
      if (!targetMap.has(h.target)) {
        targetMap.set(h.target, {
          target: h.target,
          count: 0,
          lastScan: h.timestamp
        });
      }
      targetMap.get(h.target).count++;
    });
    stats.recentTargets = Array.from(targetMap.values())
      .sort((a, b) => new Date(b.lastScan) - new Date(a.lastScan))
      .slice(0, 5);

    return stats;
  },

  /**
   * 导出历史记录
   * @param {string} format - 导出格式 (json, csv)
   * @returns {string} 导出的数据
   */
  export(format = 'json') {
    const history = this.getAll();

    if (format === 'csv') {
      const headers = ['ID', '时间', '目标', '执行时间', '执行模式', '成功', '漏洞-严重', '漏洞-高危', '漏洞-中危', '漏洞-低危'];
      const rows = history.map(h => [
        h.id,
        h.timestamp,
        h.target,
        h.executionTime,
        h.executionMode,
        h.success ? '是' : '否',
        h.vulnerabilities?.critical || 0,
        h.vulnerabilities?.high || 0,
        h.vulnerabilities?.medium || 0,
        h.vulnerabilities?.low || 0
      ]);
      
      return [headers, ...rows].map(row => row.join(',')).join('\n');
    }

    return JSON.stringify(history, null, 2);
  },

  /**
   * 导入历史记录
   * @param {string} data - 导入的数据
   * @param {string} format - 数据格式
   * @returns {number} 导入的记录数
   */
  import(data, format = 'json') {
    try {
      let importedRecords = [];

      if (format === 'json') {
        importedRecords = JSON.parse(data);
      } else {
        throw new Error('不支持的导入格式');
      }

      if (!Array.isArray(importedRecords)) {
        throw new Error('无效的数据格式');
      }

      const history = this.getAll();
      const existingIds = new Set(history.map(h => h.id));

      // 过滤已存在的记录
      const newRecords = importedRecords.filter(r => !existingIds.has(r.id));
      
      // 合并并排序
      const merged = [...newRecords, ...history]
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
        .slice(0, MAX_HISTORY);

      localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
      return newRecords.length;
    } catch (error) {
      console.error('导入扫描历史失败:', error);
      throw error;
    }
  }
};

export default scanHistoryService;
