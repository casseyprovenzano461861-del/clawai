import React, { useState, useEffect } from 'react';
import {
  Brain, Users, BarChart3, TrendingUp, Target, AlertCircle,
  CheckCircle, XCircle, Zap, Shield, Clock, GitBranch,
  Activity, PieChart, Network, Lock, Cpu,
  ArrowUpRight, ArrowDownRight, Star, Filter,
  ChevronRight, ChevronDown, HelpCircle,
  RefreshCw, Download, Upload, Settings
} from 'lucide-react';

/**
 * AI多模型协同决策可视化组件
 * 展示多模型投票、置信度加权决策、分歧解决策略和AI解释系统
 */
const AIMultiModelDecision = ({ 
  decisionData,
  explanationData,
  learningData,
  darkMode = true,
  onRefresh,
  onExport
}) => {
  const [expandedSection, setExpandedSection] = useState('decision');
  const [selectedModel, setSelectedModel] = useState(null);
  const [explanationType, setExplanationType] = useState('decision_reason');
  const [timeRange, setTimeRange] = useState('7d');
  
  // 默认数据
  const defaultDecisionData = decisionData || {
    final_decision: "rce_attack",
    status: "consensus",
    confidence: 0.82,
    timestamp: new Date().toISOString(),
    resolution_strategy: "consensus_voting",
    model_decisions: [
      {
        model_name: "deepseek",
        decision: "rce_attack",
        confidence: 0.85,
        reasoning: "检测到严重RCE漏洞，攻击成功率高，目标系统存在未授权访问",
        confidence_level: "high"
      },
      {
        model_name: "openai",
        decision: "rce_attack",
        confidence: 0.78,
        reasoning: "存在远程代码执行漏洞，建议优先利用，系统补丁滞后",
        confidence_level: "medium"
      },
      {
        model_name: "claude",
        decision: "sql_injection",
        confidence: 0.65,
        reasoning: "SQL注入攻击更隐蔽，风险更低，适合长期潜伏",
        confidence_level: "low"
      },
      {
        model_name: "local",
        decision: "rce_attack",
        confidence: 0.55,
        reasoning: "RCE攻击虽然风险高，但成功率最可靠",
        confidence_level: "low"
      }
    ],
    voting_summary: {
      total_models: 4,
      decision_distribution: {
        "rce_attack": {
          count: 3,
          average_confidence: 0.73,
          models: [
            { name: "deepseek", confidence: 0.85 },
            { name: "openai", confidence: 0.78 },
            { name: "local", confidence: 0.55 }
          ]
        },
        "sql_injection": {
          count: 1,
          average_confidence: 0.65,
          models: [
            { name: "claude", confidence: 0.65 }
          ]
        }
      },
      top_decision: "rce_attack",
      top_count: 3
    }
  };
  
  const defaultExplanationData = explanationData || {
    explanation_id: "exp_12345",
    explanation_type: "decision_reason",
    target_decision: "rce_attack",
    explanation_content: "决策分析报告:\n1. 最终决策: rce_attack\n2. 决策机制: consensus_voting\n3. 模型投票: 3/4个模型支持此决策 (支持率: 75%)\n4. 决策置信度: 82%\n5. 主要支持理由:\n   deepseek: 检测到严重RCE漏洞，攻击成功率高\n   openai: 存在远程代码执行漏洞，建议优先利用",
    confidence_score: 0.85,
    supporting_evidence: [
      "支持率: 0.75",
      "决策机制: consensus_voting",
      "模型理由数量: 4"
    ]
  };
  
  const defaultLearningData = learningData || {
    total_learning_cycles: 42,
    current_phase: "optimization",
    learning_strategy: "online",
    average_improvement: 0.65,
    performance_metrics: {
      deepseek: {
        success_rate: 0.88,
        avg_confidence: 0.82,
        total_decisions: 150,
        successful_decisions: 132,
        confidence_variance: 0.05,
        bias_score: 0.12
      },
      openai: {
        success_rate: 0.76,
        avg_confidence: 0.75,
        total_decisions: 120,
        successful_decisions: 91,
        confidence_variance: 0.08,
        bias_score: 0.18
      },
      claude: {
        success_rate: 0.81,
        avg_confidence: 0.68,
        total_decisions: 95,
        successful_decisions: 77,
        confidence_variance: 0.12,
        bias_score: 0.22
      }
    },
    recent_learning_history: [
      {
        record_id: "learn_001",
        decision_id: "dec_456",
        learning_type: "single_decision",
        improvement_score: 0.72,
        timestamp: "2024-01-15 14:30:25"
      },
      {
        record_id: "learn_002",
        decision_id: "dec_457",
        learning_type: "batch_history",
        improvement_score: 0.68,
        timestamp: "2024-01-15 13:45:10"
      }
    ]
  };
  
  const data = defaultDecisionData;
  const explanation = defaultExplanationData;
  const learning = defaultLearningData;
  
  // 获取状态颜色
  const getStatusColor = (status) => {
    const colors = {
      consensus: 'bg-green-500 text-white',
      majority: 'bg-blue-500 text-white',
      split: 'bg-yellow-500 text-gray-900',
      failed: 'bg-red-500 text-white'
    };
    return colors[status] || 'bg-gray-500 text-white';
  };
  
  // 获取置信度级别颜色
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-500';
    if (confidence >= 0.6) return 'text-yellow-500';
    return 'text-red-500';
  };
  
  // 获取置信度级别
  const getConfidenceLevel = (confidence) => {
    if (confidence >= 0.8) return '高';
    if (confidence >= 0.6) return '中';
    return '低';
  };
  
  // 获取模型颜色
  const getModelColor = (modelName) => {
    const colors = {
      deepseek: 'bg-blue-500',
      openai: 'bg-green-500',
      claude: 'bg-purple-500',
      local: 'bg-yellow-500'
    };
    return colors[modelName] || 'bg-gray-500';
  };
  
  // 获取模型图标
  const getModelIcon = (modelName) => {
    const icons = {
      deepseek: <Brain className="w-4 h-4" />,
      openai: <Activity className="w-4 h-4" />,
      claude: <Cpu className="w-4 h-4" />,
      local: <Network className="w-4 h-4" />
    };
    return icons[modelName] || <Brain className="w-4 h-4" />;
  };
  
  // 计算投票分布
  const voteDistribution = data.voting_summary?.decision_distribution || {};
  
  // 计算模型性能趋势
  const calculateModelTrend = (metrics) => {
    if (metrics.success_rate >= 0.8) return 'up';
    if (metrics.success_rate >= 0.6) return 'stable';
    return 'down';
  };
  
  return (
    <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-2xl shadow-lg overflow-hidden`}>
      {/* 头部 */}
      <div className={`p-6 ${darkMode ? 'bg-gray-900' : 'bg-gray-50'} border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold">AI多模型协同决策系统</h2>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                多模型投票机制、置信度加权决策、分歧解决策略
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={onRefresh}
              className={`p-2 rounded-lg ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
              title="刷新数据"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={onExport}
              className={`p-2 rounded-lg ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
              title="导出数据"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
      
      {/* 主内容区域 */}
      <div className="p-6">
        {/* 导航标签 */}
        <div className="flex border-b border-gray-700 mb-6">
          <button
            onClick={() => setExpandedSection('decision')}
            className={`px-4 py-2 font-medium ${expandedSection === 'decision' 
              ? 'border-b-2 border-blue-500 text-blue-500' 
              : darkMode ? 'text-gray-400 hover:text-gray-300' : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <span className="flex items-center">
              <Users className="w-4 h-4 mr-2" />
              协同决策
            </span>
          </button>
          <button
            onClick={() => setExpandedSection('explanation')}
            className={`px-4 py-2 font-medium ${expandedSection === 'explanation' 
              ? 'border-b-2 border-green-500 text-green-500' 
              : darkMode ? 'text-gray-400 hover:text-gray-300' : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <span className="flex items-center">
              <HelpCircle className="w-4 h-4 mr-2" />
              AI解释
            </span>
          </button>
          <button
            onClick={() => setExpandedSection('learning')}
            className={`px-4 py-2 font-medium ${expandedSection === 'learning' 
              ? 'border-b-2 border-purple-500 text-purple-500' 
              : darkMode ? 'text-gray-400 hover:text-gray-300' : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <span className="flex items-center">
              <TrendingUp className="w-4 h-4 mr-2" />
              AI学习
            </span>
          </button>
        </div>
        
        {/* 协同决策面板 */}
        {expandedSection === 'decision' && (
          <div className="space-y-6">
            {/* 决策概览 */}
            <div className={`p-4 rounded-xl ${darkMode ? 'bg-gray-900/50' : 'bg-gray-50'}`}>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg bg-gradient-to-br from-blue-900/30 to-blue-600/20">
                  <div className="text-sm opacity-80 mb-1">最终决策</div>
                  <div className="text-xl font-bold">{data.final_decision}</div>
                  <div className="flex items-center mt-2">
                    <span className={`px-2 py-1 rounded text-xs ${getStatusColor(data.status)}`}>
                      {data.status === 'consensus' ? '一致共识' : 
                       data.status === 'majority' ? '多数同意' : 
                       data.status === 'split' ? '分歧决策' : '决策失败'}
                    </span>
                  </div>
                </div>
                
                <div className="p-4 rounded-lg bg-gradient-to-br from-green-900/30 to-green-600/20">
                  <div className="text-sm opacity-80 mb-1">置信度</div>
                  <div className="flex items-end">
                    <span className="text-2xl font-bold mr-2">{Math.round(data.confidence * 100)}%</span>
                    <span className={`text-sm ${getConfidenceColor(data.confidence)}`}>
                      {getConfidenceLevel(data.confidence)}置信度
                    </span>
                  </div>
                  <div className="w-full h-2 bg-gray-700 rounded-full mt-2 overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-green-500 to-blue-500"
                      style={{ width: `${data.confidence * 100}%` }}
                    ></div>
                  </div>
                </div>
                
                <div className="p-4 rounded-lg bg-gradient-to-br from-purple-900/30 to-purple-600/20">
                  <div className="text-sm opacity-80 mb-1">模型数量</div>
                  <div className="text-2xl font-bold">{data.model_decisions?.length || 0}</div>
                  <div className="text-sm opacity-70 mt-1">参与决策模型</div>
                </div>
                
                <div className="p-4 rounded-lg bg-gradient-to-br from-yellow-900/30 to-yellow-600/20">
                  <div className="text-sm opacity-80 mb-1">解决策略</div>
                  <div className="text-lg font-semibold">
                    {data.resolution_strategy === 'consensus_voting' ? '共识投票' :
                     data.resolution_strategy === 'majority_voting' ? '多数投票' :
                     data.resolution_strategy === 'weighted_decision' ? '加权决策' :
                     data.resolution_strategy}
                  </div>
                  <div className="text-xs opacity-70 mt-1">决策机制</div>
                </div>
              </div>
            </div>
            
            {/* 投票分布可视化 */}
            <div className={`rounded-xl overflow-hidden ${darkMode ? 'bg-gray-900' : 'bg-gray-100'}`}>
              <div className="p-4 border-b border-gray-700">
                <h3 className="font-semibold flex items-center">
                  <PieChart className="w-5 h-5 mr-2" />
                  模型投票分布
                </h3>
              </div>
              <div className="p-4">
                {Object.entries(voteDistribution).map(([decision, info]) => (
                  <div key={decision} className="mb-4">
                    <div className="flex justify-between items-center mb-2">
                      <div className="flex items-center">
                        <div className={`w-3 h-3 rounded-full mr-2 ${decision === data.final_decision ? 'bg-green-500' : 'bg-gray-500'}`}></div>
                        <span className="font-medium">{decision}</span>
                        {decision === data.final_decision && (
                          <span className="ml-2 px-2 py-1 bg-green-900/30 text-green-400 text-xs rounded">
                            最终决策
                          </span>
                        )}
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className="text-sm opacity-70">{info.count}票</span>
                        <span className={`text-sm ${getConfidenceColor(info.average_confidence)}`}>
                          平均置信度: {Math.round(info.average_confidence * 100)}%
                        </span>
                      </div>
                    </div>
                    <div className="w-full h-4 bg-gray-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                        style={{ width: `${(info.count / data.voting_summary.total_models) * 100}%` }}
                      ></div>
                    </div>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {info.models?.map((model, idx) => (
                        <div key={idx} className="flex items-center text-xs opacity-70">
                          <div className={`w-2 h-2 rounded-full mr-1 ${getModelColor(model.name)}`}></div>
                          {model.name}: {Math.round(model.confidence * 100)}%
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* 模型决策详情 */}
            <div className={`rounded-xl overflow-hidden ${darkMode ? 'bg-gray-900' : 'bg-gray-100'}`}>
              <div className="p-4 border-b border-gray-700">
                <h3 className="font-semibold flex items-center">
                  <Users className="w-5 h-5 mr-2" />
                  模型决策详情
                </h3>
              </div>
              <div className="divide-y divide-gray-800">
                {data.model_decisions?.map((modelDecision, index) => (
                  <div 
                    key={index} 
                    className={`p-4 hover:${darkMode ? 'bg-gray-800' : 'bg-gray-200'} transition-colors cursor-pointer ${
                      selectedModel === modelDecision.model_name ? (darkMode ? 'bg-gray-800' : 'bg-gray-200') : ''
                    }`}
                    onClick={() => setSelectedModel(modelDecision.model_name === selectedModel ? null : modelDecision.model_name)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        <div className={`p-2 rounded-lg ${getModelColor(modelDecision.model_name)}`}>
                          {getModelIcon(modelDecision.model_name)}
                        </div>
                        <div>
                          <div className="flex items-center">
                            <h4 className="font-semibold">{modelDecision.model_name}</h4>
                            <span className={`ml-2 px-2 py-1 rounded text-xs ${modelDecision.decision === data.final_decision ? 'bg-green-900/30 text-green-400' : 'bg-gray-700 text-gray-400'}`}>
                              {modelDecision.decision}
                            </span>
                          </div>
                          <p className={`text-sm mt-1 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                            {modelDecision.reasoning}
                          </p>
                        </div>
                      </div>
                      <div className="flex flex-col items-end space-y-2">
                        <div className={`px-3 py-1 rounded-full ${getConfidenceColor(modelDecision.confidence)} bg-opacity-20 ${darkMode ? 'bg-gray-700' : 'bg-gray-300'}`}>
                          <span className="flex items-center">
                            {Math.round(modelDecision.confidence * 100)}%
                            <div className="ml-1 w-2 h-2 rounded-full bg-current"></div>
                          </span>
                        </div>
                        <span className="text-xs opacity-70">
                          {modelDecision.confidence_level === 'high' ? '高置信度' :
                           modelDecision.confidence_level === 'medium' ? '中置信度' : '低置信度'}
                        </span>
                      </div>
                    </div>
                    
                    {selectedModel === modelDecision.model_name && (
                      <div className="mt-3 pl-11">
                        <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-300'}`}>
                          <h5 className="font-medium mb-2">详细分析</h5>
                          <div className="grid grid-cols-2 gap-3 text-sm">
                            <div>
                              <div className="opacity-70">决策类型</div>
                              <div className="font-medium">{modelDecision.decision}</div>
                            </div>
                            <div>
                              <div className="opacity-70">置信度级别</div>
                              <div className="font-medium">
                                {modelDecision.confidence_level === 'high' ? '高 (≥80%)' :
                                 modelDecision.confidence_level === 'medium' ? '中 (60-80%)' : '低 (<60%)'}
                              </div>
                            </div>
                            <div className="col-span-2">
                              <div className="opacity-70">决策理由</div>
                              <div className="mt-1">{modelDecision.reasoning}</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        
        {/* AI解释面板 */}
        {expandedSection === 'explanation' && (
          <div className="space-y-6">
            {/* 解释类型选择 */}
            <div className="flex space-x-2 overflow-x-auto pb-2">
              {[
                { id: 'decision_reason', label: '决策原因', icon: <Brain className="w-4 h-4" />, color: 'blue' },
                { id: 'risk_assessment', label: '风险评估', icon: <Shield className="w-4 h-4" />, color: 'red' },
                { id: 'alternative_option', label: '替代方案', icon: <GitBranch className="w-4 h-4" />, color: 'green' },
                { id: 'confidence_analysis', label: '置信度分析', icon: <BarChart3 className="w-4 h-4" />, color: 'purple' },
                { id: 'model_bias', label: '模型偏差', icon: <AlertCircle className="w-4 h-4" />, color: 'yellow' }
              ].map((type) => (
                <button
                  key={type.id}
                  onClick={() => setExplanationType(type.id)}
                  className={`px-4 py-2 rounded-lg flex items-center whitespace-nowrap ${
                    explanationType === type.id 
                      ? `bg-${type.color}-500 text-white` 
                      : darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300'
                  }`}
                >
                  {type.icon}
                  <span className="ml-2">{type.label}</span>
                </button>
              ))}
            </div>
            
            {/* 解释内容 */}
            <div className={`rounded-xl overflow-hidden ${darkMode ? 'bg-gray-900' : 'bg-gray-100'}`}>
              <div className="p-4 border-b border-gray-700 flex justify-between items-center">
                <h3 className="font-semibold flex items-center">
                  <HelpCircle className="w-5 h-5 mr-2" />
                  AI解释系统
                </h3>
                <div className="flex items-center space-x-2">
                  <div className={`px-3 py-1 rounded-full bg-blue-900/30 text-blue-400 text-sm`}>
                    解释置信度: {Math.round(explanation.confidence_score * 100)}%
                  </div>
                  <div className="text-sm opacity-70">
                    {explanation.timestamp ? new Date(explanation.timestamp).toLocaleString() : '刚刚'}
                  </div>
                </div>
              </div>
              <div className="p-6">
                <div className="prose max-w-none">
                  {explanation.explanation_content.split('\n').map((line, index) => (
                    <p key={index} className={`mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                      {line}
                    </p>
                  ))}
                </div>
                
                {/* 支持证据 */}
                <div className="mt-6">
                  <h4 className="font-medium mb-3 flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    支持证据
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {explanation.supporting_evidence?.map((evidence, index) => (
                      <div key={index} className={`p-3 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-200'}`}>
                        <div className="text-sm">{evidence}</div>
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* 解释元数据 */}
                <div className="mt-6 pt-4 border-t border-gray-700">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="opacity-70">解释ID</div>
                      <div className="font-mono">{explanation.explanation_id}</div>
                    </div>
                    <div>
                      <div className="opacity-70">目标决策</div>
                      <div className="font-medium">{explanation.target_decision}</div>
                    </div>
                    <div>
                      <div className="opacity-70">解释类型</div>
                      <div className="font-medium">
                        {explanation.explanation_type === 'decision_reason' ? '决策原因' :
                         explanation.explanation_type === 'risk_assessment' ? '风险评估' :
                         explanation.explanation_type === 'alternative_option' ? '替代方案' :
                         explanation.explanation_type}
                      </div>
                    </div>
                    <div>
                      <div className="opacity-70">质量评分</div>
                      <div className="flex items-center">
                        <div className="w-16 h-2 bg-gray-700 rounded-full overflow-hidden mr-2">
                          <div 
                            className="h-full bg-gradient-to-r from-green-500 to-blue-500"
                            style={{ width: `${explanation.confidence_score * 100}%` }}
                          ></div>
                        </div>
                        <span>{Math.round(explanation.confidence_score * 100)}/100</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* 解释示例 */}
            <div className={`rounded-xl p-4 ${darkMode ? 'bg-gray-900' : 'bg-gray-100'}`}>
              <h4 className="font-medium mb-3">解释类型说明</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-200'}`}>
                  <div className="flex items-center mb-2">
                    <Brain className="w-4 h-4 mr-2 text-blue-500" />
                    <span className="font-medium">决策原因解释</span>
                  </div>
                  <p className="text-sm opacity-70">
                    解释为什么选择某个决策，包括模型投票分布、共识程度、关键支持理由等。
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-200'}`}>
                  <div className="flex items-center mb-2">
                    <Shield className="w-4 h-4 mr-2 text-red-500" />
                    <span className="font-medium">风险评估解释</span>
                  </div>
                  <p className="text-sm opacity-70">
                    分析决策涉及的风险因素、风险等级、缓解措施和潜在后果。
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-200'}`}>
                  <div className="flex items-center mb-2">
                    <GitBranch className="w-4 h-4 mr-2 text-green-500" />
                    <span className="font-medium">替代方案解释</span>
                  </div>
                  <p className="text-sm opacity-70">
                    展示考虑过的其他方案、拒绝原因、优劣对比和机会成本分析。
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-200'}`}>
                  <div className="flex items-center mb-2">
                    <AlertCircle className="w-4 h-4 mr-2 text-yellow-500" />
                    <span className="font-medium">模型偏差分析</span>
                  </div>
                  <p className="text-sm opacity-70">
                    检测模型决策中的偏差模式，如过度自信、信心不足、决策固化等。
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* AI学习面板 */}
        {expandedSection === 'learning' && (
          <div className="space-y-6">
            {/* 学习概览 */}
            <div className={`p-4 rounded-xl ${darkMode ? 'bg-gray-900/50' : 'bg-gray-50'}`}>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg bg-gradient-to-br from-blue-900/30 to-blue-600/20">
                  <div className="text-sm opacity-80 mb-1">学习周期</div>
                  <div className="text-2xl font-bold">{learning.total_learning_cycles}</div>
                  <div className="text-sm opacity-70 mt-1">总学习次数</div>
                </div>
                
                <div className="p-4 rounded-lg bg-gradient-to-br from-green-900/30 to-green-600/20">
                  <div className="text-sm opacity-80 mb-1">当前阶段</div>
                  <div className="text-xl font-bold">
                    {learning.current_phase === 'data_collection' ? '数据收集' :
                     learning.current_phase === 'pattern_recognition' ? '模式识别' :
                     learning.current_phase === 'optimization' ? '优化阶段' : '验证阶段'}
                  </div>
                  <div className="text-sm opacity-70 mt-1">学习阶段</div>
                </div>
                
                <div className="p-4 rounded-lg bg-gradient-to-br from-purple-900/30 to-purple-600/20">
                  <div className="text-sm opacity-80 mb-1">平均改进</div>
                  <div className="text-2xl font-bold">{Math.round(learning.average_improvement * 100)}%</div>
                  <div className="w-full h-2 bg-gray-700 rounded-full mt-2 overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-green-500 to-purple-500"
                      style={{ width: `${learning.average_improvement * 100}%` }}
                    ></div>
                  </div>
                </div>
                
                <div className="p-4 rounded-lg bg-gradient-to-br from-yellow-900/30 to-yellow-600/20">
                  <div className="text-sm opacity-80 mb-1">学习策略</div>
                  <div className="text-lg font-semibold">
                    {learning.learning_strategy === 'online' ? '在线学习' :
                     learning.learning_strategy === 'batch' ? '批量学习' :
                     learning.learning_strategy === 'reinforcement' ? '强化学习' : '监督学习'}
                  </div>
                  <div className="text-sm opacity-70 mt-1">策略类型</div>
                </div>
              </div>
            </div>
            
            {/* 模型性能对比 */}
            <div className={`rounded-xl overflow-hidden ${darkMode ? 'bg-gray-900' : 'bg-gray-100'}`}>
              <div className="p-4 border-b border-gray-700">
                <h3 className="font-semibold flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2" />
                  模型性能对比
                </h3>
              </div>
              <div className="p-4">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className={`text-left ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                        <th className="pb-3 px-2">模型</th>
                        <th className="pb-3 px-2">成功率</th>
                        <th className="pb-3 px-2">平均置信度</th>
                        <th className="pb-3 px-2">总决策数</th>
                        <th className="pb-3 px-2">成功决策</th>
                        <th className="pb-3 px-2">置信度方差</th>
                        <th className="pb-3 px-2">偏差评分</th>
                        <th className="pb-3 px-2">趋势</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(learning.performance_metrics || {}).map(([modelName, metrics]) => {
                        const trend = calculateModelTrend(metrics);
                        return (
                          <tr key={modelName} className="border-t border-gray-800">
                            <td className="py-3 px-2">
                              <div className="flex items-center">
                                <div className={`w-3 h-3 rounded-full mr-2 ${getModelColor(modelName)}`}></div>
                                <span className="font-medium">{modelName}</span>
                              </div>
                            </td>
                            <td className="py-3 px-2">
                              <div className="flex items-center">
                                <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden mr-2">
                                  <div 
                                    className={`h-full ${metrics.success_rate >= 0.8 ? 'bg-green-500' : metrics.success_rate >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'}`}
                                    style={{ width: `${metrics.success_rate * 100}%` }}
                                  ></div>
                                </div>
                                <span>{Math.round(metrics.success_rate * 100)}%</span>
                              </div>
                            </td>
                            <td className="py-3 px-2">
                              <span className={`${getConfidenceColor(metrics.avg_confidence)}`}>
                                {Math.round(metrics.avg_confidence * 100)}%
                              </span>
                            </td>
                            <td className="py-3 px-2">{metrics.total_decisions}</td>
                            <td className="py-3 px-2">{metrics.successful_decisions}</td>
                            <td className="py-3 px-2">
                              <span className={metrics.confidence_variance > 0.1 ? 'text-yellow-500' : 'text-green-500'}>
                                {metrics.confidence_variance.toFixed(3)}
                              </span>
                            </td>
                            <td className="py-3 px-2">
                              <span className={metrics.bias_score > 0.2 ? 'text-red-500' : 'text-green-500'}>
                                {metrics.bias_score.toFixed(2)}
                              </span>
                            </td>
                            <td className="py-3 px-2">
                              <div className="flex items-center">
                                {trend === 'up' ? (
                                  <ArrowUpRight className="w-4 h-4 text-green-500" />
                                ) : trend === 'down' ? (
                                  <ArrowDownRight className="w-4 h-4 text-red-500" />
                                ) : (
                                  <div className="w-4 h-4 text-yellow-500">—</div>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                
                <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-200'} text-sm`}>
                    <div className="opacity-70">成功率</div>
                    <div className="mt-1">
                      <span className="text-green-500">≥80%: 优秀</span>, 
                      <span className="text-yellow-500"> 60-80%: 良好</span>, 
                      <span className="text-red-500"> <60%: 需改进</span>
                    </div>
                  </div>
                  <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-200'} text-sm`}>
                    <div className="opacity-70">置信度方差</div>
                    <div className="mt-1">
                      <span className="text-green-500"><0.1: 稳定</span>, 
                      <span className="text-yellow-500"> 0.1-0.2: 波动</span>, 
                      <span className="text-red-500"> >0.2: 不稳定</span>
                    </div>
                  </div>
                  <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-200'} text-sm`}>
                    <div className="opacity-70">偏差评分</div>
                    <div className="mt-1">
                      <span className="text-green-500"><0.1: 低偏差</span>, 
                      <span className="text-yellow-500"> 0.1-0.2: 中偏差</span>, 
                      <span className="text-red-500"> >0.2: 高偏差</span>
                    </div>
                  </div>
                  <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-200'} text-sm`}>
                    <div className="opacity-70">学习效果</div>
                    <div className="mt-1">
                      平均改进: <span className="font-medium">{Math.round(learning.average_improvement * 100)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* 学习历史 */}
            <div className={`rounded-xl overflow-hidden ${darkMode ? 'bg-gray-900' : 'bg-gray-100'}`}>
              <div className="p-4 border-b border-gray-700 flex justify-between items-center">
                <h3 className="font-semibold flex items-center">
                  <Clock className="w-5 h-5 mr-2" />
                  近期学习历史
                </h3>
                <div className="flex items-center space-x-2">
                  <select 
                    value={timeRange}
                    onChange={(e) => setTimeRange(e.target.value)}
                    className={`px-3 py-1 rounded ${darkMode ? 'bg-gray-800 text-white' : 'bg-gray-200 text-gray-900'}`}
                  >
                    <option value="24h">最近24小时</option>
                    <option value="7d">最近7天</option>
                    <option value="30d">最近30天</option>
                    <option value="all">全部</option>
                  </select>
                </div>
              </div>
              <div className="p-4">
                <div className="space-y-3">
                  {learning.recent_learning_history?.map((record, index) => (
                    <div key={index} className={`p-4 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-200'}`}>
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center mb-2">
                            <div className={`px-2 py-1 rounded text-xs ${
                              record.learning_type === 'single_decision' ? 'bg-blue-900/30 text-blue-400' :
                              record.learning_type === 'batch_history' ? 'bg-green-900/30 text-green-400' :
                              'bg-gray-700 text-gray-400'
                            }`}>
                              {record.learning_type === 'single_decision' ? '单次决策学习' : '批量历史学习'}
                            </div>
                            <span className="ml-2 text-sm opacity-70">ID: {record.record_id}</span>
                          </div>
                          <div className="text-sm">
                            决策ID: <span className="font-mono">{record.decision_id}</span>
                          </div>
                        </div>
                        <div className="flex flex-col items-end">
                          <div className="text-lg font-bold text-green-500">
                            +{Math.round(record.improvement_score * 100)}%
                          </div>
                          <div className="text-sm opacity-70">{record.timestamp}</div>
                        </div>
                      </div>
                      <div className="mt-3 w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-green-500 to-blue-500"
                          style={{ width: `${record.improvement_score * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {(!learning.recent_learning_history || learning.recent_learning_history.length === 0) && (
                  <div className={`p-8 text-center ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                    <Brain className="w-12 h-12 mx-auto mb-4 opacity-30" />
                    <p>暂无学习历史记录</p>
                    <p className="text-sm mt-1">执行决策后，AI学习系统将开始记录学习历史</p>
                  </div>
                )}
              </div>
            </div>
            
            {/* 学习阶段说明 */}
            <div className={`rounded-xl p-4 ${darkMode ? 'bg-gray-900' : 'bg-gray-100'}`}>
              <h4 className="font-medium mb-4">学习阶段说明</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-200'} ${
                  learning.current_phase === 'data_collection' ? 'ring-2 ring-blue-500' : ''
                }`}>
                  <div className="flex items-center mb-2">
                    <div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>
                    <span className="font-medium">数据收集阶段</span>
                  </div>
                  <p className="text-sm opacity-70">
                    收集决策数据，建立初始学习基础。通常在前10个学习周期。
                  </p>
                </div>
                <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-200'} ${
                  learning.current_phase === 'pattern_recognition' ? 'ring-2 ring-green-500' : ''
                }`}>
                  <div className="flex items-center mb-2">
                    <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                    <span className="font-medium">模式识别阶段</span>
                  </div>
                  <p className="text-sm opacity-70">
                    识别决策模式，发现规律和关联性。通常在10-30个学习周期。
                  </p>
                </div>
                <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-200'} ${
                  learning.current_phase === 'optimization' ? 'ring-2 ring-purple-500' : ''
                }`}>
                  <div className="flex items-center mb-2">
                    <div className="w-3 h-3 rounded-full bg-purple-500 mr-2"></div>
                    <span className="font-medium">优化阶段</span>
                  </div>
                  <p className="text-sm opacity-70">
                    优化决策策略，调整模型权重和阈值。通常在30-50个学习周期。
                  </p>
                </div>
                <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-200'} ${
                  learning.current_phase === 'validation' ? 'ring-2 ring-yellow-500' : ''
                }`}>
                  <div className="flex items-center mb-2">
                    <div className="w-3 h-3 rounded-full bg-yellow-500 mr-2"></div>
                    <span className="font-medium">验证阶段</span>
                  </div>
                  <p className="text-sm opacity-70">
                    验证学习效果，确保优化后的策略稳定可靠。50+学习周期。
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* 页脚 */}
      <div className={`p-4 border-t ${darkMode ? 'border-gray-700 bg-gray-900' : 'border-gray-200 bg-gray-50'} text-center text-sm opacity-70`}>
        <div className="flex items-center justify-center">
          <Brain className="w-4 h-4 mr-2" />
          <span>AI多模型协同决策系统 v1.0 • 第4天：前端AI展示优化</span>
        </div>
      </div>
    </div>
  );
};

export default AIMultiModelDecision;