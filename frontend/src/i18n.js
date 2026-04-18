import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// 语言资源
const resources = {
  en: {
    translation: {
      // 导航
      nav: {
        dashboard: 'Dashboard',
        tools: 'Tools',
        scans: 'Scans',
        reports: 'Reports',
        settings: 'Settings',
        help: 'Help'
      },
      // 仪表盘
      dashboard: {
        title: 'ClawAI Dashboard',
        overview: 'Overview',
        recentScans: 'Recent Scans',
        vulnerabilityStats: 'Vulnerability Statistics',
        systemStatus: 'System Status',
        quickActions: 'Quick Actions',
        autoPentest: 'Auto Pentest',
        fullIATesting: 'Full IA Testing',
        vulnLab: 'Vuln Lab',
        terminal: 'Terminal',
        totalScans: 'Total Scans',
        running: 'Running',
        completed: 'Completed',
        totalVulns: 'Total Vulns',
        critical: 'Critical',
        high: 'High',
        scanStatus: 'Scan Status',
        vulnerabilitySeverity: 'Vulnerability Severity',
        activityFeed: 'Activity Feed'
      },
      // 扫描
      scan: {
        title: 'New Scan',
        target: 'Target',
        scanType: 'Scan Type',
        startScan: 'Start Scan',
        pentestGPT: 'AI Engine',
        traditional: 'Traditional',
        scanOptions: 'Scan Options',
        targetPlaceholder: 'Enter target IP or domain',
        scanTypePlaceholder: 'Select scan type',
        scanHistory: 'Scan History',
        scanResults: 'Scan Results',
        scanDetails: 'Scan Details',
        scanTime: 'Scan Time',
        status: 'Status',
        actions: 'Actions',
        viewReport: 'View Report',
        rescan: 'Rescan',
        delete: 'Delete'
      },
      // 工具
      tools: {
        title: 'Tools',
        availableTools: 'Available Tools',
        toolCategories: 'Tool Categories',
        toolName: 'Tool Name',
        description: 'Description',
        category: 'Category',
        status: 'Status',
        version: 'Version',
        execute: 'Execute',
        toolExecution: 'Tool Execution',
        parameters: 'Parameters',
        executeTool: 'Execute Tool',
        executionResult: 'Execution Result',
        running: 'Running',
        success: 'Success',
        failed: 'Failed'
      },
      // 报告
      reports: {
        title: 'Reports',
        recentReports: 'Recent Reports',
        reportDetails: 'Report Details',
        target: 'Target',
        scanDate: 'Scan Date',
        vulnerabilities: 'Vulnerabilities',
        download: 'Download',
        share: 'Share',
        delete: 'Delete'
      },
      // 设置
      settings: {
        title: 'Settings',
        general: 'General',
        apiKeys: 'API Keys',
        language: 'Language',
        theme: 'Theme',
        notifications: 'Notifications',
        save: 'Save',
        cancel: 'Cancel',
        darkMode: 'Dark Mode',
        lightMode: 'Light Mode',
        english: 'English',
        chinese: 'Chinese',
        apiKeyPlaceholder: 'Enter API key',
        saveSuccess: 'Settings saved successfully',
        saveFailed: 'Failed to save settings'
      },
      // 帮助
      help: {
        title: 'Help',
        documentation: 'Documentation',
        faq: 'FAQ',
        contact: 'Contact Support',
        about: 'About ClawAI'
      },
      // 通用
      common: {
        loading: 'Loading...',
        error: 'Error',
        success: 'Success',
        warning: 'Warning',
        info: 'Information',
        confirm: 'Confirm',
        cancel: 'Cancel',
        close: 'Close',
        search: 'Search',
        filter: 'Filter',
        sort: 'Sort',
        export: 'Export',
        import: 'Import',
        refresh: 'Refresh',
        clear: 'Clear',
        back: 'Back',
        next: 'Next',
        previous: 'Previous',
        first: 'First',
        last: 'Last',
        page: 'Page',
        of: 'of',
        itemsPerPage: 'Items per page',
        noData: 'No data available',
        noResults: 'No results found',
        pleaseWait: 'Please wait...',
        somethingWentWrong: 'Something went wrong',
        tryAgain: 'Try again',
        welcome: 'Welcome to ClawAI',
        login: 'Login',
        logout: 'Logout',
        register: 'Register',
        username: 'Username',
        password: 'Password',
        email: 'Email',
        submit: 'Submit',
        reset: 'Reset',
        forgotPassword: 'Forgot password?',
        rememberMe: 'Remember me',
        createAccount: 'Create account',
        alreadyHaveAccount: 'Already have an account?',
        confirmPassword: 'Confirm password'
      },
      // 漏洞
      vulnerability: {
        critical: 'Critical',
        high: 'High',
        medium: 'Medium',
        low: 'Low',
        info: 'Info',
        title: 'Title',
        description: 'Description',
        severity: 'Severity',
        cvss: 'CVSS Score',
        cve: 'CVE ID',
        affectedSystems: 'Affected Systems',
        remediation: 'Remediation',
        references: 'References',
        discoveredBy: 'Discovered By',
        discoveredDate: 'Discovered Date',
        status: 'Status',
        open: 'Open',
        fixed: 'Fixed',
        falsePositive: 'False Positive',
        inProgress: 'In Progress'
      },
      // 扫描状态
      scanStatus: {
        pending: 'Pending',
        running: 'Running',
        completed: 'Completed',
        failed: 'Failed',
        canceled: 'Canceled'
      }
    }
  },
  zh: {
    translation: {
      // 导航
      nav: {
        dashboard: '仪表盘',
        tools: '工具',
        scans: '扫描',
        reports: '报告',
        settings: '设置',
        help: '帮助'
      },
      // 仪表盘
      dashboard: {
        title: 'ClawAI 仪表盘',
        overview: '概览',
        recentScans: '最近扫描',
        vulnerabilityStats: '漏洞统计',
        systemStatus: '系统状态',
        quickActions: '快速操作',
        autoPentest: '自动渗透测试',
        fullIATesting: '完整安全测试',
        vulnLab: '漏洞实验室',
        terminal: '终端',
        totalScans: '总扫描数',
        running: '运行中',
        completed: '已完成',
        totalVulns: '总漏洞数',
        critical: '严重',
        high: '高',
        scanStatus: '扫描状态',
        vulnerabilitySeverity: '漏洞严重程度',
        activityFeed: '活动馈送'
      },
      // 扫描
      scan: {
        title: '新扫描',
        target: '目标',
        scanType: '扫描类型',
        startScan: '开始扫描',
        pentestGPT: 'AI Engine',
        traditional: '传统扫描',
        scanOptions: '扫描选项',
        targetPlaceholder: '输入目标IP或域名',
        scanTypePlaceholder: '选择扫描类型',
        scanHistory: '扫描历史',
        scanResults: '扫描结果',
        scanDetails: '扫描详情',
        scanTime: '扫描时间',
        status: '状态',
        actions: '操作',
        viewReport: '查看报告',
        rescan: '重新扫描',
        delete: '删除'
      },
      // 工具
      tools: {
        title: '工具',
        availableTools: '可用工具',
        toolCategories: '工具类别',
        toolName: '工具名称',
        description: '描述',
        category: '类别',
        status: '状态',
        version: '版本',
        execute: '执行',
        toolExecution: '工具执行',
        parameters: '参数',
        executeTool: '执行工具',
        executionResult: '执行结果',
        running: '运行中',
        success: '成功',
        failed: '失败'
      },
      // 报告
      reports: {
        title: '报告',
        recentReports: '最近报告',
        reportDetails: '报告详情',
        target: '目标',
        scanDate: '扫描日期',
        vulnerabilities: '漏洞',
        download: '下载',
        share: '分享',
        delete: '删除'
      },
      // 设置
      settings: {
        title: '设置',
        general: '通用',
        apiKeys: 'API密钥',
        language: '语言',
        theme: '主题',
        notifications: '通知',
        save: '保存',
        cancel: '取消',
        darkMode: '深色模式',
        lightMode: '浅色模式',
        english: '英语',
        chinese: '中文',
        apiKeyPlaceholder: '输入API密钥',
        saveSuccess: '设置保存成功',
        saveFailed: '保存设置失败'
      },
      // 帮助
      help: {
        title: '帮助',
        documentation: '文档',
        faq: '常见问题',
        contact: '联系支持',
        about: '关于ClawAI'
      },
      // 通用
      common: {
        loading: '加载中...',
        error: '错误',
        success: '成功',
        warning: '警告',
        info: '信息',
        confirm: '确认',
        cancel: '取消',
        close: '关闭',
        search: '搜索',
        filter: '筛选',
        sort: '排序',
        export: '导出',
        import: '导入',
        refresh: '刷新',
        clear: '清除',
        back: '返回',
        next: '下一步',
        previous: '上一步',
        first: '首页',
        last: '末页',
        page: '页',
        of: '共',
        itemsPerPage: '每页项目数',
        noData: '无可用数据',
        noResults: '未找到结果',
        pleaseWait: '请稍候...',
        somethingWentWrong: '出了点问题',
        tryAgain: '重试',
        welcome: '欢迎使用ClawAI',
        login: '登录',
        logout: '登出',
        register: '注册',
        username: '用户名',
        password: '密码',
        email: '邮箱',
        submit: '提交',
        reset: '重置',
        forgotPassword: '忘记密码？',
        rememberMe: '记住我',
        createAccount: '创建账户',
        alreadyHaveAccount: '已有账户？',
        confirmPassword: '确认密码'
      },
      // 漏洞
      vulnerability: {
        critical: '严重',
        high: '高',
        medium: '中',
        low: '低',
        info: '信息',
        title: '标题',
        description: '描述',
        severity: '严重程度',
        cvss: 'CVSS分数',
        cve: 'CVE ID',
        affectedSystems: '受影响系统',
        remediation: '修复建议',
        references: '参考资料',
        discoveredBy: '发现者',
        discoveredDate: '发现日期',
        status: '状态',
        open: '开放',
        fixed: '已修复',
        falsePositive: '误报',
        inProgress: '处理中'
      },
      // 扫描状态
      scanStatus: {
        pending: '待处理',
        running: '运行中',
        completed: '已完成',
        failed: '失败',
        canceled: '已取消'
      }
    }
  }
};

// 初始化i18next
i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    lng: 'zh', // 默认语言
    fallbackLng: 'en', // 回退语言
    interpolation: {
      escapeValue: false // 不转义HTML
    },
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag', 'path', 'subdomain'],
      caches: ['localStorage']
    }
  });

export default i18n;
