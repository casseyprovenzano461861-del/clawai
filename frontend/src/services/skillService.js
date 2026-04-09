/**
 * 技能库API服务
 */
import { request } from './apiClient';
import { USE_MOCK_DATA } from './config';

// 技能类型枚举
export const SkillType = {
  SCANNING: 'scanning',
  EXPLOITATION: 'exploitation',
  POST_EXPLOITATION: 'post_exploitation',
  REPORTING: 'reporting',
  ANALYSIS: 'analysis',
  UTILITY: 'utility'
};

// 技能难度枚举
export const SkillDifficulty = {
  BEGINNER: 'beginner',
  INTERMEDIATE: 'intermediate',
  ADVANCED: 'advanced',
  EXPERT: 'expert'
};

/**
 * 获取技能列表
 * @param {Object} params - 查询参数
 * @returns {Promise} 技能列表
 */
export const getSkills = async (params = {}) => {
  try {
    return await request.get('/skills', { params });
  } catch (error) {
    if (USE_MOCK_DATA) {
      console.warn('获取技能列表API失败，使用模拟数据:', error.message);

      // 模拟技能数据
      const mockSkills = [
      {
        id: 'port-scanning',
        name: '端口扫描',
        description: '使用NMAP进行端口扫描和服务识别',
        type: SkillType.SCANNING,
        difficulty: SkillDifficulty.BEGINNER,
        tags: ['nmap', 'network', 'scanning'],
        prerequisites: ['basic-networking'],
        estimated_time: '5-10分钟',
        success_rate: 98.5,
        last_used: '2026-04-06T11:30:00Z',
        usage_count: 1245,
        tools: ['nmap', 'masscan', 'rustscan'],
        tutorial: {
          steps: [
            '安装NMAP工具',
            '运行基础扫描: nmap -sS target',
            '分析开放端口',
            '识别服务版本'
          ],
          example_command: 'nmap -sS -sV -O 192.168.1.100'
        }
      },
      {
        id: 'sql-injection',
        name: 'SQL注入测试',
        description: '检测和利用SQL注入漏洞',
        type: SkillType.EXPLOITATION,
        difficulty: SkillDifficulty.INTERMEDIATE,
        tags: ['sql', 'injection', 'web'],
        prerequisites: ['port-scanning', 'web-enumeration'],
        estimated_time: '15-30分钟',
        success_rate: 65.2,
        last_used: '2026-04-06T10:45:00Z',
        usage_count: 342,
        tools: ['sqlmap', 'burpsuite', 'havij'],
        tutorial: {
          steps: [
            '识别注入点',
            '测试注入类型',
            '使用sqlmap自动化测试',
            '提取数据库信息'
          ],
          example_command: 'sqlmap -u "http://target.com/login.php" --data="user=admin&pass=test" --dbs'
        }
      },
      {
        id: 'xss-detection',
        name: 'XSS漏洞检测',
        description: '检测跨站脚本漏洞',
        type: SkillType.SCANNING,
        difficulty: SkillDifficulty.BEGINNER,
        tags: ['xss', 'web', 'javascript'],
        prerequisites: ['web-enumeration'],
        estimated_time: '10-20分钟',
        success_rate: 72.8,
        last_used: '2026-04-05T16:20:00Z',
        usage_count: 567,
        tools: ['burpsuite', 'xsser', 'beef'],
        tutorial: {
          steps: [
            '寻找用户输入点',
            '测试反射型和存储型XSS',
            '验证漏洞影响',
            '提供修复建议'
          ],
          example_payload: '<script>alert("XSS")</script>'
        }
      },
      {
        id: 'privilege-escalation',
        name: '权限提升',
        description: '在获取初始访问后提升权限',
        type: SkillType.POST_EXPLOITATION,
        difficulty: SkillDifficulty.ADVANCED,
        tags: ['post-exploitation', 'privilege', 'linux', 'windows'],
        prerequisites: ['initial-access', 'system-enumeration'],
        estimated_time: '30-60分钟',
        success_rate: 45.3,
        last_used: '2026-04-04T14:30:00Z',
        usage_count: 89,
        tools: ['linpeas', 'winpeas', 'metasploit'],
        tutorial: {
          steps: [
            '枚举系统信息',
            '检查SUID/SGID文件',
            '寻找内核漏洞',
            '利用配置错误'
          ],
          resources: ['GTFOBins', 'LOLBAS']
        }
      },
      {
        id: 'report-generation',
        name: '报告生成',
        description: '生成专业的安全评估报告',
        type: SkillType.REPORTING,
        difficulty: SkillDifficulty.INTERMEDIATE,
        tags: ['reporting', 'documentation', 'communication'],
        prerequisites: ['vulnerability-assessment'],
        estimated_time: '20-40分钟',
        success_rate: 92.1,
        last_used: '2026-04-06T12:00:00Z',
        usage_count: 234,
        tools: ['report-generator', 'word', 'latex'],
        tutorial: {
          steps: [
            '收集发现结果',
            '整理证据链',
            '编写执行摘要',
            '生成修复建议'
          ],
          template: 'executive_summary.md'
        }
      },
      {
        id: 'network-analysis',
        name: '网络流量分析',
        description: '分析网络流量和协议',
        type: SkillType.ANALYSIS,
        difficulty: SkillDifficulty.ADVANCED,
        tags: ['network', 'analysis', 'wireshark', 'pcap'],
        prerequisites: ['network-fundamentals'],
        estimated_time: '45-90分钟',
        success_rate: 78.6,
        last_used: '2026-04-03T11:15:00Z',
        usage_count: 67,
        tools: ['wireshark', 'tcpdump', 'tshark'],
        tutorial: {
          steps: [
            '捕获网络流量',
            '过滤和分析数据包',
            '识别异常流量',
            '提取恶意载荷'
          ],
          example_filter: 'tcp.port == 80 and http.request'
        }
      },
      {
        id: 'encryption-decryption',
        name: '加密解密',
        description: '密码学技术和工具使用',
        type: SkillType.UTILITY,
        difficulty: SkillDifficulty.INTERMEDIATE,
        tags: ['crypto', 'encryption', 'decryption', 'ssl'],
        prerequisites: ['cryptography-basics'],
        estimated_time: '15-30分钟',
        success_rate: 85.4,
        last_used: '2026-04-02T09:45:00Z',
        usage_count: 123,
        tools: ['openssl', 'john', 'hashcat'],
        tutorial: {
          steps: [
            '识别加密算法',
            '使用合适工具',
            '暴力破解或字典攻击',
            '验证解密结果'
          ],
          example_command: 'openssl enc -aes-256-cbc -d -in encrypted.txt -out decrypted.txt'
        }
      }
    ];

    // 应用过滤
    let filteredSkills = [...mockSkills];
    if (params.type) {
      filteredSkills = filteredSkills.filter(s => s.type === params.type);
    }
    if (params.difficulty) {
      filteredSkills = filteredSkills.filter(s => s.difficulty === params.difficulty);
    }
    if (params.search) {
      const searchLower = params.search.toLowerCase();
      filteredSkills = filteredSkills.filter(s =>
        s.name.toLowerCase().includes(searchLower) ||
        s.description.toLowerCase().includes(searchLower) ||
        s.tags.some(tag => tag.toLowerCase().includes(searchLower))
      );
    }

    // 应用排序
    if (params.sort === 'popular') {
      filteredSkills.sort((a, b) => b.usage_count - a.usage_count);
    } else if (params.sort === 'recent') {
      filteredSkills.sort((a, b) => new Date(b.last_used) - new Date(a.last_used));
    } else if (params.sort === 'success') {
      filteredSkills.sort((a, b) => b.success_rate - a.success_rate);
    }

    // 应用分页
    const page = params.page || 1;
    const pageSize = params.pageSize || 20;
    const startIndex = (page - 1) * pageSize;
    const paginatedSkills = filteredSkills.slice(startIndex, startIndex + pageSize);

    return {
      skills: paginatedSkills,
      total: filteredSkills.length,
      page,
      page_size: pageSize,
      total_pages: Math.ceil(filteredSkills.length / pageSize)
    };
    } else {
      throw error;
    }
  }
};

