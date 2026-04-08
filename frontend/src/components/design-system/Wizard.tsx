import React, { useState } from 'react';
import { Check, ChevronRight, Home, Settings, User, Shield, Zap } from 'lucide-react';
import { Button } from './Button';
import { Card } from './Card';

export interface WizardStep {
  id: string;
  title: string;
  description?: string;
  icon?: React.ReactNode;
  component: React.ReactNode;
  validate?: () => boolean | Promise<boolean>;
}

export interface WizardProps {
  steps: WizardStep[];
  initialStep?: number;
  onComplete?: () => void;
  onCancel?: () => void;
  showProgress?: boolean;
  showNavigation?: boolean;
  className?: string;
}

const Wizard: React.FC<WizardProps> = ({
  steps,
  initialStep = 0,
  onComplete,
  onCancel,
  showProgress = true,
  showNavigation = true,
  className = '',
}) => {
  const [currentStep, setCurrentStep] = useState(initialStep);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());
  const [isValidating, setIsValidating] = useState(false);

  const currentStepData = steps[currentStep];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === steps.length - 1;

  // 获取步骤图标
  const getStepIcon = (step: WizardStep, index: number) => {
    if (completedSteps.has(step.id)) {
      return <Check className="h-5 w-5 text-white" />;
    }
    
    if (index === currentStep) {
      return step.icon || <div className="h-5 w-5 text-white">{index + 1}</div>;
    }
    
    return step.icon || <div className="h-5 w-5 text-gray-400">{index + 1}</div>;
  };

  // 获取步骤状态类
  const getStepStatusClass = (step: WizardStep, index: number) => {
    if (completedSteps.has(step.id)) {
      return 'bg-success-500 border-success-500';
    }
    
    if (index === currentStep) {
      return 'bg-primary-500 border-primary-500';
    }
    
    if (index < currentStep) {
      return 'bg-gray-300 dark:bg-gray-600 border-gray-300 dark:border-gray-600';
    }
    
    return 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600';
  };

  // 验证当前步骤
  const validateCurrentStep = async (): Promise<boolean> => {
    if (!currentStepData.validate) return true;
    
    try {
      setIsValidating(true);
      const isValid = await currentStepData.validate();
      return isValid;
    } catch (error) {
      console.error('步骤验证失败:', error);
      return false;
    } finally {
      setIsValidating(false);
    }
  };

  // 下一步
  const handleNext = async () => {
    const isValid = await validateCurrentStep();
    if (!isValid) return;
    
    setCompletedSteps(prev => new Set(prev).add(currentStepData.id));
    
    if (isLastStep) {
      onComplete?.();
    } else {
      setCurrentStep(prev => prev + 1);
    }
  };

  // 上一步
  const handlePrev = () => {
    if (!isFirstStep) {
      setCurrentStep(prev => prev - 1);
    }
  };

  // 跳转到指定步骤
  const handleStepClick = async (index: number) => {
    if (index === currentStep) return;
    
    // 只能跳转到已完成的步骤或下一步
    if (index > currentStep && !completedSteps.has(steps[index - 1].id)) {
      return;
    }
    
    setCurrentStep(index);
  };

  // 计算进度
  const progressPercentage = ((currentStep + 1) / steps.length) * 100;

  return (
    <div className={`w-full ${className}`}>
      {/* 进度指示器 */}
      {showProgress && (
        <div className="mb-8">
          {/* 进度条 */}
          <div className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full mb-6">
            <div
              className="absolute top-0 left-0 h-full bg-primary-500 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
          
          {/* 步骤指示器 */}
          <div className="flex justify-between relative">
            {steps.map((step, index) => (
              <div
                key={step.id}
                className="flex flex-col items-center relative z-10"
                style={{ width: `${100 / steps.length}%` }}
              >
                {/* 连接线 */}
                {index > 0 && (
                  <div
                    className={`absolute top-4 left-0 w-full h-0.5 -translate-x-1/2 ${
                      index <= currentStep ? 'bg-primary-500' : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  />
                )}
                
                {/* 步骤圆圈 */}
                <button
                  onClick={() => handleStepClick(index)}
                  disabled={index > currentStep && !completedSteps.has(steps[index - 1].id)}
                  className={`
                    flex items-center justify-center w-8 h-8 rounded-full border-2
                    ${getStepStatusClass(step, index)}
                    transition-all duration-300
                    ${index <= currentStep || completedSteps.has(steps[index - 1]?.id)
                      ? 'cursor-pointer hover:scale-110'
                      : 'cursor-not-allowed opacity-50'
                    }
                  `}
                >
                  {getStepIcon(step, index)}
                </button>
                
                {/* 步骤标题 */}
                <div className="mt-2 text-center">
                  <div className={`text-sm font-medium ${
                    index === currentStep
                      ? 'text-primary-600 dark:text-primary-400'
                      : index < currentStep || completedSteps.has(step.id)
                      ? 'text-gray-700 dark:text-gray-300'
                      : 'text-gray-500 dark:text-gray-400'
                  }`}>
                    {step.title}
                  </div>
                  
                  {step.description && (
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {step.description}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 当前步骤内容 */}
      <Card variant="elevated" className="mb-6">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {currentStepData.title}
              </h3>
              {currentStepData.description && (
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  {currentStepData.description}
                </p>
              )}
            </div>
            
            <div className="text-sm text-gray-500">
              步骤 {currentStep + 1} / {steps.length}
            </div>
          </div>
          
          <div className="mt-6">
            {currentStepData.component}
          </div>
        </div>
      </Card>

      {/* 导航按钮 */}
      {showNavigation && (
        <div className="flex justify-between">
          <div>
            {onCancel && (
              <Button variant="outline" onClick={onCancel}>
                取消
              </Button>
            )}
          </div>
          
          <div className="flex gap-3">
            {!isFirstStep && (
              <Button variant="outline" onClick={handlePrev}>
                上一步
              </Button>
            )}
            
            <Button
              variant={isLastStep ? 'success' : 'primary'}
              onClick={handleNext}
              loading={isValidating}
              icon={isLastStep ? Check : ChevronRight}
              iconPosition="right"
            >
              {isLastStep ? '完成' : '下一步'}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

// 图标组件
const TargetIcon = () => (
  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const ScanIcon = () => (
  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
  </svg>
);

const ExploitIcon = () => (
  <Zap className="h-5 w-5" />
);

const ReportIcon = () => (
  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

// 预定义向导步骤
export const AttackWizardSteps: WizardStep[] = [
  {
    id: 'target',
    title: '目标选择',
    description: '选择要攻击的目标系统',
    icon: <TargetIcon />,
    component: (
      <div className="space-y-4">
        <p>选择您要攻击的目标系统...</p>
        {/* 这里可以添加目标选择组件 */}
      </div>
    ),
  },
  {
    id: 'scan',
    title: '漏洞扫描',
    description: '扫描目标系统的安全漏洞',
    icon: <ScanIcon />,
    component: (
      <div className="space-y-4">
        <p>正在扫描目标系统的安全漏洞...</p>
        {/* 这里可以添加扫描配置组件 */}
      </div>
    ),
  },
  {
    id: 'exploit',
    title: '漏洞利用',
    description: '利用发现的漏洞进行攻击',
    icon: <ExploitIcon />,
    component: (
      <div className="space-y-4">
        <p>正在利用发现的漏洞进行攻击...</p>
        {/* 这里可以添加漏洞利用组件 */}
      </div>
    ),
  },
  {
    id: 'report',
    title: '生成报告',
    description: '生成攻击结果报告',
    icon: <ReportIcon />,
    component: (
      <div className="space-y-4">
        <p>正在生成攻击结果报告...</p>
        {/* 这里可以添加报告生成组件 */}
      </div>
    ),
  },
];

export default Wizard;