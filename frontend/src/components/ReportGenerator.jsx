import React, { useState, useEffect } from 'react';
import {
  FileText, Download, Printer, Share2, Eye, EyeOff, Edit, 
  CheckCircle, AlertCircle, Shield, Cpu, Network, 
  Database, Globe, Lock, Calendar, User, BarChart3,
  PieChart, TrendingUp, Filter, Settings, Copy,
  ChevronDown, ChevronRight, ExternalLink, BookOpen,
  FileCode, FileJson, FileSpreadsheet,
  RefreshCw, Save, Trash2, Star, History, Clock,
  ShieldCheck, Play, Target
} from 'lucide-react';

// 导入设计系统组件
import Card from './design-system/Card';
import Button from './design-system/Button';
import Badge from './design-system/Badge';
import Alert from './design-system/Alert';

// 导入验证结果组件
import ValidationResults from './ValidationResults';

// 导入API服务
import reportService from '../services/reportService';
import attackService from '../services/attackService';
import { useScan } from '../context/ScanContext';

const ReportGenerator = () => {
  const { lastScan, selectedScan, activeTarget, scanHistory } = useScan();
  const [reportData, setReportData] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState('detailed');
  const [reportTitle, setReportTitle] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [exportFormat, setExportFormat] = useState('html');
  const [showPreview, setShowPreview] = useState(true);
  const [activeSection, setActiveSection] = useState('executive');
  const [customizations, setCustomizations] = useState({
    includeCharts: true,
    includeRecommendations: true,
    includeTechnicalDetails: true,
    includeRiskMatrix: true,
    includeTimeline: true,
    includeAttachments: false
  });

  // API相关状态
  const [reports, setReports] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [generatedReportId, setGeneratedReportId] = useState(null);

  // 扫描目标（从 context 预填）
  const [scanTarget, setScanTarget] = useState(activeTarget || '');
  const [isScanning, setIsScanning] = useState(false);
  const [scanError, setScanError] = useState(null);
  const [dataSource, setDataSource] = useState('mock'); // 'mock' | 'live'

  // 模拟报告数据
  const mockReportData = {
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
      startTime: '2026-04-06 11:30:15',
      endTime: '2026-04-06 11:45:45',
      toolsUsed: ['nmap', 'whatweb', 'nuclei', 'nikto', 'gobuster'],
      portsOpen: [22, 80, 443, 3306],
      services: [
        { port: 22, service: 'SSH', version: 'OpenSSH 8.2p1' },
        { port: 80, service: 'HTTP', version: 'Apache 2.4.41' },
        { port: 443, service: 'HTTPS', version: 'Apache 2.4.41 + OpenSSL 1.1.1' },
        { port: 3306, service: 'MySQL', version: 'MySQL 8.0.28' }
      ],
      networkInfo: {
        ip: '192.168.1.100',
        hostname: 'webserver.local',
        os: 'Ubuntu 20.04.5 LTS',
        ttl: 64
      }
    },
    
    // 建议
    recommendations: [
      '立即更新WordPress到最新版本',
      '升级PHP到8.1或更高版本',
      '配置Web应用防火墙',
      '实施严格的访问控制策略',
      '启用HTTPS强制跳转',
      '定期进行安全扫描',
      '建立安全监控和告警机制',
      '实施数据备份和恢复计划'
    ],
    
    // 风险矩阵
    riskMatrix: {
      critical: 1,
      high: 3,
      medium: 5,
      low: 8
    },
    
    // 时间线
    timeline: [
      { time: '11:30:15', event: '扫描开始', status: 'start' },
      { time: '11:32:30', event: '端口扫描完成', status: 'success' },
      { time: '11:35:45', event: '服务识别完成', status: 'success' },
      { time: '11:40:20', event: '漏洞扫描进行中', status: 'warning' },
      { time: '11:43:10', event: '发现严重漏洞', status: 'error' },
      { time: '11:45:45', event: '扫描完成', status: 'success' }
    ]
  };

  // 报告模板
  const reportTemplates = [
    {
      id: 'executive',
      name: '执行摘要报告',
      description: '面向管理层的简要报告，突出关键风险和行动建议',
      icon: <BarChart3 className="w-5 h-5" />,
      sections: ['executive', 'findings', 'recommendations'],
      length: '1-2页'
    },
    {
      id: 'detailed',
      name: '详细技术报告',
      description: '完整的技术报告，包含所有发现和详细分析',
      icon: <FileCode className="w-5 h-5" />,
      sections: ['executive', 'findings', 'vulnerabilities', 'scanDetails', 'recommendations', 'appendix'],
      length: '10-15页'
    },
    {
      id: 'compliance',
      name: '合规性报告',
      description: '针对特定合规标准（如PCI DSS、ISO 27001）的报告',
      icon: <Shield className="w-5 h-5" />,
      sections: ['executive', 'compliance', 'findings', 'recommendations'],
      length: '5-8页'
    },
    {
      id: 'custom',
      name: '自定义报告',
      description: '根据需求自定义的报告内容和格式',
      icon: <Settings className="w-5 h-5" />,
      sections: ['all'],
      length: '可变'
    }
  ];

  // 导出格式选项
  const exportFormats = [
    { id: 'html', name: 'HTML', icon: <FileText className="w-4 h-4" />, description: '交互式网页报告' },
    { id: 'pdf', name: 'PDF', icon: <FileText className="w-4 h-4" />, description: '可打印文档' },
    { id: 'json', name: 'JSON', icon: <FileJson className="w-4 h-4" />, description: '结构化数据' },
    { id: 'csv', name: 'CSV', icon: <FileSpreadsheet className="w-4 h-4" />, description: '表格数据' }
  ];

  // 执行真实攻击扫描，获取报告数据
  const runLiveScan = async () => {
    if (!scanTarget.trim()) {
      setScanError('请输入目标 IP 或域名');
      return;
    }
    setIsScanning(true);
    setScanError(null);
    try {
      const result = await attackService.runAttack(scanTarget, {
        useReal: false,
        ruleEngineMode: true,
      });
      // 与 mock 数据合并，确保缺失字段不崩溃
      const mock = reportService.getMockReportData();
      setReportData({ ...mock, ...result });
      setReportTitle(result.title || mock.title);
      setDataSource('live');
    } catch (err) {
      console.error('扫描失败:', err);
      setScanError(`扫描失败: ${err.message}`);
    } finally {
      setIsScanning(false);
    }
  };

  // 获取报告列表
  const fetchReports = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await reportService.getReports({ page: 1, pageSize: 10 });
      setReports(response.reports || []);

      // 如果有报告，使用第一个报告作为预览
      if (response.reports && response.reports.length > 0) {
        const firstReport = response.reports[0];
        setReportTitle(firstReport.title);
        // 可以在这里获取报告详情，或使用模拟数据预览
        setReportData(reportService.getMockReportData());
      } else {
        // 没有报告时使用模拟数据
        setReportData(reportService.getMockReportData());
        setReportTitle(reportService.getMockReportData().title);
      }
    } catch (err) {
      console.error('获取报告列表失败:', err);
      setError(err.message);
      // 失败时使用模拟数据
      setReportData(reportService.getMockReportData());
      setReportTitle(reportService.getMockReportData().title);
    } finally {
      setIsLoading(false);
    }
  };

  // ScanContext：selectedScan / lastScan 变化时自动用真实数据填充报告
  useEffect(() => {
    const source = selectedScan || lastScan;
    if (source) {
      const mock = reportService.getMockReportData();
      setReportData({ ...mock, ...source });
      setReportTitle(
        source.title ||
        `安全评估报告 - ${activeTarget || source.target || mock.target}`
      );
      setDataSource('live');
    }
  }, [selectedScan, lastScan, activeTarget]);

  useEffect(() => {
    fetchReports();
  }, []);

  const generateReport = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      // 准备报告数据
      const reportData = {
        title: reportTitle || '安全评估报告',
        description: '使用ClawAI生成的安全评估报告',
        format: exportFormat === 'pdf' ? 'pdf' : 'html',
        template: selectedTemplate,
        target: '192.168.1.100', // 可以从表单获取
        parameters: {
          includeCharts: customizations.includeCharts,
          includeRecommendations: customizations.includeRecommendations,
          includeTechnicalDetails: customizations.includeTechnicalDetails,
          includeRiskMatrix: customizations.includeRiskMatrix,
          includeTimeline: customizations.includeTimeline
        }
      };

      // 调用API生成报告
      const response = await reportService.createReport(reportData);

      setGeneratedReportId(response.id);

      // 显示成功消息
      alert(`报告生成成功！报告ID: ${response.id}。报告正在后台生成中。`);

      // 刷新报告列表
      fetchReports();

    } catch (err) {
      console.error('生成报告失败:', err);
      setError(`生成报告失败: ${err.message}`);
      alert(`报告生成失败: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const exportReport = async () => {
    const formatName = exportFormats.find(f => f.id === exportFormat)?.name;

    try {
      if (generatedReportId) {
        // 下载已生成的报告
        alert(`正在下载${formatName}格式的报告...`);
        const blob = await reportService.downloadReport(generatedReportId, exportFormat);

        // 创建下载链接
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report_${generatedReportId}.${exportFormat}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        alert(`报告已成功下载为${formatName}格式！`);
      } else {
        // 如果没有已生成的报告，提示先生成报告
        alert('请先生成报告，然后再导出。');
      }
    } catch (err) {
      console.error('导出报告失败:', err);
      alert(`导出报告失败: ${err.message}`);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'bg-red-500/100 text-white',
      high: 'bg-orange-500 text-white',
      medium: 'bg-yellow-500/100 text-gray-100',
      low: 'bg-green-500/100 text-white',
      informational: 'bg-blue-500/100 text-white'
    };
    return colors[severity] || 'bg-[#111827]0 text-white';
  };

  const getSeverityIcon = (severity) => {
    const icons = {
      critical: <AlertCircle className="w-5 h-5" />,
      high: <AlertCircle className="w-5 h-5" />,
      medium: <AlertCircle className="w-5 h-5" />,
      low: <CheckCircle className="w-5 h-5" />,
      informational: <CheckCircle className="w-5 h-5" />
    };
    return icons[severity] || <CheckCircle className="w-5 h-5" />;
  };

  const toggleCustomization = (key) => {
    setCustomizations(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const TemplateCard = ({ template }) => {
    const isSelected = selectedTemplate === template.id;
    
    return (
      <div 
        className={`p-4 rounded-xl border cursor-pointer transition-all ${
          isSelected 
            ? 'border-blue-500 bg-blue-500/100/10' 
            : 'border-white/10 hover:border-white/15 hover:bg-[#0a0e17]/40'
        }`}
        onClick={() => setSelectedTemplate(template.id)}
      >
        <div className="flex items-start mb-3">
          <div className={`p-2 rounded-lg mr-3 ${
            isSelected ? 'bg-blue-500/100/20 text-blue-400' : 'bg-[#111827] text-gray-400'
          }`}>
            {template.icon}
          </div>
          <div className="flex-1">
            <h3 className="font-semibold">{template.name}</h3>
            <p className="text-sm text-gray-400 mt-1">{template.description}</p>
          </div>
          {isSelected && (
            <CheckCircle className="w-5 h-5 text-green-500 ml-2" />
          )}
        </div>
        <div className="flex justify-between text-xs text-gray-500">
          <span>包含: {template.sections.length}个部分</span>
          <span>{template.length}</span>
        </div>
      </div>
    );
  };

  const FormatOption = ({ format }) => {
    const isSelected = exportFormat === format.id;
    
    return (
      <div 
        className={`p-3 rounded-lg border cursor-pointer flex items-center ${
          isSelected 
            ? 'border-blue-500 bg-blue-500/100/10' 
            : 'border-white/10 hover:border-white/15'
        }`}
        onClick={() => setExportFormat(format.id)}
      >
        <div className={`p-2 rounded mr-3 ${
          isSelected ? 'bg-blue-500/100/20 text-blue-400' : 'bg-[#111827] text-gray-400'
        }`}>
          {format.icon}
        </div>
        <div>
          <div className="font-medium">{format.name}</div>
          <div className="text-xs text-gray-400">{format.description}</div>
        </div>
        {isSelected && (
          <CheckCircle className="w-4 h-4 text-green-500 ml-auto" />
        )}
      </div>
    );
  };

  const SectionButton = ({ id, label, icon: Icon }) => {
    const isActive = activeSection === id;
    
    return (
      <button
        onClick={() => setActiveSection(id)}
        className={`flex items-center px-4 py-3 rounded-lg transition-colors ${
          isActive 
            ? 'bg-blue-500/100 text-white' 
            : 'hover:bg-[#111827]/50 text-gray-400'
        }`}
      >
        <Icon className="w-5 h-5 mr-3" />
        <span>{label}</span>
      </button>
    );
  };

  if (!reportData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-400">加载报告数据...</p>
        </div>
      </div>
    );
  }

  // 实时扫描输入面板（渲染在报告配置卡上方）
  const LiveScanPanel = () => (
    <div className="bg-[#0a0e17]/70 border border-blue-700/40 rounded-xl p-5 mb-6">
      <div className="flex items-center gap-2 mb-3">
        <Target className="w-5 h-5 text-blue-400" />
        <h3 className="font-semibold text-blue-300">接入真实攻击 API</h3>
        {dataSource === 'live' && (
          <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-green-700 text-green-100">实时数据</span>
        )}
        {dataSource === 'mock' && (
          <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-[#1a2035] text-gray-300">演示数据</span>
        )}
      </div>
      <div className="flex gap-3">
        <input
          type="text"
          value={scanTarget}
          onChange={e => setScanTarget(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && runLiveScan()}
          placeholder="例如: example.com 或 192.168.1.100"
          className="flex-1 px-4 py-2.5 bg-[#060910] border border-white/15 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-500"
          disabled={isScanning}
        />
        <Button
          variant="primary"
          onClick={runLiveScan}
          loading={isScanning}
          disabled={isScanning}
          className="flex items-center whitespace-nowrap"
        >
          <Play className="w-4 h-4 mr-1.5" />
          {isScanning ? '扫描中...' : '开始扫描'}
        </Button>
      </div>
      {isScanning && (
        <div className="mt-3 flex items-center gap-2 text-sm text-blue-400">
          <RefreshCw className="w-4 h-4 animate-spin" />
          正在执行安全评估，请稍候（可能需要 1-3 分钟）…
        </div>
      )}
      {scanError && (
        <div className="mt-3 flex items-center gap-2 text-sm text-red-400 bg-red-900/20 px-3 py-2 rounded-lg">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {scanError}
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-[#060910] text-white">
      {/* 报告生成器头部 */}
      <div className="bg-[#0a0e17]/85 backdrop-blur-sm border-b border-white/10 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">可视化报告系统</h1>
              <p className="text-gray-400 mt-1">生成专业的安全评估报告</p>
            </div>
            
            <div className="flex items-center space-x-3 mt-4 md:mt-0">
              <Button
                variant="outline"
                onClick={() => setShowPreview(!showPreview)}
                className="flex items-center"
              >
                {showPreview ? <Eye className="w-4 h-4 mr-2" /> : <EyeOff className="w-4 h-4 mr-2" />}
                {showPreview ? '隐藏预览' : '显示预览'}
              </Button>
              
              <Button
                variant="primary"
                onClick={generateReport}
                loading={isGenerating}
                className="flex items-center"
              >
                <FileText className="w-4 h-4 mr-2" />
                {isGenerating ? '生成中...' : '生成报告'}
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 左侧：报告配置 */}
          <div className="lg:col-span-2">
            <LiveScanPanel />
            {/* 报告基本信息 */}
            <Card className="mb-8">
              <div className="flex items-center mb-6">
                <FileText className="w-6 h-6 text-blue-400 mr-2" />
                <h2 className="text-xl font-semibold">报告配置</h2>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-2">报告标题</label>
                  <input
                    type="text"
                    value={reportTitle}
                    onChange={(e) => setReportTitle(e.target.value)}
                    className="w-full px-4 py-3 bg-[#0a0e17] border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="输入报告标题"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-3">选择报告模板</label>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {reportTemplates.map(template => (
                      <TemplateCard key={template.id} template={template} />
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-3">自定义报告内容</label>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {Object.entries(customizations).map(([key, value]) => {
                      const labelMap = {
                        includeCharts: '包含图表',
                        includeRecommendations: '包含建议',
                        includeTechnicalDetails: '包含技术细节',
                        includeRiskMatrix: '包含风险矩阵',
                        includeTimeline: '包含时间线',
                        includeAttachments: '包含附件'
                      };
                      
                      return (
                        <div 
                          key={key}
                          className={`p-3 rounded-lg border cursor-pointer flex items-center ${
                            value ? 'border-green-500 bg-green-500/100/10' : 'border-white/10 hover:border-white/15'
                          }`}
                          onClick={() => toggleCustomization(key)}
                        >
                          <div className={`w-5 h-5 rounded border mr-3 flex items-center justify-center ${
                            value ? 'bg-green-500/100 border-green-500' : 'border-white/15'
                          }`}>
                            {value && <CheckCircle className="w-3 h-3 text-white" />}
                          </div>
                          <div>
                            <div className="font-medium text-sm">{labelMap[key] || key}</div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-3">导出格式</label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {exportFormats.map(format => (
                      <FormatOption key={format.id} format={format} />
                    ))}
                  </div>
                </div>
              </div>
            </Card>

            {/* 报告预览 */}
            {showPreview && (
              <Card>
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center">
                    <Eye className="w-6 h-6 text-blue-400 mr-2" />
                    <h2 className="text-xl font-semibold">报告预览</h2>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={exportReport}
                      className="flex items-center"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      导出报告
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="flex items-center"
                    >
                      <Printer className="w-4 h-4 mr-2" />
                      打印
                    </Button>
                  </div>
                </div>

                {/* 报告预览内容 */}
                <div className="bg-[#0d1117] text-gray-100 rounded-lg p-8">
                  {/* 报告头部 */}
                  <div className="border-b pb-6 mb-6">
                    <div className="flex justify-between items-start">
                      <div>
                        <h1 className="text-3xl font-bold mb-2">{reportTitle}</h1>
                        <div className="flex items-center space-x-4 text-gray-400">
                          <div className="flex items-center">
                            <Calendar className="w-4 h-4 mr-2" />
                            <span>{reportData.date}</span>
                          </div>
                          <div className="flex items-center">
                            <Clock className="w-4 h-4 mr-2" />
                            <span>扫描时长: {reportData.duration}</span>
                          </div>
                          <div className="flex items-center">
                            <Shield className="w-4 h-4 mr-2" />
                            <span>风险等级: <span className="font-semibold text-red-600">{reportData.severity}</span></span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-500">报告ID</div>
                        <div className="font-mono font-bold">{reportData.id}</div>
                        <Badge variant="success" className="mt-2">已完成</Badge>
                      </div>
                    </div>
                  </div>

                  {/* 执行摘要 */}
                  <div className="mb-8">
                    <h2 className="text-2xl font-bold mb-4 border-b pb-2">执行摘要</h2>
                    <div className="bg-blue-500/10 p-4 rounded-lg mb-4">
                      <p className="text-lg">{reportData.executiveSummary.overview}</p>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                      <div className="bg-[#111827] p-4 rounded-lg">
                        <div className="text-sm text-gray-400 mb-1">风险等级</div>
                        <div className="text-2xl font-bold text-red-600">{reportData.executiveSummary.riskLevel}</div>
                      </div>
                      <div className="bg-[#111827] p-4 rounded-lg">
                        <div className="text-sm text-gray-400 mb-1">置信度</div>
                        <div className="text-2xl font-bold text-blue-600">{reportData.executiveSummary.confidence}</div>
                      </div>
                      <div className="bg-[#111827] p-4 rounded-lg">
                        <div className="text-sm text-gray-400 mb-1">建议数量</div>
                        <div className="text-2xl font-bold text-green-600">{reportData.executiveSummary.recommendationsCount}</div>
                      </div>
                    </div>
                  </div>

                  {/* 发现统计 */}
                  {customizations.includeCharts && (
                    <div className="mb-8">
                      <h2 className="text-2xl font-bold mb-4 border-b pb-2">发现统计</h2>
                      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
                        <div className="text-center p-4 bg-red-500/10 rounded-lg">
                          <div className="text-3xl font-bold text-red-600">{reportData.findings.critical}</div>
                          <div className="text-sm text-gray-400">严重</div>
                        </div>
                        <div className="text-center p-4 bg-orange-50 rounded-lg">
                          <div className="text-3xl font-bold text-orange-600">{reportData.findings.high}</div>
                          <div className="text-sm text-gray-400">高危</div>
                        </div>
                        <div className="text-center p-4 bg-yellow-500/10 rounded-lg">
                          <div className="text-3xl font-bold text-yellow-600">{reportData.findings.medium}</div>
                          <div className="text-sm text-gray-400">中危</div>
                        </div>
                        <div className="text-center p-4 bg-green-500/10 rounded-lg">
                          <div className="text-3xl font-bold text-green-600">{reportData.findings.low}</div>
                          <div className="text-sm text-gray-400">低危</div>
                        </div>
                        <div className="text-center p-4 bg-blue-500/10 rounded-lg">
                          <div className="text-3xl font-bold text-blue-600">{reportData.findings.informational}</div>
                          <div className="text-sm text-gray-400">信息</div>
                        </div>
                        <div className="text-center p-4 bg-[#111827] rounded-lg">
                          <div className="text-3xl font-bold text-gray-400">{reportData.findings.total}</div>
                          <div className="text-sm text-gray-400">总计</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 漏洞详情 */}
                  {customizations.includeTechnicalDetails && (
                    <div className="mb-8">
                      <h2 className="text-2xl font-bold mb-4 border-b pb-2">漏洞详情</h2>
                      <div className="space-y-4">
                        {(reportData.vulnerabilities || []).map((vuln, index) => (
                          <div key={vuln.id} className="border rounded-lg p-4">
                            <div className="flex justify-between items-start mb-3">
                              <div>
                                <div className="flex items-center mb-2">
                                  <span className={`px-3 py-1 rounded-full text-sm font-medium mr-3 ${getSeverityColor(vuln.severity)}`}>
                                    {vuln.severity.toUpperCase()}
                                  </span>
                                  <h3 className="text-lg font-semibold">{vuln.title}</h3>
                                </div>
                                <div className="text-sm text-gray-400 mb-2">CVSS评分: <span className="font-bold">{vuln.cvssScore}</span></div>
                              </div>
                              <Badge variant="info">ID: {vuln.id}</Badge>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                              <div>
                                <h4 className="font-medium mb-1">描述</h4>
                                <p className="text-sm">{vuln.description}</p>
                              </div>
                              <div>
                                <h4 className="font-medium mb-1">影响</h4>
                                <p className="text-sm">{vuln.impact}</p>
                              </div>
                            </div>
                            
                            <div className="mb-4">
                              <h4 className="font-medium mb-1">修复建议</h4>
                              <p className="text-sm bg-green-500/10 p-3 rounded">{vuln.remediation}</p>
                            </div>
                            
                            <div className="flex flex-wrap gap-2">
                              <div className="text-xs">
                                <span className="font-medium">受影响组件: </span>
                                {(vuln.affectedComponents || []).join(', ')}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 建议 */}
                  {customizations.includeRecommendations && (
                    <div className="mb-8">
                      <h2 className="text-2xl font-bold mb-4 border-b pb-2">安全建议</h2>
                      <div className="space-y-3">
                        {(reportData.recommendations || []).map((rec, index) => {
                          // rec 可能是字符串或对象
                          const isObj = rec && typeof rec === 'object';
                          const title = isObj ? (rec.title || rec.description || JSON.stringify(rec)) : rec;
                          const description = isObj ? rec.description : null;
                          const steps = isObj && Array.isArray(rec.steps) ? rec.steps : [];
                          const priority = isObj ? rec.priority : null;
                          const priorityColor = { critical: 'text-red-600', high: 'text-orange-500', medium: 'text-yellow-600', low: 'text-green-600' }[priority] || 'text-gray-400';
                          return (
                            <div key={index} className="p-3 bg-blue-500/10 rounded-lg">
                              <div className="flex items-start">
                                <CheckCircle className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <span className="font-medium">{title}</span>
                                    {priority && <span className={`text-xs font-semibold uppercase ${priorityColor}`}>[{priority}]</span>}
                                  </div>
                                  {description && title !== description && (
                                    <p className="text-sm text-gray-400 mt-1">{description}</p>
                                  )}
                                  {steps.length > 0 && (
                                    <ol className="mt-2 space-y-0.5 list-decimal list-inside text-sm text-gray-400">
                                      {steps.map((step, i) => <li key={i}>{step}</li>)}
                                    </ol>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* 验证结果 */}
                  {(reportData.verified_findings?.length > 0 || reportData.unverified_findings?.length > 0) && (
                    <div className="mb-8">
                      <div className="flex items-center gap-2 mb-4 border-b pb-2">
                        <ShieldCheck className="w-6 h-6 text-green-600" />
                        <h2 className="text-2xl font-bold">漏洞验证结果</h2>
                        <span className="ml-2 px-2.5 py-0.5 text-xs font-bold rounded-full bg-green-600 text-white">
                          AI 实际验证
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 mb-4">
                        以下结果由 VulnValidatorAgent 通过真实 Payload 注入验证，区分确认漏洞与疑似漏洞。
                      </p>
                      <ValidationResults
                        verifiedFindings={reportData.verified_findings || []}
                        unverifiedFindings={reportData.unverified_findings || []}
                      />
                    </div>
                  )}

                  {/* 报告底部 */}
                  <div className="border-t pt-6 mt-8">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="text-sm text-gray-400">生成时间</div>
                        <div className="font-medium">{new Date().toLocaleString('zh-CN')}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-400">ClawAI Security Platform</div>
                        <div className="font-medium">企业级安全评估工具</div>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            )}
          </div>

          {/* 右侧：报告管理和操作 */}
          <div className="space-y-8">
            {/* 报告操作 */}
            <Card>
              <div className="flex items-center mb-6">
                <Settings className="w-6 h-6 text-blue-400 mr-2" />
                <h2 className="text-xl font-semibold">报告操作</h2>
              </div>

              <div className="space-y-3">
                <Button
                  variant="primary"
                  fullWidth
                  onClick={generateReport}
                  loading={isGenerating}
                  className="flex items-center justify-center"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  {isGenerating ? '生成中...' : '生成报告'}
                </Button>

                <Button
                  variant="outline"
                  fullWidth
                  onClick={exportReport}
                  className="flex items-center justify-center"
                >
                  <Download className="w-4 h-4 mr-2" />
                  导出报告 ({exportFormats.find(f => f.id === exportFormat)?.name})
                </Button>

                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant="ghost"
                    fullWidth
                    className="flex items-center justify-center"
                  >
                    <Share2 className="w-4 h-4 mr-2" />
                    分享
                  </Button>
                  <Button
                    variant="ghost"
                    fullWidth
                    className="flex items-center justify-center"
                  >
                    <Copy className="w-4 h-4 mr-2" />
                    复制
                  </Button>
                </div>

                <div className="pt-4 border-t border-white/10">
                  <h3 className="font-medium mb-3">快速操作</h3>
                  <div className="space-y-2">
                    <button className="w-full text-left p-3 rounded-lg hover:bg-[#111827]/50 flex items-center justify-between">
                      <div className="flex items-center">
                        <History className="w-4 h-4 mr-3 opacity-70" />
                        <span>查看历史报告</span>
                      </div>
                      <ChevronRight className="w-4 h-4 opacity-50" />
                    </button>
                    <button className="w-full text-left p-3 rounded-lg hover:bg-[#111827]/50 flex items-center justify-between">
                      <div className="flex items-center">
                        <Star className="w-4 h-4 mr-3 opacity-70" />
                        <span>保存为模板</span>
                      </div>
                      <ChevronRight className="w-4 h-4 opacity-50" />
                    </button>
                    <button className="w-full text-left p-3 rounded-lg hover:bg-[#111827]/50 flex items-center justify-between">
                      <div className="flex items-center">
                        <Trash2 className="w-4 h-4 mr-3 opacity-70" />
                        <span>删除草稿</span>
                      </div>
                      <ChevronRight className="w-4 h-4 opacity-50" />
                    </button>
                  </div>
                </div>
              </div>
            </Card>

            {/* 报告信息 */}
            <Card>
              <div className="flex items-center mb-6">
                <BookOpen className="w-6 h-6 text-green-400 mr-2" />
                <h2 className="text-xl font-semibold">报告信息</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <div className="text-sm text-gray-400 mb-1">目标</div>
                  <div className="font-medium">{reportData.target}</div>
                </div>
                
                <div>
                  <div className="text-sm text-gray-400 mb-1">扫描时间</div>
                  <div className="font-medium">{reportData.scanDetails?.startTime} - {reportData.scanDetails?.endTime}</div>
                </div>
                
                <div>
                  <div className="text-sm text-gray-400 mb-1">使用工具</div>
                  <div className="flex flex-wrap gap-1">
                    {(reportData.scanDetails?.toolsUsed || []).map((tool, index) => (
                      <Badge key={index} variant="info" size="sm">{tool}</Badge>
                    ))}
                  </div>
                </div>
                
                <div>
                  <div className="text-sm text-gray-400 mb-1">开放端口</div>
                  <div className="flex flex-wrap gap-1">
                    {(reportData.scanDetails?.portsOpen || []).map((port, index) => (
                      <Badge key={index} variant="outline" size="sm">{port}</Badge>
                    ))}
                  </div>
                </div>
                
                <div>
                  <div className="text-sm text-gray-400 mb-1">操作系统</div>
                  <div className="font-medium">{reportData.scanDetails?.networkInfo?.os}</div>
                </div>
              </div>
            </Card>

            {/* 报告历史 */}
            <Card>
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <History className="w-6 h-6 text-purple-400 mr-2" />
                  <h2 className="text-xl font-semibold">最近报告</h2>
                </div>
                <Badge variant="info" size="sm">3个</Badge>
              </div>

              <div className="space-y-3">
                {[
                  { id: 'REP-2026-04-05-001', title: '日常安全扫描', date: '2026-04-05', findings: 12, severity: 'medium' },
                  { id: 'REP-2026-04-04-001', title: '渗透测试报告', date: '2026-04-04', findings: 28, severity: 'high' },
                  { id: 'REP-2026-04-03-001', title: '漏洞验证报告', date: '2026-04-03', findings: 5, severity: 'low' }
                ].map((report) => (
                  <div key={report.id} className="p-3 rounded-lg bg-[#0a0e17]/40 hover:bg-[#0a0e17]/60 cursor-pointer">
                    <div className="flex justify-between items-start mb-2">
                      <div className="font-medium text-sm">{report.title}</div>
                      <Badge variant={report.severity === 'high' ? 'danger' : report.severity === 'medium' ? 'warning' : 'success'} size="sm">
                        {report.severity}
                      </Badge>
                    </div>
                    <div className="flex justify-between text-xs text-gray-400">
                      <span>{report.date}</span>
                      <span>{report.findings} 个发现</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </div>

      {/* 底部信息栏 */}
      <div className="mt-12 py-6 border-t border-white/8">
        <div className="container mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="mb-4 md:mb-0">
              <div className="flex items-center space-x-2">
                <Shield className="w-5 h-5 text-blue-500" />
                <span className="font-medium">ClawAI 报告系统</span>
              </div>
              <div className="text-sm text-gray-400 mt-1">
                版本 2.0 | 专业安全评估报告生成工具
              </div>
            </div>
            <div className="flex items-center space-x-4 text-sm">
              <span className="text-gray-400">状态: <span className="text-green-500">● 报告系统正常</span></span>
              <button className="text-blue-400 hover:text-blue-300">
                帮助文档
              </button>
              <button className="text-blue-400 hover:text-blue-300">
                反馈问题
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportGenerator;