/**
 * 获取技能详情
 * @param {string} skillId - 技能ID
 * @returns {Promise} 技能详情
 */
export const getSkill = async (skillId) => {
  try {
    return await request.get(`/skills/${skillId}`);
  } catch (error) {
    if (USE_MOCK_DATA) {
      console.warn('获取技能详情API失败，使用模拟数据:', error.message);

      // 从模拟技能列表中查找
      const mockSkills = await getSkills();
      const skill = mockSkills.skills.find(s => s.id === skillId);

      if (skill) {
        return skill;
      }
    }

    throw new Error(`技能 ${skillId} 未找到`);
  }
};

/**
 * 获取技能统计
 * @returns {Promise} 技能统计
 */
export const getSkillStats = async () => {
  try {
    return await request.get('/skills/stats');
  } catch (error) {
    if (USE_MOCK_DATA) {
      console.warn('获取技能统计API失败，使用模拟数据:', error.message);

      // 模拟技能统计
      return {
      total_skills: 7,
      total_usage: 2757,
      avg_success_rate: 77.4,
      most_popular: 'port-scanning',
      recent_activity: '2026-04-06T12:00:00Z',
      by_type: {
        [SkillType.SCANNING]: 2,
        [SkillType.EXPLOITATION]: 1,
        [SkillType.POST_EXPLOITATION]: 1,
        [SkillType.REPORTING]: 1,
        [SkillType.ANALYSIS]: 1,
        [SkillType.UTILITY]: 1
      },
      by_difficulty: {
        [SkillDifficulty.BEGINNER]: 2,
        [SkillDifficulty.INTERMEDIATE]: 3,
        [SkillDifficulty.ADVANCED]: 2,
        [SkillDifficulty.EXPERT]: 0
      }
    };
    } else {
      throw error;
    }
  }
};

