import React from 'react';
import { Target, Play, CheckCircle, AlertCircle, Shield, Zap, Brain, Info } from 'lucide-react';

/**
 * 简单视图组件 - 为初学者提供最简化的界面
 */
const SimpleView = ({
  target,
  setTarget,
  onAttack,
  loading,
  attackData,
  error,
  darkMode = true
}) => {

  const handleQuickTarget = (quickTarget) => {
    setTarget(quickTarget);
  };

  // 提取简化的结果信息
  const getSimpleResults = () => {
    if (!attackData) return null;

    const totalSteps = attackData.attack_chain?.length || 0;
    const criticalFindings = attackData.attack_chain?.filter(step =>
      step.severity === 'critical' || step.severity === 'high'
    ).length || 0;

    const successSteps = attackData.attack_chain?.filter(step =>
      step.success
    ).length || 0;

    return {
      totalSteps,
      criticalFindings,
      successSteps,
      successRate: totalSteps > 0 ? Math.round((successSteps / totalSteps) * 100) : 0,
      executionTime: attackData.execution_time || '未知',
      target: attackData.target
    };
  };

  const simpleResults = getSimpleResults();

  return (
    <div className="space-y-6">
      {/* 欢迎标题 */}
      <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gradient-to-r from-blue-900/30 to-purple-900/30' : 'bg-gradient-to-r from-blue-50 to-purple-50'}`}>
        <div className="flex items-center">
          <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl mr-4">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">ClawAI 安全检测</h1>
            <p className="opacity-80 mt-1">简单易用的网站安全检查工具</p>
          </div>
        </div>
        <div className={`mt-4 p-3 rounded-lg ${darkMode ? 'bg-blue-900/20' : 'bg-blue-50'} text-sm`}>
          <div className="flex items-center">
            <Info className="w-4 h-4 mr-2 text-blue-400" />
            <span>输入网站地址，一键检测安全漏洞</span>
          </div>
        </div>
      </div>

      {/* 目标输入区域 */}
      <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
        <h2 className="text-xl font-semibold mb-4">🔍 检测目标</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">网站地址</label>
            <div className="flex space-x-3">
              <input
                type="text"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="例如: example.com 或 192.168.1.1"
                className={`flex-1 px-4 py-3 rounded-lg ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'} border focus:outline-none focus:ring-2 focus:ring-blue-500`}
              />
              <button
                onClick={onAttack}
                disabled={loading || !target.trim()}
                className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-lg hover:opacity-90 disabled:opacity-50 flex items-center"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    检测中...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5 mr-2" />
                    开始检测
                  </>
                )}
              </button>
            </div>
            {error && (
              <div className="mt-2 flex items-center text-red-400 text-sm">
                <AlertCircle className="w-4 h-4 mr-1" />
                {error}
              </div>
            )}
          </div>

          {/* 快速目标 */}
          <div>
            <p className="text-sm opacity-70 mb-2">快速选择:</p>
            <div className="flex flex-wrap gap-2">
              {['example.com', 'localhost', '192.168.1.1', 'scanme.nmap.org'].map((quickTarget) => (
                <button
                  key={quickTarget}
                  onClick={() => handleQuickTarget(quickTarget)}
                  className={`px-3 py-2 rounded-lg text-sm ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-100 hover:bg-gray-200'}`}
                >
                  {quickTarget}
                </button>
              ))}
            </div>
          </div>

          {/* 说明卡片 */}
          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
            <div className="flex items-center mb-2">
              <Brain className="w-5 h-5 text-green-400 mr-2" />
              <span className="font-medium">智能检测</span>
            </div>
            <p className="text-sm opacity-70">自动扫描网站漏洞，生成安全报告，提供修复建议。</p>
          </div>
        </div>
      </div>

      {/* 结果展示区域 */}
      {attackData && simpleResults && (
        <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
          <h2 className="text-xl font-semibold mb-4">📊 检测结果</h2>

          {/* 结果概览 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <div className="text-sm text-gray-400 mb-1">检测步骤</div>
              <div className="text-2xl font-bold">{simpleResults.totalSteps}</div>
            </div>
            <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <div className="text-sm text-gray-400 mb-1">严重发现</div>
              <div className="text-2xl font-bold text-red-500">{simpleResults.criticalFindings}</div>
            </div>
            <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <div className="text-sm text-gray-400 mb-1">成功率</div>
              <div className="text-2xl font-bold text-green-500">{simpleResults.successRate}%</div>
            </div>
            <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <div className="text-sm text-gray-400 mb-1">检测时间</div>
              <div className="text-lg font-semibold">{simpleResults.executionTime}</div>
            </div>
          </div>

          {/* 安全状态 */}
          <div className={`p-4 rounded-lg ${simpleResults.criticalFindings > 0 ? 'bg-red-500/10 border-red-500/30' : 'bg-green-500/10 border-green-500/30'} border mb-6`}>
            <div className="flex items-center">
              {simpleResults.criticalFindings > 0 ? (
                <>
                  <AlertCircle className="w-6 h-6 text-red-500 mr-3" />
                  <div>
                    <h3 className="font-bold text-red-500">⚠️ 发现安全风险</h3>
                    <p className="text-sm opacity-90 mt-1">
                      检测到 {simpleResults.criticalFindings} 个严重安全问题，建议立即处理。
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <CheckCircle className="w-6 h-6 text-green-500 mr-3" />
                  <div>
                    <h3 className="font-bold text-green-500">✅ 安全状态良好</h3>
                    <p className="text-sm opacity-90 mt-1">
                      未发现严重安全漏洞，网站安全性良好。
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* 操作建议 */}
          <div>
            <h3 className="font-medium mb-3">📋 建议操作</h3>
            <div className="space-y-2">
              {simpleResults.criticalFindings > 0 ? (
                <>
                  <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-100'} flex items-center`}>
                    <div className="w-2 h-2 rounded-full bg-red-500 mr-3"></div>
                    <span>查看详细漏洞报告</span>
                  </div>
                  <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-100'} flex items-center`}>
                    <div className="w-2 h-2 rounded-full bg-orange-500 mr-3"></div>
                    <span>按照修复建议处理漏洞</span>
                  </div>
                  <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-100'} flex items-center`}>
                    <div className="w-2 h-2 rounded-full bg-blue-500 mr-3"></div>
                    <span>定期进行安全检查</span>
                  </div>
                </>
              ) : (
                <>
                  <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-100'} flex items-center`}>
                    <div className="w-2 h-2 rounded-full bg-green-500 mr-3"></div>
                    <span>继续保持安全配置</span>
                  </div>
                  <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-100'} flex items-center`}>
                    <div className="w-2 h-2 rounded-full bg-blue-500 mr-3"></div>
                    <span>定期更新系统和软件</span>
                  </div>
                  <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-100'} flex items-center`}>
                    <div className="w-2 h-2 rounded-full bg-purple-500 mr-3"></div>
                    <span>设置安全监控告警</span>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* 下一步按钮 */}
          <div className="mt-6 pt-6 border-t border-gray-700">
            <div className="flex space-x-3">
              <button className="px-4 py-2 bg-gray-700 rounded-lg hover:bg-gray-600">
                导出报告
              </button>
              <button className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:opacity-90">
                查看详细分析
              </button>
              <button
                onClick={() => setTarget('')}
                className="px-4 py-2 border border-gray-600 rounded-lg hover:bg-gray-700"
              >
                检测新目标
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 使用说明 */}
      {!attackData && (
        <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
          <h2 className="text-xl font-semibold mb-4">ℹ️ 使用说明</h2>
          <div className="space-y-4">
            <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <div className="flex items-center mb-2">
                <Target className="w-5 h-5 text-blue-400 mr-2" />
                <span className="font-medium">第一步：输入目标</span>
              </div>
              <p className="text-sm opacity-70">输入您要检测的网站地址或IP地址。</p>
            </div>
            <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <div className="flex items-center mb-2">
                <Zap className="w-5 h-5 text-green-400 mr-2" />
                <span className="font-medium">第二步：开始检测</span>
              </div>
              <p className="text-sm opacity-70">点击"开始检测"按钮，系统将自动扫描安全漏洞。</p>
            </div>
            <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <div className="flex items-center mb-2">
                <Shield className="w-5 h-5 text-red-400 mr-2" />
                <span className="font-medium">第三步：查看结果</span>
              </div>
              <p className="text-sm opacity-70">查看检测报告，了解安全状态和修复建议。</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SimpleView;