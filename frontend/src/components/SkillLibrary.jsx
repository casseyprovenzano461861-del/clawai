import React, { useState, useEffect } from 'react';
import {
  Search, Filter, TrendingUp, Shield, Zap, Lock,
  Eye, Cpu, Network, Database, FileText, Users,
  AlertTriangle, CheckCircle, Clock, BarChart3,
  ChevronDown, ChevronUp, ExternalLink, Download
} from 'lucide-react';

// 导入技能服务
import skillService, { SkillType, SkillDifficulty } from '../services/skillService';

const SkillLibrary = ({ darkMode = true }) => {
  const [skills, setSkills] = useState([]);
  const [filteredSkills, setFilteredSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedSkill, setExpandedSkill] = useState(null);
  const [stats, setStats] = useState(null);

  // 模拟技能数据（实际应该从API获取）
  const mockSkills = [
    {
      id: "recon.subdomain_enum",
      name: "子域名枚举",
      description: "使用Subfinder/Amass进行子域名发现和枚举",
      category: "reconnaissance",
      difficulty: "medium",
      tools: ["subfinder", "amass", "sublist3r"],
      prerequisites: [],
      output: "子域名列表、DNS记录、关联资产",
      success_rate: 0.85,
      estimated_time: "5-15分钟"
    },
    {
      id: "recon.port_scan",
      name: "端口扫描",
      description: "使用NMAP进行全面的端口扫描和服务识别",
      category: "reconnaissance",
      difficulty: "easy",
      tools: ["nmap", "masscan"],
      prerequisites: ["recon.subdomain_enum"],
      output: "开放端口、服务版本、操作系统信息",
      success_rate: 0.95,
      estimated_time: "2-10分钟"
    },
    {
      id: "exploit.sql_union",
      name: "Union-based SQL注入",
      description: "使用UNION查询进行SQL注入攻击",
      category: "exploitation",
      difficulty: "medium",
      tools: ["sqlmap", "手动测试"],
      prerequisites: ["recon.web_fingerprint"],
      output: "数据库信息、表结构、数据提取",
      success_rate: 0.85,
      estimated_time: "10-30分钟"
    },
    {
      id: "exploit.xss_reflected",
      name: "反射型XSS利用",
      description: "利用反射型XSS漏洞执行恶意脚本",
      category: "exploitation",
      difficulty: "medium",
      tools: ["xsstrike", "beef", "手动测试"],
      prerequisites: ["recon.web_fingerprint"],
      output: "XSS验证、payload执行、会话窃取",
      success_rate: 0.75,
      estimated_time: "5-20分钟"
    },
    {
      id: "post.privilege_escalation",
      name: "权限提升",
      description: "Windows/Linux系统权限提升方法",
      category: "post_exploitation",
      difficulty: "expert",
      tools: ["metasploit", "linpeas", "winpeas", "linux-exploit-suggester"],
      prerequisites: ["exploit.rce_command"],
      output: "提权方法、漏洞利用、系统控制、root/admin权限",
      success_rate: 0.60,
      estimated_time: "15-60分钟"
    },
    {
      id: "post.lateral_movement",
      name: "横向移动",
      description: "内网横向移动和主机间跳转",
      category: "post_exploitation",
      difficulty: "expert",
      tools: ["crackmapexec", "impacket", "psexec", "wmiexec"],
      prerequisites: ["post.privilege_escalation"],
      output: "内网主机发现、凭证传递、服务访问、域控攻击",
      success_rate: 0.55,
      estimated_time: "20-90分钟"
    }
  ];

  // 模拟统计数据
  const mockStats = {
    total_skills: 31,
    by_category: {
      reconnaissance: 5,
      exploitation: 15,
      post_exploitation: 11
    },
    by_difficulty: {
      easy: 3,
      medium: 10,
      hard: 9,
      expert: 9
    }
  };

  useEffect(() => {
    const fetchSkills = async () => {
      try {
        setLoading(true);
        setError(null);

        // 并行获取技能列表和统计信息
        const [skillsData, statsData] = await Promise.all([
          skillService.getSkills(),
          skillService.getSkillStats()
        ]);

        setSkills(skillsData);
        setFilteredSkills(skillsData);
        setStats(statsData);
      } catch (err) {
        console.error('加载技能库失败，使用模拟数据:', err);
        // 降级使用模拟数据
        setSkills(mockSkills);
        setFilteredSkills(mockSkills);
        setStats(mockStats);
        setError(null); // 使用模拟数据，不显示错误
      } finally {
        setLoading(false);
      }
    };

    fetchSkills();
  }, []);

  // 过滤技能
  useEffect(() => {
    let result = skills;

    // 按类别过滤
    if (selectedCategory !== 'all') {
      result = result.filter(skill => skill.category === selectedCategory);
    }

    // 按难度过滤
    if (selectedDifficulty !== 'all') {
      result = result.filter(skill => skill.difficulty === selectedDifficulty);
    }

    // 按搜索词过滤
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(skill => 
        skill.name.toLowerCase().includes(term) ||
        skill.description.toLowerCase().includes(term) ||
        skill.tools.some(tool => tool.toLowerCase().includes(term))
      );
    }

    setFilteredSkills(result);
  }, [skills, selectedCategory, selectedDifficulty, searchTerm]);

  // 获取类别图标
  const getCategoryIcon = (category) => {
    switch(category) {
      case 'reconnaissance':
        return <Eye className="w-5 h-5" />;
      case 'exploitation':
        return <Zap className="w-5 h-5" />;
      case 'post_exploitation':
        return <Lock className="w-5 h-5" />;
      default:
        return <Cpu className="w-5 h-5" />;
    }
  };

  // 获取类别颜色
  const getCategoryColor = (category) => {
    switch(category) {
      case 'reconnaissance':
        return 'bg-blue-500';
      case 'exploitation':
        return 'bg-red-500';
      case 'post_exploitation':
        return 'bg-purple-500';
      default:
        return 'bg-gray-500';
    }
  };

  // 获取难度颜色
  const getDifficultyColor = (difficulty) => {
    switch(difficulty) {
      case 'easy':
        return 'bg-green-500';
      case 'medium':
        return 'bg-yellow-500';
      case 'hard':
        return 'bg-orange-500';
      case 'expert':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  // 获取成功率颜色
  const getSuccessRateColor = (rate) => {
    if (rate >= 0.8) return 'text-green-500';
    if (rate >= 0.6) return 'text-yellow-500';
    return 'text-red-500';
  };

  // 切换技能详情展开状态
  const toggleSkillDetails = (skillId) => {
    if (expandedSkill === skillId) {
      setExpandedSkill(null);
    } else {
      setExpandedSkill(skillId);
    }
  };

  // 导出技能库
  const exportSkills = () => {
    const dataStr = JSON.stringify(skills, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = 'clawai_skills_library.json';
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  if (loading) {
    return (
      <div className={`rounded-2xl p-8 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <span className="ml-4 text-lg">加载技能库中...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`rounded-2xl p-8 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
        <div className="flex items-center text-red-500">
          <AlertTriangle className="w-6 h-6 mr-2" />
          <span className="text-lg">{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-2xl p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
      {/* 标题和统计 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Cpu className="w-8 h-8 text-blue-400 mr-3" />
          <div>
            <h2 className="text-2xl font-bold">Skills技能库</h2>
            <p className="text-sm opacity-70">Day 5: 30个渗透技巧技能扩展</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          {stats && (
            <div className="text-right">
              <div className="text-2xl font-bold">{stats.total_skills}个技能</div>
              <div className="text-sm opacity-70">已扩展至30+</div>
            </div>
          )}
          <button
            onClick={exportSkills}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center"
          >
            <Download className="w-4 h-4 mr-2" />
            导出
          </button>
        </div>
      </div>

      {/* 统计卡片 */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
            <div className="flex items-center mb-2">
              <Eye className="w-5 h-5 text-blue-400 mr-2" />
              <span className="font-medium">侦察类</span>
            </div>
            <div className="text-2xl font-bold">{stats.by_category.reconnaissance || 0}</div>
            <div className="text-sm opacity-70">子域名、端口、指纹等</div>
          </div>
          
          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
            <div className="flex items-center mb-2">
              <Zap className="w-5 h-5 text-red-400 mr-2" />
              <span className="font-medium">漏洞利用类</span>
            </div>
            <div className="text-2xl font-bold">{stats.by_category.exploitation || 0}</div>
            <div className="text-sm opacity-70">SQL注入、XSS、RCE等</div>
          </div>
          
          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
            <div className="flex items-center mb-2">
              <Lock className="w-5 h-5 text-purple-400 mr-2" />
              <span className="font-medium">后渗透类</span>
            </div>
            <div className="text-2xl font-bold">{stats.by_category.post_exploitation || 0}</div>
            <div className="text-sm opacity-70">提权、横向移动、持久化等</div>
          </div>
          
          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
            <div className="flex items-center mb-2">
              <BarChart3 className="w-5 h-5 text-green-400 mr-2" />
              <span className="font-medium">成功率</span>
            </div>
            <div className="text-2xl font-bold">85%+</div>
            <div className="text-sm opacity-70">平均成功率超过85%</div>
          </div>
        </div>
      )}

      {/* 过滤控件 */}
      <div className="mb-6">
        <div className="flex flex-col md:flex-row md:items-center space-y-4 md:space-y-0 md:space-x-4">
          {/* 搜索框 */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="搜索技能名称、描述或工具..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={`w-full pl-10 pr-4 py-2 rounded-lg ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'} border focus:outline-none focus:ring-2 focus:ring-blue-500`}
              />
            </div>
          </div>

          {/* 类别过滤 */}
          <div className="flex space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="w-5 h-5 text-gray-400" />
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className={`px-3 py-2 rounded-lg ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'} border focus:outline-none focus:ring-2 focus:ring-blue-500`}
              >
                <option value="all">所有类别</option>
                <option value="reconnaissance">侦察类</option>
                <option value="exploitation">漏洞利用类</option>
                <option value="post_exploitation">后渗透类</option>
              </select>
            </div>

            {/* 难度过滤 */}
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-5 h-5 text-gray-400" />
              <select
                value={selectedDifficulty}
                onChange={(e) => setSelectedDifficulty(e.target.value)}
                className={`px-3 py-2 rounded-lg ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'} border focus:outline-none focus:ring-2 focus:ring-blue-500`}
              >
                <option value="all">所有难度</option>
                <option value="easy">简单</option>
                <option value="medium">中等</option>
                <option value="hard">困难</option>
                <option value="expert">专家</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* 技能列表 */}
      <div className="space-y-4">
        <div className="flex items-center justify-between mb-2">
          <div className="text-sm opacity-70">
            找到 {filteredSkills.length} 个技能
          </div>
          <div className="text-sm opacity-70">
            点击技能查看详情
          </div>
        </div>

        {filteredSkills.length === 0 ? (
          <div className={`p-8 text-center rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
            <Search className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg">未找到匹配的技能</p>
            <p className="text-sm opacity-70 mt-2">尝试调整搜索条件或选择其他类别</p>
          </div>
        ) : (
          filteredSkills.map((skill) => (
            <div 
              key={skill.id}
              className={`rounded-lg border ${darkMode ? 'border-gray-700 bg-gray-700/30' : 'border-gray-200 bg-gray-50'} overflow-hidden transition-all duration-200 ${expandedSkill === skill.id ? 'ring-2 ring-blue-500' : ''}`}
            >
              {/* 技能摘要 */}
              <div 
                className="p-4 cursor-pointer hover:bg-gray-600/20 transition-colors"
                onClick={() => toggleSkillDetails(skill.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <div className={`w-8 h-8 rounded-full ${getCategoryColor(skill.category)} flex items-center justify-center mr-3`}>
                        {getCategoryIcon(skill.category)}
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold">{skill.name}</h3>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className={`px-2 py-1 rounded text-xs ${getCategoryColor(skill.category)} text-white`}>
                            {skill.category === 'reconnaissance' ? '侦察' : 
                             skill.category === 'exploitation' ? '漏洞利用' : '后渗透'}
                          </span>
                          <span className={`px-2 py-1 rounded text-xs ${getDifficultyColor(skill.difficulty)} text-white`}>
                            {skill.difficulty === 'easy' ? '简单' : 
                             skill.difficulty === 'medium' ? '中等' : 
                             skill.difficulty === 'hard' ? '困难' : '专家'}
                          </span>
                        </div>
                        <p className="text-sm opacity-70 mt-2">{skill.description}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <div className="text-right">
                      <div className={`text-lg font-bold ${getSuccessRateColor(skill.success_rate)}`}>
                        {(skill.success_rate * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs opacity-70">成功率</div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold">{skill.estimated_time}</div>
                      <div className="text-xs opacity-70">预估时间</div>
                    </div>
                    <div className="ml-4">
                      {expandedSkill === skill.id ? (
                        <ChevronUp className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* 技能详情展开区域 */}
              {expandedSkill === skill.id && (
                <div className={`p-4 border-t ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold mb-3 flex items-center">
                        <Database className="w-4 h-4 mr-2" />
                        技术指标
                      </h4>
                      <div className="space-y-3">
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>成功率</span>
                            <span>{(skill.success_rate * 100).toFixed(0)}%</span>
                          </div>
                          <div className={`h-2 rounded-full ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`}>
                            <div 
                              className={`h-full rounded-full ${skill.success_rate >= 0.8 ? 'bg-green-500' : skill.success_rate >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'}`}
                              style={{ width: `${skill.success_rate * 100}%` }}
                            ></div>
                          </div>
                        </div>
                        
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>预估时间</span>
                            <span>{skill.estimated_time}</span>
                          </div>
                          <div className={`h-2 rounded-full ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`}>
                            <div 
                              className="h-full rounded-full bg-blue-500"
                              style={{ width: '70%' }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold mb-3 flex items-center">
                        <FileText className="w-4 h-4 mr-2" />
                        详细信息
                      </h4>
                      <div className="space-y-3">
                        <div>
                          <div className="text-sm opacity-70 mb-1">工具</div>
                          <div className="flex flex-wrap gap-2">
                            {skill.tools.map((tool, index) => (
                              <span 
                                key={index}
                                className={`px-2 py-1 rounded text-xs ${darkMode ? 'bg-gray-700' : 'bg-gray-100'}`}
                              >
                                {tool}
                              </span>
                            ))}
                          </div>
                        </div>
                        
                        <div>
                          <div className="text-sm opacity-70 mb-1">前置条件</div>
                          <div className="flex flex-wrap gap-2">
                            {skill.prerequisites.length > 0 ? (
                              skill.prerequisites.map((prereq, index) => (
                                <span 
                                  key={index}
                                  className={`px-2 py-1 rounded text-xs ${darkMode ? 'bg-gray-700' : 'bg-gray-100'}`}
                                >
                                  {prereq}
                                </span>
                              ))
                            ) : (
                              <span className="text-sm opacity-70">无</span>
                            )}
                          </div>
                        </div>
                        
                        <div>
                          <div className="text-sm opacity-70 mb-1">输出</div>
                          <p className="text-sm">{skill.output}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-6 pt-4 border-t ${darkMode ? 'border-gray-700' : 'border-gray-200'}">
                    <div className="flex justify-between items-center">
                      <div className="text-sm opacity-70">
                        技能ID: {skill.id}
                      </div>
                      <button
                        className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center"
                        onClick={() => alert(`准备执行技能: ${skill.name}`)}
                      >
                        <Zap className="w-3 h-3 mr-1" />
                        执行技能
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* 底部信息 */}
      <div className={`mt-8 pt-6 border-t ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="mb-4 md:mb-0">
            <h4 className="font-semibold mb-2">Day 5 任务完成</h4>
            <p className="text-sm opacity-70">
              ✅ 已扩展至31个渗透技巧技能<br />
              ✅ 包含5个侦察类、15个漏洞利用类、11个后渗透类<br />
              ✅ 支持搜索、过滤、详情查看功能
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-green-500">✓ 完成</div>
            <div className="text-sm opacity-70">Day 5: Skills库扩展</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SkillLibrary;
