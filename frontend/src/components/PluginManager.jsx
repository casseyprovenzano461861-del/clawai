import React, { useState, useEffect, useRef } from 'react';
import {
  Package, Plug, Settings, Download, Trash2, RefreshCw,
  Play, StopCircle, Search, Shield, Database,
  Network, BarChart3, FileText, Globe, MoreVertical,
  Info, CheckCircle, Zap, Cpu, Lock, Key, Code,
  TrendingUp, Award, Clock, Filter, X, ChevronRight,
  Terminal, Box, Layers, AlertTriangle, Upload,
} from 'lucide-react';

import pluginService, { PluginStatus } from '../services/pluginService';

/* ─────────────────────────────────────────
   Data
───────────────────────────────────────── */
const CATEGORIES = [
  { id: 'all',          name: '全部',       icon: Layers,    color: '#00d4ff' },
  { id: 'scanner',      name: '扫描器',     icon: Shield,    color: '#3b82f6' },
  { id: 'exploit',      name: '漏洞利用',   icon: Zap,       color: '#ef4444' },
  { id: 'recon',        name: '信息收集',   icon: Search,    color: '#06b6d4' },
  { id: 'post-exploit', name: '后渗透',     icon: Terminal,  color: '#f97316' },
  { id: 'brute-force',  name: '密码破解',   icon: Key,       color: '#eab308' },
  { id: 'proxy',        name: '代理工具',   icon: Network,   color: '#8b5cf6' },
  { id: 'reporting',    name: '报告生成',   icon: FileText,  color: '#22c55e' },
  { id: 'skill',        name: 'AI 技能库',  icon: Cpu,       color: '#a855f7' },
  { id: 'ai_enhanced',  name: 'AI 增强',    icon: Box,       color: '#ec4899' },
];

