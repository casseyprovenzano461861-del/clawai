import React, { useState, useEffect } from 'react';
import {
  Target, Play, Brain, Shield, Zap, CheckCircle, AlertCircle,
  Cpu, Network, Lock, RefreshCw, Activity, Search, Settings,
  BarChart3, Clock, AlertTriangle
} from 'lucide-react';

const ClawAIDashboard = () => {
  const [target, setTarget] = useState('');
  const [loading, setLoading] = useState(false);
  const [attackData, setAttackData] = useState(null);
  const [error, setError] = useState(null);
  const [tools, setTools] = useState([]);
  const [health, setHealth] = useState(null);
  const [darkMode] = useState(true);

  // 获取工具列表
  const fetchTools = async () => {
    try {
      const response = await fetch('/tools');
      if (response.ok) {
        const data = await response.json();
        setTools(data.tools || []);
      }
    } catch (err) {
      console.error('获取工具列表失败:', err);
    }
  };

  // 获取健康状态
  const fetchHealth = async () => {
    try {
      const response = await fetch('/health');
      if (response.ok) {
        const data = await response.json();
        setHealth(data);
      }
    } catch (err) {
      console.error('获取健康状态失败:', err);
    }
  };

  // 执行扫描
  const executeScan = async () => {
    if (!target.trim()) {
      setError('请输入目标IP或域名');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/attack', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target: target.trim(),
          use_real: false,
          rule_engine_mode: true
        }),
      });

      if (!response.ok) {
        throw new Error(`API请求失败: ${response.status}`);
      }

      const data = await response.json();
      setAttackData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 初始化加载
  useEffect(() => {
    fetchTools();
    fetchHealth();
  }, []);

  // 严重性颜色映射
  const severityColors = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-yellow-500',
    low: 'bg-blue-500',
    info: 'bg-gray-500'
  };

  return (
    <div className={`min-h-screen ${darkMode ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-900'}`}>
      {/* 导航栏 */}
      <header className={`${darkMode ? 'bg-gray-800' : 'bg-white'} border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-purple-500" />
              <span className="ml-2 text-xl font-bold">ClawAI</span>
              <span className="ml-2 text-sm opacity-70">智能安全评估系统</span>
            </div>
            <div className="flex items-center space-x-4">
              <button className="p-2 rounded-lg hover:bg-gray-700">
                <Settings className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 健康状态卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-xl p-6 shadow-lg`}>
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-green-500 mr-3" />
              <div>
                <h3 className="text-lg font-semibold">系统状态</h3>
                <p className="text-sm opacity-70">
                  {health ? (health.status === 'healthy' ? '运行正常' : '服务异常') : '检查中...'}
                </p>
              </div>
            </div>
          </div>

          <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-xl p-6 shadow-lg`}>
            <div className="flex items-center">
              <Cpu className="h-8 w-8 text-blue-500 mr-3" />
              <div>
                <h3 className="text-lg font-semibold">工具集成</h3>
                <p className="text-sm opacity-70">
                  {tools.filter(t => t.status === 'available').length} / {tools.length} 个工具可用
                </p>
              </div>
            </div>
          </div>

          <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-xl p-6 shadow-lg`}>
            <div className="flex items-center">
              <Brain className="h-8 w-8 text-purple-500 mr-3" />
              <div>
                <h3 className="text-lg font-semibold">AI引擎</h3>
                <p className="text-sm opacity-70">规则引擎已就绪</p>
              </div>
            </div>
          </div>
        </div>

        {/* 主扫描区域 */}
        <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-2xl p-8 shadow-xl mb-8`}>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold">安全扫描</h2>
              <p className="opacity-70 mt-1">输入目标进行AI驱动的安全评估</p>
            </div>
            <Zap className="h-10 w-10 text-yellow-500" />
          </div>

          {/* 目标输入 */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">目标地址</label>
              <div className="flex space-x-4">
                <input
                  type="text"
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  placeholder="例如: example.com 或 192.168.1.1"
                  className={`flex-1 px-4 py-3 rounded-lg ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-gray-100 border-gray-300'} border focus:outline-none focus:ring-2 focus:ring-purple-500`}
                />
                <button
                  onClick={executeScan}
                  disabled={loading}
                  className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold hover:opacity-90 disabled:opacity-50 flex items-center"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
                      扫描中...
                    </>
                  ) : (
                    <>
                      <Play className="h-5 w-5 mr-2" />
                      开始扫描
                    </>
                  )}
                </button>
              </div>
              {error && (
                <div className="mt-3 p-3 bg-red-900/30 border border-red-700 rounded-lg">
                  <div className="flex items-center">
                    <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
                    <span className="text-red-300">{error}</span>
                  </div>
                </div>
              )}
            </div>

            {/* 安全警告 */}
            <div className="p-4 bg-yellow-900/20 border border-yellow-700 rounded-lg">
              <div className="flex items-start">
                <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2 mt-0.5" />
                <div>
                  <p className="font-medium text-yellow-300">安全警告</p>
                  <p className="text-sm opacity-80 mt-1">
                    仅扫描您拥有权限的网站或系统。未经授权的扫描可能违反法律。
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 扫描结果 */}
        {attackData && (
          <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-2xl p-8 shadow-xl mb-8`}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold">扫描结果</h2>
                <p className="opacity-70 mt-1">
                  目标: <span className="font-mono">{attackData.target}</span> • 时间: {attackData.execution_time}
                </p>
              </div>
              <CheckCircle className="h-10 w-10 text-green-500" />
            </div>

            {/* 攻击链 */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">攻击链 ({attackData.attack_chain?.length || 0}个步骤)</h3>
              <div className="space-y-3">
                {attackData.attack_chain?.map((step, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg border-l-4 ${step.highlight ? 'border-red-500 bg-red-900/10' : 'border-blue-500'} ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center">
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${severityColors[step.severity] || 'bg-gray-500'}`}>
                            {step.severity?.toUpperCase()}
                          </span>
                          <span className="ml-3 font-medium">步骤 {step.step}: {step.title}</span>
                        </div>
                        <p className="mt-2 opacity-80">{step.description}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-sm opacity-70">{step.duration}</div>
                        <div className={`text-sm mt-1 ${step.success ? 'text-green-500' : 'text-red-500'}`}>
                          {step.success ? '✅ 成功' : '❌ 失败'}
                        </div>
                      </div>
                    </div>
                    <div className="mt-2 text-sm opacity-70 flex items-center">
                      <Cpu className="h-4 w-4 mr-1" />
                      工具: {step.tool}
                    </div>
                  </div>
                ))}
              </div>

              {/* 规则引擎决策 */}
              {attackData.rule_engine_decision && (
                <div className="mt-6 p-4 rounded-lg bg-gradient-to-r from-purple-900/20 to-blue-900/20 border border-purple-700/30">
                  <h4 className="font-semibold mb-2">规则引擎决策</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm opacity-70">选择路径</p>
                      <p className="font-mono">{attackData.rule_engine_decision.selected_path_type}</p>
                    </div>
                    <div>
                      <p className="text-sm opacity-70">置信度</p>
                      <p className="font-mono">{(attackData.rule_engine_decision.confidence * 100).toFixed(1)}%</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 工具列表 */}
        <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-2xl p-8 shadow-xl`}>
          <h2 className="text-2xl font-bold mb-6">集成工具</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tools.map((tool, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border ${darkMode ? 'border-gray-700' : 'border-gray-200'} ${tool.status === 'available' ? 'bg-green-900/10' : 'bg-gray-900/10'}`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold">{tool.name}</h4>
                    <p className="text-sm opacity-70 mt-1">{tool.description}</p>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded ${tool.status === 'available' ? 'bg-green-500' : 'bg-gray-500'}`}>
                    {tool.status === 'available' ? '可用' : '不可用'}
                  </span>
                </div>
                <div className="mt-3 text-xs opacity-70">
                  <span className="px-2 py-1 bg-gray-700 rounded">{tool.category}</span>
                  {tool.required && <span className="ml-2 px-2 py-1 bg-red-700 rounded">必需</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>

      <footer className={`${darkMode ? 'bg-gray-800' : 'bg-gray-100'} border-t ${darkMode ? 'border-gray-700' : 'border-gray-200'} mt-8`}>
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <div className="text-sm opacity-70">
              ClawAI v2.0.0 • AI驱动的安全评估系统
            </div>
            <button
              onClick={() => {
                fetchTools();
                fetchHealth();
              }}
              className="p-2 rounded-lg hover:bg-gray-700"
            >
              <RefreshCw className="h-5 w-5" />
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default ClawAIDashboard;