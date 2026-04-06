import React, { useState, useEffect } from 'react';
import { 
  Zap, Cpu, Brain, Target, Clock, TrendingUp, CheckCircle, 
  AlertCircle, Settings, RefreshCw, Download, Eye, EyeOff,
  Sparkles, MessageSquare, ThumbsUp, ThumbsDown, Star,
  BarChart, Shield, Lock, Unlock, Settings as SettingsIcon,
  Bell, User, Home, FileText, Search, Filter, Grid, List
} from 'lucide-react';

/**
 * 用户体验优化组件
 * 第五阶段：用户体验提升
 * 提供实时反馈、个性化配置、性能指标等功能
 */
const UXOptimizer = ({ 
  darkMode = true,
  onSettingsChange,
  initialConfig = {}
}) => {
  const [config, setConfig] = useState({
    // 视觉设置
    theme: 'dark',
    fontSize: 'medium',
    density: 'comfortable',
    
    // 功能设置
    realTimeFeedback: true,
    performanceMetrics: true,
    aiSuggestions: true,
    autoRefresh: false,
    notifications: true,
    
    // 显示设置
    showToolTips: true,
    showProgressBars: true,
    showAnimations: true,
    compactMode: false,
    
    // 个性化设置
    preferredModel: 'rule_engine',
    riskTolerance: 'medium',
    scanningSpeed: 'balanced',
    
    ...initialConfig
  });
  
  const [performanceMetrics, setPerformanceMetrics] = useState({
    responseTime: 150,
    successRate: 92.5,
    userSatisfaction: 4.3,
    featureUsage: {
      aiThinking: 85,
      multiModel: 78,
      realExecution: 65,
      reporting: 72
    },
    recentInteractions: [
      { time: '2分钟前', action: '执行攻击', duration: '3.2s', success: true },
      { time: '5分钟前', action: '查看报告', duration: '1.8s', success: true },
      { time: '10分钟前', action: '配置设置', duration: '4.1s', success: true },
      { time: '15分钟前', action: '导出结果', duration: '2.3s', success: true }
    ]
  });
  
  const [userFeedback, setUserFeedback] = useState({
    positive: 124,
    negative: 8,
    suggestions: [
      '希望增加更多可视化图表',
      '攻击步骤可以更详细',
      '规则引擎决策解释更清晰',
      '导出功能可以更强大'
    ]
  });
  
  const [aiSuggestions, setAiSuggestions] = useState([
    {
      id: 1,
      type: 'optimization',
      title: '优化攻击路径',
      description: '检测到相似目标的成功攻击模式，建议尝试新的路径组合',
      priority: 'high',
      action: '查看详情'
    },
    {
      id: 2,
      type: 'learning',
      title: '模型学习建议',
      description: '规则引擎发现新的漏洞模式，建议更新模型规则',
      priority: 'medium',
      action: '学习更新'
    },
    {
      id: 3,
      type: 'performance',
      title: '性能优化',
      description: '最近几次扫描响应时间较长，建议调整扫描参数',
      priority: 'low',
      action: '优化设置'
    }
  ]);
  
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // 处理配置更改
  const handleConfigChange = (key, value) => {
    const newConfig = { ...config, [key]: value };
    setConfig(newConfig);
    
    // 通知父组件
    if (onSettingsChange) {
      onSettingsChange(newConfig);
    }
    
    // 保存到localStorage
    localStorage.setItem('clawai_ux_config', JSON.stringify(newConfig));
  };
  
  // 加载配置
  useEffect(() => {
    const savedConfig = localStorage.getItem('clawai_ux_config');
    if (savedConfig) {
      try {
        setConfig(JSON.parse(savedConfig));
      } catch (e) {
        console.error('配置加载失败:', e);
      }
    }
  }, []);
  
  // 模拟性能指标更新
  useEffect(() => {
    const interval = setInterval(() => {
      setPerformanceMetrics(prev => ({
        ...prev,
        responseTime: Math.max(50, Math.min(prev.responseTime + (Math.random() - 0.5) * 10, 300)),
        successRate: Math.max(85, Math.min(prev.successRate + (Math.random() - 0.2), 100)),
        userSatisfaction: Math.max(3.5, Math.min(prev.userSatisfaction + (Math.random() - 0.1), 5)),
        featureUsage: {
          aiThinking: Math.max(70, Math.min(prev.featureUsage.aiThinking + (Math.random() - 0.5) * 5, 95)),
          multiModel: Math.max(65, Math.min(prev.featureUsage.multiModel + (Math.random() - 0.5) * 5, 90)),
          realExecution: Math.max(55, Math.min(prev.featureUsage.realExecution + (Math.random() - 0.5) * 5, 80)),
          reporting: Math.max(65, Math.min(prev.featureUsage.reporting + (Math.random() - 0.5) * 5, 85))
        }
      }));
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);
  
  const renderDashboard = () => (
    <div className="space-y-6">
      {/* 欢迎卡片 */}
      <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gradient-to-r from-blue-900/30 to-purple-900/30' : 'bg-gradient-to-r from-blue-50 to-purple-50'}`}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold mb-2">🎯 用户体验优化中心</h2>
            <p className="opacity-80">第五阶段：用户体验提升 - 提供更智能、更个性化的使用体验</p>
          </div>
          <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
        </div>
      </div>
      
      {/* 性能指标 */}
      <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
        <div className="flex items-center mb-6">
          <BarChart className="w-6 h-6 text-green-400 mr-2" />
          <h3 className="text-lg font-semibold">性能指标</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
            <div className="flex items-center mb-2">
              <Clock className="w-5 h-5 text-blue-400 mr-2" />
              <span className="text-sm text-gray-400">响应时间</span>
            </div>
            <div className="text-2xl font-bold">{performanceMetrics.responseTime.toFixed(1)}ms</div>
            <div className="text-xs text-green-400">⚡ 快速</div>
          </div>
          
          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
            <div className="flex items-center mb-2">
              <CheckCircle className="w-5 h-5 text-green-400 mr-2" />
              <span className="text-sm text-gray-400">成功率</span>
            </div>
            <div className="text-2xl font-bold">{performanceMetrics.successRate.toFixed(1)}%</div>
            <div className="text-xs text-green-400">📈 优秀</div>
          </div>
          
          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
            <div className="flex items-center mb-2">
              <Star className="w-5 h-5 text-yellow-400 mr-2" />
              <span className="text-sm text-gray-400">用户满意度</span>
            </div>
            <div className="text-2xl font-bold">{performanceMetrics.userSatisfaction.toFixed(1)}/5</div>
            <div className="text-xs text-green-400">👍 很高</div>
          </div>
          
          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
            <div className="flex items-center mb-2">
              <TrendingUp className="w-5 h-5 text-purple-400 mr-2" />
              <span className="text-sm text-gray-400">功能使用率</span>
            </div>
            <div className="text-2xl font-bold">85%</div>
            <div className="text-xs text-green-400">🚀 活跃</div>
          </div>
        </div>
        
        {/* 功能使用率图表 */}
        <div className="mt-6">
          <h4 className="text-sm font-medium mb-3">功能使用率</h4>
          <div className="space-y-2">
            {Object.entries(performanceMetrics.featureUsage).map(([feature, usage]) => (
              <div key={feature} className="flex items-center">
                <span className="w-32 text-sm">{getFeatureName(feature)}</span>
                <div className="flex-1 h-4 bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-blue-500 to-purple-600"
                    style={{ width: `${usage}%` }}
                  ></div>
                </div>
                <span className="w-12 text-right text-sm ml-2">{usage}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* AI建议 */}
      <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <Brain className="w-6 h-6 text-blue-400 mr-2" />
            <h3 className="text-lg font-semibold">AI个性化建议</h3>
          </div>
          <button className="px-3 py-1 bg-gray-700 rounded-lg text-sm hover:bg-gray-600">
            查看全部
          </button>
        </div>
        
        <div className="space-y-4">
          {aiSuggestions.map(suggestion => (
            <div key={suggestion.id} className={`p-4 rounded-lg border-l-4 ${getPriorityColor(suggestion.priority)} ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <div className={`p-2 rounded-lg ${getSuggestionColor(suggestion.type)} mr-3`}>
                    {getSuggestionIcon(suggestion.type)}
                  </div>
                  <div>
                    <h4 className="font-medium">{suggestion.title}</h4>
                    <span className={`text-xs px-2 py-1 rounded ${getPriorityBadgeColor(suggestion.priority)}`}>
                      {getPriorityText(suggestion.priority)}
                    </span>
                  </div>
                </div>
                <button className="px-3 py-1 bg-blue-600 rounded-lg text-sm hover:bg-blue-700">
                  {suggestion.action}
                </button>
              </div>
              <p className="text-sm opacity-70">{suggestion.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
  
  const renderSettings = () => (
    <div className="space-y-6">
      <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
        <div className="flex items-center mb-6">
          <SettingsIcon className="w-6 h-6 text-blue-400 mr-2" />
          <h3 className="text-lg font-semibold">个性化设置</h3>
        </div>
        
        <div className="space-y-6">
          {/* 视觉设置 */}
          <div>
            <h4 className="font-medium mb-4">视觉设置</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                <div className="font-medium mb-2">主题</div>
                <div className="space-y-2">
                  {['dark', 'light', 'auto'].map(theme => (
                    <button
                      key={theme}
                      onClick={() => handleConfigChange('theme', theme)}
                      className={`w-full px-3 py-2 rounded text-sm ${config.theme === theme ? 'bg-blue-600' : 'hover:bg-gray-600'}`}
                    >
                      {getThemeName(theme)}
                    </button>
                  ))}
                </div>
              </div>
              
              <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                <div className="font-medium mb-2">字体大小</div>
                <div className="space-y-2">
                  {['small', 'medium', 'large'].map(size => (
                    <button
                      key={size}
                      onClick={() => handleConfigChange('fontSize', size)}
                      className={`w-full px-3 py-2 rounded text-sm ${config.fontSize === size ? 'bg-blue-600' : 'hover:bg-gray-600'}`}
                    >
                      {getFontSizeName(size)}
                    </button>
                  ))}
                </div>
              </div>
              
              <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                <div className="font-medium mb-2">布局密度</div>
                <div className="space-y-2">
                  {['compact', 'comfortable', 'spacious'].map(density => (
                    <button
                      key={density}
                      onClick={() => handleConfigChange('density', density)}
                      className={`w-full px-3 py-2 rounded text-sm ${config.density === density ? 'bg-blue-600' : 'hover:bg-gray-600'}`}
                    >
                      {getDensityName(density)}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
          
          {/* 功能设置 */}
          <div>
            <h4 className="font-medium mb-4">功能设置</h4>
            <div className="space-y-3">
              {[
                { key: 'realTimeFeedback', label: '实时反馈', icon: <Zap className="w-4 h-4" /> },
                { key: 'performanceMetrics', label: '性能指标', icon: <BarChart className="w-4 h-4" /> },
                { key: 'aiSuggestions', label: 'AI建议', icon: <Brain className="w-4 h-4" /> },
                { key: 'autoRefresh', label: '自动刷新', icon: <RefreshCw className="w-4 h-4" /> },
                { key: 'notifications', label: '通知', icon: <Bell className="w-4 h-4" /> }
              ].map(item => (
                <div key={item.key} className="flex items-center justify-between p-3 rounded-lg bg-gray-700/30">
                  <div className="flex items-center">
                    <div className="mr-3 text-blue-400">{item.icon}</div>
                    <span>{item.label}</span>
                  </div>
                  <button
                    onClick={() => handleConfigChange(item.key, !config[item.key])}
                    className={`w-12 h-6 rounded-full transition-colors ${config[item.key] ? 'bg-green-500' : 'bg-gray-600'}`}
                  >
                    <div className={`w-4 h-4 bg-white rounded-full transform transition-transform ${config[item.key] ? 'translate-x-7' : 'translate-x-1'}`} />
                  </button>
                </div>
              ))}
            </div>
          </div>
          
          {/* 显示设置 */}
          <div>
            <h4 className="font-medium mb-4">显示设置</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { key: 'showToolTips', label: '显示提示', icon: <MessageSquare className="w-4 h-4" /> },
                { key: 'showProgressBars', label: '显示进度条', icon: <TrendingUp className="w-4 h-4" /> },
                { key: 'showAnimations', label: '显示动画', icon: <Sparkles className="w-4 h-4" /> },
                { key: 'compactMode', label: '紧凑模式', icon: <Grid className="w-4 h-4" /> }
              ].map(item => (
                <div key={item.key} className="flex items-center justify-between p-3 rounded-lg bg-gray-700/30">
                  <div className="flex items-center">
                    <div className="mr-3 text-purple-400">{item.icon}</div>
                    <span className="text-sm">{item.label}</span>
                  </div>
                  <button
                    onClick={() => handleConfigChange(item.key, !config[item.key])}
                    className={`w-10 h-5 rounded-full transition-colors ${config[item.key] ? 'bg-blue-500' : 'bg-gray-600'}`}
                  >
                    <div className={`w-3 h-3 bg-white rounded-full transform transition-transform ${config[item.key] ? 'translate-x-6' : 'translate-x-1'}`} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      
      {/* 导出设置 */}
      <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
        <div className="flex items-center mb-6">
          <Download className="w-6 h-6 text-green-400 mr-2" />
          <h3 className="text-lg font-semibold">数据管理</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="p-4 rounded-lg bg-gray-700/30 hover:bg-gray-600 transition-colors">
            <div className="flex items-center mb-2">
              <Download className="w-5 h-5 mr-2" />
              <span className="font-medium">导出配置</span>
            </div>
            <p className="text-sm opacity-70">导出当前个性化设置</p>
          </button>
          
          <button className="p-4 rounded-lg bg-gray-700/30 hover:bg-gray-600 transition-colors">
            <div className="flex items-center mb-2">
              <FileText className="w-5 h-5 mr-2" />
              <span className="font-medium">导出使用数据</span>
            </div>
            <p className="text-sm opacity-70">导出性能指标和反馈数据</p>
          </button>
          
          <button className="p-4 rounded-lg bg-gray-700/30 hover:bg-gray-600 transition-colors">
            <div className="flex items-center mb-2">
              <RefreshCw className="w-5 h-5 mr-2" />
              <span className="font-medium">重置设置</span>
            </div>
            <p className="text-sm opacity-70">恢复到默认设置</p>
          </button>
        </div>
      </div>
    </div>
  );
  
  const renderFeedback = () => (
    <div className="space-y-6">
      <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
        <div className="flex items-center mb-6">
          <MessageSquare className="w-6 h-6 text-yellow-400 mr-2" />
          <h3 className="text-lg font-semibold">用户反馈</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
            <div className="flex items-center mb-2">
              <ThumbsUp className="w-5 h-5 text-green-400 mr-2" />
              <span className="text-gray-400">正面反馈</span>
            </div>
            <div className="text-2xl font-bold">{userFeedback.positive}</div>
          </div>
          
          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
            <div className="flex items-center mb-2">
              <ThumbsDown className="w-5 h-5 text-red-400 mr-2" />
              <span className="text-gray-400">负面反馈</span>
            </div>
            <div className="text-2xl font-bold">{userFeedback.negative}</div>
          </div>
          
          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
            <div className="flex items-center mb-2">
              <Star className="w-5 h-5 text-yellow-400 mr-2" />
              <span className="text-gray-400">满意度</span>
            </div>
            <div className="text-2xl font-bold">{((userFeedback.positive / (userFeedback.positive + userFeedback.negative)) * 100).toFixed(1)}%</div>
          </div>
        </div>
        
        <div>
          <h4 className="font-medium mb-4">用户建议</h4>
          <div className="space-y-3">
            {userFeedback.suggestions.map((suggestion, index) => (
              <div key={index} className="flex items-start p-3 rounded-lg bg-gray-700/30">
                <div className="p-1 bg-blue-500/20 rounded mr-3">
                  <MessageSquare className="w-4 h-4 text-blue-400" />
                </div>
                <span className="text-sm">{suggestion}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* 提交反馈 */}
      <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
        <h4 className="font-medium mb-4">提交您的反馈</h4>
        <div className="space-y-4">
          <div>
            <label className="block text-sm mb-2">反馈类型</label>
            <select className={`w-full px-4 py-2 rounded-lg ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'} border`}>
              <option>建议</option>
              <option>问题报告</option>
              <option>功能请求</option>
              <option>其他</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm mb-2">反馈内容</label>
            <textarea 
              rows="4"
              className={`w-full px-4 py-2 rounded-lg ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'} border`}
              placeholder="请详细描述您的反馈..."
            />
          </div>
          
          <button className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:opacity-90">
            提交反馈
          </button>
        </div>
      </div>
    </div>
  );
  
  // 辅助函数
  const getFeatureName = (feature) => {
    const names = {
      aiThinking: 'AI思考动画',
      multiModel: '多模型决策',
      realExecution: '真实执行',
      reporting: '报告功能'
    };
    return names[feature] || feature;
  };
  
  const getPriorityColor = (priority) => {
    const colors = {
      high: 'border-red-500',
      medium: 'border-yellow-500',
      low: 'border-green-500'
    };
    return colors[priority] || 'border-gray-500';
  };
  
  const getPriorityBadgeColor = (priority) => {
    const colors = {
      high: 'bg-red-500/20 text-red-400',
      medium: 'bg-yellow-500/20 text-yellow-400',
      low: 'bg-green-500/20 text-green-400'
    };
    return colors[priority] || 'bg-gray-500/20 text-gray-400';
  };
  
  const getPriorityText = (priority) => {
    const texts = {
      high: '高优先级',
      medium: '中优先级',
      low: '低优先级'
    };
    return texts[priority] || priority;
  };
  
  const getSuggestionColor = (type) => {
    const colors = {
      optimization: 'bg-blue-500/20',
      learning: 'bg-purple-500/20',
      performance: 'bg-green-500/20'
    };
    return colors[type] || 'bg-gray-500/20';
  };
  
  const getSuggestionIcon = (type) => {
    const icons = {
      optimization: <Zap className="w-4 h-4 text-blue-400" />,
      learning: <Brain className="w-4 h-4 text-purple-400" />,
      performance: <TrendingUp className="w-4 h-4 text-green-400" />
    };
    return icons[type] || <Sparkles className="w-4 h-4" />;
  };
  
  const getThemeName = (theme) => {
    const names = {
      dark: '深色主题',
      light: '浅色主题',
      auto: '自动切换'
    };
    return names[theme] || theme;
  };
  
  const getFontSizeName = (size) => {
    const names = {
      small: '小号字体',
      medium: '中号字体',
      large: '大号字体'
    };
    return names[size] || size;
  };
  
  const getDensityName = (density) => {
    const names = {
      compact: '紧凑布局',
      comfortable: '舒适布局',
      spacious: '宽敞布局'
    };
    return names[density] || density;
  };
  
  return (
    <div className={`${darkMode ? 'text-white' : 'text-gray-900'}`}>
      {/* 标签页导航 */}
      <div className="flex border-b border-gray-700 mb-6">
        {[
          { id: 'dashboard', label: '概览', icon: <Home className="w-4 h-4" /> },
          { id: 'settings', label: '设置', icon: <Settings className="w-4 h-4" /> },
          { id: 'feedback', label: '反馈', icon: <MessageSquare className="w-4 h-4" /> }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center px-4 py-3 border-b-2 transition-colors ${
              activeTab === tab.id 
                ? 'border-blue-500 text-blue-400' 
                : 'border-transparent hover:bg-gray-700'
            }`}
          >
            <span className="mr-2">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>
      
      {/* 内容区域 */}
      {activeTab === 'dashboard' && renderDashboard()}
      {activeTab === 'settings' && renderSettings()}
      {activeTab === 'feedback' && renderFeedback()}
      
      {/* 快速操作栏 */}
      <div className="mt-6 pt-6 border-t border-gray-700">
        <div className="flex items-center justify-between">
          <div className="text-sm opacity-70">
            当前配置: {getThemeName(config.theme)} • {getFontSizeName(config.fontSize)} • {getDensityName(config.density)}
          </div>
          <div className="flex space-x-2">
            <button className="px-3 py-1 bg-gray-700 rounded-lg text-sm hover:bg-gray-600">
              保存配置
            </button>
            <button className="px-3 py-1 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg text-sm hover:opacity-90">
              应用更改
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UXOptimizer;