import React from 'react';
import {
  Target, Play, Brain, GitBranch, CheckCircle, AlertCircle,
  Network, Cpu, Shield, Zap, Lock, BarChart3, Clock, Users
} from 'lucide-react';

/**
 * 标准视图组件 - 为有一定经验的用户提供适度简化的界面
 */
const StandardView = ({
  target,
  setTarget,
  onAttack,
  loading,
  attackData,
  error,
  darkMode = true,
  ruleEngineMode = true,
  onToggleRuleEngine
}) => {

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'bg-red-500 text-white',
      high: 'bg-orange-500 text-white',
      medium: 'bg-yellow-500 text-gray-900',
      low: 'bg-green-500 text-white'
    };
    return colors[severity] || 'bg-gray-500 text-white';
  };

  const getToolIcon = (tool) => {
    const icons = {
      nmap: <Network className="w-5 h-5" />,
      whatweb: <Cpu className="w-5 h-5" />,
      nuclei: <Shield className="w-5 h-5" />,
      exploit: <Zap className="w-5 h-5" />,
      post: <Lock className="w-5 h-5" />
    };
    return icons[tool] || <Network className="w-5 h-5" />;
  };

  const getToolColor = (tool) => {
    const colors = {
      nmap: 'bg-blue-500',
      whatweb: 'bg-purple-500',
      nuclei: 'bg-green-500',
      exploit: 'bg-red-500',
      post: 'bg-yellow-500'
    };
    return colors[tool] || 'bg-gray-500';
  };

  return (
    <div className="space-y-6">
      {/* 控制面板 */}
      <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">ClawAI 安全评估</h1>
            <p className="opacity-80">专业的网站安全扫描与漏洞检测</p>
          </div>
          <div className="flex items-center space-x-3">
            <div className={`px-4 py-2 rounded-full ${ruleEngineMode ? 'bg-green-900/30 text-green-400' : 'bg-gray-700 text-gray-400'}`}>
              <span className="flex items-center">
                <Brain className="w-4 h-4 mr-2" />
                {ruleEngineMode ? '智能模式' : '基础模式'}
              </span>
            </div>
            <button
              onClick={onToggleRuleEngine}
              className="p-2 rounded-lg hover:bg-gray-700"
              title="切换智能决策模式"
            >
              <Brain className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 目标输入 */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">检测目标</label>
            <div className="flex space-x-3">
              <input
                type="text"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="输入网站地址、IP或域名"
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
                    扫描中...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5 mr-2" />
                    开始扫描
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

          {/* 快速目标和模式说明 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <h3 className="font-medium mb-2">快速目标</h3>
              <div className="flex flex-wrap gap-2">
                {['example.com', 'localhost', '192.168.1.1', 'scanme.nmap.org'].map((quickTarget) => (
                  <button
                    key={quickTarget}
                    onClick={() => setTarget(quickTarget)}
                    className="px-3 py-1 text-sm rounded hover:bg-gray-600"
                  >
                    {quickTarget}
                  </button>
                ))}
              </div>
            </div>
            <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <div className="flex items-center mb-2">
                <Brain className="w-5 h-5 text-green-400 mr-2" />
                <span className="font-medium">智能决策模式</span>
              </div>
              <p className="text-sm opacity-70">
                {ruleEngineMode
                  ? '使用规则引擎智能选择最优攻击路径'
                  : '使用基础扫描模式，快速检测常见漏洞'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 结果展示区域 */}
      {attackData && (
        <>
          {/* 扫描概览 */}
          <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
            <div className="flex items-center mb-6">
              <BarChart3 className="w-6 h-6 text-blue-400 mr-2" />
              <h2 className="text-xl font-semibold">扫描概览</h2>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                <div className="text-sm text-gray-400 mb-1">目标</div>
                <div className="text-lg font-semibold">{attackData.target}</div>
              </div>
              <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                <div className="text-sm text-gray-400 mb-1">扫描时间</div>
                <div className="text-lg font-semibold">{attackData.execution_time}</div>
              </div>
              <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                <div className="text-sm text-gray-400 mb-1">攻击步骤</div>
                <div className="text-lg font-semibold">{attackData.attack_chain?.length || 0}</div>
              </div>
              <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                <div className="text-sm text-gray-400 mb-1">模式</div>
                <div className="text-lg font-semibold">{attackData.rule_engine_used ? '智能' : '基础'}</div>
              </div>
            </div>

            {/* 扫描结果摘要 */}
            <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'} mb-6`}>
              <h3 className="font-medium mb-3">扫描结果摘要</h3>
              {attackData.attack_chain && attackData.attack_chain.length > 0 && (
                <div className="space-y-2">
                  {attackData.attack_chain.slice(0, 3).map((step) => (
                    <div key={step.step} className="flex items-center justify-between p-2 hover:bg-gray-700/30 rounded">
                      <div className="flex items-center">
                        <div className={`w-8 h-8 rounded-full ${getToolColor(step.tool)} flex items-center justify-center mr-3`}>
                          {getToolIcon(step.tool)}
                        </div>
                        <div>
                          <div className="font-medium text-sm">步骤 {step.step}: {step.title}</div>
                          <div className="text-xs opacity-70">{step.description}</div>
                        </div>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(step.severity)}`}>
                        {step.severity}
                      </span>
                    </div>
                  ))}
                  {attackData.attack_chain.length > 3 && (
                    <div className="text-center text-sm opacity-70 pt-2">
                      还有 {attackData.attack_chain.length - 3} 个步骤...
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* 严重性统计 */}
            <div>
              <h3 className="font-medium mb-3">漏洞严重性分布</h3>
              <div className="grid grid-cols-4 gap-2">
                {['critical', 'high', 'medium', 'low'].map((severity) => {
                  const count = attackData.attack_chain?.filter(step => step.severity === severity).length || 0;
                  return (
                    <div key={severity} className="text-center">
                      <div className={`w-12 h-12 rounded-full ${getSeverityColor(severity)} flex items-center justify-center mx-auto mb-2`}>
                        <span className="font-bold">{count}</span>
                      </div>
                      <div className="text-xs capitalize">{severity}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* 攻击链可视化 */}
          <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
            <div className="flex items-center mb-6">
              <GitBranch className="w-6 h-6 text-purple-400 mr-2" />
              <h2 className="text-xl font-semibold">攻击链可视化</h2>
            </div>

            <div className="relative mb-8">
              {/* 连接线 */}
              <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 -translate-y-1/2 z-0"></div>

              {/* 攻击步骤 */}
              <div className="relative z-10 flex justify-between items-center">
                {attackData.attack_chain && attackData.attack_chain.slice(0, 5).map((step) => (
                  <div key={step.step} className="flex flex-col items-center">
                    <div className={`w-14 h-14 rounded-full ${getToolColor(step.tool)} flex items-center justify-center mb-3 relative ring-2 ${getSeverityColor(step.severity)}`}>
                      <div className="text-white">{getToolIcon(step.tool)}</div>
                      <div className="absolute -top-2 -right-2 w-6 h-6 bg-gray-900 rounded-full border border-white flex items-center justify-center">
                        <span className="text-xs font-bold text-white">{step.step}</span>
                      </div>
                    </div>
                    <div className="text-center max-w-[100px]">
                      <div className="font-semibold mb-1 text-xs">{step.title}</div>
                      <div className="text-xs opacity-70">{step.tool}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 步骤详情 */}
            <div className="space-y-3">
              {attackData.attack_chain && attackData.attack_chain.map((step) => (
                <div key={step.step} className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-100'}`}>
                  <div className="flex items-center">
                    <div className={`w-10 h-10 rounded-full ${getToolColor(step.tool)} flex items-center justify-center mr-3`}>
                      {getToolIcon(step.tool)}
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">步骤 {step.step}: {step.title}</div>
                      <div className="text-sm opacity-70">{step.description}</div>
                      <div className="flex items-center mt-1">
                        <Clock className="w-3 h-3 mr-1" />
                        <span className="text-xs opacity-70">{step.duration}</span>
                        <span className="mx-2">•</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${getSeverityColor(step.severity)}`}>
                          {step.severity}
                        </span>
                      </div>
                    </div>
                    {step.success ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 规则引擎决策（如果启用） */}
          {attackData.rule_engine_decision && (
            <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
              <div className="flex items-center mb-6">
                <Brain className="w-6 h-6 text-green-400 mr-2" />
                <h2 className="text-xl font-semibold">智能决策分析</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                  <h3 className="font-medium mb-3">最优攻击路径</h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">路径类型</span>
                      <span className="font-medium">{attackData.rule_engine_decision.selected_path_type}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">决策评分</span>
                      <div className="flex items-center">
                        <span className="text-2xl font-bold mr-2">{attackData.rule_engine_decision.selected_score}</span>
                        <span className="text-gray-400">/10</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">置信度</span>
                      <span className="font-medium text-green-400">
                        {Math.round(attackData.rule_engine_decision.confidence * 100)}%
                      </span>
                    </div>
                  </div>
                </div>

                <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                  <h3 className="font-medium mb-3">主要选择原因</h3>
                  <ul className="space-y-1">
                    {attackData.rule_engine_decision.selection_reasons?.slice(0, 3).map((reason, index) => (
                      <li key={index} className="flex items-start text-sm">
                        <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 mr-2 flex-shrink-0" />
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* 操作按钮 */}
          <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
            <h3 className="font-medium mb-4">后续操作</h3>
            <div className="flex flex-wrap gap-3">
              <button className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:opacity-90">
                生成详细报告
              </button>
              <button className="px-4 py-2 bg-gray-700 rounded-lg hover:bg-gray-600">
                导出扫描结果
              </button>
              <button className="px-4 py-2 border border-gray-600 rounded-lg hover:bg-gray-700">
                分享结果
              </button>
              <button
                onClick={() => setTarget('')}
                className="px-4 py-2 border border-gray-600 rounded-lg hover:bg-gray-700"
              >
                扫描新目标
              </button>
            </div>
          </div>
        </>
      )}

      {/* 功能说明（无结果时显示） */}
      {!attackData && (
        <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
          <h2 className="text-xl font-semibold mb-4">功能特性</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <div className="flex items-center mb-2">
                <Network className="w-5 h-5 text-blue-400 mr-2" />
                <span className="font-medium">全面扫描</span>
              </div>
              <p className="text-sm opacity-70">端口扫描、服务识别、漏洞检测一体化</p>
            </div>
            <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <div className="flex items-center mb-2">
                <Brain className="w-5 h-5 text-green-400 mr-2" />
                <span className="font-medium">智能决策</span>
              </div>
              <p className="text-sm opacity-70">规则引擎自动选择最优攻击路径</p>
            </div>
            <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <div className="flex items-center mb-2">
                <Shield className="w-5 h-5 text-red-400 mr-2" />
                <span className="font-medium">风险评估</span>
              </div>
              <p className="text-sm opacity-70">详细的风险评估和安全建议</p>
            </div>
            <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <div className="flex items-center mb-2">
                <Users className="w-5 h-5 text-purple-400 mr-2" />
                <span className="font-medium">团队协作</span>
              </div>
              <p className="text-sm opacity-70">支持报告分享和团队协作</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StandardView;