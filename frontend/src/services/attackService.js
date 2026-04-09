/**
 * attackService.js
 * 封装 POST /attack 调用，将后端响应规范化为前端统一消费格式。
 *
 * 后端基础 URL: http://localhost:8000  (非 /api/v1，attack 挂在根路径)
 * 后端响应字段: attack_chain, target_analysis, rule_engine_decision, execution_mode …
 *
 * 本服务额外做两件事：
 *  1. normalizeToReportData()  — 把 attack 响应转成 ReportGenerator 期望的 reportData 形状
 *  2. extractValidationFindings() — 从 attack_chain 提取 verified / unverified findings
 *     供 ValidationResults 组件消费（后端目前不单独返回这两个字段，由前端派生）
 */

import axios from 'axios';

// 攻击接口直接挂在后端根路径，不走 /api/v1
const ATTACK_BASE = import.meta.env.VITE_ATTACK_BASE || 'http://localhost:8001';

// 创建专用 axios 实例（超时放长，攻击可能耗时 2-5 分钟）
const attackClient = axios.create({
  baseURL: ATTACK_BASE,
  timeout: 360000, // 6 分钟
  headers: { 'Content-Type': 'application/json' },
});

// 注入 Bearer token（与 apiClient 保持一致）
attackClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ─────────────────────────────────────────────────────────────────────────────
// 核心工具函数
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 把 attack_chain 步骤提炼为 verified_findings / unverified_findings
 * 规则：
 *   - severity=critical/high  且 success=true  且 highlight=true  → verified
 *   - severity=critical/high  且 (success=false || highlight=false) → unverified
 *   - 其余步骤忽略（reconnaissance / info 级别不产生验证结果）
 */
function extractValidationFindings(attackChain = [], target = '') {
  const verified = [];
  const unverified = [];

  for (const step of attackChain) {
    const sev = (step.severity || '').toLowerCase();
    if (sev !== 'critical' && sev !== 'high') continue;

    const isVerified = step.success === true && step.highlight === true;
    const finding = {
      vuln_type: guessVulnType(step.tool, step.title, step.description),
      target: step.details?.url || target,
      confidence: isVerified
        ? (sev === 'critical' ? 0.92 : 0.78)
        : (sev === 'critical' ? 0.55 : 0.38),
      evidence: buildEvidence(step),
      exploit_proof: step.details?.payload
        ? `Tool: ${step.tool}\n${step.details.payload}`
        : step.description || '',
      suggested_next: step.details?.suggested_next || suggestNext(step.tool),
      raw_findings: step.details ? [step.details] : [],
      // 未验证字段
      description: step.description,
      error: step.success === false ? `工具 ${step.tool} 执行失败` : undefined,
    };

    if (isVerified) {
      verified.push(finding);
    } else {
      unverified.push(finding);
    }
  }

  return { verified_findings: verified, unverified_findings: unverified };
}

function guessVulnType(tool = '', title = '', desc = '') {
  const text = `${tool} ${title} ${desc}`.toLowerCase();
  if (text.includes('sql')) return 'sqli';
  if (text.includes('xss') || text.includes('cross-site scripting')) return 'xss';
  if (text.includes('rce') || text.includes('remote code')) return 'rce';
  if (text.includes('lfi') || text.includes('local file')) return 'lfi';
  if (text.includes('ssrf')) return 'ssrf';
  if (text.includes('xxe')) return 'xxe';
  if (text.includes('ssti')) return 'ssti';
  if (text.includes('auth') || text.includes('bypass')) return 'auth_bypass';
  if (text.includes('inject')) return 'injection';
  return tool || 'unknown';
}

function buildEvidence(step) {
  const parts = [];
  if (step.tool) parts.push(`工具: ${step.tool}`);
  if (step.duration) parts.push(`耗时: ${step.duration}`);
  if (step.details?.payload) parts.push(`Payload: ${step.details.payload}`);
  if (step.details?.response_time) parts.push(`响应延迟: ${step.details.response_time}`);
  if (step.description) parts.push(step.description);
  return parts;
}

function suggestNext(tool = '') {
  const map = {
    sqlmap: '尝试 sqlmap --dump 获取数据库内容，或 --os-shell 获取系统权限。',
    nikto: '对发现的路径做目录爆破，使用 gobuster/dirsearch 进一步枚举。',
    nuclei: '根据 CVE 编号查找 PoC，验证是否可利用并评估修复优先级。',
    nmap: '对开放端口的服务做版本探测，识别已知漏洞版本。',
    wpscan: '枚举 WordPress 用户名、插件漏洞，尝试暴力破解弱密码账户。',
    gobuster: '对发现的隐藏路径做进一步探测，寻找上传接口或管理后台。',
  };
  return map[tool.toLowerCase()] || '对发现的漏洞进行人工确认，评估实际可利用性。';
}

/**
 * 将 /attack 响应转换为 ReportGenerator 期望的 reportData 形状
 * 同时注入 verified_findings / unverified_findings
 */
