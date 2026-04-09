import React, { useState, useEffect } from 'react';
import {
  Clock, Target, CheckCircle, XCircle, Trash2,
  Download, Upload, RefreshCw, ChevronRight, AlertTriangle,
  AlertCircle, Info, Search, Filter, X
} from 'lucide-react';
import scanHistoryService from '../services/scanHistoryService';
import { Skeleton, TextSkeleton } from './Skeleton';
import { useScan } from '../context/ScanContext';

/**
 * 扫描历史组件
 */
const ScanHistory = ({ onLoadScan, darkMode = true }) => {
  const { scanHistory, refreshHistory, selectScan } = useScan();
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSuccess, setFilterSuccess] = useState('all'); // all, success, failed

  // 加载历史记录
  const loadHistory = () => {
    setLoading(true);
    try {
      const data = scanHistoryService.getAll();
      const statistics = scanHistoryService.getStats();
      setHistory(data);
      setStats(statistics);
    } catch (error) {
      console.error('加载历史记录失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // ScanContext 历史变化时自动刷新
  useEffect(() => {
    loadHistory();
  }, [scanHistory]); // eslint-disable-line react-hooks/exhaustive-deps

  // 删除记录
  const handleDelete = (id, e) => {
    e.stopPropagation();
    if (confirm('确定要删除这条记录吗？')) {
      scanHistoryService.delete(id);
      refreshHistory();
      loadHistory();
    }
  };

  // 清空所有
  const handleClearAll = () => {
    if (confirm('确定要清空所有历史记录吗？此操作不可恢复。')) {
      scanHistoryService.clear();
      refreshHistory();
      loadHistory();
    }
  };

  // 导出
  const handleExport = () => {
    const data = scanHistoryService.export('json');
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `clawai-history-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // 导入
  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (file) {
        const text = await file.text();
        try {
          const count = scanHistoryService.import(text, 'json');
          alert(`成功导入 ${count} 条记录`);
          loadHistory();
        } catch (error) {
          alert('导入失败: ' + error.message);
        }
      }
    };
    input.click();
  };

  // 加载历史扫描结果
  const handleLoadScan = (record) => {
    setSelectedRecord(record);
    // 通知 ScanContext（全局联动）
    selectScan(record);
    if (onLoadScan && record.result) {
      onLoadScan(record.result);
    }
  };

  // 过滤历史记录
  const filteredHistory = history.filter(item => {
    // 搜索过滤
    if (searchTerm && !item.target.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    // 成功/失败过滤
    if (filterSuccess === 'success' && !item.success) return false;
    if (filterSuccess === 'failed' && item.success) return false;
    return true;
  });

  // 格式化时间
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;
    if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`;

    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 获取漏洞图标
  const getVulnerabilityIcon = (type, count) => {
    if (count === 0) return null;
    const icons = {
      critical: <AlertTriangle className="w-4 h-4 text-red-500" />,
      high: <AlertCircle className="w-4 h-4 text-orange-500" />,
      medium: <Info className="w-4 h-4 text-yellow-500" />,
      low: <Info className="w-4 h-4 text-blue-500" />
    };
    return icons[type];
  };

  const baseClass = darkMode ? 'bg-[#0a0e17] text-white' : 'bg-[#0a0e17] text-gray-900';
  const borderClass = darkMode ? 'border-white/10' : 'border-gray-200';

  return (
    <div className={`${baseClass} rounded-2xl shadow-xl overflow-hidden`}>
      {/* 头部 */}
      <div className={`p-6 border-b ${borderClass}`}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold">扫描历史</h2>
            <p className="opacity-70 mt-1">查看和管理历史扫描记录</p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleImport}
              className={`p-2 rounded-lg ${darkMode ? 'hover:bg-[#111827]' : 'hover:bg-gray-100'}`}
              title="导入"
            >
              <Upload className="w-5 h-5" />
            </button>
            <button
              onClick={handleExport}
              className={`p-2 rounded-lg ${darkMode ? 'hover:bg-[#111827]' : 'hover:bg-gray-100'}`}
              title="导出"
            >
              <Download className="w-5 h-5" />
            </button>
            <button
              onClick={loadHistory}
              className={`p-2 rounded-lg ${darkMode ? 'hover:bg-[#111827]' : 'hover:bg-gray-100'}`}
              title="刷新"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 搜索和过滤 */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 opacity-50" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="搜索目标..."
              className={`w-full pl-10 pr-4 py-2 rounded-lg ${darkMode ? 'bg-[#111827] border-white/15' : 'bg-gray-100 border-gray-300'} border focus:outline-none focus:ring-2 focus:ring-blue-500`}
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 opacity-50 hover:opacity-100"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          <select
            value={filterSuccess}
            onChange={(e) => setFilterSuccess(e.target.value)}
            className={`px-4 py-2 rounded-lg ${darkMode ? 'bg-[#111827] border-white/15' : 'bg-gray-100 border-gray-300'} border focus:outline-none focus:ring-2 focus:ring-blue-500`}
          >
            <option value="all">全部</option>
            <option value="success">成功</option>
            <option value="failed">失败</option>
          </select>
        </div>
      </div>

      {/* 统计卡片 */}
      {stats && (
        <div className={`grid grid-cols-2 sm:grid-cols-4 gap-4 p-6 border-b ${borderClass} ${darkMode ? 'bg-[#060910]/50' : 'bg-[#111827]'}`}>
          <div className="text-center">
            <div className="text-2xl font-bold">{stats.total}</div>
            <div className="text-sm opacity-70">总扫描次数</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-500">{stats.successful}</div>
            <div className="text-sm opacity-70">成功</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-500">{stats.failed}</div>
            <div className="text-sm opacity-70">失败</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-500">{stats.uniqueTargets}</div>
            <div className="text-sm opacity-70">独立目标</div>
          </div>
        </div>
      )}

      {/* 历史列表 */}
      <div className="divide-y divide-white/10">
        {loading ? (
          <div className="p-6 space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center space-x-4">
                <Skeleton className="w-10 h-10 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-1/3" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : filteredHistory.length === 0 ? (
          <div className="p-12 text-center opacity-70">
            <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>暂无扫描历史</p>
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="mt-2 text-blue-500 hover:underline"
              >
                清除搜索条件
              </button>
            )}
          </div>
        ) : (
          filteredHistory.map((item) => (
            <div
              key={item.id}
              onClick={() => handleLoadScan(item)}
              className={`p-4 flex items-center cursor-pointer transition-colors ${darkMode ? 'hover:bg-[#111827]/50' : 'hover:bg-[#111827]'}`}
            >
              {/* 状态图标 */}
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${item.success ? 'bg-green-500/100/20' : 'bg-red-500/100/20'}`}>
                {item.success ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-500" />
                )}
              </div>

              {/* 内容 */}
              <div className="flex-1 ml-4">
                <div className="flex items-center">
                  <Target className="w-4 h-4 mr-2 opacity-50" />
                  <span className="font-medium font-mono">{item.target}</span>
                </div>
                <div className="flex items-center mt-1 text-sm opacity-70">
                  <Clock className="w-4 h-4 mr-1" />
                  {formatTime(item.timestamp)}
                  <span className="mx-2">•</span>
                  {item.executionTime}
                  <span className="mx-2">•</span>
                  {item.executionMode}
                </div>
              </div>

              {/* 漏洞统计 */}
              <div className="hidden sm:flex items-center space-x-2 mr-4">
                {item.vulnerabilities?.critical > 0 && (
                  <div className="flex items-center px-2 py-1 rounded bg-red-500/100/20">
                    <AlertTriangle className="w-3 h-3 text-red-500 mr-1" />
                    <span className="text-xs text-red-500">{item.vulnerabilities?.critical}</span>
                  </div>
                )}
                {item.vulnerabilities?.high > 0 && (
                  <div className="flex items-center px-2 py-1 rounded bg-orange-500/20">
                    <AlertCircle className="w-3 h-3 text-orange-500 mr-1" />
                    <span className="text-xs text-orange-500">{item.vulnerabilities?.high}</span>
                  </div>
                )}
              </div>

              {/* 操作按钮 */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={(e) => handleDelete(item.id, e)}
                  className={`p-2 rounded-lg ${darkMode ? 'hover:bg-[#1a2035]' : 'hover:bg-gray-200'} text-red-500`}
                  title="删除"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <ChevronRight className="w-5 h-5 opacity-50" />
              </div>
            </div>
          ))
        )}
      </div>

      {/* 底部 */}
      {history.length > 0 && (
        <div className={`p-4 border-t ${borderClass} ${darkMode ? 'bg-[#060910]/50' : 'bg-[#111827]'} flex justify-between items-center`}>
          <span className="text-sm opacity-70">
            共 {history.length} 条记录
          </span>
          <button
            onClick={handleClearAll}
            className="text-sm text-red-500 hover:text-red-400"
          >
            清空所有
          </button>
        </div>
      )}

      {/* 详情弹窗 */}
      {selectedRecord && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className={`${baseClass} rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-auto`}>
            <div className={`p-6 border-b ${borderClass} flex items-center justify-between`}>
              <div>
                <h3 className="text-xl font-bold">扫描详情</h3>
                <p className="text-sm opacity-70 mt-1">
                  {new Date(selectedRecord.timestamp).toLocaleString('zh-CN')}
                </p>
              </div>
              <button
                onClick={() => setSelectedRecord(null)}
                className={`p-2 rounded-lg ${darkMode ? 'hover:bg-[#111827]' : 'hover:bg-gray-100'}`}
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <label className="text-sm opacity-70">目标</label>
                  <p className="font-mono">{selectedRecord.target}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm opacity-70">执行时间</label>
                    <p>{selectedRecord.executionTime}</p>
                  </div>
                  <div>
                    <label className="text-sm opacity-70">执行模式</label>
                    <p>{selectedRecord.executionMode}</p>
                  </div>
                </div>
                <div>
                  <label className="text-sm opacity-70">漏洞统计</label>
                  <div className="flex space-x-4 mt-2">
                    {Object.entries(selectedRecord.vulnerabilities || {}).map(([type, count]) => (
                      count > 0 && (
                        <div key={type} className="flex items-center">
                          {getVulnerabilityIcon(type, count)}
                          <span className="ml-1">{count} {type}</span>
                        </div>
                      )
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setSelectedRecord(null)}
                  className={`px-4 py-2 rounded-lg ${darkMode ? 'bg-[#111827] hover:bg-[#1a2035]' : 'bg-gray-200 hover:bg-gray-300'}`}
                >
                  关闭
                </button>
                <button
                  onClick={() => {
                    handleLoadScan(selectedRecord);
                    setSelectedRecord(null);
                  }}
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white"
                >
                  加载此扫描
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScanHistory;
