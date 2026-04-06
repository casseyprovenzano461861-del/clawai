import React, { useState, useEffect } from 'react';
import { X, ChevronRight, ChevronLeft, HelpCircle, Play, Target, Brain, Shield, CheckCircle } from 'lucide-react';

const OnboardingGuide = ({ onComplete, darkMode }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isOpen, setIsOpen] = useState(true);
  const [showOnFirstVisit, setShowOnFirstVisit] = useState(true);

  // 检查是否是首次访问
  useEffect(() => {
    const hasSeenGuide = localStorage.getItem('clawai_guide_seen');
    if (hasSeenGuide) {
      setIsOpen(false);
      setShowOnFirstVisit(false);
    }
  }, []);

  const steps = [
    {
      title: "欢迎使用 ClawAI",
      description: "基于规则引擎的渗透测试演示平台",
      content: (
        <div className="space-y-3">
          <p className="text-sm">ClawAI 是一个演示平台，展示如何将规则引擎用于安全测试的决策过程。</p>
          <div className={`p-3 rounded-lg ${darkMode ? 'bg-blue-900/20' : 'bg-blue-50'}`}>
            <p className="text-xs flex items-center">
              <HelpCircle className="w-4 h-4 mr-2" />
              <strong>重要提示：</strong> 这是一个演示系统，主要基于规则引擎和模拟数据进行展示。
            </p>
          </div>
        </div>
      ),
      target: null,
      position: 'center'
    },
    {
      title: "核心功能：目标输入",
      description: "开始你的第一次安全测试",
      content: (
        <div className="space-y-2">
          <p className="text-sm">输入目标地址（IP、域名或URL），然后点击"开始攻击"。</p>
          <p className="text-xs opacity-70">系统会自动扫描目标并生成攻击链。</p>
        </div>
      ),
      target: '.target-input-section',
      position: 'bottom'
    },
    {
      title: "执行模式",
      description: "了解不同的执行方式",
      content: (
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span className="text-sm">真实执行：调用实际安全工具</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-blue-500"></div>
            <span className="text-sm">模拟演示：使用预设数据进行展示</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-purple-500"></div>
            <span className="text-sm">规则引擎模式：使用规则进行智能决策</span>
          </div>
        </div>
      ),
      target: '.execution-mode-section',
      position: 'right'
    },
    {
      title: "查看攻击结果",
      description: "分析生成的攻击链",
      content: (
        <div className="space-y-2">
          <p className="text-sm">攻击完成后，你可以看到：</p>
          <ul className="space-y-1 text-xs">
            <li className="flex items-center">
              <CheckCircle className="w-3 h-3 mr-2 text-green-500" />
              可视化攻击链步骤
            </li>
            <li className="flex items-center">
              <CheckCircle className="w-3 h-3 mr-2 text-green-500" />
              规则引擎决策分析
            </li>
            <li className="flex items-center">
              <CheckCircle className="w-3 h-3 mr-2 text-green-500" />
              目标安全评估
            </li>
          </ul>
        </div>
      ),
      target: '.attack-results-section',
      position: 'left'
    },
    {
      title: "侧边栏导航",
      description: "访问其他功能",
      content: (
        <div className="space-y-2">
          <p className="text-sm">使用侧边栏切换到不同功能模块：</p>
          <ul className="space-y-1 text-xs">
            <li className="flex items-center">
              <Target className="w-3 h-3 mr-2" />
              攻击模拟
            </li>
            <li className="flex items-center">
              <Brain className="w-3 h-3 mr-2" />
              规则引擎分析
            </li>
            <li className="flex items-center">
              <Shield className="w-3 h-3 mr-2" />
              工具库
            </li>
          </ul>
        </div>
      ),
      target: '.sidebar-navigation',
      position: 'right'
    },
    {
      title: "开始你的第一个测试",
      description: "准备好了吗？",
      content: (
        <div className="space-y-3">
          <p className="text-sm">建议从简单的目标开始：</p>
          <div className="grid grid-cols-2 gap-2">
            <div className={`p-2 rounded text-center text-xs ${darkMode ? 'bg-gray-700' : 'bg-gray-100'}`}>
              192.168.1.1
            </div>
            <div className={`p-2 rounded text-center text-xs ${darkMode ? 'bg-gray-700' : 'bg-gray-100'}`}>
              example.com
            </div>
            <div className={`p-2 rounded text-center text-xs ${darkMode ? 'bg-gray-700' : 'bg-gray-100'}`}>
              localhost
            </div>
            <div className={`p-2 rounded text-center text-xs ${darkMode ? 'bg-gray-700' : 'bg-gray-100'}`}>
              scanme.nmap.org
            </div>
          </div>
        </div>
      ),
      target: '.quick-targets-section',
      position: 'top'
    }
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    localStorage.setItem('clawai_guide_seen', 'true');
    setIsOpen(false);
    if (onComplete) onComplete();
  };

  const handleSkip = () => {
    if (confirm('确定要跳过新手引导吗？你可以随时通过帮助按钮重新查看。')) {
      handleComplete();
    }
  };

  if (!isOpen) {
    // 显示帮助按钮
    return (
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 z-50 p-3 rounded-full shadow-lg ${darkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'} text-white`}
        title="查看新手引导"
      >
        <HelpCircle className="w-6 h-6" />
      </button>
    );
  }

  const currentStepData = steps[currentStep];

  return (
    <>
      {/* 遮罩层 */}
      <div className="fixed inset-0 bg-black/50 z-40" onClick={handleSkip}></div>
      
      {/* 引导卡片 */}
      <div className={`fixed z-50 rounded-xl shadow-2xl ${darkMode ? 'bg-gray-800' : 'bg-white'} border ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}
        style={{
          width: '400px',
          ...getPosition(currentStepData.position, currentStepData.target)
        }}
      >
        {/* 标题栏 */}
        <div className={`flex items-center justify-between p-4 border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
          <div>
            <h3 className="font-bold text-lg">{currentStepData.title}</h3>
            <p className="text-sm opacity-70">{currentStepData.description}</p>
          </div>
          <button
            onClick={handleSkip}
            className={`p-1 rounded ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 内容 */}
        <div className="p-4">
          {currentStepData.content}
          
          {/* 进度指示器 */}
          <div className="flex items-center justify-between mt-4">
            <div className="flex space-x-1">
              {steps.map((_, index) => (
                <div
                  key={index}
                  className={`w-2 h-2 rounded-full ${index === currentStep ? 'bg-blue-500' : darkMode ? 'bg-gray-600' : 'bg-gray-300'}`}
                ></div>
              ))}
            </div>
            
            <div className="flex items-center space-x-2">
              {currentStep > 0 && (
                <button
                  onClick={handlePrev}
                  className={`px-3 py-1 rounded ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
              )}
              
              <button
                onClick={handleNext}
                className={`px-4 py-1 rounded flex items-center ${darkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'} text-white`}
              >
                {currentStep === steps.length - 1 ? (
                  <>
                    开始使用
                    <Play className="w-4 h-4 ml-1" />
                  </>
                ) : (
                  <>
                    下一步
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 高亮目标元素 */}
      {currentStepData.target && (
        <div className="fixed z-40 border-2 border-blue-500 rounded-lg shadow-lg shadow-blue-500/50 animate-pulse"
          style={getHighlightPosition(currentStepData.target)}>
        </div>
      )}
    </>
  );
};

// 根据目标选择器获取位置
const getPosition = (position, targetSelector) => {
  if (!targetSelector) {
    return { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' };
  }

  const targetElement = document.querySelector(targetSelector);
  if (!targetElement) {
    return { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' };
  }

  const rect = targetElement.getBoundingClientRect();
  
  switch(position) {
    case 'top':
      return {
        top: `${rect.top - 220}px`,
        left: `${rect.left + rect.width/2 - 200}px`
      };
    case 'bottom':
      return {
        top: `${rect.bottom + 10}px`,
        left: `${rect.left + rect.width/2 - 200}px`
      };
    case 'left':
      return {
        top: `${rect.top + rect.height/2 - 100}px`,
        left: `${rect.left - 420}px`
      };
    case 'right':
      return {
        top: `${rect.top + rect.height/2 - 100}px`,
        left: `${rect.right + 10}px`
      };
    default:
      return {
        top: `${rect.bottom + 10}px`,
        left: `${rect.left + rect.width/2 - 200}px`
      };
  }
};

// 获取高亮元素位置
const getHighlightPosition = (targetSelector) => {
  const targetElement = document.querySelector(targetSelector);
  if (!targetElement) {
    return { display: 'none' };
  }

  const rect = targetElement.getBoundingClientRect();
  return {
    top: `${rect.top - 4}px`,
    left: `${rect.left - 4}px`,
    width: `${rect.width + 8}px`,
    height: `${rect.height + 8}px`,
    pointerEvents: 'none'
  };
};

export default OnboardingGuide;