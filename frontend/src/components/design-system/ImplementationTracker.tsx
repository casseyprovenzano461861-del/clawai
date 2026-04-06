import React, { useState } from 'react';
import { CheckCircle, Circle, Clock, AlertCircle, TrendingUp, Users, Zap, Code } from 'lucide-react';
import { Card, CardTitle, CardContent } from './Card';
import { Badge } from './index';

interface Task {
  id: string;
  title: string;
  description: string;
  status: 'todo' | 'in-progress' | 'review' | 'done';
  priority: 'low' | 'medium' | 'high' | 'critical';
  assignee: string;
  dueDate: string;
  estimatedHours: number;
  actualHours?: number;
}

interface Milestone {
  id: string;
  title: string;
  description: string;
  dueDate: string;
  progress: number;
  tasks: Task[];
}

const ImplementationTracker: React.FC = () => {
  const [milestones, setMilestones] = useState<Milestone[]>([
    {
      id: '1',
      title: '设计系统建立',
      description: '建立统一的设计语言和组件库',
      dueDate: '2024-03-15',
      progress: 85,
      tasks: [
        {
          id: '1-1',
          title: '颜色系统设计',
          description: '定义主色板、语义色和中性色',
          status: 'done',
          priority: 'high',
          assignee: '张三',
          dueDate: '2024-03-05',
          estimatedHours: 8,
          actualHours: 7,
        },
        {
          id: '1-2',
          title: '字体和排版系统',
          description: '建立字体规范和排版层级',
          status: 'done',
          priority: 'high',
          assignee: '李四',
          dueDate: '2024-03-06',
          estimatedHours: 6,
          actualHours: 6,
        },
        {
          id: '1-3',
          title: '间距和布局系统',
          description: '定义间距比例和响应式网格',
          status: 'in-progress',
          priority: 'medium',
          assignee: '王五',
          dueDate: '2024-03-08',
          estimatedHours: 8,
          actualHours: 4,
        },
        {
          id: '1-4',
          title: '组件库优化',
          description: '统一基础组件和交互状态',
          status: 'todo',
          priority: 'high',
          assignee: '赵六',
          dueDate: '2024-03-10',
          estimatedHours: 12,
        },
      ],
    },
    {
      id: '2',
      title: '交互流程优化',
      description: '优化用户操作路径和交互体验',
      dueDate: '2024-03-22',
      progress: 40,
      tasks: [
        {
          id: '2-1',
          title: '用户流程分析',
          description: '分析当前用户操作路径和瓶颈',
          status: 'in-progress',
          priority: 'high',
          assignee: '张三',
          dueDate: '2024-03-12',
          estimatedHours: 10,
          actualHours: 6,
        },
        {
          id: '2-2',
          title: '攻击执行流程优化',
          description: '简化攻击执行步骤，实现一键式操作',
          status: 'todo',
          priority: 'critical',
          assignee: '李四',
          dueDate: '2024-03-15',
          estimatedHours: 16,
        },
      ],
    },
    {
      id: '3',
      title: '前端性能优化',
      description: '提升前端加载速度和运行性能',
      dueDate: '2024-03-29',
      progress: 20,
      tasks: [
        {
          id: '3-1',
          title: '性能分析',
          description: '使用工具分析当前性能状况',
          status: 'todo',
          priority: 'medium',
          assignee: '王五',
          dueDate: '2024-03-18',
          estimatedHours: 8,
        },
        {
          id: '3-2',
          title: '代码分割和懒加载',
          description: '优化代码打包和加载策略',
          status: 'todo',
          priority: 'high',
          assignee: '赵六',
          dueDate: '2024-03-20',
          estimatedHours: 12,
        },
      ],
    },
  ]);

  const [selectedMilestone, setSelectedMilestone] = useState<string>('1');

  // 获取状态图标
  const getStatusIcon = (status: Task['status']) => {
    switch (status) {
      case 'done':
        return <CheckCircle className="h-5 w-5 text-success-500" />;
      case 'in-progress':
        return <Clock className="h-5 w-5 text-warning-500 animate-pulse" />;
      case 'review':
        return <AlertCircle className="h-5 w-5 text-info-500" />;
      default:
        return <Circle className="h-5 w-5 text-gray-400" />;
    }
  };

  // 获取状态文本
  const getStatusText = (status: Task['status']) => {
    switch (status) {
      case 'done': return '已完成';
      case 'in-progress': return '进行中';
      case 'review': return '审核中';
      default: return '待开始';
    }
  };

  // 获取优先级徽章
  const getPriorityBadge = (priority: Task['priority']) => {
    const config = {
      low: { variant: 'secondary' as const, label: '低' },
      medium: { variant: 'info' as const, label: '中' },
      high: { variant: 'warning' as const, label: '高' },
      critical: { variant: 'error' as const, label: '紧急' },
    };
    
    return <Badge variant={config[priority].variant}>{config[priority].label}</Badge>;
  };

  // 计算总体进度
  const totalProgress = milestones.reduce((sum, milestone) => sum + milestone.progress, 0) / milestones.length;
  const completedTasks = milestones.flatMap(m => m.tasks).filter(t => t.status === 'done').length;
  const totalTasks = milestones.flatMap(m => m.tasks).length;
  const totalEstimatedHours = milestones.flatMap(m => m.tasks).reduce((sum, t) => sum + t.estimatedHours, 0);
  const totalActualHours = milestones.flatMap(m => m.tasks).filter(t => t.actualHours).reduce((sum, t) => sum + (t.actualHours || 0), 0);

  // 获取当前里程碑
  const currentMilestone = milestones.find(m => m.id === selectedMilestone);

  return (
    <div className="space-y-6">
      {/* 总体统计 */}
      <Card variant="elevated">
        <CardTitle>实施进度总览</CardTitle>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <TrendingUp className="h-8 w-8 text-primary-500 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {totalProgress.toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">总体进度</div>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <CheckCircle className="h-8 w-8 text-success-500 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {completedTasks}/{totalTasks}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">任务完成</div>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <Users className="h-8 w-8 text-warning-500 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">4</div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">团队成员</div>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <Zap className="h-8 w-8 text-error-500 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {totalActualHours}/{totalEstimatedHours}h
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">工时统计</div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 里程碑选择 */}
      <Card variant="elevated">
        <CardTitle>里程碑进度</CardTitle>
        <CardContent>
          <div className="flex flex-wrap gap-2 mb-6">
            {milestones.map((milestone) => (
              <button
                key={milestone.id}
                onClick={() => setSelectedMilestone(milestone.id)}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  selectedMilestone === milestone.id
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}
              >
                {milestone.title}
              </button>
            ))}
          </div>

          {currentMilestone && (
            <div className="space-y-4">
              {/* 里程碑信息 */}
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {currentMilestone.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mt-1">
                    {currentMilestone.description}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-primary-600">
                    {currentMilestone.progress}%
                  </div>
                  <div className="text-sm text-gray-500">截止: {currentMilestone.dueDate}</div>
                </div>
              </div>

              {/* 进度条 */}
              <div className="relative h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="absolute top-0 left-0 h-full bg-primary-500"
                  style={{ width: `${currentMilestone.progress}%` }}
                />
              </div>

              {/* 任务列表 */}
              <div className="space-y-3">
                {currentMilestone.tasks.map((task) => (
                  <div
                    key={task.id}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        {getStatusIcon(task.status)}
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="font-medium text-gray-900 dark:text-white">
                              {task.title}
                            </h4>
                            {getPriorityBadge(task.priority)}
                          </div>
                          <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">
                            {task.description}
                          </p>
                          <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                            <span>负责人: {task.assignee}</span>
                            <span>截止: {task.dueDate}</span>
                            <span>预估: {task.estimatedHours}h</span>
                            {task.actualHours && (
                              <span>实际: {task.actualHours}h</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-sm font-medium ${
                          task.status === 'done' ? 'text-success-600' :
                          task.status === 'in-progress' ? 'text-warning-600' :
                          'text-gray-500'
                        }`}>
                          {getStatusText(task.status)}
                        </div>
                        {task.actualHours && (
                          <div className={`text-xs mt-1 ${
                            task.actualHours <= task.estimatedHours
                              ? 'text-success-500'
                              : 'text-error-500'
                          }`}>
                            {task.actualHours <= task.estimatedHours ? '提前' : '超时'}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 实施建议 */}
      <Card variant="elevated">
        <CardTitle>实施建议</CardTitle>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start">
              <Code className="h-5 w-5 text-primary-500 mr-3 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">代码质量</h4>
                <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">
                  建议在开发过程中持续进行代码审查，确保代码质量和一致性。
                </p>
              </div>
            </div>
            
            <div className="flex items-start">
              <Clock className="h-5 w-5 text-warning-500 mr-3 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">时间管理</h4>
                <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">
                  高风险任务建议提前安排，留出缓冲时间应对意外情况。
                </p>
              </div>
            </div>
            
            <div className="flex items-start">
              <Users className="h-5 w-5 text-success-500 mr-3 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">团队协作</h4>
                <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">
                  建议每周召开进度同步会议，及时解决遇到的问题。
                </p>
              </div>
            </div>
            
            <div className="flex items-start">
              <AlertCircle className="h-5 w-5 text-error-500 mr-3 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">风险管理</h4>
                <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">
                  识别关键路径上的风险点，制定应急预案。
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ImplementationTracker;