function normalizeToReportData(response, target) {
  const chain = response.attack_chain || [];
  const analysis = response.target_analysis || {};
  const { verified_findings, unverified_findings } = extractValidationFindings(chain, target);

  // 从 attack_chain 提取漏洞列表
  const vulnerabilities = chain
    .filter(s => s.severity === 'critical' || s.severity === 'high')
    .map((s, i) => ({
      id: `VULN-${String(i + 1).padStart(3, '0')}`,
      title: s.title || `${s.tool} 发现漏洞`,
      severity: s.severity || 'medium',
      cvssScore: s.severity === 'critical' ? 9.0 : s.severity === 'high' ? 7.5 : 5.0,
      description: s.description || '',
      impact: s.details?.impact || '攻击者可能利用此漏洞获取未授权访问。',
      remediation: s.details?.remediation || '请参考安全建议进行修复。',
      affectedComponents: s.details?.affected ? [s.details.affected] : [target],
      references: s.details?.cve ? [s.details.cve] : [],
    }));

  const severity = verified_findings.some(f => f.vuln_type !== 'unknown')
    ? 'high'
    : 'medium';

  return {
    id: `REP-${new Date().toISOString().split('T')[0].replace(/-/g, '')}-${String(Math.floor(Math.random() * 999)).padStart(3, '0')}`,
    title: `安全评估报告 - ${target}`,
    target,
    date: new Date().toLocaleDateString('zh-CN'),
    duration: response.execution_time || '未知',
    status: 'completed',
    severity,
    executiveSummary: {
      overview: `本次对 ${target} 的安全评估共执行 ${chain.length} 个攻击步骤，发现 ${verified_findings.length} 个已验证漏洞，${unverified_findings.length} 个疑似漏洞。执行模式: ${response.execution_mode || '未知'}。`,
      riskLevel: severity === 'high' ? '高' : '中',
      confidence: verified_findings.length > 0
        ? `${Math.round(verified_findings.reduce((s, f) => s + f.confidence, 0) / verified_findings.length * 100)}%`
        : '—',
      recommendationsCount: Math.max(vulnerabilities.length, 3),
    },
    findings: {
      critical: chain.filter(s => s.severity === 'critical').length,
      high: chain.filter(s => s.severity === 'high').length,
      medium: chain.filter(s => s.severity === 'medium').length,
      low: chain.filter(s => s.severity === 'low').length,
      informational: chain.filter(s => !s.severity || s.severity === 'info').length,
      total: chain.length,
    },
    vulnerabilities,
    scanDetails: {
      startTime: response.timestamp || new Date().toISOString(),
      endTime: new Date().toISOString(),
      toolsUsed: [...new Set(chain.map(s => s.tool).filter(Boolean))],
      portsOpen: analysis.open_ports ? [analysis.open_ports] : [],
      networkInfo: {
        ip: target,
        hostname: target,
        os: analysis.os || '未知',
        ttl: 64,
      },
    },
    recommendations: buildRecommendations(vulnerabilities, response),
    riskMatrix: {
      critical: chain.filter(s => s.severity === 'critical').length,
      high: chain.filter(s => s.severity === 'high').length,
      medium: chain.filter(s => s.severity === 'medium').length,
      low: chain.filter(s => s.severity === 'low').length,
    },
    timeline: chain.map((s, i) => ({
      time: `Step ${i + 1}`,
      event: s.title || s.tool,
      status: s.success ? 'success' : 'error',
    })),

    // ── 验证结果（新字段）──
    verified_findings,
    unverified_findings,
    verified_count: verified_findings.length,
    unverified_count: unverified_findings.length,

    // 原始响应保留（调试用）
    _raw: response,
  };
}

function buildRecommendations(vulns, response) {
  const recs = new Set();
  for (const v of vulns) {
    if (v.remediation) recs.add(v.remediation);
  }
  // 通用建议
  recs.add('配置 Web 应用防火墙 (WAF)，拦截常见注入攻击。');
  recs.add('定期更新所有组件和依赖到最新安全版本。');
  recs.add('启用 HTTPS 强制跳转，禁用不安全的 TLS 版本。');
  recs.add('建立安全监控和告警机制，实时检测异常访问。');
  return [...recs].slice(0, 8);
}

// ─────────────────────────────────────────────────────────────────────────────
// 公开 API
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 执行攻击扫描，返回规范化 reportData
 *
 * @param {string} target         目标 URL / IP
 * @param {object} options
 * @param {boolean} options.useReal        是否真实执行（默认 false = 模拟）
 * @param {boolean} options.ruleEngineMode 是否启用规则引擎（默认 true）
 * @param {number}  options.timeout        后端超时秒数（默认 300）
 * @param {function} options.onRaw         可选回调，接收原始响应
 * @returns {Promise<object>}  规范化 reportData
 */
export async function runAttack(target, options = {}) {
  const {
    useReal = false,
    ruleEngineMode = true,
    timeout = 300,
    onRaw,
  } = options;

  const payload = {
    target: target.trim(),
    use_real: useReal,
    rule_engine_mode: ruleEngineMode,
    timeout,
  };

  const response = await attackClient.post('/attack', payload);
  const raw = response.data;
  if (onRaw) onRaw(raw);

  return normalizeToReportData(raw, target.trim());
}

/**
 * 只做提取，不发请求 — 用于把已有的 attackData（来自 Dashboard）转换为验证结果
 *
 * @param {object} attackData   Dashboard 的 attackData 状态
 * @returns {{ verified_findings: [], unverified_findings: [] }}
 */
export function extractFindings(attackData) {
  if (!attackData) return { verified_findings: [], unverified_findings: [] };
  // 如果后端直接返回了这两个字段，优先使用
  if (attackData.verified_findings || attackData.unverified_findings) {
    return {
      verified_findings: attackData.verified_findings || [],
      unverified_findings: attackData.unverified_findings || [],
    };
  }
  return extractValidationFindings(attackData.attack_chain || [], attackData.target || '');
}

const attackService = { runAttack, extractFindings, normalizeToReportData };
export default attackService;
