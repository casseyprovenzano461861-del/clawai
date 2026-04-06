# ClawAI 设计系统规范

## 🎨 设计原则

### 1. 用户为中心
- **直观性**：界面直观，用户无需培训即可使用
- **效率**：操作流程简洁，减少不必要的步骤
- **反馈**：所有操作都有明确的反馈
- **容错**：允许用户犯错并提供恢复路径

### 2. 一致性
- **视觉一致**：统一的颜色、字体、间距
- **交互一致**：相似的操作有相似的行为
- **术语一致**：使用统一的术语和文案
- **模式一致**：重复使用已验证的设计模式

### 3. 可访问性
- **对比度**：确保足够的颜色对比度
- **键盘导航**：支持完整的键盘操作
- **屏幕阅读器**：提供适当的ARIA标签
- **响应式**：适配不同屏幕尺寸和设备

## 🎨 颜色系统

### 主色板
| 颜色 | 变量名 | HEX值 | 使用场景 |
|------|--------|-------|----------|
| 主蓝 | `--color-primary` | `#3B82F6` | 主要按钮、重要操作 |
| 深蓝 | `--color-primary-dark` | `#1D4ED8` | 悬停状态、激活状态 |
| 浅蓝 | `--color-primary-light` | `#93C5FD` | 背景、次要元素 |

### 语义色
| 颜色 | 变量名 | HEX值 | 使用场景 |
|------|--------|-------|----------|
| 成功 | `--color-success` | `#10B981` | 成功状态、完成操作 |
| 警告 | `--color-warning` | `#F59E0B` | 警告信息、注意提示 |
| 错误 | `--color-error` | `#EF4444` | 错误状态、危险操作 |
| 信息 | `--color-info` | `#3B82F6` | 信息提示、说明文字 |

### 中性色
| 颜色 | 变量名 | HEX值 | 使用场景 |
|------|--------|-------|----------|
| 黑 | `--color-black` | `#111827` | 主要文字、标题 |
| 深灰 | `--color-gray-800` | `#1F2937` | 次要文字、边框 |
| 中灰 | `--color-gray-600` | `#4B5563` | 辅助文字、图标 |
| 浅灰 | `--color-gray-300` | `#D1D5DB` | 边框、分隔线 |
| 白灰 | `--color-gray-100` | `#F3F4F6` | 背景、卡片背景 |
| 白 | `--color-white` | `#FFFFFF` | 背景、文字反色 |

### 主题配置
```css
/* 深色主题 */
:root[data-theme="dark"] {
  --color-bg-primary: #111827;
  --color-bg-secondary: #1F2937;
  --color-text-primary: #F9FAFB;
  --color-text-secondary: #D1D5DB;
}

/* 浅色主题 */
:root[data-theme="light"] {
  --color-bg-primary: #FFFFFF;
  --color-bg-secondary: #F9FAFB;
  --color-text-primary: #111827;
  --color-text-secondary: #4B5563;
}
```

## 🔤 字体系统

### 字体家族
- **主要字体**：Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
- **等宽字体**：'SF Mono', Monaco, 'Cascadia Code', 'Courier New', monospace

### 字号规范
| 名称 | 大小 | 行高 | 字重 | 使用场景 |
|------|------|------|------|----------|
| 超大标题 | 48px | 56px | 700 | 页面主标题 |
| 大标题 | 36px | 44px | 700 | 章节标题 |
| 标题 | 24px | 32px | 600 | 卡片标题 |
| 副标题 | 20px | 28px | 600 | 次要标题 |
| 正文大 | 18px | 28px | 400 | 主要正文 |
| 正文 | 16px | 24px | 400 | 常规正文 |
| 正文小 | 14px | 20px | 400 | 辅助文字 |
| 标注 | 12px | 16px | 400 | 标签、说明 |