/**
 * 执行技能
 * @param {string} skillId - 技能ID
 * @param {Object} parameters - 执行参数
 * @returns {Promise} 执行结果
 */
export const executeSkill = async (skillId, parameters = {}) => {
  try {
    return await request.post(`/skills/${skillId}/execute`, parameters);
  } catch (error) {
    if (USE_MOCK_DATA) {
      console.warn('执行技能API失败，使用模拟响应:', error.message);

      // 模拟执行响应
      return {
      success: true,
      skill_id: skillId,
      execution_id: `exec_${Date.now()}`,
      status: 'running',
      started_at: new Date().toISOString(),
      estimated_completion: new Date(Date.now() + 300000).toISOString(), // 5分钟后
      parameters: parameters
    };
    } else {
      throw error;
    }
  }
};

/**
 * 获取执行状态
 * @param {string} executionId - 执行ID
 * @returns {Promise} 执行状态
 */
export const getExecutionStatus = async (executionId) => {
  try {
    return await request.get(`/skills/executions/${executionId}`);
  } catch (error) {
    if (USE_MOCK_DATA) {
      console.warn('获取执行状态API失败，使用模拟数据:', error.message);

      // 模拟执行状态
      const progress = Math.min(100, Math.floor((Date.now() % 300000) / 3000)); // 模拟进度

    return {
      execution_id: executionId,
      status: progress < 100 ? 'running' : 'completed',
      progress: progress,
      start_time: new Date(Date.now() - (progress * 3000)).toISOString(),
      estimated_completion: new Date(Date.now() + (100 - progress) * 3000).toISOString(),
      findings: progress >= 100 ? [
        { type: 'vulnerability', count: 3 },
        { type: 'information', count: 12 },
        { type: 'warning', count: 5 }
      ] : []
    };
    } else {
      throw error;
    }
  }
};

/**
 * 获取技能学习路径
 * @returns {Promise} 学习路径
 */
export const getLearningPaths = async () => {
  try {
    return await request.get('/skills/learning-paths');
  } catch (error) {
    if (USE_MOCK_DATA) {
      console.warn('获取学习路径API失败，使用模拟数据:', error.message);

      // 模拟学习路径
      return [
      {
        id: 'web-penetration',
        name: 'Web渗透测试',
        description: '从入门到精通的Web安全测试学习路径',
        target_level: SkillDifficulty.ADVANCED,
        estimated_duration: '3-6个月',
        skills: ['port-scanning', 'web-enumeration', 'sql-injection', 'xss-detection', 'csrf-attack'],
        prerequisites: ['basic-networking', 'web-fundamentals']
      },
      {
        id: 'network-security',
        name: '网络安全专家',
        description: '网络攻防和安全运维学习路径',
        target_level: SkillDifficulty.EXPERT,
        estimated_duration: '6-12个月',
        skills: ['port-scanning', 'network-analysis', 'firewall-config', 'ids-evasion', 'vpn-security'],
        prerequisites: ['network-fundamentals', 'linux-basics']
      },
      {
        id: 'incident-response',
        name: '事件响应分析师',
        description: '安全事件检测、分析和响应学习路径',
        target_level: SkillDifficulty.ADVANCED,
        estimated_duration: '4-8个月',
        skills: ['log-analysis', 'malware-analysis', 'forensics', 'report-generation', 'threat-hunting'],
        prerequisites: ['os-fundamentals', 'security-basics']
      }
    ];
    } else {
      throw error;
    }
  }
};

// 技能服务
const skillService = {
  getSkills,
  getSkill,
  getSkillStats,
  executeSkill,
  getExecutionStatus,
  getLearningPaths,
  SkillType,
  SkillDifficulty
};

export default skillService;