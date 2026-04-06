import React from 'react';
import { 
  CheckCircle, 
  Clock, 
  TrendingUp, 
  Users, 
  Zap, 
  Code, 
  Palette,
  Cpu,
  Shield,
  Target,
  BarChart3,
  GitBranch,
  Cloud,
  Database,
  Lock,
  Globe,
  Smartphone,
  Monitor
} from 'lucide-react';
import { Card, CardTitle, CardContent, CardFooter } from '../components/design-system/Card';
import { Button } from '../components/design-system/Button';
import PerformanceMonitor from '../components/design-system/PerformanceMonitor';
import ImplementationTracker from '../components/design-system/ImplementationTracker';

const ImplementationSummary: React.FC = () => {
  const features = [
    {
      icon: Palette,
      title: '设计系统',
      description: '统一的设计语言和组件库',
      status: '已完成',
      progress: 85,
      color: 'primary',
    },
    {
      icon: Cpu,
      title: '性能优化',
      description: '前端性能提升和优化',
      status: '进行中',
      progress: 40,
      color: 'warning',
    },
    {
      icon: Shield,
      title: '安全加固',
      description: '安全漏洞修复和防护',
      status: '待开始',
      progress: 10,
      color: 'error',
    },
    {
      icon: Target,
      title: '用户体验',
      description: '交互流程优化和体验提升',
      status: '进行中',
      progress: 60,
      color: 'success',
    },
    {
      icon: BarChart3,
      title: '数据分析',
      description: '数据可视化和分析功能',
      status: '规划中',
      progress: 5,
      color: 'info',
    },
    {
      icon: GitBranch,
      title: 'CI/CD',
      description: '持续集成和部署流程',
      status: '待开始',
      progress: 15,
      color: 'secondary',
    },
  ];

  const teamMembers = [
    { name: '张三', role: '前端负责人', avatar: '张', tasks: 12, completed: 10 },
    { name: '李四', role: 'UI设计师', avatar: '李', tasks: 8, completed: 7 },
    { name: '王五', role: '后端工程师', avatar: '王', tasks: 15, completed: 9 },
    { name: '赵六', role: '测试工程师', avatar: '赵', tasks: 10, completed: 8 },
  ];

  const technologies = [
    { name: 'React', version: '18.2.0', category: '前端框架' },
    { name: 'TypeScript', version: '5.0.0', category: '开发语言' },
    { name: 'Tailwind CSS', version: '3.4.0', category: '样式框架' },
    { name: 'Vite', version: '5.0.10', category: '构建工具' },
    { name: 'Flask', version: '3.0.0', category: '后端框架' },
    { name: 'Python', version: '3.11', category: '后端语言' },
    { name: 'MySQL', version: '8.0', category: '数据库' },
    { name: 'Docker', version: '24.0', category: '容器化' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* 头部 */}
        <header className="mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                ClawAI 实施进度总结
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                短期实施计划（1-2个月）进度跟踪和总结
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-2xl font-bold text-primary-600">42%</div>
                <div className="text-sm text-gray-500">总体进度</div>
              </div>
              <Button variant="primary" icon={TrendingUp}>
                生成报告
              </Button>
            </div>
          </div>
        </header>

        {/* 主要内容 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 左侧栏 */}
          <div className="lg:col-span-2 space-y-8">
            {/* 实施跟踪器 */}
            <ImplementationTracker />

            {/* 功能模块进度 */}
            <Card variant="elevated">
              <CardTitle>功能模块进度</CardTitle>
              <CardContent>
                <div className="space-y-6">
                  {features.map((feature, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <feature.icon className={`h-5 w-5 mr-3 text-${feature.color}-500`} />
                          <div>
                            <h4 className="font-medium text-gray-900 dark:text-white">
                              {feature.title}
                            </h4>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {feature.description}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className={`font-semibold text-${feature.color}-600`}>
                            {feature.progress}%
                          </div>
                          <div className="text-sm text-gray-500">{feature.status}</div>
                        </div>
                      </div>
                      <div className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className={`absolute top-0 left-0 h-full bg-${feature.color}-500`}
                          style={{ width: `${feature.progress}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* 技术栈 */}
            <Card variant="elevated">
              <CardTitle>技术栈概览</CardTitle>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {technologies.map((tech, index) => (
                    <div
                      key={index}
                      className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg hover:shadow-md transition-shadow"
                    >
                      <div className="font-medium text-gray-900 dark:text-white">
                        {tech.name}
                      </div>
                      <div className="text-sm text-gray-500 mt-1">v{tech.version}</div>
                      <div className="text-xs text-gray-400 mt-2">{tech.category}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 右侧栏 */}
          <div className="space-y-8">
            {/* 性能监控 */}
            <PerformanceMonitor />

            {/* 团队状态 */}
            <Card variant="elevated">
              <CardTitle>团队状态</CardTitle>
              <CardContent>
                <div className="space-y-4">
                  {teamMembers.map((member, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center mr-3">
                          <span className="font-medium text-primary-600">
                            {member.avatar}
                          </span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">
                            {member.name}
                          </div>
                          <div className="text-sm text-gray-500">{member.role}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium text-gray-900 dark:text-white">
                          {member.completed}/{member.tasks}
                        </div>
                        <div className="text-sm text-gray-500">任务</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
              <CardFooter>
                <div className="w-full">
                  <div className="flex justify-between text-sm text-gray-500 mb-2">
                    <span>团队效率</span>
                    <span>85%</span>
                  </div>
                  <div className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="absolute top-0 left-0 h-full bg-success-500"
                      style={{ width: '85%' }}
                    />
                  </div>
                </div>
              </CardFooter>
            </Card>

            {/* 关键指标 */}
            <Card variant="elevated">
              <CardTitle>关键指标</CardTitle>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Code className="h-5 w-5 text-gray-400 mr-3" />
                      <span className="text-gray-700 dark:text-gray-300">代码行数</span>
                    </div>
                    <span className="font-semibold">24,568</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <CheckCircle className="h-5 w-5 text-gray-400 mr-3" />
                      <span className="text-gray-700 dark:text-gray-300">测试覆盖率</span>
                    </div>
                    <span className="font-semibold text-success-600">78%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Zap className="h-5 w-5 text-gray-400 mr-3" />
                      <span className="text-gray-700 dark:text-gray-300">构建时间</span>
                    </div>
                    <span className="font-semibold">2.4s</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Users className="h-5 w-5 text-gray-400 mr-3" />
                      <span className="text-gray-700 dark:text-gray-300">活跃贡献者</span>
                    </div>
                    <span className="font-semibold">8</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 下一步计划 */}
            <Card variant="elevated">
              <CardTitle>下一步计划</CardTitle>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-start">
                    <Clock className="h-4 w-4 text-warning-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      完成设计系统组件库
                    </span>
                  </div>
                  <div className="flex items-start">
                    <Clock className="h-4 w-4 text-warning-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      优化攻击执行流程
                    </span>
                  </div>
                  <div className="flex items-start">
                    <Clock className="h-4 w-4 text-warning-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      实施前端性能优化
                    </span>
                  </div>
                  <div className="flex items-start">
                    <Clock className="h-4 w-4 text-warning-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      建立监控和告警系统
                    </span>
                  </div>
                </div>
              </CardContent>
              <CardFooter>
                <Button variant="outline" fullWidth>
                  查看详细计划
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>

        {/* 实施成果 */}
        <div className="mt-8">
          <Card variant="elevated">
            <CardTitle>实施成果</CardTitle>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-primary-100 mb-3">
                    <Globe className="h-6 w-6 text-primary-600" />
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">100%</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">响应式支持</div>
                </div>
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-success-100 mb-3">
                    <Smartphone className="h-6 w-6 text-success-600" />
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">3x</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">移动端性能提升</div>
                </div>
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-warning-100 mb-3">
                    <Monitor className="h-6 w-6 text-warning-600" />
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">50%</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">加载时间减少</div>
                </div>
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-error-100 mb-3">
                    <Lock className="h-6 w-6 text-error-600" />
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">0</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">安全漏洞</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 页脚 */}
        <footer className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-800">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                ClawAI 短期实施计划
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                版本 1.0.0 · 预计完成: 2024年4月
              </p>
            </div>
            <div className="flex gap-4">
              <Button variant="ghost" size="sm">
                导出报告
              </Button>
              <Button variant="primary" size="sm">
                分享进度
              </Button>
            </div>
          </div>
          <p className="text-center text-gray-500 dark:text-gray-400 text-sm mt-6">
            © 2024 ClawAI. 实施进度报告自动生成，数据更新于 {new Date().toLocaleDateString('zh-CN')}
          </p>
        </footer>
      </div>
    </div>
  );
};

export default ImplementationSummary;