### 响应式字体
```css
/* 基础字体大小 */
html {
  font-size: 16px;
}

/* 小屏幕 */
@media (max-width: 640px) {
  html {
    font-size: 14px;
  }
}

/* 大屏幕 */
@media (min-width: 1536px) {
  html {
    font-size: 18px;
  }
}
```

## 📏 间距系统

### 间距比例（4px基数）
| 名称 | 大小 | 使用场景 |
|------|------|----------|
| xs | 4px | 元素内边距、微小间距 |
| sm | 8px | 图标与文字间距、小间距 |
| md | 16px | 常规间距、卡片内边距 |
| lg | 24px | 组件间距、区块间距 |
| xl | 32px | 大间距、章节间距 |
| 2xl | 48px | 超大间距、页面间距 |
| 3xl | 64px | 特大间距、页面边距 |

### 布局网格
```css
/* 容器 */
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 1rem;
}

/* 网格系统 */
.grid {
  display: grid;
  gap: 1rem; /* 16px */
}

/* 响应式断点 */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
@media (min-width: 1536px) { /* 2xl */ }
```

## 🧩 组件规范

### 按钮组件
```jsx
// 按钮变体
const ButtonVariants = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700',
  secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
  success: 'bg-green-600 text-white hover:bg-green-700',
  danger: 'bg-red-600 text-white hover:bg-red-700',
  outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50',
  ghost: 'text-gray-700 hover:bg-gray-100'
};

// 按钮大小
const ButtonSizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg'
};
```

### 卡片组件
```jsx
// 卡片基础样式
const CardBase = 'rounded-lg border border-gray-200 bg-white shadow-sm';

// 卡片变体
const CardVariants = {
  default: CardBase,
  elevated: 'rounded-lg border border-gray-200 bg-white shadow-lg',
  flat: 'rounded-lg border border-gray-200 bg-white',
  ghost: 'rounded-lg bg-transparent'
};
```

### 表单组件
```jsx
// 输入框基础样式
const InputBase = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent';

// 输入框状态
const InputStates = {
  default: InputBase,
  error: 'border-red-500 focus:ring-red-500',
  success: 'border-green-500 focus:ring-green-500',
  disabled: 'bg-gray-100 cursor-not-allowed'
};
```

## 🎭 交互状态

### 悬停状态
```css
/* 基础悬停 */
.hover-lift {
  transition: transform 0.2s ease;
}
.hover-lift:hover {
  transform: translateY(-2px);
}

/* 颜色悬停 */
.hover-color {
  transition: background-color 0.2s ease, color 0.2s ease;
}
```

### 激活状态
```css
/* 按钮激活 */
.btn:active {
  transform: scale(0.98);
}

/* 链接激活 */
.link:active {
  color: var(--color-primary-dark);
}
```

### 禁用状态
```css
/* 禁用元素 */
.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}
```

### 加载状态
```css
/* 加载动画 */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading {
  animation: spin 1s linear infinite;
}
```

## 🎬 动画规范

### 持续时间
| 名称 | 时间 | 使用场景 |
|------|------|----------|
| 快速 | 150ms | 悬停、点击反馈 |
| 常规 | 300ms | 页面过渡、模态框 |
| 慢速 | 500ms | 复杂动画、强调效果 |

### 缓动函数
| 名称 | 函数 | 使用场景 |
|------|------|----------|
| 线性 | `linear` | 进度条、加载动画 |
| 缓入 | `ease-in` | 元素进入 |
| 缓出 | `ease-out` | 元素退出 |
| 缓入缓出 | `ease-in-out` | 页面过渡 |

### 动画示例
```css
/* 淡入淡出 */
.fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 滑动进入 */
.slide-in {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
```

## 📱 响应式设计

### 断点系统
| 名称 | 最小宽度 | 使用场景 |
|------|----------|----------|
| xs | 0px | 手机（竖屏） |
| sm | 640px | 手机（横屏）、小平板 |
| md | 768px | 平板、小笔记本 |
| lg | 1024px | 笔记本、桌面 |
| xl | 1280px | 大桌面 |
| 2xl | 1536px | 超大桌面 |

