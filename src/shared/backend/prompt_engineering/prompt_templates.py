# -*- coding: utf-8 -*-
"""
提示模板模块
定义和管理不同类型的提示模板
"""

class PromptTemplates:
    """提示模板类"""
    
    def __init__(self):
        self.templates = {
            "reconnaissance": self._get_reconnaissance_template(),
            "scanning": self._get_scanning_template(),
            "exploitation": self._get_exploitation_template(),
            "post_exploitation": self._get_post_exploitation_template(),
            "reporting": self._get_reporting_template(),
            "ctf": self._get_ctf_template(),
            "web_application": self._get_web_application_template(),
            "network": self._get_network_template(),
            "privilege_escalation": self._get_privilege_escalation_template(),
            "password_cracking": self._get_password_cracking_template(),
            "vulnerability_analysis": self._get_vulnerability_analysis_template()
        }
    
    def _get_reconnaissance_template(self):
        """侦察阶段提示模板"""
        return """
你是一个专业的渗透测试人员，现在需要对目标进行侦察。

目标信息:
- 目标: {target}
- 目标类型: {target_type}

请执行以下侦察任务:
1. 收集目标的基本信息，包括IP地址、域名信息、WHOIS信息等
2. 进行子域名枚举，发现所有可能的子域名
3. 收集目标的网络信息，包括开放端口、运行的服务等
4. 收集目标的Web应用信息，包括使用的技术栈、CMS类型等
5. 收集目标的员工信息，包括邮箱、社交媒体账号等

请使用以下工具进行侦察:
- subfinder: 用于子域名枚举
- amass: 用于子域名枚举和信息收集
- nmap: 用于端口扫描和服务探测
- theHarvester: 用于电子邮件和子域名收集
- recon-ng: 用于Web侦察

请提供详细的侦察结果，包括所有发现的信息。
"""
    
    def _get_scanning_template(self):
        """扫描阶段提示模板"""
        return """
你是一个专业的渗透测试人员，现在需要对目标进行漏洞扫描。

目标信息:
- 目标: {target}
- 目标类型: {target_type}
- 侦察结果: {reconnaissance_result}

请执行以下扫描任务:
1. 对目标进行漏洞扫描，发现所有可能的漏洞
2. 对Web应用进行详细的安全扫描
3. 检查目标的SSL/TLS配置
4. 检查目标的WAF配置
5. 扫描目标的目录和文件，发现敏感信息

请使用以下工具进行扫描:
- nmap: 用于漏洞扫描
- nuclei: 用于漏洞扫描
- sqlmap: 用于SQL注入扫描
- nikto: 用于Web服务器扫描
- gobuster: 用于目录爆破
- dirsearch: 用于目录扫描
- testssl.sh: 用于SSL/TLS安全测试
- wafw00f: 用于WAF检测

请提供详细的扫描结果，包括所有发现的漏洞和安全问题。
"""
    
    def _get_exploitation_template(self):
        """利用阶段提示模板"""
        return """
你是一个专业的渗透测试人员，现在需要对目标进行漏洞利用。

目标信息:
- 目标: {target}
- 目标类型: {target_type}
- 扫描结果: {scanning_result}

请执行以下利用任务:
1. 利用发现的漏洞获取目标系统的访问权限
2. 尝试获取目标系统的shell
3. 尝试获取目标系统的敏感信息
4. 尝试绕过目标的安全措施

请使用以下工具进行利用:
- metasploit: 用于漏洞利用
- msfvenom: 用于生成payload
- searchsploit: 用于搜索漏洞利用代码

请提供详细的利用结果，包括所有成功的利用和获取的访问权限。
"""
    
    def _get_post_exploitation_template(self):
        """后渗透阶段提示模板"""
        return """
你是一个专业的渗透测试人员，现在需要进行后渗透测试。

目标信息:
- 目标: {target}
- 目标类型: {target_type}
- 利用结果: {exploitation_result}

请执行以下后渗透任务:
1. 进行权限提升，获取更高的系统权限
2. 进行横向移动，访问更多的系统和资源
3. 建立持久化访问，确保能够再次访问目标系统
4. 清除痕迹，删除所有操作记录
5. 收集目标系统的敏感信息

请使用以下工具进行后渗透测试:
- metasploit: 用于后渗透测试
- hashcat: 用于密码破解
- john: 用于密码破解
- hydra: 用于暴力破解

请提供详细的后渗透测试结果，包括所有获取的权限和收集的信息。
"""
    
    def _get_reporting_template(self):
        """报告阶段提示模板"""
        return """
你是一个专业的渗透测试人员，现在需要生成渗透测试报告。

目标信息:
- 目标: {target}
- 目标类型: {target_type}
- 测试结果: {test_results}

请生成一份详细的渗透测试报告，包括以下内容:
1. 执行摘要: 简要描述测试的目的、范围和结果
2. 测试方法: 描述使用的测试方法和工具
3. 发现的漏洞: 详细描述所有发现的漏洞，包括严重程度、影响和修复建议
4. 攻击路径: 描述成功的攻击路径和获取的访问权限
5. 修复建议: 提供详细的修复建议和安全最佳实践
6. 结论: 总结测试结果和安全建议

报告应该专业、详细、清晰，便于技术和非技术人员理解。
"""
    
    def _get_ctf_template(self):
        """CTF挑战提示模板"""
        return """
你是一个专业的CTF选手，现在需要解决CTF挑战。

挑战信息:
- 挑战名称: {challenge_name}
- 挑战描述: {challenge_description}
- 目标: {target}
- 难度: {difficulty}

请执行以下任务:
1. 分析挑战的要求和目标
2. 发现挑战中的漏洞或线索
3. 利用漏洞或线索获取flag
4. 提供详细的解题过程

请使用以下工具解决挑战:
- nmap: 用于端口扫描
- sqlmap: 用于SQL注入
- gobuster: 用于目录爆破
- hashcat: 用于密码破解
- metasploit: 用于漏洞利用

请提供详细的解题过程，包括所有发现的线索和获取的flag。
"""
    
    def _get_web_application_template(self):
        """Web应用测试提示模板"""
        return """
你是一个专业的Web应用安全测试人员，现在需要测试Web应用的安全性。

应用信息:
- 目标URL: {target_url}
- 应用类型: {application_type}
- 技术栈: {tech_stack}

请执行以下测试任务:
1. 测试SQL注入漏洞
2. 测试XSS漏洞
3. 测试CSRF漏洞
4. 测试认证和授权漏洞
5. 测试文件上传漏洞
6. 测试目录遍历漏洞
7. 测试命令注入漏洞
8. 测试敏感信息泄露

请使用以下工具进行测试:
- sqlmap: 用于SQL注入测试
- nikto: 用于Web服务器扫描
- gobuster: 用于目录爆破
- dirsearch: 用于目录扫描
- nuclei: 用于漏洞扫描

请提供详细的测试结果，包括所有发现的漏洞和安全问题。
"""
    
    def _get_network_template(self):
        """网络安全测试提示模板"""
        return """
你是一个专业的网络安全测试人员，现在需要测试网络的安全性。

网络信息:
- 目标网络: {target_network}
- 网络范围: {network_range}

请执行以下测试任务:
1. 进行网络扫描，发现所有活动的主机
2. 进行端口扫描，发现开放的端口和服务
3. 进行漏洞扫描，发现网络中的漏洞
4. 测试网络设备的安全性
5. 测试网络访问控制的有效性

请使用以下工具进行测试:
- nmap: 用于网络扫描和端口扫描
- masscan: 用于高速网络扫描
- rustscan: 用于快速端口扫描
- unicornscan: 用于异步网络扫描

请提供详细的测试结果，包括所有发现的主机、端口、服务和漏洞。
"""
    
    def _get_privilege_escalation_template(self):
        """权限提升提示模板"""
        return """
你是一个专业的渗透测试人员，现在需要进行权限提升测试。

目标信息:
- 目标: {target}
- 当前权限: {current_privilege}
- 系统信息: {system_info}

请执行以下权限提升任务:
1. 分析目标系统的漏洞和弱点
2. 尝试利用系统漏洞进行权限提升
3. 尝试利用配置错误进行权限提升
4. 尝试利用服务漏洞进行权限提升
5. 尝试利用内核漏洞进行权限提升

请使用以下工具进行权限提升:
- metasploit: 用于权限提升
- searchsploit: 用于搜索漏洞利用代码
- linpeas: 用于Linux权限提升枚举
- winpeas: 用于Windows权限提升枚举

请提供详细的权限提升结果，包括所有尝试的方法和成功的权限提升。
"""
    
    def _get_password_cracking_template(self):
        """密码破解提示模板"""
        return """
你是一个专业的密码破解专家，现在需要破解密码。

密码信息:
- 哈希类型: {hash_type}
- 哈希值: {hash_value}
- 目标用户: {target_user}

请执行以下密码破解任务:
1. 分析哈希类型和可能的密码策略
2. 选择合适的密码破解方法
3. 使用字典攻击尝试破解密码
4. 使用暴力攻击尝试破解密码
5. 使用彩虹表尝试破解密码

请使用以下工具进行密码破解:
- hashcat: 用于密码破解
- john: 用于密码破解
- hydra: 用于在线密码破解
- medusa: 用于并行密码破解

请提供详细的密码破解结果，包括所有尝试的方法和成功破解的密码。
"""
    
    def _get_vulnerability_analysis_template(self):
        """漏洞分析提示模板"""
        return """
你是一个专业的漏洞分析师，现在需要分析漏洞。

漏洞信息:
- 漏洞名称: {vulnerability_name}
- 漏洞描述: {vulnerability_description}
- 影响系统: {affected_systems}
- CVSS评分: {cvss_score}

请执行以下漏洞分析任务:
1. 分析漏洞的技术细节和攻击向量
2. 分析漏洞的影响范围和严重程度
3. 分析漏洞的利用条件和难度
4. 分析漏洞的修复方法和缓解措施
5. 提供详细的漏洞分析报告

请使用以下工具进行漏洞分析:
- searchsploit: 用于搜索漏洞利用代码
- metasploit: 用于测试漏洞
- nmap: 用于验证漏洞

请提供详细的漏洞分析结果，包括所有发现的信息和建议。
"""
    
    def get_template(self, template_name):
        """获取提示模板"""
        return self.templates.get(template_name, self.templates.get("reconnaissance"))
    
    def list_templates(self):
        """列出所有提示模板"""
        return list(self.templates.keys())
