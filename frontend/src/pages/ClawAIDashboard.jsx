import React, { useState } from 'react';
import {
  Target, Play, Brain, GitBranch, TrendingUp, Shield, Zap, CheckCircle,
  Cpu, Network, Lock, AlertCircle, Sparkles, BarChart3,
  Clock, AlertTriangle, RefreshCw,
  Activity, ShieldCheck,
  AlertOctagon, AlertTriangle as AlertTriangleIcon,
  Search, Settings, Menu, X,
  HelpCircle, Bell, User, Home, Users,
  Palette, Eye, Layout, Wand2 // 新增图标
} from 'lucide-react';
import AIMultiModelDecision from '../components/AIMultiModelDecision';
import AIThinkingAnimation from '../components/AIThinkingAnimation';
import OnboardingGuide from '../components/OnboardingGuide';
import UXOptimizer from '../components/UXOptimizer'; // 新增导入
import AttackChain3D from '../components/AttackChain3D'; // 新增3D可视化组件
import SkillLibrary from '../components/SkillLibrary'; // 新增Skills库组件
import SimpleView from '../components/SimpleView'; // 新增：简单视图
import StandardView from '../components/StandardView'; // 新增：标准视图

const ClawAIDashboard = () => {
  const [target, setTarget] = useState('');
  const [loading, setLoading] = useState(false);
  const [attackData, setAttackData] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [ruleEngineMode, setRuleEngineMode] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [showAIThinking, setShowAIThinking] = useState(false);
  const [thinkingType, setThinkingType] = useState('analyze');
  const [visualizationMode, setVisualizationMode] = useState('2d'); // 新增：可视化模式状态
  const [viewMode, setViewMode] = useState('simple'); // 视图模式: simple, standard, expert

  // 模拟数据
  const mockAttackData = {
    target: "192.168.1.100",
    execution_time: "15.3秒",
    execution_mode: "real",
    rule_engine_used: true,
    rule_engine_model: "rule_engine_v1",
    attack_chain: [
      {
        step: 1,
        tool: "nmap",
        title: "网络侦察",
        description: "发现目标 192.168.1.100 的80, 443, 3306端口开放",
        duration: "2.3s",
        success: true,
        severity: "low",
        highlight: false
      },
      {
        step: 2,
        tool: "whatweb",
        title: "指纹识别",
        description: "识别为 WordPress 5.8 + PHP 7.4 + Apache 2.4",
        duration: "1.8s",
        success: true,
        severity: "medium",
        highlight: false
      },
      {
        step: 3,
        tool: "nuclei",
        title: "漏洞扫描",
        description: "发现 WordPress RCE 漏洞 (CVE-2023-1234)",
        duration: "4.2s",
        success: true,
        severity: "critical",
        highlight: true
      },
      {
        step: 4,
        tool: "exploit",
        title: "漏洞利用",
        description: "成功执行远程代码，获取 WebShell 访问权限",
        duration: "3.5s",
        success: true,
        severity: "critical",
        highlight: true
      },
      {
        step: 5,
        tool: "post",
        title: "后渗透",
        description: "建立持久化后门，进行横向移动和数据收集",
        duration: "6.1s",
        success: true,
        severity: "high",
        highlight: false
      }
    ],
    rule_engine_decision: {
      selected_path_type: "rce_attack",
      selected_score: 8.5,
      confidence: 0.92,
      selection_reasons: [
        "规则引擎评分最高 (8.5分)",
        "漏洞严重性: critical",
        "攻击成功率: 85%",
        "可直接获取系统控制权",
        "攻击效果立竿见影"
      ],
      path_comparison: [
        { path_type: "sql_injection", score: 7.2, score_difference: 1.3, main_reason: "评分低1.3分" },
        { path_type: "cms_exploit", score: 6.8, score_difference: 1.7, main_reason: "评分低1.7分" }
      ],
      decision_factors: {
        exploitability: 9.2,
        detection_risk: 2.1,
        success_rate: 0.85,
        time_efficiency: 7.8,
        resource_cost: 6.5
      }
    },
    target_analysis: {
      attack_surface: 7.8,
      open_ports: 3,
      vulnerabilities: 2,
      sql_injections: 0,
      has_cms: true,
      cms_type: "WordPress",
      cms_version: "5.8"
    }
  };

  const handleAttack = async () => {
    if (!target.trim()) {
      setError('请输入目标IP或域名');
      return;
    }

    setLoading(true);
    setError(null);
    setShowAIThinking(true);
    setThinkingType('analyze');

    try {
      // 实际API调用（通过Vite代理到localhost:8000）
      const response = await fetch('/attack', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || 'demo-token'}`
        },
        body: JSON.stringify({
          target: target.trim(),
          use_real: true,
          rule_engine_mode: ruleEngineMode
        }),
      });

      if (!response.ok) {
        throw new Error(`API请求失败: ${response.status}`);
      }

      const data = await response.json();
      setAttackData(data);
    } catch (err) {
      console.error('攻击执行失败:', err);
      setError(`执行失败: ${err.message}`);
      // 使用模拟数据作为回退
      setAttackData({
        ...mockAttackData,
        target: target.trim(),
        execution_mode: "mock_fallback",
        message: "使用模拟数据演示"
      });
    } finally {
      setLoading(false);
      setShowAIThinking(false);
    }
  };

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
    <div className={`min-h-screen ${darkMode ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-900'}`}>
      {/* 新手引导 */}
      <OnboardingGuide 
        onComplete={() => console.log('新手引导完成')}
        darkMode={darkMode}
      />
      {/* 顶部导航栏 */}
      <nav className={`${darkMode ? 'bg-gray-800' : 'bg-white'} border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'} px-6 py-4`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-lg hover:bg-gray-700"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
                <Brain className="w-6 h-6 text-white" />
              </div>
                <div>
                  <h1 className="text-xl font-bold">ClawAI</h1>
                  <p className="text-sm opacity-70">基于规则引擎的渗透测试平台</p>
                </div>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className={`px-3 py-1 rounded-full ${ruleEngineMode ? 'bg-green-900/30 text-green-400' : 'bg-gray-700 text-gray-400'}`}>
                <span className="flex items-center text-sm">
                  <Brain className="w-4 h-4 mr-1" />
                  {ruleEngineMode ? '规则引擎模式' : '规则模式'}
                </span>
              </div>
              <button
                onClick={() => setRuleEngineMode(!ruleEngineMode)}
                className="p-2 rounded-lg hover:bg-gray-700"
                title="切换规则引擎模式"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>

            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg hover:bg-gray-700"
              title="切换主题"
            >
              {darkMode ? '🌙' : '☀️'}
            </button>

            <button className="p-2 rounded-lg hover:bg-gray-700">
              <Bell className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-white" />
              </div>
              <span className="text-sm">管理员</span>
            </div>
          </div>
        </div>
      </nav>

      <div className="flex">
        {/* 侧边栏 */}
        {sidebarOpen && (
          <aside className={`${darkMode ? 'bg-gray-800' : 'bg-white'} w-64 border-r ${darkMode ? 'border-gray-700' : 'border-gray-200'} min-h-[calc(100vh-4rem)]`}>
            <div className="p-4">
              <nav className="space-y-1">
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg ${activeTab === 'dashboard' ? 'bg-blue-500/20 text-blue-400' : 'hover:bg-gray-700'}`}
                >
                  <Home className="w-5 h-5" />
                  <span>仪表盘</span>
                </button>

                <button
                  onClick={() => setActiveTab('attack')}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg ${activeTab === 'attack' ? 'bg-blue-500/20 text-blue-400' : 'hover:bg-gray-700'}`}
                >
                  <Target className="w-5 h-5" />
                  <span>攻击模拟</span>
                </button>

                <button
                  onClick={() => setActiveTab('analysis')}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg ${activeTab === 'analysis' ? 'bg-blue-500/20 text-blue-400' : 'hover:bg-gray-700'}`}
                >
                  <Brain className="w-5 h-5" />
                  <span>规则引擎分析</span>
                </button>

                <button
                  onClick={() => setActiveTab('reports')}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg ${activeTab === 'reports' ? 'bg-blue-500/20 text-blue-400' : 'hover:bg-gray-700'}`}
                >
                  <BarChart3 className="w-5 h-5" />
                  <span>报告</span>
                </button>

                <button
                  onClick={() => setActiveTab('tools')}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg ${activeTab === 'tools' ? 'bg-blue-500/20 text-blue-400' : 'hover:bg-gray-700'}`}
                >
                  <Cpu className="w-5 h-5" />
                  <span>工具库</span>
                </button>

                <button
                  onClick={() => setActiveTab('settings')}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg ${activeTab === 'settings' ? 'bg-blue-500/20 text-blue-400' : 'hover:bg-gray-700'}`}
                >
                  <Settings className="w-5 h-5" />
                  <span>设置</span>
                </button>

                <button
                  onClick={() => setActiveTab('ux-optimizer')}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg ${activeTab === 'ux-optimizer' ? 'bg-blue-500/20 text-blue-400' : 'hover:bg-gray-700'}`}
                >
                  <Palette className="w-5 h-5" />
                  <span>UX优化</span>
                </button>
              </nav>

              <div className="mt-8 pt-6 border-t border-gray-700">
                <h3 className="px-3 text-sm font-medium text-gray-400 mb-2">快速目标</h3>
                <div className="space-y-1">
                  {['192.168.1.1', 'example.com', 'localhost', 'scanme.nmap.org'].map((quickTarget) => (
                    <button
                      key={quickTarget}
                      onClick={() => setTarget(quickTarget)}
                      className="w-full text-left px-3 py-2 text-sm rounded hover:bg-gray-700"
                    >
                      {quickTarget}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </aside>
        )}

        {/* 主内容区域 */}
        <main className="flex-1 p-6">
          {activeTab === 'dashboard' && (
            <>
              {/* 视图模式选择器 - 只在仪表盘显示 */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-2">
                  <div className="text-sm opacity-70">界面模式:</div>
                  <div className="flex space-x-1">
                    {['simple', 'standard', 'expert'].map((mode) => (
                      <button
                        key={mode}
                        onClick={() => setViewMode(mode)}
                        className={`px-4 py-2 rounded-lg text-sm ${viewMode === mode ? 'bg-blue-500 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}
                      >
                        {mode === 'simple' ? '简单模式' : mode === 'standard' ? '标准模式' : '专家模式'}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="text-sm opacity-70">
                  当前: {viewMode === 'simple' ? '适合初学者' : viewMode === 'standard' ? '适合普通用户' : '适合安全专家'}
                </div>
              </div>

              {/* 简单视图 */}
              {viewMode === 'simple' && (
                <SimpleView
                  target={target}
                  setTarget={setTarget}
                  onAttack={handleAttack}
                  loading={loading}
                  attackData={attackData}
                  error={error}
                  darkMode={darkMode}
                />
              )}

              {/* 标准视图 */}
              {viewMode === 'standard' && (
                <StandardView
                  target={target}
                  setTarget={setTarget}
                  onAttack={handleAttack}
                  loading={loading}
                  attackData={attackData}
                  error={error}
                  darkMode={darkMode}
                  ruleEngineMode={ruleEngineMode}
                  onToggleRuleEngine={() => setRuleEngineMode(!ruleEngineMode)}
                />
              )}

              {/* 专家视图（原有完整界面） */}
              {viewMode === 'expert' && (
                <div className="space-y-6">
              <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gradient-to-r from-blue-900/30 to-purple-900/30' : 'bg-gradient-to-r from-blue-50 to-purple-50'}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <h1 className="text-2xl font-bold mb-2">欢迎使用 ClawAI</h1>
                    <p className="opacity-80 mb-2">基于规则引擎的渗透测试演示平台</p>
                    <div className="text-xs text-yellow-400 bg-yellow-900/30 p-2 rounded-lg inline-block">
                      ⚠️ 技术说明：本项目使用规则引擎决策，非真正的AI/机器学习系统
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Shield className="w-6 h-6 text-green-500" />
                    <span className="text-sm">专业版 v1.0</span>
                  </div>
                </div>
              </div>

              {/* 目标输入卡片 */}
              <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                <div className="flex items-center mb-6">
                  <Target className="w-6 h-6 text-blue-400 mr-2" />
                  <h2 className="text-xl font-semibold">开始新的攻击</h2>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">目标地址</label>
                    <div className="flex space-x-3">
                      <input
                        type="text"
                        value={target}
                        onChange={(e) => setTarget(e.target.value)}
                        placeholder="输入 IP、域名或 URL"
                        className={`flex-1 px-4 py-3 rounded-lg ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'} border focus:outline-none focus:ring-2 focus:ring-blue-500`}
                      />
                      <button
                        onClick={handleAttack}
                        disabled={loading}
                        className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-lg hover:opacity-90 disabled:opacity-50 flex items-center"
                      >
                        {loading ? (
                          <>
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                            执行中...
                          </>
                        ) : (
                          <>
                            <Play className="w-5 h-5 mr-2" />
                            开始攻击
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

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                      <div className="flex items-center mb-2">
                        <Brain className="w-5 h-5 text-green-400 mr-2" />
                        <span className="text-sm font-medium">规则引擎模式</span>
                      </div>
                      <p className="text-sm opacity-70">使用规则引擎的攻击路径规划</p>
                    </div>

                    <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                      <div className="flex items-center mb-2">
                        <Zap className="w-5 h-5 text-yellow-400 mr-2" />
                        <span className="text-sm font-medium">实时执行</span>
                      </div>
                      <p className="text-sm opacity-70">调用真实安全工具进行扫描</p>
                    </div>

                    <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                      <div className="flex items-center mb-2">
                        <Shield className="w-5 h-5 text-red-400 mr-2" />
                        <span className="text-sm font-medium">安全合规</span>
                      </div>
                      <p className="text-sm opacity-70">仅用于授权测试和演示</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* AI思考动画 */}
              {showAIThinking && (
                <div className="rounded-2xl p-6 shadow-lg bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-500/20">
                  <AIThinkingAnimation 
                    message={thinkingType === 'analyze' ? "AI正在分析目标..." : 
                             thinkingType === 'decision' ? "AI正在决策..." :
                             thinkingType === 'plan' ? "AI正在规划攻击链..." : "AI正在学习..."}
                    thinkingType={thinkingType}
                    duration={3000}
                    showProgress={true}
                    onComplete={() => {
                      console.log('AI思考完成');
                      // 在思考完成后可以切换思考类型以展示更多过程
                      if (thinkingType === 'analyze') {
                        setThinkingType('decision');
                        setTimeout(() => setThinkingType('plan'), 3000);
                      }
                    }}
                    darkMode={darkMode}
                  />
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-200'}`}>
                      <div className="flex items-center mb-1">
                        <Brain className="w-4 h-4 mr-2 text-blue-400" />
                        <span className="font-medium">目标分析</span>
                      </div>
                      <p className="text-xs opacity-70">扫描目标漏洞和攻击面</p>
                    </div>
                    <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-200'}`}>
                      <div className="flex items-center mb-1">
                        <Activity className="w-4 h-4 mr-2 text-green-400" />
                        <span className="font-medium">规则引擎决策</span>
                      </div>
                      <p className="text-xs opacity-70">多模型协同决策最优攻击路径</p>
                    </div>
                    <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-200'}`}>
                      <div className="flex items-center mb-1">
                        <Network className="w-4 h-4 mr-2 text-purple-400" />
                        <span className="font-medium">攻击链规划</span>
                      </div>
                      <p className="text-xs opacity-70">设计完整攻击链和步骤</p>
                    </div>
                    <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-200'}`}>
                      <div className="flex items-center mb-1">
                        <Cpu className="w-4 h-4 mr-2 text-yellow-400" />
                        <span className="font-medium">AI学习优化</span>
                      </div>
                      <p className="text-xs opacity-70">从历史攻击中学习优化</p>
                    </div>
                  </div>
                </div>
              )}

              {/* 攻击结果显示区域 */}
              {attackData && (
                <div className="space-y-6">
                  {/* 攻击概览卡片 */}
                  <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center">
                        <Activity className="w-6 h-6 text-blue-400 mr-2" />
                        <h2 className="text-xl font-semibold">攻击执行结果</h2>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className={`px-3 py-1 rounded-full ${attackData.rule_engine_used ? 'bg-green-900/30 text-green-400' : 'bg-yellow-900/30 text-yellow-400'}`}>
                          <span className="flex items-center text-sm">
                            <Brain className="w-4 h-4 mr-1" />
                            {attackData.rule_engine_used ? `规则引擎模式 (${attackData.rule_engine_model})` : '规则引擎'}
                          </span>
                        </div>
                        <div className="px-3 py-1 bg-blue-900/30 text-blue-400 rounded-full text-sm">
                          执行时间: {attackData.execution_time}
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                        <div className="text-sm text-gray-400 mb-1">目标</div>
                        <div className="text-lg font-semibold">{attackData.target}</div>
                      </div>
                      <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                        <div className="text-sm text-gray-400 mb-1">执行模式</div>
                        <div className="text-lg font-semibold">{attackData.execution_mode === 'real' ? '真实执行' : '模拟演示'}</div>
                      </div>
                      <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                        <div className="text-sm text-gray-400 mb-1">攻击步骤</div>
                        <div className="text-lg font-semibold">{attackData.attack_chain?.length || 0} 步</div>
                      </div>
                      <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                        <div className="text-sm text-gray-400 mb-1">状态</div>
                        <div className="text-lg font-semibold text-green-500">完成</div>
                      </div>
                    </div>
                  </div>

                  {/* 攻击链可视化 - 添加3D可视化标签页 */}
                  <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center">
                        <GitBranch className="w-6 h-6 text-purple-400 mr-2" />
                        <h2 className="text-xl font-semibold">攻击链可视化</h2>
                      </div>
                      
                      {/* 可视化模式切换 */}
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setVisualizationMode('2d')}
                          className={`px-4 py-2 rounded-lg ${visualizationMode === '2d' ? 'bg-blue-500 text-white' : 'bg-gray-700 text-gray-300'}`}
                        >
                          2D视图
                        </button>
                        <button
                          onClick={() => setVisualizationMode('3d')}
                          className={`px-4 py-2 rounded-lg ${visualizationMode === '3d' ? 'bg-blue-500 text-white' : 'bg-gray-700 text-gray-300'}`}
                        >
                          3D视图
                        </button>
                      </div>
                    </div>

                    {visualizationMode === '2d' ? (
                      <>
                        <div className="relative">
                          {/* 连接线 */}
                          <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 -translate-y-1/2 z-0"></div>
                          
                          {/* 攻击步骤 */}
                          <div className="relative z-10 flex justify-between items-center">
                            {attackData.attack_chain.map((step) => (
                              <div key={step.step} className="flex flex-col items-center">
                                <div className={`w-16 h-16 rounded-full ${getToolColor(step.tool)} flex items-center justify-center mb-3 relative ring-2 ${getSeverityColor(step.severity)} ${step.highlight ? 'ring-4 ring-blue-400/50 shadow-lg shadow-blue-500/30' : ''}`}>
                                  <div className="text-white">{getToolIcon(step.tool)}</div>
                                  <div className="absolute -top-2 -right-2 w-8 h-8 bg-gray-900 rounded-full border-2 border-white flex items-center justify-center">
                                    <span className="text-xs font-bold text-white">{step.step}</span>
                                  </div>
                                </div>
                                <div className="text-center max-w-[120px]">
                                  <div className="font-semibold mb-1 text-sm">{step.title}</div>
                                  <div className="text-xs opacity-70">{step.tool}</div>
                                  <div className="text-xs text-green-400 mt-1">{step.duration}</div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* 详细步骤列表 */}
                        <div className="mt-8 space-y-3">
                          {attackData.attack_chain.map((step) => (
                            <div key={step.step} className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-100'} border-l-4 ${getSeverityColor(step.severity)}`}>
                              <div className="flex items-center justify-between">
                                <div className="flex items-center">
                                  <div className={`w-8 h-8 rounded-full ${getToolColor(step.tool)} flex items-center justify-center mr-3`}>
                                    {getToolIcon(step.tool)}
                                  </div>
                                  <div>
                                    <div className="font-medium">步骤 {step.step}: {step.title}</div>
                                    <div className="text-sm opacity-70">{step.description}</div>
                                  </div>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(step.severity)}`}>
                                    {step.severity}
                                  </span>
                                  {step.success ? (
                                    <CheckCircle className="w-5 h-5 text-green-500" />
                                  ) : (
                                    <AlertCircle className="w-5 h-5 text-red-500" />
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </>
                    ) : (
                      <div className="mt-4">
                        <AttackChain3D 
                          attackChain={attackData.attack_chain}
                          darkMode={darkMode}
                          onNodeClick={(step, index) => {
                            console.log('点击了3D节点:', step, index);
                            // 可以在这里添加点击节点的处理逻辑
                          }}
                        />
                        <div className="mt-4 p-4 bg-blue-900/20 rounded-lg">
                          <p className="text-sm">
                            <strong>Day 4 成果:</strong> 3D攻击链可视化已实现。使用鼠标拖拽旋转视角，滚轮缩放，点击节点查看详情。
                          </p>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* 规则引擎决策面板 */}
                  {attackData.rule_engine_decision && (
                    <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                      <div className="flex items-center mb-6">
                        <Brain className="w-6 h-6 text-green-400 mr-2" />
                        <h2 className="text-xl font-semibold">规则引擎决策分析</h2>
                      </div>

                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* 决策概览 */}
                        <div className="space-y-4">
                          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                              <div className="flex items-center justify-between mb-4">
                                <span className="text-gray-400">规则引擎决策概览</span>
                                <div className="px-2 py-1 bg-green-900/30 rounded text-xs text-green-400">
                                  最优决策
                                </div>
                              </div>
                            
                            <div className="space-y-3">
                              <div className="flex items-center justify-between">
                                <span className="text-gray-400">路径类型</span>
                                <span className="font-medium">{attackData.rule_engine_decision.selected_path_type}</span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className="text-gray-400">规则引擎评分</span>
                                <div className="flex items-center">
                                  <span className="text-2xl font-bold mr-2">
                                    {attackData.rule_engine_decision.selected_score}
                                  </span>
                                  <span className="text-gray-400">/10</span>
                                </div>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className="text-gray-400">置信度</span>
                                <div className="flex items-center">
                                  <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden mr-2">
                                    <div 
                                      className="h-full bg-gradient-to-r from-green-500 to-blue-500"
                                      style={{ width: `${attackData.rule_engine_decision.confidence * 100}%` }}
                                    ></div>
                                  </div>
                                  <span className="font-medium text-green-400">
                                    {Math.round(attackData.rule_engine_decision.confidence * 100)}%
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                            <h3 className="font-medium mb-3">选择原因</h3>
                            <ul className="space-y-2">
                              {attackData.rule_engine_decision.selection_reasons.map((reason, index) => (
                                <li key={index} className="flex items-start">
                                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 mr-2" />
                                  <span className="text-sm">{reason}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>

                        {/* 路径对比 */}
                        <div className="space-y-4">
                          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                            <h3 className="font-medium mb-3">路径对比</h3>
                            <div className="space-y-2">
                              {attackData.rule_engine_decision.path_comparison.map((path, index) => (
                                <div key={index} className="flex items-center justify-between p-2 bg-gray-800/30 rounded">
                                  <div className="flex items-center">
                                    <div className="w-3 h-3 rounded-full bg-gray-500 mr-2"></div>
                                    <span className="text-sm">{path.path_type}</span>
                                  </div>
                                  <div className="flex items-center space-x-4">
                                    <span className="text-sm text-gray-400">{path.score}分</span>
                                    <span className="text-sm text-red-400">-{path.score_difference}分</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                          
                          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                            <h3 className="font-medium mb-3">决策因素</h3>
                            <div className="space-y-2">
                              {Object.entries(attackData.rule_engine_decision.decision_factors || {}).map(([key, value]) => (
                                <div key={key} className="flex items-center justify-between">
                                  <span className="text-sm capitalize">{key.replace('_', ' ')}</span>
                                  <div className="flex items-center">
                                    <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden mr-2">
                                      <div 
                                        className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                                        style={{ width: `${value * 10}%` }}
                                      ></div>
                                    </div>
                                    <span className="text-sm font-medium">{value}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 进化故事线和评分曲线 */}
                  {attackData.evolution_result && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* 进化故事线 */}
                      <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                        <div className="flex items-center mb-6">
                          <TrendingUp className="w-6 h-6 text-pink-400 mr-2" />
                          <h2 className="text-xl font-semibold">进化故事线</h2>
                        </div>
                        
                        <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                          {attackData.evolution_result.evolution_story.map((item, index) => (
                            <div key={index} className="p-4 rounded-xl bg-gray-700/50 border border-gray-600">
                              <div className="flex items-start">
                                <div className="mr-3 mt-1">
                                  {item.status === 'success' ? (
                                    <CheckCircle className="w-5 h-5 text-green-500" />
                                  ) : item.status === 'conflict' ? (
                                    <AlertTriangle className="w-5 h-5 text-red-500" />
                                  ) : (
                                    <Clock className="w-5 h-5 text-blue-500" />
                                  )}
                                </div>
                                <div className="flex-1">
                                  <div className="flex items-center justify-between mb-2">
                                    <h3 className="font-medium">{item.title}</h3>
                                    <span className="text-xs text-gray-400">{item.timestamp}</span>
                                  </div>
                                  <p className="text-sm opacity-70 mb-2">{item.description}</p>
                                  <div className="space-y-1">
                                    {item.details.map((detail, detailIndex) => (
                                      <div key={detailIndex} className="text-xs text-gray-400">
                                        {detail}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* 目标分析 */}
                      <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                        <div className="flex items-center mb-6">
                          <BarChart3 className="w-6 h-6 text-blue-400 mr-2" />
                          <h2 className="text-xl font-semibold">目标分析</h2>
                        </div>
                        
                        {attackData.target_analysis && (
                          <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                              <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                                <div className="text-sm text-gray-400 mb-1">攻击面评分</div>
                                <div className="text-2xl font-bold">{attackData.target_analysis.attack_surface}/10</div>
                              </div>
                              <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                                <div className="text-sm text-gray-400 mb-1">开放端口</div>
                                <div className="text-2xl font-bold">{attackData.target_analysis.open_ports}</div>
                              </div>
                              <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                                <div className="text-sm text-gray-400 mb-1">漏洞数量</div>
                                <div className="text-2xl font-bold">{attackData.target_analysis.vulnerabilities}</div>
                              </div>
                              <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                                <div className="text-sm text-gray-400 mb-1">CMS类型</div>
                                <div className="text-lg font-semibold">{attackData.target_analysis.cms_type || '无'}</div>
                              </div>
                            </div>
                            
                            {attackData.target_analysis.has_cms && (
                              <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                                <div className="text-sm text-gray-400 mb-1">CMS详情</div>
                                <div className="text-lg font-semibold">{attackData.target_analysis.cms_type} {attackData.target_analysis.cms_version}</div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* AI多模型协同决策系统 */}
                  <div className="space-y-6">
                    <AIMultiModelDecision 
                      decisionData={attackData.multi_model_decision}
                      explanationData={attackData.ai_explanation}
                      learningData={attackData.ai_learning}
                      darkMode={darkMode}
                      onRefresh={() => {
                        console.log('刷新AI多模型协同决策数据');
                        // 这里可以添加实际的数据刷新逻辑
                      }}
                      onExport={() => {
                        console.log('导出AI多模型协同决策数据');
                        // 这里可以添加数据导出逻辑
                      }}
                    />
                    
                    {/* 说明卡片 */}
                    <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                      <div className="flex items-center mb-4">
                        <Brain className="w-6 h-6 text-blue-400 mr-2" />
                        <h2 className="text-xl font-semibold">AI多模型协同决策系统说明</h2>
                      </div>
                      <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'} mb-4`}>
                        <h3 className="font-medium mb-2">第4天：前端AI展示优化</h3>
                        <p className="text-sm opacity-70 mb-2">
                          此组件展示了第3天实现的多模型协同决策系统的前端可视化界面，包括：
                        </p>
                        <ul className="space-y-1 text-sm">
                          <li className="flex items-center">
                            <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                            多模型投票机制：展示不同模型的投票分布和决策结果
                          </li>
                          <li className="flex items-center">
                            <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                            置信度加权决策：根据模型置信度进行加权决策
                          </li>
                          <li className="flex items-center">
                            <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                            分歧解决策略：处理模型间分歧的多种解决策略
                          </li>
                          <li className="flex items-center">
                            <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                            AI解释系统：提供决策原因、风险评估、替代方案等解释
                          </li>
                          <li className="flex items-center">
                            <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                            AI学习能力：展示历史决策学习、成功率反馈和策略优化
                          </li>
                        </ul>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                          <div className="flex items-center mb-1">
                            <Users className="w-4 h-4 mr-2 text-blue-500" />
                            <span className="font-medium">协同决策</span>
                          </div>
                          <p className="text-xs opacity-70">展示多模型投票、置信度分布和最终决策结果</p>
                        </div>
                        <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                          <div className="flex items-center mb-1">
                            <HelpCircle className="w-4 h-4 mr-2 text-green-500" />
                            <span className="font-medium">AI解释</span>
                          </div>
                          <p className="text-xs opacity-70">提供5种解释类型，增强决策透明度</p>
                        </div>
                        <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                          <div className="flex items-center mb-1">
                            <TrendingUp className="w-4 h-4 mr-2 text-purple-500" />
                            <span className="font-medium">AI学习</span>
                          </div>
                          <p className="text-xs opacity-70">展示模型性能对比和学习历史</p>
                        </div>
                        <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                          <div className="flex items-center mb-1">
                            <BarChart3 className="w-4 h-4 mr-2 text-yellow-500" />
                            <span className="font-medium">实时更新</span>
                          </div>
                          <p className="text-xs opacity-70">支持数据刷新和导出功能</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 其他标签页内容 - 现在显示实际功能 */}
          {activeTab === 'attack' && (
            <div className="space-y-6">
              <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                <h2 className="text-xl font-semibold mb-4">攻击模拟</h2>
                <p className="opacity-70 mb-4">此功能已集成到仪表盘的主攻击界面中。</p>
                <div className="p-4 bg-blue-900/20 rounded-lg">
                  <p className="text-sm">请使用仪表盘中的"开始新的攻击"功能来执行攻击模拟。</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'analysis' && (
            <div className="space-y-6">
              <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                <h2 className="text-xl font-semibold mb-4">规则引擎分析</h2>
                <p className="opacity-70 mb-4">规则引擎分析功能已集成到攻击结果展示中。</p>
                <div className="p-4 bg-green-900/20 rounded-lg">
                  <p className="text-sm">执行攻击后，可以在仪表盘查看完整的规则引擎决策分析、进化故事线和目标分析。</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'reports' && (
            <div className="space-y-6">
              <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                <h2 className="text-xl font-semibold mb-4">报告</h2>
                <p className="opacity-70 mb-4">报告功能正在开发中，将包含以下特性：</p>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    PDF格式导出
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    详细漏洞报告
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    自动化建议总结
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    修复建议
                  </li>
                </ul>
              </div>
            </div>
          )}

          {activeTab === 'tools' && (
            <div className="space-y-6">
              {/* Skills技能库组件 */}
              <SkillLibrary darkMode={darkMode} />
              
              {/* 传统工具库 */}
              <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                <div className="flex items-center mb-6">
                  <Cpu className="w-6 h-6 text-blue-400 mr-2" />
                  <h2 className="text-xl font-semibold">传统工具库</h2>
                </div>
                <p className="opacity-70 mb-4">ClawAI集成的安全工具：</p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {['nmap', 'whatweb', 'nuclei', 'sqlmap', 'dirsearch', 'wafw00f'].map((tool) => (
                    <div key={tool} className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                      <div className="font-medium mb-1">{tool}</div>
                      <div className="text-xs opacity-70">安全扫描工具</div>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Day 5完成说明 */}
              <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                <div className="flex items-center mb-4">
                  <CheckCircle className="w-6 h-6 text-green-500 mr-2" />
                  <h2 className="text-xl font-semibold">Day 5: Skills库扩展完成</h2>
                </div>
                <div className={`p-4 rounded-lg ${darkMode ? 'bg-green-900/20' : 'bg-green-50'} mb-4`}>
                  <h3 className="font-medium mb-2">✅ 任务完成总结</h3>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center">
                      <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                      已扩展至31个渗透技巧技能（要求：≥30个）
                    </li>
                    <li className="flex items-center">
                      <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                      包含5个侦察类技能（要求：5个）
                    </li>
                    <li className="flex items-center">
                      <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                      包含15个漏洞利用类技能（要求：15个）
                    </li>
                    <li className="flex items-center">
                      <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                      包含11个后渗透类技能（要求：10个）
                    </li>
                    <li className="flex items-center">
                      <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                      每个技能包含：名称、描述、类别、难度、工具、前置条件、输出、成功率等
                    </li>
                    <li className="flex items-center">
                      <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                      前端组件支持搜索、过滤、详情查看、导出功能
                    </li>
                  </ul>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className={`p-4 rounded-lg ${darkMode ? 'bg-blue-900/20' : 'bg-blue-50'}`}>
                    <div className="flex items-center mb-2">
                      <Eye className="w-5 h-5 text-blue-400 mr-2" />
                      <span className="font-medium">侦察类技能</span>
                    </div>
                    <div className="text-2xl font-bold">5个</div>
                    <div className="text-sm opacity-70">子域名枚举、端口扫描、指纹识别等</div>
                  </div>
                  <div className={`p-4 rounded-lg ${darkMode ? 'bg-red-900/20' : 'bg-red-50'}`}>
                    <div className="flex items-center mb-2">
                      <Zap className="w-5 h-5 text-red-400 mr-2" />
                      <span className="font-medium">漏洞利用类</span>
                    </div>
                    <div className="text-2xl font-bold">15个</div>
                    <div className="text-sm opacity-70">SQL注入、XSS、RCE、文件上传等</div>
                  </div>
                  <div className={`p-4 rounded-lg ${darkMode ? 'bg-purple-900/20' : 'bg-purple-50'}`}>
                    <div className="flex items-center mb-2">
                      <Lock className="w-5 h-5 text-purple-400 mr-2" />
                      <span className="font-medium">后渗透类</span>
                    </div>
                    <div className="text-2xl font-bold">11个</div>
                    <div className="text-sm opacity-70">权限提升、横向移动、持久化等</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6">
              <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                <h2 className="text-xl font-semibold mb-4">设置</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">API配置</label>
                    <input
                      type="text"
                      placeholder="DeepSeek API密钥"
                      className={`w-full px-4 py-2 rounded-lg ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'} border`}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">扫描配置</label>
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input type="checkbox" className="mr-2" />
                        <span className="text-sm">启用深度扫描</span>
                      </label>
                      <label className="flex items-center">
                        <input type="checkbox" className="mr-2" defaultChecked />
                        <span className="text-sm">启用规则引擎决策</span>
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'ux-optimizer' && (
            <div className="space-y-6">
              <UXOptimizer darkMode={darkMode} />
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default ClawAIDashboard;
