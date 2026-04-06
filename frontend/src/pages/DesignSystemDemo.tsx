import React, { useState } from 'react';
import {
  Button,
  Card,
  CardTitle,
  CardContent,
  CardFooter,
  Input,
  Badge,
  Alert,
} from '../components/design-system';
import ThemeToggle from '../components/design-system/ThemeToggle';
import {
  Search,
  User,
  Mail,
  Lock,
  Check,
  AlertCircle,
  Info,
  Star,
  Download,
  Upload,
  Settings,
  Bell,
  Home,
} from 'lucide-react';

const DesignSystemDemo: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showAlert, setShowAlert] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    alert(`表单提交: ${email}, ${password}`);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* 头部 */}
        <header className="mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                ClawAI 设计系统
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                统一的设计语言和组件库，确保产品体验一致性
              </p>
            </div>
            <ThemeToggle showLabel size="md" />
          </div>
        </header>

        {/* 主要内容 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 左侧导航 */}
          <div className="lg:col-span-1">
            <Card variant="elevated" hoverable>
              <CardTitle>设计系统导航</CardTitle>
              <CardContent>
                <nav className="space-y-2">
                  {['颜色', '字体', '间距', '按钮', '表单', '卡片', '徽章', '提示', '主题'].map(
                    (item) => (
                      <a
                        key={item}
                        href={`#${item}`}
                        className="block px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                      >
                        {item}
                      </a>
                    )
                  )}
                </nav>
              </CardContent>
            </Card>

            {/* 设计原则 */}
            <Card className="mt-6" variant="elevated">
              <CardTitle>设计原则</CardTitle>
              <CardContent>
                <ul className="space-y-3">
                  <li className="flex items-start">
                    <Check className="h-5 w-5 text-success-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700 dark:text-gray-300">
                      <strong>一致性：</strong>统一的视觉语言和交互模式
                    </span>
                  </li>
                  <li className="flex items-start">
                    <Check className="h-5 w-5 text-success-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700 dark:text-gray-300">
                      <strong>可用性：</strong>直观易用，降低学习成本
                    </span>
                  </li>
                  <li className="flex items-start">
                    <Check className="h-5 w-5 text-success-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700 dark:text-gray-300">
                      <strong>可访问性：</strong>支持所有用户，包括残障人士
                    </span>
                  </li>
                  <li className="flex items-start">
                    <Check className="h-5 w-5 text-success-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700 dark:text-gray-300">
                      <strong>响应式：</strong>适配所有设备和屏幕尺寸
                    </span>
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* 右侧内容 */}
          <div className="lg:col-span-2 space-y-8">
            {/* 按钮示例 */}
            <section id="按钮">
              <Card variant="elevated">
                <CardTitle>按钮组件</CardTitle>
                <CardContent>
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                        按钮变体
                      </h3>
                      <div className="flex flex-wrap gap-3">
                        <Button variant="primary">主要按钮</Button>
                        <Button variant="secondary">次要按钮</Button>
                        <Button variant="outline">轮廓按钮</Button>
                        <Button variant="ghost">幽灵按钮</Button>
                        <Button variant="success">成功按钮</Button>
                        <Button variant="warning">警告按钮</Button>
                        <Button variant="error">错误按钮</Button>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                        按钮大小
                      </h3>
                      <div className="flex flex-wrap items-center gap-3">
                        <Button size="sm">小按钮</Button>
                        <Button size="md">中按钮</Button>
                        <Button size="lg">大按钮</Button>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                        带图标按钮
                      </h3>
                      <div className="flex flex-wrap gap-3">
                        <Button icon={Download} iconPosition="left">
                          下载
                        </Button>
                        <Button icon={Upload} iconPosition="right">
                          上传
                        </Button>
                        <Button icon={Settings} variant="outline" />
                        <Button icon={Bell} variant="ghost" />
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                        状态按钮
                      </h3>
                      <div className="flex flex-wrap gap-3">
                        <Button loading>加载中</Button>
                        <Button disabled>已禁用</Button>
                        <Button fullWidth>全宽按钮</Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </section>

            {/* 表单示例 */}
            <section id="表单">
              <Card variant="elevated">
                <CardTitle>表单组件</CardTitle>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <Input
                        label="用户名"
                        placeholder="请输入用户名"
                        icon={User}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        required
                      />
                      <Input
                        label="邮箱地址"
                        type="email"
                        placeholder="user@example.com"
                        icon={Mail}
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        helperText="请输入有效的邮箱地址"
                      />
                    </div>

                    <Input
                      label="密码"
                      type="password"
                      placeholder="请输入密码"
                      icon={Lock}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      error={password.length > 0 && password.length < 6 ? '密码长度至少6位' : ''}
                    />

                    <Input
                      label="搜索"
                      placeholder="搜索..."
                      icon={Search}
                      iconPosition="right"
                    />

                    <div className="flex gap-3">
                      <Button type="submit" variant="primary">
                        提交表单
                      </Button>
                      <Button type="button" variant="outline">
                        重置
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            </section>

            {/* 卡片和徽章示例 */}
            <section id="卡片">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card variant="elevated" hoverable>
                  <CardTitle>用户卡片</CardTitle>
                  <CardContent>
                    <div className="flex items-center gap-4">
                      <div className="h-12 w-12 rounded-full bg-primary-100 flex items-center justify-center">
                        <User className="h-6 w-6 text-primary-600" />
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white">
                          张三
                        </h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          高级安全工程师
                        </p>
                        <div className="flex gap-2 mt-2">
                          <Badge variant="primary">管理员</Badge>
                          <Badge variant="success">在线</Badge>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                  <CardFooter align="right">
                    <Button size="sm" variant="outline">
                      查看详情
                    </Button>
                  </CardFooter>
                </Card>

                <Card variant="elevated" hoverable>
                  <CardTitle>任务卡片</CardTitle>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-gray-900 dark:text-white">
                          漏洞扫描
                        </span>
                        <Badge variant="warning">进行中</Badge>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        对目标系统进行全面的安全漏洞扫描
                      </p>
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <Star className="h-4 w-4" />
                        <span>高优先级</span>
                      </div>
                    </div>
                  </CardContent>
                  <CardFooter>
                    <div className="flex justify-between items-center w-full">
                      <span className="text-sm text-gray-500">进度: 65%</span>
                      <Button size="sm" variant="primary">
                        继续
                      </Button>
                    </div>
                  </CardFooter>
                </Card>
              </div>
            </section>

            {/* 徽章示例 */}
            <section id="徽章">
              <Card variant="elevated">
                <CardTitle>徽章组件</CardTitle>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                        徽章变体
                      </h3>
                      <div className="flex flex-wrap gap-3">
                        <Badge variant="primary">主要</Badge>
                        <Badge variant="secondary">次要</Badge>
                        <Badge variant="success">成功</Badge>
                        <Badge variant="warning">警告</Badge>
                        <Badge variant="error">错误</Badge>
                        <Badge variant="info">信息</Badge>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                        徽章大小
                      </h3>
                      <div className="flex flex-wrap items-center gap-3">
                        <Badge size="sm">小徽章</Badge>
                        <Badge size="md">中徽章</Badge>
                        <Badge size="lg">大徽章</Badge>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                        带图标徽章
                      </h3>
                      <div className="flex flex-wrap gap-3">
                        <Badge icon={Star} variant="warning">
                          推荐
                        </Badge>
                        <Badge icon={Check} variant="success">
                          已验证
                        </Badge>
                        <Badge icon={AlertCircle} variant="error">
                          错误
                        </Badge>
                        <Badge icon={Info} variant="info">
                          信息
                        </Badge>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </section>

            {/* 提示示例 */}
            <section id="提示">
              <Card variant="elevated">
                <CardTitle>提示组件</CardTitle>
                <CardContent>
                  <div className="space-y-4">
                    {showAlert && (
                      <Alert
                        variant="info"
                        title="信息提示"
                        dismissible
                        onDismiss={() => setShowAlert(false)}
                      >
                        这是一个信息提示，用于向用户传达重要信息。
                      </Alert>
                    )}

                    <Alert variant="success" title="操作成功">
                      您的操作已成功完成！系统已保存所有更改。
                    </Alert>

                    <Alert variant="warning" title="警告提示">
                      请注意：此操作可能会影响系统性能，请谨慎操作。
                    </Alert>

                    <Alert variant="error" title="错误提示">
                      操作失败：系统遇到未知错误，请稍后重试。
                    </Alert>

                    <Alert variant="info">
                      这是一个没有标题的简单信息提示。
                    </Alert>
                  </div>
                </CardContent>
              </Card>
            </section>

            {/* 设计系统信息 */}
            <section>
              <Card variant="elevated">
                <CardTitle>设计系统信息</CardTitle>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary-600">24+</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">组件</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-success-600">100%</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">可访问性</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-warning-600">3</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">主题模式</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-error-600">5+</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">颜色系统</div>
                      </div>
                    </div>

                    <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                      <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                        设计系统特点
                      </h4>
                      <ul className="space-y-2 text-gray-600 dark:text-gray-400">
                        <li className="flex items-center">
                          <Check className="h-4 w-4 text-success-500 mr-2" />
                          基于Tailwind CSS，高度可定制
                        </li>
                        <li className="flex items-center">
                          <Check className="h-4 w-4 text-success-500 mr-2" />
                          完全TypeScript支持，类型安全
                        </li>
                        <li className="flex items-center">
                          <Check className="h-4 w-4 text-success-500 mr-2" />
                          响应式设计，适配所有设备
                        </li>
                        <li className="flex items-center">
                          <Check className="h-4 w-4 text-success-500 mr-2" />
                          暗黑模式支持，保护用户视力
                        </li>
                        <li className="flex items-center">
                          <Check className="h-4 w-4 text-success-500 mr-2" />
                          WCAG 2.1 AA标准，无障碍访问
                        </li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
                <CardFooter align="center">
                  <Button variant="primary" icon={Download}>
                    下载设计系统文档
                  </Button>
                </CardFooter>
              </Card>
            </section>
          </div>
        </div>

        {/* 页脚 */}
        <footer className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-800">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-center md:text-left">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                ClawAI 设计系统
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                版本 1.0.0 · 最后更新: 2024年3月
              </p>
            </div>
            <div className="flex gap-4">
              <Button variant="ghost" size="sm" icon={Home}>
                首页
              </Button>
              <Button variant="ghost" size="sm" icon={Info}>
                文档
              </Button>
              <Button variant="ghost" size="sm" icon={Settings}>
                设置
              </Button>
            </div>
          </div>
          <p className="text-center text-gray-500 dark:text-gray-400 text-sm mt-6">
            © 2024 ClawAI. 保留所有权利。设计系统仅供内部使用。
          </p>
        </footer>
      </div>
    </div>
  );
};

export default DesignSystemDemo;