### 响应式实用类
```css
/* 隐藏/显示 */
.hidden-xs { display: none; }
@media (min-width: 640px) { .hidden-xs { display: block; } }

/* 布局调整 */
.flex-col { flex-direction: column; }
@media (min-width: 768px) { .flex-col-md { flex-direction: row; } }

/* 间距调整 */
.m-2 { margin: 0.5rem; }
@media (min-width: 1024px) { .m-lg-4 { margin: 1rem; } }
```

## 🎯 可访问性

### 键盘导航
```css
/* 焦点样式 */
:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* 跳过导航链接 */
.skip-nav {
  position: absolute;
  top: -40px;
  left: 0;
  background: var(--color-primary);
  color: white;
  padding: 8px;
  z-index: 100;
}
.skip-nav:focus {
  top: 0;
}
```

### ARIA属性
```jsx
// 按钮ARIA
<button
  aria-label="关闭对话框"
  aria-expanded={isOpen}
  aria-controls="dialog-content"
>
  关闭
</button>

// 进度指示器
<div
  role="progressbar"
  aria-valuenow={progress}
  aria-valuemin="0"
  aria-valuemax="100"
>
  {progress}%
</div>
```

### 屏幕阅读器
```css
/* 仅屏幕阅读器可见 */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

## 📋 设计令牌

### CSS变量定义
```css
:root {
  /* 颜色 */
  --color-primary: #3B82F6;
  --color-primary-dark: #1D4ED8;
  --color-primary-light: #93C5FD;
  
  /* 间距 */
  --spacing-xs: 0.25rem;  /* 4px */
  --spacing-sm: 0.5rem;   /* 8px */
  --spacing-md: 1rem;     /* 16px */
  --spacing-lg: 1.5rem;   /* 24px */
  --spacing-xl: 2rem;     /* 32px */
  
  /* 字体 */
  --font-size-sm: 0.875rem;  /* 14px */
  --font-size-base: 1rem;    /* 16px */
  --font-size-lg: 1.125rem;  /* 18px */
  --font-size-xl: 1.25rem;   /* 20px */
  
  /* 圆角 */
  --radius-sm: 0.25rem;  /* 4px */
  --radius-md: 0.375rem; /* 6px */
  --radius-lg: 0.5rem;   /* 8px */
  --radius-xl: 0.75rem;  /* 12px */
  
  /* 阴影 */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}
```

## 📚 使用指南

### 1. 颜色使用
```jsx
// 正确：使用语义化颜色
<button className="bg-primary text-white">主要按钮</button>

// 错误：直接使用颜色值
<button className="bg-[#3B82F6] text-white">主要按钮</button>
```

### 2. 间距使用
```jsx
// 正确：使用间距系统
<div className="p-4"> {/* 16px内边距 */}
  <div className="mb-2"> {/* 8px下边距 */}
    内容
  </div>
</div>

// 错误：硬编码间距
<div className="p-[16px]">
  <div className="mb-[8px]">
    内容
  </div>
</div>
```

### 3. 组件使用
```jsx
// 正确：使用组件库
<Button variant="primary" size="md">
  提交
</Button>

// 错误：重复编写样式
<button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
  提交
</button>
```

## 🔧 工具和资源

### 设计工具
- **Figma**：界面设计和原型
- **Storybook**：组件文档和测试
- **Tailwind CSS**：样式框架
- **Lucide React**：图标库

### 开发工具
- **ESLint**：代码质量检查
- **Prettier**：代码格式化
- **Stylelint**：CSS代码检查
- **Husky**：Git钩子

### 测试工具
- **Jest**：单元测试
- **React Testing Library**：组件测试
- **Cypress**：端到端测试
- **Lighthouse**：性能测试

---

**设计系统版本**: v1.0  
**更新日期**: 2024年3月  
**维护团队**: 前端开发团队

**备注**: 本设计系统将根据项目发展和用户反馈持续更新和优化。