import React, { useState, useEffect } from 'react';
import { Brain, Zap, Cpu, Network, Activity, Sparkles } from 'lucide-react';

/**
 * AI思考动画组件
 * 展示AI思考过程的可视化动画
 */
const AIThinkingAnimation = ({ 
  message = "AI正在思考...",
  thinkingType = "analyze",
  duration = 3000,
  showProgress = true,
  onComplete,
  darkMode = true
}) => {
  const [progress, setProgress] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [thoughts, setThoughts] = useState([]);
  
  // 思考类型配置
  const thinkingConfigs = {
    analyze: {
      icon: <Brain className="w-6 h-6" />,
      color: "blue",
      thoughts: [
        "分析目标结构...",
        "评估攻击面...",
        "计算风险评分...",
        "规划攻击路径...",
        "生成最终决策..."
      ]
    },
    decision: {
      icon: <Activity className="w-6 h-6" />,
      color: "purple",
      thoughts: [
        "收集模型意见...",
        "计算置信度...",
        "评估投票结果...",
        "解决模型分歧...",
        "生成最终决策..."
      ]
    },
    plan: {
      icon: <Network className="w-6 h-6" />,
      color: "green",
      thoughts: [
        "侦察目标信息...",
        "识别漏洞点...",
        "设计攻击链...",
        "优化执行路径...",
        "生成完整计划..."
      ]
    },
    learn: {
      icon: <Cpu className="w-6 h-6" />,
      color: "yellow",
      thoughts: [
        "分析历史数据...",
        "识别模式...",
        "优化决策策略...",
        "更新模型权重...",
        "完成学习循环..."
      ]
    }
  };
  
  const config = thinkingConfigs[thinkingType] || thinkingConfigs.analyze;
  
  // 进度动画
  useEffect(() => {
    if (isComplete) return;
    
    const interval = 50;
    const totalSteps = duration / interval;
    const step = 100 / totalSteps;
    
    const timer = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(timer);
          setIsComplete(true);
          if (onComplete) {
            setTimeout(onComplete, 500);
          }
          return 100;
        }
        return prev + step;
      });
    }, interval);
    
    return () => clearInterval(timer);
  }, [duration, onComplete, isComplete]);
  
  // 思考气泡动画
  useEffect(() => {
    if (isComplete) return;
    
    const interval = duration / (config.thoughts.length + 1);
    
    const timer = setInterval(() => {
      setThoughts(prev => {
        const nextIndex = prev.length;
        if (nextIndex >= config.thoughts.length) {
          clearInterval(timer);
          return prev;
        }
        return [...prev, config.thoughts[nextIndex]];
      });
    }, interval);
    
    return () => clearInterval(timer);
  }, [duration, config.thoughts.length, isComplete]);
  
  const getColorClasses = () => {
    const colors = {
      blue: {
        bg: darkMode ? 'bg-blue-900/30' : 'bg-blue-100',
        border: darkMode ? 'border-blue-500/50' : 'border-blue-300',
        text: 'text-blue-400',
        gradient: 'from-blue-500 to-purple-600'
      },
      purple: {
        bg: darkMode ? 'bg-purple-900/30' : 'bg-purple-100',
        border: darkMode ? 'border-purple-500/50' : 'border-purple-300',
        text: 'text-purple-400',
        gradient: 'from-purple-500 to-pink-600'
      },
      green: {
        bg: darkMode ? 'bg-green-900/30' : 'bg-green-100',
        border: darkMode ? 'border-green-500/50' : 'border-green-300',
        text: 'text-green-400',
        gradient: 'from-green-500 to-emerald-600'
      },
      yellow: {
        bg: darkMode ? 'bg-yellow-900/30' : 'bg-yellow-100',
        border: darkMode ? 'border-yellow-500/50' : 'border-yellow-300',
        text: 'text-yellow-400',
        gradient: 'from-yellow-500 to-orange-600'
      }
    };
    
    return colors[config.color] || colors.blue;
  };
  
  const colorClasses = getColorClasses();
  
  return (
    <div className={`relative ${darkMode ? 'text-white' : 'text-gray-900'}`}>
      {/* 主容器 */}
      <div className={`rounded-2xl p-6 ${colorClasses.bg} border ${colorClasses.border}`}>
        {/* 头部 */}
        <div className="flex items-center mb-6">
          <div className={`p-3 rounded-xl bg-gradient-to-br ${colorClasses.gradient} mr-4`}>
            <div className="text-white">
              {config.icon}
            </div>
          </div>
          <div>
            <h3 className="text-lg font-semibold">{message}</h3>
            <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              {thinkingType === 'analyze' && '目标分析与路径规划'}
              {thinkingType === 'decision' && '多模型协同决策'}
              {thinkingType === 'plan' && '攻击链设计优化'}
              {thinkingType === 'learn' && 'AI学习与优化'}
            </p>
          </div>
        </div>
        
        {/* 大脑动画 */}
        <div className="relative flex justify-center mb-8">
          <div className="relative">
            {/* 脑波环 */}
            <div className="absolute inset-0">
              {[...Array(3)].map((_, i) => (
                <div
                  key={i}
                  className={`absolute rounded-full border-2 ${colorClasses.border} animate-pulse`}
                  style={{
                    width: `${80 + i * 40}px`,
                    height: `${80 + i * 40}px`,
                    top: `-${20 + i * 20}px`,
                    left: `-${20 + i * 20}px`,
                    animationDelay: `${i * 0.3}s`
                  }}
                />
              ))}
            </div>
            
            {/* 大脑图标 */}
            <div className={`relative z-10 p-4 rounded-full bg-gradient-to-br ${colorClasses.gradient}`}>
              <Brain className="w-12 h-12 text-white" />
            </div>
            
            {/* 思考粒子 */}
            <div className="absolute inset-0">
              {[...Array(8)].map((_, i) => (
                <div
                  key={i}
                  className={`absolute w-2 h-2 rounded-full bg-gradient-to-br ${colorClasses.gradient}`}
                  style={{
                    animation: `particle-${i % 2 === 0 ? 'orbit' : 'orbit-reverse'} 3s linear infinite`,
                    animationDelay: `${i * 0.4}s`,
                    top: '50%',
                    left: '50%'
                  }}
                />
              ))}
            </div>
          </div>
        </div>
        
        {/* 思考过程 */}
        <div className="space-y-3">
          {thoughts.map((thought, index) => (
            <div
              key={index}
              className="flex items-center"
              style={{
                animation: `fadeInUp 0.5s ease-out ${index * 0.3}s both`
              }}
            >
              <div className={`w-2 h-2 rounded-full ${colorClasses.text} mr-3`}></div>
              <span className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                {thought}
              </span>
              <div className="ml-auto">
                {index < thoughts.length - 1 ? (
                  <div className={`w-2 h-2 rounded-full ${colorClasses.text} animate-pulse`}></div>
                ) : (
                  <Sparkles className={`w-4 h-4 ${colorClasses.text}`} />
                )}
              </div>
            </div>
          ))}
        </div>
        
        {/* 进度条 */}
        {showProgress && (
          <div className="mt-6">
            <div className="flex justify-between text-sm mb-2">
              <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>思考进度</span>
              <span className={`font-medium ${colorClasses.text}`}>{Math.round(progress)}%</span>
            </div>
            <div className={`w-full h-2 rounded-full ${darkMode ? 'bg-gray-800' : 'bg-gray-200'} overflow-hidden`}>
              <div
                className={`h-full bg-gradient-to-r ${colorClasses.gradient} transition-all duration-300 ease-out`}
                style={{ width: `${progress}%` }}
              >
                <div className="progress-shine h-full"></div>
              </div>
            </div>
          </div>
        )}
        
        {/* 完成状态 */}
        {isComplete && (
          <div className="mt-6 p-4 rounded-xl bg-gradient-to-r from-green-900/30 to-emerald-900/30 border border-green-500/30">
            <div className="flex items-center">
              <div className="p-2 bg-green-500/20 rounded-lg mr-3">
                <Zap className="w-5 h-5 text-green-400" />
              </div>
              <div>
                <h4 className="font-medium text-green-400">思考完成</h4>
                <p className="text-sm text-green-300/70">AI已生成最优决策方案</p>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* 样式定义 */}
      <style jsx>{`
        @keyframes particle-orbit {
          0% {
            transform: translate(-50%, -50%) rotate(0deg) translateX(60px) rotate(0deg);
          }
          100% {
            transform: translate(-50%, -50%) rotate(360deg) translateX(60px) rotate(-360deg);
          }
        }
        
        @keyframes particle-orbit-reverse {
          0% {
            transform: translate(-50%, -50%) rotate(0deg) translateX(40px) rotate(0deg);
          }
          100% {
            transform: translate(-50%, -50%) rotate(-360deg) translateX(40px) rotate(360deg);
          }
        }
        
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-pulse {
          animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
        
        .progress-shine {
          background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.4),
            transparent
          );
          background-size: 200% 100%;
          animation: progress-shine 2s infinite;
        }
        
        @keyframes progress-shine {
          0% {
            background-position: -200% 0;
          }
          100% {
            background-position: 200% 0;
          }
        }
      `}</style>
    </div>
  );
};

export default AIThinkingAnimation;