const ALL_PLUGINS = [
  // ── 扫描器（12个，nmap/nuclei/httpx/ffuf/gobuster 已激活）──────────────────────────
  {
    id:'nmap', name:'Nmap', subtitle:'端口扫描 / 服务识别',
    version:'7.94', author:'Gordon Lyon', category:'scanner', status:'active', installed:true, enabled:true,
    downloads:87, size:'8.2 MB', icon:'🔍', license:'GPL-2.0', featured:true,
    tags:['端口扫描','服务识别','OS检测'],
    description:'业界标准网络探测与安全审计工具，支持端口扫描、服务识别、OS检测、NSE脚本引擎',
    permissions:['network:scan','port:detect'],
  },
  {
    id:'masscan', name:'Masscan', subtitle:'互联网级高速扫描',
    version:'1.3.2', author:'Robert Graham', category:'scanner', status:'available', installed:false,
    downloads:34, size:'1.8 MB', icon:'⚡', license:'AGPL', featured:false,
    tags:['高速','端口','批量'],
    description:'互联网级别高速端口扫描器，速度可达每秒千万数据包，适合大规模资产发现',
    permissions:['network:scan'],
  },
  {
    id:'rustscan', name:'RustScan', subtitle:'Rust超快扫描器',
    version:'2.1.1', author:'RustScan Project', category:'scanner', status:'available', installed:false,
    downloads:27, size:'5.4 MB', icon:'🦀', license:'GPL-3.0', featured:false,
    tags:['Rust','高速','Nmap集成'],
    description:'Rust编写的超快端口扫描器，与Nmap无缝集成，比传统扫描快100倍',
    permissions:['network:scan'],
  },
  {
    id:'nuclei', name:'Nuclei', subtitle:'模板漏洞扫描器',
    version:'3.1.4', author:'ProjectDiscovery', category:'scanner', status:'active', installed:true, enabled:true,
    downloads:73, size:'45 MB', icon:'☢️', license:'MIT', featured:true,
    tags:['CVE','模板','批量'],
    description:'基于YAML模板的漏洞扫描器，内置7000+个CVE模板，支持自定义扩展',
    permissions:['vulnerability:scan'],
  },
  {
    id:'nikto', name:'Nikto', subtitle:'Web服务器扫描',
    version:'2.1.6', author:'Chris Sullo', category:'scanner', status:'available', installed:false,
    downloads:41, size:'2.1 MB', icon:'🕵️', license:'GPL-2.0', featured:false,
    tags:['Web','配置','过时版本'],
    description:'Web服务器扫描器，检测6700+危险文件/配置问题/过时版本',
    permissions:['web:scan'],
  },
  {
    id:'httpx', name:'httpx', subtitle:'HTTP批量探测',
    version:'1.3.7', author:'ProjectDiscovery', category:'scanner', status:'active', installed:true, enabled:true,
    downloads:29, size:'12.3 MB', icon:'🌐', license:'MIT', featured:false,
    tags:['HTTP','指纹','批量'],
    description:'快速多功能HTTP工具包，支持批量探测状态码、技术栈指纹、截图',
    permissions:['http:probe'],
  },
  {
    id:'ffuf', name:'ffuf', subtitle:'Web模糊测试工具',
    version:'2.1.0', author:'Joohoi', category:'scanner', status:'active', installed:true, enabled:true,
    downloads:38, size:'9.1 MB', icon:'🎯', license:'MIT', featured:true,
    tags:['模糊测试','目录','参数'],
    description:'Go编写的高速Web模糊测试工具，支持目录/参数/VHost发现',
    permissions:['web:fuzz'],
  },
  {
    id:'gobuster', name:'Gobuster', subtitle:'目录/DNS暴力枚举',
    version:'3.6.0', author:'OJ Reeves', category:'scanner', status:'active', installed:true, enabled:true,
    downloads:31, size:'7.8 MB', icon:'📂', license:'Apache-2.0', featured:false,
    tags:['目录','DNS','VHost'],
    description:'Go编写的目录/DNS/VHost暴力破解工具，支持多种扩展名枚举',
    permissions:['directory:fuzz'],
  },
  {
    id:'dirsearch', name:'Dirsearch', subtitle:'目录暴力扫描',
    version:'0.4.3', author:'maurosoria', category:'scanner', status:'available', installed:false,
    downloads:19, size:'3.8 MB', icon:'📁', license:'GPL-2.0', featured:false,
    tags:['目录','字典','递归'],
    description:'高速Web路径暴力破解工具，内置庞大字典库，支持递归扫描',
    permissions:['directory:fuzz'],
  },
  {
    id:'wpscan', name:'WPScan', subtitle:'WordPress安全扫描',
    version:'3.8.25', author:'WPScan Team', category:'scanner', status:'available', installed:false,
    downloads:23, size:'4.3 MB', icon:'📰', license:'WPScan', featured:false,
    tags:['WordPress','CMS','枚举'],
    description:'WordPress安全扫描器，枚举用户/插件/主题并检测已知漏洞',
    permissions:['wordpress:scan'],
  },
  {
    id:'wafw00f', name:'wafw00f', subtitle:'WAF指纹识别',
    version:'2.2.0', author:'EnableSecurity', category:'scanner', status:'available', installed:false,
    downloads:14, size:'1.5 MB', icon:'🛡️', license:'BSD', featured:false,
    tags:['WAF','指纹','检测'],
    description:'自动检测目标前端WAF防火墙，支持170+种WAF指纹识别',
    permissions:['waf:detect'],
  },
  {
    id:'zaproxy', name:'ZAP', subtitle:'OWASP主动扫描器',
    version:'2.14.0', author:'OWASP', category:'scanner', status:'available', installed:false,
    downloads:47, size:'98 MB', icon:'🔮', license:'Apache-2.0', featured:true,
    tags:['OWASP','主动扫描','REST'],
    description:'OWASP官方Web应用安全扫描器，支持主动/被动扫描与REST API测试',
    permissions:['vulnerability:scan'],
  },

  // ── 漏洞利用（6个，sqlmap/xsstrike 已激活）──────────────────────────────
  {
    id:'sqlmap', name:'sqlmap', subtitle:'SQL注入自动化利用',
    version:'1.8.0', author:'Bernardo & Miroslav', category:'exploit', status:'active', installed:true, enabled:true,
    downloads:91, size:'5.1 MB', icon:'💉', license:'GPL-2.0', featured:true,
    tags:['SQL注入','数据库','自动化'],
    description:'自动化SQL注入漏洞检测与利用，支持所有主流数据库，内置绕过技巧',
    permissions:['sql:inject'],
  },
  {
    id:'xsstrike', name:'XSStrike', subtitle:'高级XSS检测套件',
    version:'3.1.5', author:'s0md3v', category:'exploit', status:'active', installed:true, enabled:true,
    downloads:16, size:'2.3 MB', icon:'🎭', license:'GPL-3.0', featured:false,
    tags:['XSS','爬虫','模糊测试'],
    description:'高级XSS检测套件，内置爬虫和模糊测试引擎，自动绕过过滤',
    permissions:['xss:test'],
  },
  {
    id:'commix', name:'Commix', subtitle:'命令注入利用',
    version:'3.9', author:'Anastasios Stasinopoulos', category:'exploit', status:'available', installed:false,
    downloads:9, size:'4.7 MB', icon:'💻', license:'GPL-3.0', featured:false,
    tags:['命令注入','RCE','自动化'],
    description:'自动化OS命令注入漏洞检测与利用，支持多种注入技术',
    permissions:['rce:test'],
  },
  {
    id:'metasploit', name:'Metasploit', subtitle:'渗透测试框架',
    version:'6.3.44', author:'Rapid7', category:'exploit', status:'available', installed:false,
    downloads:112, size:'512 MB', icon:'💀', license:'BSD', featured:true,
    tags:['框架','Exploit','后渗透'],
    description:'世界最广泛使用的渗透测试框架，内置2000+漏洞利用模块与后渗透工具',
    permissions:['exploit:run'],
  },
  {
    id:'tplmap', name:'Tplmap', subtitle:'SSTI模板注入利用',
    version:'0.5', author:'epinna', category:'exploit', status:'available', installed:false,
    downloads:7, size:'3.1 MB', icon:'🧪', license:'MIT', featured:false,
    tags:['SSTI','模板注入','Jinja2'],
    description:'服务器端模板注入漏洞自动检测与利用，支持Jinja2/Twig等10+引擎',
    permissions:['ssti:test'],
  },
  {
    id:'responder', name:'Responder', subtitle:'LLMNR毒化捕获',
    version:'3.1.4', author:'Laurent Gaffie', category:'exploit', status:'available', installed:false,
    downloads:11, size:'2.4 MB', icon:'📡', license:'GPL-3.0', featured:false,
    tags:['LLMNR','NTLM哈希','毒化'],
    description:'LLMNR/NBT-NS毒化攻击工具，自动捕获NTLMv1/v2哈希用于离线破解',
    permissions:['network:poison'],
  },

  // ── 信息收集（4个，amass/subfinder 已激活）───────────────────────────────
  {
    id:'amass', name:'Amass', subtitle:'攻击面映射',
    version:'4.2.0', author:'OWASP', category:'recon', status:'active', installed:true, enabled:true,
    downloads:33, size:'18.6 MB', icon:'🗺️', license:'Apache-2.0', featured:true,
    tags:['子域名','OSINT','攻击面'],
    description:'深度攻击面映射工具，整合50+数据源，支持主动/被动子域名发现',
    permissions:['subdomain:enum'],
  },
  {
    id:'subfinder', name:'Subfinder', subtitle:'被动子域名发现',
    version:'2.6.3', author:'ProjectDiscovery', category:'recon', status:'active', installed:true, enabled:true,
    downloads:28, size:'8.9 MB', icon:'🔭', license:'MIT', featured:false,
    tags:['子域名','被动','OSINT'],
    description:'被动子域名发现工具，整合47+数据源，速度快且无噪音',
    permissions:['subdomain:enum'],
  },
  {
    id:'theharvester', name:'theHarvester', subtitle:'OSINT信息聚合',
    version:'4.4.3', author:'Christian Martorella', category:'recon', status:'available', installed:false,
    downloads:21, size:'3.2 MB', icon:'🌾', license:'GPL-2.0', featured:false,
    tags:['邮箱','OSINT','搜索引擎'],
    description:'收集邮件地址、子域名、IP等OSINT信息，整合多搜索引擎',
    permissions:['osint:collect'],
  },
  {
    id:'bloodhound', name:'BloodHound', subtitle:'AD域攻击路径分析',
    version:'4.3.1', author:'SpecterOps', category:'recon', status:'available', installed:false,
    downloads:17, size:'45 MB', icon:'🐕', license:'GPL-3.0', featured:true,
    tags:['AD','域渗透','图分析'],
    description:'Active Directory攻击路径可视化分析，图形化展示域内权限关系',
    permissions:['ad:analyze'],
  },

  // ── 后渗透（6个，impacket/mimikatz 已激活）──────────────────────────────
  {
    id:'impacket', name:'Impacket', subtitle:'网络协议工具集',
    version:'0.12.0', author:'SecureAuth', category:'post-exploit', status:'active', installed:true, enabled:true,
    downloads:26, size:'8.4 MB', icon:'🧰', license:'Apache-2.0', featured:true,
    tags:['SMB','Kerberos','NTLM'],
    description:'Python网络协议工具集，支持SMB/NTLM/Kerberos攻击，包含psexec/secretsdump',
    permissions:['smb:attack','kerberos:attack'],
  },
  {
    id:'evil-winrm', name:'Evil-WinRM', subtitle:'WinRM渗透Shell',
    version:'3.5', author:'Hackplayers', category:'post-exploit', status:'available', installed:false,
    downloads:13, size:'2.1 MB', icon:'😈', license:'MIT', featured:false,
    tags:['WinRM','Windows','Shell'],
    description:'专为渗透测试设计的WinRM Shell，支持文件传输/加载器/混淆',
    permissions:['winrm:shell'],
  },
  {
    id:'crackmapexec', name:'CrackMapExec', subtitle:'内网批量评估',
    version:'5.4.0', author:'mpgn', category:'post-exploit', status:'available', installed:false,
    downloads:18, size:'15.6 MB', icon:'🗡️', license:'BSD', featured:false,
    tags:['SMB','横向移动','内网'],
    description:'内网评估瑞士军刀，支持SMB/LDAP/MSSQL批量认证与横向移动',
    permissions:['smb:attack','lateral:move'],
  },
  {
    id:'mimikatz', name:'Mimikatz', subtitle:'Windows凭据提取',
    version:'2.2.0', author:'gentilkiwi', category:'post-exploit', status:'active', installed:true, enabled:true,
    downloads:44, size:'1.5 MB', icon:'🔐', license:'CC BY 4.0', featured:true,
    tags:['凭据','LSASS','PTH'],
    description:'Windows凭据提取工具，支持LSASS内存转储、Pass-the-Hash/Ticket',
    permissions:['credential:dump'],
  },
  {
    id:'linpeas', name:'LinPEAS', subtitle:'Linux提权枚举',
    version:'20240101', author:'carlospolop', category:'post-exploit', status:'available', installed:false,
    downloads:22, size:'1.2 MB', icon:'🐧', license:'MIT', featured:false,
    tags:['Linux','提权','SUID'],
    description:'Linux权限提升路径自动枚举脚本，检测SUID/sudo/crontab/内核漏洞路径',
    permissions:['privesc:linux'],
  },
  {
    id:'chisel', name:'Chisel', subtitle:'HTTP隧道穿透',
    version:'1.9.1', author:'jpillora', category:'post-exploit', status:'available', installed:false,
    downloads:8, size:'8.3 MB', icon:'⛏️', license:'MIT', featured:false,
    tags:['隧道','穿透','端口转发'],
    description:'基于HTTP的TCP/UDP隧道工具，支持内网穿透与反向代理',
    permissions:['network:tunnel'],
  },

  // ── 密码破解（3个，hydra 已激活）────────────────────────────────────────────
  {
    id:'hashcat', name:'Hashcat', subtitle:'GPU加速哈希破解',
    version:'6.2.6', author:'Hashcat Project', category:'brute-force', status:'available', installed:false,
    downloads:103, size:'22 MB', icon:'⚙️', license:'MIT', featured:true,
    tags:['GPU','哈希','破解'],
    description:'世界最快GPU密码恢复工具，支持350+哈希算法，兼容NVIDIA/AMD',
    permissions:['hash:crack'],
  },
  {
    id:'hydra', name:'Hydra', subtitle:'在线密码爆破',
    version:'9.5', author:'van Hauser', category:'brute-force', status:'active', installed:true, enabled:true,
    downloads:57, size:'1.2 MB', icon:'🔓', license:'AGPL', featured:false,
    tags:['在线爆破','50+协议','SSH'],
    description:'支持50+协议的快速在线密码破解工具，SSH/FTP/HTTP/SMB全覆盖',
    permissions:['brute:force'],
  },
  {
    id:'john', name:'John the Ripper', subtitle:'经典哈希破解',
    version:'1.9.0', author:'Solar Designer', category:'brute-force', status:'available', installed:false,
    downloads:68, size:'3.1 MB', icon:'🔑', license:'GPL-2.0', featured:false,
    tags:['字典','暴力破解','哈希'],
    description:'经典密码破解工具，字典攻击与暴力破解，自动识别哈希类型',
    permissions:['hash:crack'],
  },

  // ── 代理工具（2个）────────────────────────────────────────────────────────────
  {
    id:'burpsuite', name:'Burp Suite CE', subtitle:'Web渗透抓包代理',
    version:'2024.1', author:'PortSwigger', category:'proxy', status:'available', installed:false,
    downloads:89, size:'110 MB', icon:'🦟', license:'Free/Pro', featured:true,
    tags:['HTTP代理','拦截','重放'],
    description:'业界标准Web应用安全测试平台，支持HTTP拦截/重放/Intruder爆破/Scanner扫描',
    permissions:['http:intercept','http:replay'],
  },
  {
    id:'mitmproxy', name:'mitmproxy', subtitle:'交互式HTTPS代理',
    version:'10.2.2', author:'mitmproxy Project', category:'proxy', status:'available', installed:false,
    downloads:31, size:'18 MB', icon:'🕸️', license:'MIT', featured:false,
    tags:['HTTPS代理','脚本','流量分析'],
    description:'命令行交互式HTTPS代理，支持Python脚本拦截修改流量，适合API安全测试',
    permissions:['http:intercept','traffic:modify'],
  },

  // ── 报告生成（2个）────────────────────────────────────────────────────────────
  {
    id:'dradis', name:'Dradis CE', subtitle:'渗透测试报告协作平台',
    version:'4.10.0', author:'Dradis Framework', category:'reporting', status:'available', installed:false,
    downloads:12, size:'55 MB', icon:'📋', license:'GPL-2.0', featured:false,
    tags:['报告','协作','漏洞管理'],
    description:'开源渗透测试报告协作框架，支持多人协作、漏洞跟踪、自动导入工具输出',
    permissions:['report:write','finding:import'],
  },
  {
    id:'serpico', name:'Serpico', subtitle:'渗透报告自动生成',
    version:'1.3.5', author:'NtobecSecurity', category:'reporting', status:'available', installed:false,
    downloads:8, size:'22 MB', icon:'🐍', license:'BSD', featured:false,
    tags:['报告模板','Word导出','自动化'],
    description:'渗透测试报告自动生成工具，内置漏洞描述库，支持Word/HTML格式导出',
    permissions:['report:write','report:export'],
  },

  // ── 扫描器补充（2个）──────────────────────────────────────────────────────────
  {
    id:'openvas', name:'OpenVAS', subtitle:'全功能漏洞管理扫描',
    version:'22.4', author:'Greenbone', category:'scanner', status:'available', installed:false,
    downloads:53, size:'280 MB', icon:'🛰️', license:'GPL-2.0', featured:true,
    tags:['漏洞管理','CVE','网络扫描'],
    description:'开源综合漏洞扫描平台，CVE库每日更新，支持认证/未认证扫描与合规检测',
    permissions:['vulnerability:scan','network:scan'],
  },
  {
    id:'feroxbuster', name:'Feroxbuster', subtitle:'递归目录强力扫描',
    version:'2.10.1', author:'epi052', category:'scanner', status:'available', installed:false,
    downloads:22, size:'6.7 MB', icon:'💥', license:'MIT', featured:false,
    tags:['递归扫描','目录枚举','高速'],
    description:'Rust编写的高速递归目录扫描工具，自动跟进子目录，支持过滤/状态码筛选',
    permissions:['directory:fuzz'],
  },

  // ── AI 技能库（10个，全部预装，因为是ClawAI内置能力）────────────────────────
  { id:'skill_sqli_basic',         name:'SQL 基础注入',     subtitle:'布尔/报错盲注',    version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:24,  size:'0.2 MB', icon:'💉', license:'MIT', featured:false, tags:['SQL注入','盲注'],      description:'基础SQL注入检测：单引号探测、布尔盲注、报错注入，自动识别注入点', permissions:['sql:inject'] },
  { id:'skill_sqli_union',         name:'SQL Union 注入',   subtitle:'联合查询数据提取', version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:17,  size:'0.2 MB', icon:'🔗', license:'MIT', featured:false, tags:['UNION','数据提取'],    description:'基于UNION SELECT的SQL注入，提取数据库表结构和敏感数据',         permissions:['sql:inject'] },
  { id:'skill_xss_reflected',      name:'XSS 反射型注入',   subtitle:'DOM/反射型检测',   version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:21,  size:'0.2 MB', icon:'🎭', license:'MIT', featured:false, tags:['XSS','反射'],          description:'检测反射型XSS漏洞，测试script/img/svg等Payload，自动绕过过滤', permissions:['xss:test'] },
  { id:'skill_rce_command_inject', name:'命令注入 RCE',     subtitle:'OS命令执行检测',   version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:14,  size:'0.2 MB', icon:'💻', license:'MIT', featured:true,  tags:['RCE','命令注入'],      description:'OS命令注入漏洞检测，测试;/&&/|分隔符及反引号，支持带外检测',  permissions:['rce:test'] },
  { id:'skill_lfi_basic',          name:'LFI 文件包含',     subtitle:'路径遍历检测',     version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:11,  size:'0.2 MB', icon:'📂', license:'MIT', featured:false, tags:['LFI','路径遍历'],      description:'本地文件包含漏洞检测，../etc/passwd路径遍历，支持多种绕过技巧', permissions:['lfi:test'] },
  { id:'skill_xxe_testing',        name:'XXE 实体注入',     subtitle:'XML外部实体攻击',  version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:9,   size:'0.2 MB', icon:'📄', license:'MIT', featured:false, tags:['XXE','XML'],           description:'XML外部实体注入检测，读取本地文件或进行SSRF，支持盲XXE',       permissions:['xxe:test'] },
  { id:'skill_ssrf_testing',       name:'SSRF 请求伪造',    subtitle:'服务端请求伪造',   version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:12,  size:'0.2 MB', icon:'🌐', license:'MIT', featured:false, tags:['SSRF','内网探测'],     description:'检测SSRF漏洞，探测内网服务和云元数据接口，支持多种协议',       permissions:['ssrf:test'] },
  { id:'skill_privesc_linux',      name:'Linux 提权',       subtitle:'权限提升路径检测', version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:13,  size:'0.3 MB', icon:'🐧', license:'MIT', featured:false, tags:['提权','Linux'],        description:'Linux权限提升检测：SUID/sudo/cron/内核漏洞路径，自动推荐EXP', permissions:['privesc:linux'] },
  { id:'skill_flag_detector',      name:'Flag 自动检测',    subtitle:'CTF Flag识别',     version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:19,  size:'0.1 MB', icon:'🚩', license:'MIT', featured:false, tags:['CTF','Flag'],          description:'CTF Flag模式自动识别，支持flag{}/CTF{}/HTB{}等格式，正则匹配', permissions:['ctf:detect'] },
  { id:'skill_payload_mutator',    name:'Payload 变异器',   subtitle:'WAF绕过变体生成',  version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:16,  size:'0.2 MB', icon:'🧬', license:'MIT', featured:true,  tags:['WAF绕过','混淆'],      description:'WAF绕过Payload自动变异：编码/大小写/注释/Unicode混淆，15+WAF指纹', permissions:['payload:mutate'] },

  // ── AI 增强（3个，全部预装）─────────────────────────────────────────────────
  { id:'jwt_scanner',       name:'JWT 安全检测器',    subtitle:'JWT漏洞全面检测',  version:'1.0.0', author:'ClawAI Team', category:'ai_enhanced', status:'active', installed:true, enabled:true, downloads:31, size:'0.3 MB', icon:'🔐', license:'MIT', featured:true,  tags:['JWT','alg:none','弱密钥'], description:'检测JWT alg:none混淆攻击、弱签名密钥（内置500+字典）、敏感信息泄露', permissions:['http:request','finding:report'] },
  { id:'log4shell_scanner', name:'Log4Shell 检测器',  subtitle:'CVE-2021-44228专项',version:'1.2.0', author:'ClawAI Team', category:'ai_enhanced', status:'active', installed:true, enabled:true, downloads:43, size:'0.5 MB', icon:'🔥', license:'MIT', featured:true,  tags:['Log4j','JNDI','RCE'],      description:'CVE-2021-44228专项检测，内置JNDI Payload变体+HTTP回调，无需外部DNSLOG', permissions:['http:request','dns:listen','network:callback','finding:report'] },
  { id:'ai_payload_gen',    name:'AI Payload 生成器', subtitle:'LLM驱动绕过生成',  version:'2.0.0', author:'ClawAI Team', category:'ai_enhanced', status:'active', installed:true, enabled:true, downloads:27, size:'0.4 MB', icon:'🤖', license:'MIT', featured:true,  tags:['LLM','WAF绕过','自动化'],  description:'LLM智能生成绕过WAF的Payload变体，支持SQLi/XSS/SSTI/SSRF/RCE等10+漏洞类型', permissions:['llm:call','finding:read','finding:update'] },

  // ── 扫描器补充（更多品类）────────────────────────────────────────────────────
  {
    id:'testssl', name:'testssl.sh', subtitle:'TLS/SSL配置审计',
    version:'3.2', author:'Dirk Wetter', category:'scanner', status:'available', installed:false,
    downloads:29, size:'2.9 MB', icon:'🔒', license:'GPL-2.0', featured:false,
    tags:['TLS','SSL','证书'],
    description:'全面TLS/SSL配置检测：协议弱密码套件、BEAST/POODLE/Heartbleed/FREAK等漏洞，支持JSON输出',
    permissions:['tls:scan'],
  },
  {
    id:'sslscan', name:'SSLScan', subtitle:'SSL/TLS快速枚举',
    version:'2.1.3', author:'rbsec', category:'scanner', status:'available', installed:false,
    downloads:19, size:'1.4 MB', icon:'🏷️', license:'GPL-3.0', featured:false,
    tags:['SSL','密码套件','证书链'],
    description:'快速枚举SSL/TLS密码套件与协议版本，检测弱加密配置与自签名证书',
    permissions:['tls:scan'],
  },
  {
    id:'shodan_cli', name:'Shodan CLI', subtitle:'互联网资产搜索引擎',
    version:'1.11.1', author:'John Matherly', category:'recon', status:'available', installed:false,
    downloads:38, size:'0.8 MB', icon:'👁️', license:'MIT', featured:true,
    tags:['OSINT','互联网扫描','暴露资产'],
    description:'Shodan命令行客户端，搜索互联网暴露服务、工控设备、IoT资产，支持Facets查询',
    permissions:['api:shodan','osint:collect'],
  },
  {
    id:'censys_cli', name:'Censys CLI', subtitle:'互联网证书与资产发现',
    version:'2.2.1', author:'Censys Team', category:'recon', status:'available', installed:false,
    downloads:14, size:'1.1 MB', icon:'🌍', license:'Apache-2.0', featured:false,
    tags:['证书透明度','ASN','OSINT'],
    description:'Censys命令行工具，基于证书透明度数据库和IPv4扫描发现资产与子域',
    permissions:['api:censys','osint:collect'],
  },
  {
    id:'dnsx', name:'dnsx', subtitle:'DNS批量解析与枚举',
    version:'1.2.0', author:'ProjectDiscovery', category:'recon', status:'available', installed:false,
    downloads:22, size:'7.2 MB', icon:'📡', license:'MIT', featured:false,
    tags:['DNS','AXFR','批量解析'],
    description:'高速DNS工具包，支持A/AAAA/CNAME/MX/TXT批量解析、区域传输探测',
    permissions:['dns:query'],
  },
  {
    id:'arjun', name:'Arjun', subtitle:'HTTP参数发现',
    version:'2.2.1', author:'s0md3v', category:'scanner', status:'available', installed:false,
    downloads:16, size:'1.8 MB', icon:'🎪', license:'GPL-3.0', featured:false,
    tags:['参数发现','隐藏参数','API'],
    description:'HTTP参数发现工具，内置大型参数字典，用于挖掘API隐藏参数和未文档化端点',
    permissions:['http:probe'],
  },
  {
    id:'dalfox', name:'Dalfox', subtitle:'高速XSS扫描分析器',
    version:'2.9.2', author:'hahwul', category:'scanner', status:'available', installed:false,
    downloads:24, size:'11.3 MB', icon:'🦊', license:'MIT', featured:true,
    tags:['XSS','DOM','自动化'],
    description:'Go编写的高速XSS参数分析与扫描工具，内置DOM分析引擎，支持pipe流式输入',
    permissions:['xss:test'],
  },
  {
    id:'gau', name:'gau', subtitle:'历史URL收集器',
    version:'2.2.3', author:'lc', category:'recon', status:'available', installed:false,
    downloads:31, size:'5.5 MB', icon:'📜', license:'MIT', featured:false,
    tags:['Wayback','历史URL','OSINT'],
    description:'从Wayback Machine/Common Crawl/URLScan批量获取历史URL，用于攻击面发现',
    permissions:['osint:collect'],
  },
  {
    id:'katana', name:'Katana', subtitle:'新一代Web爬虫',
    version:'1.1.0', author:'ProjectDiscovery', category:'scanner', status:'available', installed:false,
    downloads:18, size:'13.6 MB', icon:'⚔️', license:'MIT', featured:false,
    tags:['爬虫','JS渲染','端点发现'],
    description:'Go编写的高速Web爬虫，支持JS渲染、headless浏览器，自动发现API端点',
    permissions:['web:crawl'],
  },

  // ── 漏洞利用补充 ──────────────────────────────────────────────────────────────
  {
    id:'printspoofer', name:'PrintSpoofer', subtitle:'Windows打印服务提权',
    version:'1.0', author:'itm4n', category:'exploit', status:'available', installed:false,
    downloads:11, size:'0.3 MB', icon:'🖨️', license:'MIT', featured:false,
    tags:['Windows','提权','Service Token'],
    description:'利用SeImpersonatePrivilege通过打印服务从Service账户提权至SYSTEM',
    permissions:['exploit:run'],
  },
  {
    id:'juicypotato', name:'JuicyPotato', subtitle:'COM服务提权',
    version:'0.1', author:'ohpe', category:'exploit', status:'available', installed:false,
    downloads:14, size:'0.5 MB', icon:'🥝', license:'MIT', featured:false,
    tags:['Windows','COM','CLSID提权'],
    description:'通过滥用COM服务从低权限账户提权至SYSTEM，依赖SeImpersonatePrivilege',
    permissions:['exploit:run'],
  },
  {
    id:'ghauri', name:'Ghauri', subtitle:'高级SQL注入工具',
    version:'1.3.1', author:'r0oth3x49', category:'exploit', status:'available', installed:false,
    downloads:9, size:'3.2 MB', icon:'🗡️', license:'MIT', featured:false,
    tags:['SQL注入','绕过','高级'],
    description:'高级SQL注入检测利用工具，支持DNS带外、自定义WAF绕过规则，性能优于sqlmap',
    permissions:['sql:inject'],
  },
  {
    id:'ysoserial', name:'ysoserial', subtitle:'Java反序列化利用',
    version:'0.0.6', author:'frohoff', category:'exploit', status:'available', installed:false,
    downloads:22, size:'7.8 MB', icon:'☕', license:'MIT', featured:true,
    tags:['Java','反序列化','RCE'],
    description:'Java反序列化漏洞利用工具，生成Commons/Spring等流行库的反序列化Payload',
    permissions:['exploit:run','rce:test'],
  },
  {
    id:'coercer', name:'Coercer', subtitle:'Windows身份验证强制',
    version:'2.4.3', author:'p0dalirius', category:'exploit', status:'available', installed:false,
    downloads:8, size:'1.4 MB', icon:'🧲', license:'GPL-3.0', featured:false,
    tags:['NTLM强制','Relay','AD域'],
    description:'强制Windows服务器发起NTLM认证请求，配合Responder/ntlmrelayx实施Relay攻击',
    permissions:['network:poison','smb:attack'],
  },
  {
    id:'kerbrute', name:'Kerbrute', subtitle:'Kerberos用户枚举与爆破',
    version:'1.0.3', author:'ropnop', category:'exploit', status:'available', installed:false,
    downloads:17, size:'4.1 MB', icon:'🎫', license:'MIT', featured:false,
    tags:['Kerberos','AS-REP','用户枚举'],
    description:'Kerberos预认证爆破与用户枚举，支持Password Spray和AS-REP Roasting',
    permissions:['kerberos:attack'],
  },

  // ── 后渗透补充 ────────────────────────────────────────────────────────────────
  {
    id:'sliver', name:'Sliver', subtitle:'开源C2框架',
    version:'1.5.43', author:'BishopFox', category:'post-exploit', status:'available', installed:false,
    downloads:19, size:'88 MB', icon:'🐍', license:'GPL-3.0', featured:true,
    tags:['C2','Beacon','隐蔽通信'],
    description:'现代化开源C2框架，支持mTLS/HTTP/DNS多协议，内置反溯源混淆、BOF执行',
    permissions:['c2:control','network:tunnel'],
  },
  {
    id:'havoc', name:'Havoc', subtitle:'现代后渗透C2框架',
    version:'0.7', author:'HavocFramework', category:'post-exploit', status:'available', installed:false,
    downloads:12, size:'65 MB', icon:'👾', license:'MIT', featured:false,
    tags:['C2','Demon','内存驻留'],
    description:'新一代C2框架，Demon植入体支持动态链接、进程注入、ETW/AMSI绕过',
    permissions:['c2:control'],
  },
  {
    id:'winpeas', name:'WinPEAS', subtitle:'Windows提权枚举',
    version:'20240101', author:'carlospolop', category:'post-exploit', status:'available', installed:false,
    downloads:27, size:'2.1 MB', icon:'🪟', license:'MIT', featured:false,
    tags:['Windows','提权','注册表'],
    description:'Windows权限提升路径自动枚举，检测AlwaysInstallElevated/服务弱权限/注册表敏感信息',
    permissions:['privesc:windows'],
  },
  {
    id:'ligolo_ng', name:'Ligolo-ng', subtitle:'反向隧道内网穿透',
    version:'0.6.2', author:'nicocha30', category:'post-exploit', status:'available', installed:false,
    downloads:15, size:'12.8 MB', icon:'🌉', license:'GPL-3.0', featured:false,
    tags:['内网穿透','隧道','TUN接口'],
    description:'轻量级反向代理隧道，无需SOCKS5，直接创建TUN接口访问内网，延迟低',
    permissions:['network:tunnel','lateral:move'],
  },
  {
    id:'bloodhound_ce', name:'BloodHound CE', subtitle:'AD攻击路径社区版',
    version:'5.4.0', author:'SpecterOps', category:'post-exploit', status:'available', installed:false,
    downloads:21, size:'120 MB', icon:'🩸', license:'Apache-2.0', featured:true,
    tags:['AD','域提权','最短路径'],
    description:'BloodHound社区版，图可视化展示AD域内最短权限提升路径，支持Cypher自定义查询',
    permissions:['ad:analyze','credential:dump'],
  },
  {
    id:'secretsdump', name:'secretsdump', subtitle:'域控哈希批量转储',
    version:'0.12.0', author:'SecureAuth', category:'post-exploit', status:'available', installed:false,
    downloads:16, size:'8.4 MB', icon:'🗄️', license:'Apache-2.0', featured:false,
    tags:['DC Sync','NTDS.dit','哈希转储'],
    description:'无需登录域控主机，远程执行DCSync导出全域NTLM哈希，支持VSS卷影复制',
    permissions:['credential:dump','smb:attack'],
  },

  // ── 密码破解补充 ──────────────────────────────────────────────────────────────
  {
    id:'medusa', name:'Medusa', subtitle:'并行在线密码爆破',
    version:'2.3', author:'JoMo-Kun', category:'brute-force', status:'available', installed:false,
    downloads:21, size:'1.8 MB', icon:'🪐', license:'GPL-2.0', featured:false,
    tags:['并行','在线爆破','多协议'],
    description:'高速并行在线密码爆破工具，支持SSH/FTP/HTTP/MySQL/RDP/SMB等20+协议',
    permissions:['brute:force'],
  },
  {
    id:'crunch', name:'Crunch', subtitle:'自定义密码字典生成',
    version:'3.6', author:'Mimayin', category:'brute-force', status:'available', installed:false,
    downloads:12, size:'0.3 MB', icon:'🌀', license:'GPL-2.0', featured:false,
    tags:['字典生成','规则','掩码'],
    description:'根据字符集和掩码规则生成自定义密码字典，支持管道直连hashcat/hydra',
    permissions:['hash:crack'],
  },
  {
    id:'cewl', name:'CeWL', subtitle:'目标网站字典爬取',
    version:'6.1', author:'Robin Wood', category:'brute-force', status:'available', installed:false,
    downloads:9, size:'0.5 MB', icon:'🕷️', license:'GPL-3.0', featured:false,
    tags:['社工字典','爬虫','词频'],
    description:'爬取目标网站关键词生成专属密码字典，结合社会工程学提升爆破成功率',
    permissions:['web:crawl','brute:force'],
  },
  {
    id:'hcxtools', name:'hcxtools', subtitle:'WiFi握手包破解套件',
    version:'6.3.4', author:'ZerBea', category:'brute-force', status:'available', installed:false,
    downloads:17, size:'2.2 MB', icon:'📶', license:'MIT', featured:false,
    tags:['WPA2','握手包','PMKID'],
    description:'WiFi哈希转换套件，捕获并转换WPA2握手包/PMKID为hashcat可用格式',
    permissions:['wireless:capture','hash:crack'],
  },

  // ── 代理工具补充 ──────────────────────────────────────────────────────────────
  {
    id:'proxychains', name:'ProxyChains-ng', subtitle:'全局代理链路由',
    version:'4.16', author:'haad', category:'proxy', status:'available', installed:false,
    downloads:44, size:'0.6 MB', icon:'⛓️', license:'GPL-2.0', featured:false,
    tags:['SOCKS5','代理链','匿名'],
    description:'强制任意程序通过SOCKS4/5代理，支持动态链/严格链/随机链，隐藏真实IP',
    permissions:['network:proxy'],
  },
  {
    id:'caido', name:'Caido', subtitle:'轻量Web渗透代理',
    version:'0.41.0', author:'Caido Labs', category:'proxy', status:'available', installed:false,
    downloads:22, size:'45 MB', icon:'🌊', license:'Free/Pro', featured:true,
    tags:['HTTP代理','Replay','轻量'],
    description:'新一代轻量级Web渗透代理，Rust编写，界面现代，内置Replay/Automate/Workflows',
    permissions:['http:intercept','http:replay'],
  },
  {
    id:'frida', name:'Frida', subtitle:'动态插桩逆向框架',
    version:'16.3.3', author:'Frida Project', category:'proxy', status:'available', installed:false,
    downloads:28, size:'8.4 MB', icon:'💉', license:'LGPL-2.1', featured:false,
    tags:['动态插桩','Hook','移动端'],
    description:'跨平台动态插桩框架，Hook iOS/Android/桌面应用函数，实时修改内存和行为',
    permissions:['process:hook','memory:read'],
  },

  // ── 报告生成补充 ──────────────────────────────────────────────────────────────
  {
    id:'pwndoc', name:'PwnDoc', subtitle:'渗透报告协作管理',
    version:'0.5.3', author:'pwndoc-ng', category:'reporting', status:'available', installed:false,
    downloads:15, size:'28 MB', icon:'📝', license:'MIT', featured:true,
    tags:['报告','漏洞库','Word模板'],
    description:'基于Web的渗透测试报告管理平台，内置漏洞描述库，支持Word模板批量导出',
    permissions:['report:write','finding:import','report:export'],
  },
  {
    id:'ghostwriter', name:'Ghostwriter', subtitle:'红队作战报告平台',
    version:'3.3.0', author:'GhostManager', category:'reporting', status:'available', installed:false,
    downloads:11, size:'350 MB', icon:'👻', license:'BSD', featured:false,
    tags:['红队','时间线','客户管理'],
    description:'红队项目管理与报告平台，记录作战时间线、IOC、发现项，自动生成执行摘要',
    permissions:['report:write','finding:manage'],
  },
  {
    id:'markdown_reporter', name:'Markdown 报告器', subtitle:'轻量Markdown报告导出',
    version:'1.1.0', author:'ClawAI Team', category:'reporting', status:'active', installed:true, enabled:true,
    downloads:33, size:'0.1 MB', icon:'✍️', license:'MIT', featured:false,
    tags:['Markdown','PDF','快速'],
    description:'将扫描结果一键导出为结构化Markdown报告，支持PDF/HTML转换，内置ClawAI模板',
    permissions:['report:write','report:export'],
  },

  // ── AI 技能库补充 ─────────────────────────────────────────────────────────────
  { id:'skill_sqli_time_blind',   name:'SQL 时间盲注',      subtitle:'延迟注入检测',     version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:8,  size:'0.2 MB', icon:'⏱️', license:'MIT', featured:false, tags:['SQL注入','时间盲注','Sleep'], description:'基于时间延迟的盲注检测，自动计算延迟阈值，支持MySQL/MSSQL/PostgreSQL语法', permissions:['sql:inject'] },
  { id:'skill_auth_bypass_sql',   name:'认证绕过注入',      subtitle:'登录表单SQL注入',  version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:15, size:'0.2 MB', icon:'🚪', license:'MIT', featured:false, tags:['认证绕过','登录','SQLi'],     description:'针对登录表单的SQL注入绕过，测试\'OR 1=1等经典Payload，自动识别绕过成功', permissions:['sql:inject','auth:bypass'] },
  { id:'skill_auth_bruteforce',   name:'认证暴力破解',      subtitle:'登录接口爆破',     version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:12, size:'0.2 MB', icon:'🔨', license:'MIT', featured:false, tags:['爆破','登录','字典'],         description:'登录接口暴力破解，支持表单和HTTP Basic认证，自动识别验证码和速率限制', permissions:['brute:force','auth:bypass'] },
  { id:'skill_info_backup_files', name:'备份文件探测',      subtitle:'敏感备份路径扫描', version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:10, size:'0.2 MB', icon:'🗃️', license:'MIT', featured:false, tags:['备份','信息泄露','敏感文件'], description:'扫描.bak/.zip/.tar/.sql等备份文件路径，发现源码泄露和数据库备份文件', permissions:['http:probe'] },
  { id:'skill_xss_stored',        name:'XSS 存储型注入',    subtitle:'持久化XSS检测',    version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:11, size:'0.2 MB', icon:'💾', license:'MIT', featured:false, tags:['XSS','存储型','持久化'],      description:'存储型XSS检测，注入持久化Payload并验证二次触发，适用于评论/留言等功能', permissions:['xss:test'] },
  { id:'skill_ssti_testing',      name:'SSTI 模板注入',      subtitle:'多引擎模板注入',   version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:9,  size:'0.2 MB', icon:'🧪', license:'MIT', featured:false, tags:['SSTI','Jinja2','Twig'],      description:'服务端模板注入检测，覆盖Jinja2/Twig/FreeMarker/Pebble等主流引擎，RCE验证', permissions:['ssti:test'] },
  { id:'skill_waf_detect',        name:'WAF 指纹识别',       subtitle:'15+WAF指纹库',     version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:14, size:'0.2 MB', icon:'🛡️', license:'MIT', featured:false, tags:['WAF','指纹','Bypass'],       description:'通过响应特征和Cookie识别15+主流WAF（Cloudflare/ModSecurity/Akamai等），推荐绕过策略', permissions:['http:probe'] },
  { id:'skill_idor_testing',      name:'IDOR 越权测试',      subtitle:'不安全直接对象引用', version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:13, size:'0.2 MB', icon:'🔄', license:'MIT', featured:false, tags:['IDOR','越权','水平越权'],    description:'自动化IDOR越权漏洞检测，替换用户ID/订单号等参数，验证未授权数据访问', permissions:['http:probe','auth:bypass'] },
  { id:'skill_file_upload',       name:'文件上传绕过',       subtitle:'上传点安全测试',   version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:16, size:'0.3 MB', icon:'📤', license:'MIT', featured:true,  tags:['文件上传','WebShell','绕过'], description:'测试文件上传点：MIME类型绕过、双扩展名、Content-Type伪造，尝试上传Webshell', permissions:['file:upload','rce:test'] },
  { id:'skill_csrf_testing',      name:'CSRF 跨站请求伪造',  subtitle:'CSRF漏洞检测',     version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:7,  size:'0.2 MB', icon:'🎣', license:'MIT', featured:false, tags:['CSRF','Token验证','SameSite'], description:'检测CSRF防护缺失，分析Token有效性、SameSite属性、Referer校验逻辑', permissions:['http:probe'] },
  { id:'skill_nosql_injection',   name:'NoSQL 注入',         subtitle:'MongoDB/Redis注入', version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:8,  size:'0.2 MB', icon:'🍃', license:'MIT', featured:false, tags:['NoSQL','MongoDB','注入'],    description:'NoSQL数据库注入检测，测试MongoDB操作符注入（$where/$regex）和Redis命令注入', permissions:['sql:inject'] },
  { id:'skill_deserialization',   name:'反序列化检测',       subtitle:'Java/.NET反序列化', version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:10, size:'0.3 MB', icon:'📦', license:'MIT', featured:false, tags:['反序列化','Java','RCE'],     description:'检测Java/PHP/.NET反序列化漏洞，发送序列化Gadget Chain探测RCE可行性', permissions:['exploit:run','rce:test'] },
  { id:'skill_openssh_enum',      name:'OpenSSH 用户枚举',   subtitle:'CVE-2018-15473',   version:'1.1.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:6,  size:'0.2 MB', icon:'🔑', license:'MIT', featured:false, tags:['SSH','用户枚举','CVE'],      description:'利用CVE-2018-15473枚举有效SSH用户名，为后续爆破攻击提供有效账户列表', permissions:['network:scan'] },
  { id:'skill_privesc_windows',   name:'Windows 提权',       subtitle:'Windows权限提升',  version:'1.0.0', author:'ClawAI Team', category:'skill', status:'active', installed:true, enabled:true, downloads:12, size:'0.3 MB', icon:'🪟', license:'MIT', featured:false, tags:['Windows','提权','SYSTEM'],  description:'Windows权限提升路径检测：服务弱权限/令牌模拟/AlwaysInstallElevated/计划任务', permissions:['privesc:windows'] },

  // ── AI 增强补充 ────────────────────────────────────────────────────────────────
  {
    id:'ai_recon_agent', name:'AI 侦察代理', subtitle:'自动化OSINT编排',
    version:'1.5.0', author:'ClawAI Team', category:'ai_enhanced', status:'active', installed:true, enabled:true,
    downloads:22, size:'0.6 MB', icon:'🕵️', license:'MIT', featured:true,
    tags:['OSINT','AI编排','自动化'],
    description:'LLM驱动的侦察编排代理，自动规划子域枚举→端口扫描→指纹识别→漏洞匹配全链路',
    permissions:['llm:call','osint:collect','network:scan'],
  },
  {
    id:'ai_report_gen', name:'AI 报告生成器', subtitle:'智能漏洞报告撰写',
    version:'2.1.0', author:'ClawAI Team', category:'ai_enhanced', status:'active', installed:true, enabled:true,
    downloads:36, size:'0.5 MB', icon:'📊', license:'MIT', featured:true,
    tags:['报告','LLM','漏洞描述'],
    description:'LLM自动撰写专业渗透测试报告，根据发现项生成漏洞描述、风险评级、修复建议',
    permissions:['llm:call','finding:read','report:write'],
  },
  {
    id:'ai_vuln_correlator', name:'AI 漏洞关联器', subtitle:'多漏洞攻击链分析',
    version:'1.0.0', author:'ClawAI Team', category:'ai_enhanced', status:'active', installed:true, enabled:true,
    downloads:18, size:'0.4 MB', icon:'🧠', license:'MIT', featured:false,
    tags:['攻击链','关联分析','AI'],
    description:'分析多个低危漏洞的组合利用可能性，AI推断攻击链并给出CVSS综合评分',
    permissions:['llm:call','finding:read','finding:report'],
  },
  {
    id:'spring4shell_scanner', name:'Spring4Shell 检测器', subtitle:'CVE-2022-22965专项',
    version:'1.1.0', author:'ClawAI Team', category:'ai_enhanced', status:'active', installed:true, enabled:true,
    downloads:28, size:'0.4 MB', icon:'🌱', license:'MIT', featured:false,
    tags:['Spring','RCE','CVE-2022'],
    description:'CVE-2022-22965 Spring Framework RCE专项检测，支持多版本Payload自动适配',
    permissions:['http:request','finding:report'],
  },
  {
    id:'shiro_scanner', name:'Shiro 反序列化检测器', subtitle:'Apache Shiro CVE专项',
    version:'1.0.3', author:'ClawAI Team', category:'ai_enhanced', status:'active', installed:true, enabled:true,
    downloads:19, size:'0.3 MB', icon:'🏯', license:'MIT', featured:false,
    tags:['Shiro','CVE-2016-4437','RememberMe'],
    description:'Apache Shiro RememberMe反序列化RCE检测，自动枚举常见密钥并生成利用载荷',
    permissions:['http:request','exploit:run','finding:report'],
  },
  {
    id:'graphql_cop', name:'GraphQL Cop', subtitle:'GraphQL安全审计',
    version:'1.4', author:'dolevf', category:'ai_enhanced', status:'available', installed:false,
    downloads:13, size:'0.7 MB', icon:'⬡', license:'MIT', featured:false,
    tags:['GraphQL','内省','批量查询'],
    description:'GraphQL API安全审计工具，检测内省开放、批量查询DoS、字段建议泄露等10+安全问题',
    permissions:['http:request','finding:report'],
  },
];

const FEATURED_IDS = ALL_PLUGINS.filter(p => p.featured).map(p => p.id);

/* ─────────────────────────────────────────
   Helpers
───────────────────────────────────────── */
const fmtDl = n => String(n);

const catColor = (id) => CATEGORIES.find(c => c.id === id)?.color ?? '#94a3b8';
const catName  = (id) => CATEGORIES.find(c => c.id === id)?.name  ?? id;

const statusMeta = {
  active:    { label: '已激活', color: '#22c55e', dot: 'bg-green-400' },
  inactive:  { label: '已禁用', color: '#f97316', dot: 'bg-orange-400' },
  available: { label: '可安装', color: '#3b82f6', dot: 'bg-blue-400' },
  updating:  { label: '更新中', color: '#eab308', dot: 'bg-yellow-400' },
  error:     { label: '错误',   color: '#ef4444', dot: 'bg-red-400' },
};

function highlight(text, term) {
  if (!term) return text;
  const idx = text.toLowerCase().indexOf(term.toLowerCase());
  if (idx === -1) return text;
  return (
    <>
      {text.slice(0, idx)}
      <mark className="bg-cyan-500/30 text-cyan-200 rounded px-0.5">{text.slice(idx, idx + term.length)}</mark>
      {text.slice(idx + term.length)}
    </>
  );
}

/* ─────────────────────────────────────────
   Sub-components
───────────────────────────────────────── */

/** 顶部 Banner：精选插件轮播 */
function FeaturedBanner({ plugins, onInstall, onSelect }) {
  const featured = plugins.filter(p => p.featured);
  const [idx, setIdx] = useState(0);
  const p = featured[idx % featured.length];
  if (!p) return null;

  return (
    <div
      className="relative rounded-xl overflow-hidden mb-8"
      style={{
        background: 'linear-gradient(135deg, #0a0e17 0%, #111827 50%, #0a0e17 100%)',
        border: '1px solid rgba(0,212,255,0.2)',
        boxShadow: '0 0 40px rgba(0,212,255,0.06)',
      }}
    >
      {/* 扫描线动画 */}
      <div className="absolute inset-0 pointer-events-none"
        style={{ backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,212,255,0.015) 2px, rgba(0,212,255,0.015) 4px)' }}
      />
      <div className="relative flex items-center gap-8 p-8">
        {/* 大图标 */}
        <div className="shrink-0 w-24 h-24 rounded-2xl flex items-center justify-center text-5xl"
          style={{ background: 'rgba(0,212,255,0.08)', border: '1px solid rgba(0,212,255,0.2)' }}>
          {p.icon}
        </div>
        {/* 信息 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1">
            <span className="text-xs font-mono px-2 py-0.5 rounded"
              style={{ background: 'rgba(0,212,255,0.12)', color: '#00d4ff', border: '1px solid rgba(0,212,255,0.25)' }}>
              ★ 精选推荐
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full"
              style={{ background: `${catColor(p.category)}20`, color: catColor(p.category), border: `1px solid ${catColor(p.category)}40` }}>
              {catName(p.category)}
            </span>
          </div>
          <h2 className="text-2xl font-bold text-white mb-1">{p.name}
            <span className="ml-2 text-base font-normal text-gray-400">{p.subtitle}</span>
          </h2>
          <p className="text-gray-400 text-sm mb-3 line-clamp-2">{p.description}</p>
          <div className="flex items-center gap-6 text-sm text-gray-500">
            <span className="flex items-center gap-1"><Download size={13} /> {fmtDl(p.downloads)} 次安装</span>
            <span>{p.size}</span>
            <span className="font-mono text-xs text-gray-600">v{p.version}</span>
          </div>
        </div>
        {/* 操作 */}
        <div className="shrink-0 flex flex-col gap-3">
          {p.installed ? (
            <div className="flex items-center gap-2 px-4 py-2 rounded-lg text-green-400 text-sm"
              style={{ background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.25)' }}>
              <CheckCircle size={14} /> 已安装
            </div>
          ) : (
            <button onClick={() => onInstall(p.id)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all hover:scale-105"
              style={{ background: 'linear-gradient(135deg, #00d4ff, #8b5cf6)', color: '#000' }}>
              <Download size={14} /> 立即安装
            </button>
          )}
          <button onClick={() => onSelect(p)}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm text-gray-300 hover:text-white transition-colors"
            style={{ border: '1px solid rgba(255,255,255,0.1)' }}>
            <Info size={14} /> 查看详情
          </button>
        </div>
      </div>
      {/* 轮播点 */}
      <div className="flex items-center justify-center gap-2 pb-4">
        {featured.map((_, i) => (
          <button key={i} onClick={() => setIdx(i)}
            className="w-1.5 h-1.5 rounded-full transition-all"
            style={{ background: i === idx % featured.length ? '#00d4ff' : 'rgba(255,255,255,0.2)', width: i === idx % featured.length ? 24 : 6 }}
          />
        ))}
      </div>
    </div>
  );
}

/** 安装进度动画 */
function InstallProgress({ pluginId, onDone }) {
  const [pct, setPct] = useState(0);
  const [phase, setPhase] = useState('downloading'); // downloading → verifying → installing → done
  const phases = ['downloading', 'verifying', 'installing'];
  const labels = { downloading: '下载中...', verifying: '安全校验...', installing: '安装中...' };

  useEffect(() => {
    let v = 0;
    const t = setInterval(() => {
      v += Math.random() * 8 + 2;
      if (v >= 100) { v = 100; clearInterval(t); setPhase('done'); setTimeout(onDone, 600); }
      setPct(Math.min(v, 100));
      if (v > 33 && phase === 'downloading') setPhase('verifying');
      if (v > 66 && phase === 'verifying')   setPhase('installing');
    }, 80);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="mt-3 space-y-1.5">
      <div className="flex items-center justify-between text-xs text-gray-400">
        <span>{labels[phase] ?? '完成'}</span>
        <span className="font-mono">{pct.toFixed(0)}%</span>
      </div>
      <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.08)' }}>
        <div className="h-full rounded-full transition-all duration-100"
          style={{
            width: `${pct}%`,
            background: pct < 100
              ? 'linear-gradient(90deg, #00d4ff, #8b5cf6)'
              : 'linear-gradient(90deg, #22c55e, #00d4ff)',
            boxShadow: '0 0 8px rgba(0,212,255,0.6)',
          }}
        />
      </div>
    </div>
  );
}

/** 单张插件卡片 */
function PluginCard({ plugin, searchTerm, onInstall, onToggle, onUninstall, onSelect, installing }) {
  const sm = statusMeta[plugin.status] ?? statusMeta.available;
  const cc = catColor(plugin.category);
  const [showProgress, setShowProgress] = useState(false);

  const doInstall = () => {
    setShowProgress(true);
    onInstall(plugin.id);
  };

  return (
    <div
      className="group relative rounded-xl p-5 transition-all duration-300 cursor-pointer flex flex-col gap-3"
      style={{
        background: 'rgba(10,14,23,0.8)',
        border: `1px solid rgba(255,255,255,0.07)`,
        boxShadow: '0 2px 12px rgba(0,0,0,0.3)',
      }}
      onMouseEnter={e => { e.currentTarget.style.border = `1px solid ${cc}40`; e.currentTarget.style.boxShadow = `0 4px 24px ${cc}12`; }}
      onMouseLeave={e => { e.currentTarget.style.border = '1px solid rgba(255,255,255,0.07)'; e.currentTarget.style.boxShadow = '0 2px 12px rgba(0,0,0,0.3)'; }}
    >
      {/* 类别颜色条 */}
      <div className="absolute top-0 left-0 right-0 h-0.5 rounded-t-xl" style={{ background: `linear-gradient(90deg, ${cc}, transparent)` }} />

      {/* 顶部：图标 + 名称 + 状态 */}
      <div className="flex items-start gap-3">
        <div className="shrink-0 w-11 h-11 rounded-xl flex items-center justify-center text-2xl"
          style={{ background: `${cc}15`, border: `1px solid ${cc}30` }}>
          {plugin.icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-white text-sm">{highlight(plugin.name, searchTerm)}</span>
            {plugin.featured && (
              <span className="text-[10px] px-1.5 py-0.5 rounded font-mono"
                style={{ background: 'rgba(0,212,255,0.12)', color: '#00d4ff', border: '1px solid rgba(0,212,255,0.2)' }}>★</span>
            )}
          </div>
          <div className="text-xs text-gray-500 truncate">{highlight(plugin.subtitle, searchTerm)}</div>
        </div>
        {/* 状态点 */}
        <div className={`w-2 h-2 rounded-full mt-1 shrink-0 ${sm.dot}`} title={sm.label} />
      </div>

      {/* 描述 */}
      <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed">{highlight(plugin.description, searchTerm)}</p>

      {/* 标签 */}
      <div className="flex flex-wrap gap-1">
        {plugin.tags.slice(0, 3).map(t => (
          <span key={t} className="text-[10px] px-1.5 py-0.5 rounded-full"
            style={{ background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.5)', border: '1px solid rgba(255,255,255,0.08)' }}>
            {t}
          </span>
        ))}
      </div>

      {/* 元数据行 */}
      <div className="flex items-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1"><Download size={11} />{fmtDl(plugin.downloads)}</span>
        <span>{plugin.size}</span>
        <span className="ml-auto font-mono text-[10px] text-gray-600">v{plugin.version}</span>
      </div>

      {/* 安装进度条 */}
      {showProgress && installing === plugin.id && (
        <InstallProgress pluginId={plugin.id} onDone={() => setShowProgress(false)} />
      )}

      {/* 操作按钮 */}
      <div className="flex items-center gap-2 pt-1 border-t border-white/[0.06]">
        <button onClick={() => onSelect(plugin)}
          className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors px-2 py-1 rounded"
          style={{ background: 'rgba(255,255,255,0.04)' }}>
          <Info size={11} /> 详情
        </button>
        <div className="flex-1" />
        {plugin.installed ? (
          <>
            <button onClick={() => onToggle(plugin.id)}
              className="flex items-center gap-1 text-xs px-2.5 py-1 rounded transition-all"
              style={{ background: plugin.enabled ? 'rgba(239,68,68,0.1)' : 'rgba(34,197,94,0.1)', color: plugin.enabled ? '#f87171' : '#4ade80', border: `1px solid ${plugin.enabled ? 'rgba(239,68,68,0.2)' : 'rgba(34,197,94,0.2)'}` }}>
              {plugin.enabled ? <><StopCircle size={11} /> 禁用</> : <><Play size={11} /> 启用</>}
            </button>
            <button onClick={() => onUninstall(plugin.id)}
              className="text-xs p-1.5 rounded text-gray-600 hover:text-red-400 transition-colors"
              style={{ border: '1px solid rgba(255,255,255,0.06)' }}>
              <Trash2 size={11} />
            </button>
          </>
        ) : plugin.status === 'updating' ? (
          <span className="flex items-center gap-1 text-xs text-yellow-400 px-2.5 py-1 rounded"
            style={{ background: 'rgba(234,179,8,0.1)', border: '1px solid rgba(234,179,8,0.2)' }}>
            <RefreshCw size={11} className="animate-spin" /> 更新中
          </span>
        ) : (
          <button onClick={doInstall}
            className="flex items-center gap-1 text-xs px-3 py-1.5 rounded font-semibold transition-all hover:scale-105"
            style={{ background: 'linear-gradient(135deg, rgba(0,212,255,0.8), rgba(139,92,246,0.8))', color: '#fff' }}>
            <Download size={11} /> 安装
          </button>
        )}
      </div>
    </div>
  );
}

/** 详情弹窗 */
function DetailModal({ plugin, onClose, onInstall, onToggle, onUninstall }) {
  if (!plugin) return null;
  const cc = catColor(plugin.category);
  const sm = statusMeta[plugin.status] ?? statusMeta.available;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)' }}>
      <div className="relative w-full max-w-xl rounded-2xl overflow-hidden"
        style={{ background: '#0a0e17', border: `1px solid ${cc}30`, boxShadow: `0 0 60px ${cc}15` }}>
        {/* 顶部色带 */}
        <div className="h-1" style={{ background: `linear-gradient(90deg, ${cc}, #8b5cf6)` }} />
        <div className="p-6">
          {/* 头部 */}
          <div className="flex items-start gap-4 mb-6">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-4xl shrink-0"
              style={{ background: `${cc}15`, border: `1px solid ${cc}30` }}>
              {plugin.icon}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <h3 className="text-xl font-bold text-white">{plugin.name}</h3>
                <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: `${cc}20`, color: cc, border: `1px solid ${cc}40` }}>{catName(plugin.category)}</span>
                <span className={`w-2 h-2 rounded-full ${sm.dot}`} />
                <span className="text-xs text-gray-500">{sm.label}</span>
              </div>
              <p className="text-sm text-gray-400">{plugin.subtitle}</p>
            </div>
            <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors p-1">
              <X size={18} />
            </button>
          </div>

          {/* 描述 */}
          <p className="text-sm text-gray-300 leading-relaxed mb-5">{plugin.description}</p>

          {/* 元数据网格 */}
          <div className="grid grid-cols-2 gap-3 mb-5">
            {[
              ['作者', plugin.author],
              ['版本', `v${plugin.version}`],
              ['大小', plugin.size],
              ['许可证', plugin.license],
              ['安装量', `${fmtDl(plugin.downloads)} 次`],
            ].map(([k, v]) => (
              <div key={k} className="rounded-lg px-3 py-2" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}>
                <div className="text-[10px] text-gray-600 mb-0.5">{k}</div>
                <div className="text-sm text-gray-200 font-mono">{v}</div>
              </div>
            ))}
          </div>

          {/* 标签 */}
          <div className="flex flex-wrap gap-1.5 mb-5">
            {plugin.tags.map(t => (
              <span key={t} className="text-xs px-2 py-1 rounded-full"
                style={{ background: `${cc}10`, color: cc, border: `1px solid ${cc}25` }}>
                {t}
              </span>
            ))}
          </div>

          {/* 权限 */}
          <div className="mb-6">
            <div className="text-xs text-gray-500 mb-2 flex items-center gap-1"><Lock size={11} /> 所需权限</div>
            <div className="flex flex-wrap gap-1.5">
              {plugin.permissions.map(p => (
                <span key={p} className="text-[10px] px-2 py-0.5 rounded font-mono"
                  style={{ background: 'rgba(239,68,68,0.08)', color: '#fca5a5', border: '1px solid rgba(239,68,68,0.15)' }}>
                  {p}
                </span>
              ))}
            </div>
          </div>

          {/* 操作 */}
          <div className="flex gap-3">
            <button onClick={onClose}
              className="flex-1 py-2.5 rounded-lg text-sm text-gray-400 hover:text-white transition-colors"
              style={{ border: '1px solid rgba(255,255,255,0.1)' }}>
              关闭
            </button>
            {plugin.installed ? (
              <>
                <button onClick={() => { onToggle(plugin.id); onClose(); }}
                  className="flex-1 py-2.5 rounded-lg text-sm transition-all"
                  style={{ background: plugin.enabled ? 'rgba(239,68,68,0.15)' : 'rgba(34,197,94,0.15)', color: plugin.enabled ? '#f87171' : '#4ade80', border: `1px solid ${plugin.enabled ? 'rgba(239,68,68,0.3)' : 'rgba(34,197,94,0.3)'}` }}>
                  {plugin.enabled ? '禁用插件' : '启用插件'}
                </button>
                <button onClick={() => { onUninstall(plugin.id); onClose(); }}
                  className="flex-1 py-2.5 rounded-lg text-sm text-red-400 hover:text-red-300 transition-colors"
                  style={{ border: '1px solid rgba(239,68,68,0.2)' }}>
                  卸载
                </button>
              </>
            ) : (
              <button onClick={() => { onInstall(plugin.id); onClose(); }}
                className="flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all hover:scale-105"
                style={{ background: 'linear-gradient(135deg, #00d4ff, #8b5cf6)', color: '#000' }}>
                <Download size={14} className="inline mr-1.5" /> 安装插件
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────
   Main Component
───────────────────────────────────────── */
const PluginManager = () => {
  const [plugins, setPlugins]           = useState(ALL_PLUGINS);
  const [loading, setLoading]           = useState(true);
  const [searchTerm, setSearchTerm]     = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [activeTab, setActiveTab]       = useState('marketplace'); // marketplace | installed | updates
  const [sortBy, setSortBy]             = useState('downloads');    // downloads | name | newest
  const [selectedPlugin, setSelectedPlugin] = useState(null);
  const [installing, setInstalling]     = useState(null); // pluginId currently installing

  useEffect(() => {
    // 插件商城使用本地静态数据，不依赖后端认证
    setPlugins(ALL_PLUGINS);
    setLoading(false);
  }, []);

  /* ── Derived lists ── */
  const visiblePlugins = (() => {
    let list = [...plugins];
    if (activeTab === 'installed') list = list.filter(p => p.installed);
    if (activeTab === 'updates')   list = list.filter(p => p.status === 'updating');
    if (activeCategory !== 'all')  list = list.filter(p => p.category === activeCategory);
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      list = list.filter(p =>
        p.name.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q) ||
        p.tags.some(t => t.toLowerCase().includes(q)) ||
        p.author.toLowerCase().includes(q)
      );
    }
    switch (sortBy) {
      case 'downloads': list.sort((a, b) => b.downloads - a.downloads); break;
      case 'name':      list.sort((a, b) => a.name.localeCompare(b.name)); break;
      case 'newest':    list.sort((a, b) => b.version.localeCompare(a.version)); break;
      default:          list.sort((a, b) => b.downloads - a.downloads); break;
    }
    return list;
  })();

  const installedCount = plugins.filter(p => p.installed).length;
  const activeCount    = plugins.filter(p => p.enabled).length;
  const updateCount    = plugins.filter(p => p.status === 'updating').length;
  const availableCount = plugins.filter(p => !p.installed).length;

  /* ── Handlers ── */
  const handleInstall = async (id) => {
    setInstalling(id);
    try {
      await pluginService.installPlugin(id);
    } catch (_) {}
    setTimeout(() => {
      setPlugins(prev => prev.map(p => p.id === id ? { ...p, installed: true, enabled: true, status: 'active' } : p));
      setInstalling(null);
    }, 3200);
  };

  const handleToggle = async (id) => {
    const p = plugins.find(x => x.id === id);
    if (!p) return;
    try {
      p.enabled ? await pluginService.disablePlugin(id) : await pluginService.enablePlugin(id);
    } catch (_) {}
    setPlugins(prev => prev.map(x => x.id === id ? { ...x, enabled: !x.enabled, status: !x.enabled ? 'active' : 'inactive' } : x));
  };

  const handleUninstall = (id) => {
    const p = plugins.find(x => x.id === id);
    if (!p || !window.confirm(`确定卸载 "${p.name}"？`)) return;
    pluginService.uninstallPlugin(id).catch(() => {});
    setPlugins(prev => prev.map(x => x.id === id ? { ...x, installed: false, enabled: false, status: 'available' } : x));
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: '#060910' }}>
      <div className="text-center space-y-4">
        <div className="w-12 h-12 rounded-full border-2 border-t-cyan-400 border-cyan-400/20 animate-spin mx-auto" />
        <p className="text-gray-500 text-sm font-mono">加载插件商城...</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen text-white" style={{ background: '#060910' }}>

      {/* ── 顶部导航栏 ── */}
      <div className="sticky top-0 z-40"
        style={{ background: 'rgba(6,9,16,0.95)', backdropFilter: 'blur(16px)', borderBottom: '1px solid rgba(0,212,255,0.1)' }}>
        <div className="max-w-screen-xl mx-auto px-6 py-3 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Package size={18} className="text-cyan-400" />
            <span className="font-bold text-sm tracking-wider" style={{ color: '#00d4ff' }}>PLUGIN STORE</span>
            <span className="text-xs text-gray-600 font-mono">v2.0</span>
          </div>
          {/* 搜索框 */}
          <div className="flex-1 max-w-md relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              placeholder="搜索插件、工具、技能..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm rounded-lg outline-none transition-all"
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: '#e2e8f0' }}
              onFocus={e => { e.target.style.border = '1px solid rgba(0,212,255,0.4)'; e.target.style.boxShadow = '0 0 12px rgba(0,212,255,0.1)'; }}
              onBlur={e => { e.target.style.border = '1px solid rgba(255,255,255,0.08)'; e.target.style.boxShadow = 'none'; }}
            />
            {searchTerm && (
              <button onClick={() => setSearchTerm('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
                <X size={13} />
              </button>
            )}
          </div>
          {/* 排序 */}
          <select value={sortBy} onChange={e => setSortBy(e.target.value)}
            className="text-xs px-3 py-2 rounded-lg outline-none"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: '#94a3b8' }}>
            <option value="downloads">最多下载</option>
            <option value="name">名称排序</option>
            <option value="newest">最新版本</option>
          </select>
          {/* 上传 */}
          <button className="flex items-center gap-1.5 text-xs px-3 py-2 rounded-lg text-gray-400 hover:text-gray-200 transition-colors"
            style={{ border: '1px solid rgba(255,255,255,0.1)' }}>
            <Upload size={12} /> 上传插件
          </button>
        </div>
        {/* Tab 行 */}
        <div className="max-w-screen-xl mx-auto px-6 flex items-center gap-1 pb-0">
          {[
            { id: 'marketplace', label: '插件商城', count: availableCount + installedCount },
            { id: 'installed',   label: '已安装',   count: installedCount },
            { id: 'updates',     label: '待更新',   count: updateCount },
          ].map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)}
              className="px-4 py-2.5 text-sm font-medium border-b-2 transition-all"
              style={{ borderColor: activeTab === t.id ? '#00d4ff' : 'transparent', color: activeTab === t.id ? '#00d4ff' : '#6b7280' }}>
              {t.label}
              {t.count > 0 && (
                <span className="ml-1.5 text-xs px-1.5 py-0.5 rounded-full"
                  style={{ background: activeTab === t.id ? 'rgba(0,212,255,0.15)' : 'rgba(255,255,255,0.06)', color: activeTab === t.id ? '#00d4ff' : '#6b7280' }}>
                  {t.count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="max-w-screen-xl mx-auto px-6 py-6 flex gap-6">

        {/* ── 左侧：分类侧边栏 ── */}
        <aside className="w-48 shrink-0 space-y-1">
          <div className="text-[10px] text-gray-600 font-mono mb-3 pl-2">CATEGORIES</div>
          {CATEGORIES.map(cat => {
            const count = plugins.filter(p => cat.id === 'all' || p.category === cat.id).length;
            const Icon = cat.icon;
            return (
              <button key={cat.id} onClick={() => setActiveCategory(cat.id)}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all text-left"
                style={{
                  background: activeCategory === cat.id ? `${cat.color}15` : 'transparent',
                  border: `1px solid ${activeCategory === cat.id ? `${cat.color}30` : 'transparent'}`,
                  color: activeCategory === cat.id ? cat.color : '#6b7280',
                }}>
                <Icon size={13} />
                <span className="flex-1 truncate">{cat.name}</span>
                <span className="text-[10px] font-mono opacity-60">{count}</span>
              </button>
            );
          })}

          {/* 统计小卡片 */}
          <div className="pt-4 space-y-2">
            <div className="text-[10px] text-gray-600 font-mono mb-2 pl-2">STATS</div>
            {[
              { label: '已安装', value: installedCount, color: '#22c55e' },
              { label: '已激活', value: activeCount,    color: '#00d4ff' },
              { label: '待更新', value: updateCount,    color: '#eab308' },
            ].map(s => (
              <div key={s.label} className="flex items-center justify-between px-3 py-2 rounded-lg"
                style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                <span className="text-xs text-gray-500">{s.label}</span>
                <span className="text-sm font-bold font-mono" style={{ color: s.color }}>{s.value}</span>
              </div>
            ))}
          </div>
        </aside>

        {/* ── 主体内容 ── */}
        <main className="flex-1 min-w-0">
          {/* 精选 Banner（仅商城首页+无搜索时显示） */}
          {activeTab === 'marketplace' && !searchTerm && activeCategory === 'all' && (
            <FeaturedBanner plugins={plugins} onInstall={handleInstall} onSelect={setSelectedPlugin} />
          )}

          {/* 结果信息行 */}
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm text-gray-500">
              {searchTerm
                ? <><span className="text-gray-200">{visiblePlugins.length}</span> 个结果 · 搜索 "<span className="text-cyan-400">{searchTerm}</span>"</>
                : <><span className="text-gray-200">{visiblePlugins.length}</span> 个插件</>
              }
            </div>
          </div>

          {/* 插件网格 */}
          {visiblePlugins.length === 0 ? (
            <div className="text-center py-24 text-gray-600">
              <Package size={48} className="mx-auto mb-4 opacity-30" />
              <p className="text-lg mb-1">未找到匹配插件</p>
              <p className="text-sm">尝试调整搜索词或类别筛选</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {visiblePlugins.map(plugin => (
                <PluginCard
                  key={plugin.id}
                  plugin={plugin}
                  searchTerm={searchTerm}
                  onInstall={handleInstall}
                  onToggle={handleToggle}
                  onUninstall={handleUninstall}
                  onSelect={setSelectedPlugin}
                  installing={installing}
                />
              ))}
            </div>
          )}
        </main>
      </div>

      {/* 详情弹窗 */}
      {selectedPlugin && (
        <DetailModal
          plugin={selectedPlugin}
          onClose={() => setSelectedPlugin(null)}
          onInstall={handleInstall}
          onToggle={handleToggle}
          onUninstall={handleUninstall}
        />
      )}
    </div>
  );
};

export default PluginManager;
