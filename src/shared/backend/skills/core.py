# -*- coding: utf-8 -*-
"""
Skills 库 - 核心 Skill 类定义

Skills 是可被 AI 自动调用的渗透测试技能单元
包括：POC、Exploit 脚本、利用方法等
"""

import json
import os
import sys
import re
import shlex
import subprocess
import logging
from typing import TYPE_CHECKING, Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

if TYPE_CHECKING:
    from .context import SkillContext

logger = logging.getLogger(__name__)


class SkillType(Enum):
    """技能类型"""
    POC = "poc"              # 漏洞验证脚本
    EXPLOIT = "exploit"       # 漏洞利用脚本
    SCANNER = "scanner"      # 扫描脚本
    BRUTEFORCE = "bruteforce" # 暴力破解
    RECON = "recon"          # 信息收集
    POST = "post"            # 后渗透


class SkillCategory(Enum):
    """技能分类"""
    SQL_INJECTION = "sqli"
    XSS = "xss"
    RCE = "rce"
    LFI = "lfi"
    AUTH_BYPASS = "auth_bypass"
    INFO_DISCLOSURE = "info_disc"
    FILE_UPLOAD = "file_upload"
    SSRF = "ssrf"
    XXE = "xxe"
    CSRF = "csrf"
    GENERAL = "general"


@dataclass
class SkillParameter:
    """技能参数"""
    name: str
    type: str  # string, integer, boolean, list
    required: bool = True
    default: Any = None
    description: str = ""


@dataclass
class Skill:
    """技能定义"""
    id: str                          # 唯一标识
    name: str                        # 技能名称
    type: SkillType                  # 技能类型
    category: SkillCategory          # 技能分类
    description: str                 # 详细描述
    parameters: List[SkillParameter] # 参数列表
    target_type: str = "url"         # 目标类型: url, host, port, file
    severity: str = "medium"         # 漏洞严重性
    cve_id: Optional[str] = None     # CVE 编号
    references: List[str] = field(default_factory=list)  # 参考链接
    tags: List[str] = field(default_factory=list)        # 标签
    author: str = "ClawAI"           # 作者
    enabled: bool = True             # 是否启用
    
    # 执行相关
    executor: str = "python"         # 执行器: python, bash, curl
    code: str = ""                   # 脚本代码
    command_template: str = ""       # 命令模板
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        d = asdict(self)
        d['type'] = self.type.value
        d['category'] = self.category.value
        d['parameters'] = [asdict(p) for p in self.parameters]
        return d
    
    def get_openai_schema(self) -> Dict[str, Any]:
        """生成 OpenAI Function Calling Schema"""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description
            }
            if param.default is not None:
                prop["default"] = param.default
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        # 添加目标参数
        if "target" not in properties:
            properties["target"] = {
                "type": "string",
                "description": "目标地址"
            }
            required.append("target")
        
        return {
            "type": "function",
            "function": {
                "name": f"skill_{self.id}",
                "description": f"[{self.severity.upper()}] {self.description}",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }


class SkillExecutor:
    """技能执行器"""
    
    def __init__(self, skills_dir: str = None):
        self.skills_dir = skills_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "skills"
        )
    
    def execute(self, skill: Skill, params: Dict[str, Any], context: Optional["SkillContext"] = None) -> Dict[str, Any]:
        """
        执行技能
        
        Args:
            skill: 技能定义
            params: 执行参数
            context: 可选的 SkillContext 依赖注入（session 状态、findings、abort 控制等）
            
        Returns:
            执行结果
        """
        result = {
            "skill_id": skill.id,
            "skill_name": skill.name,
            "success": False,
            "vulnerable": False,
            "output": "",
            "evidence": None,
            "error": None
        }
        
        try:
            # 检查 abort 信号
            if context is not None and context.is_aborted():
                result["error"] = "已收到中止信号，跳过执行"
                return result

            # 验证参数
            validated_params = self._validate_params(skill, params)
            
            # 执行
            if skill.executor == "python":
                output = self._execute_python(skill, validated_params, context=context)
            elif skill.executor == "bash":
                output = self._execute_bash(skill, validated_params, context=context)
            elif skill.executor == "curl":
                output = self._execute_curl(skill, validated_params, context=context)
            elif skill.executor == "builtin":
                output = self._execute_builtin(skill, validated_params, context=context)
            else:
                raise ValueError(f"未知的执行器: {skill.executor}")
            
            result["output"] = output
            result["success"] = True
            
            # 检测漏洞是否存在
            result["vulnerable"] = self._detect_vulnerability(skill, output)
            
            # 提取证据
            if result["vulnerable"]:
                result["evidence"] = self._extract_evidence(skill, output)
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"技能执行失败 {skill.id}: {e}")
        
        return result
    
    def _validate_params(self, skill: Skill, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证并补全参数"""
        validated = {}
        
        for param in skill.parameters:
            if param.name in params:
                validated[param.name] = params[param.name]
            elif param.default is not None:
                validated[param.name] = param.default
            elif param.required:
                raise ValueError(f"缺少必需参数: {param.name}")
        
        # 添加目标
        if "target" in params:
            validated["target"] = params["target"]
        
        return validated
    
    # 危险字符模式，用于检测参数中的命令注入尝试
    _DANGEROUS_PATTERNS = re.compile(r'[;|`$]', re.IGNORECASE)

    def _sanitize_param(self, value: Any) -> str:
        """清理参数值，防止命令注入"""
        str_val = str(value)
        if self._DANGEROUS_PATTERNS.search(str_val):
            raise ValueError(
                f"参数包含潜在危险字符（;|`$），拒绝执行: {str_val[:50]}"
            )
        return str_val

    def _execute_python(self, skill: Skill, params: Dict[str, Any], context: Optional["SkillContext"] = None) -> str:
        """执行 Python 脚本"""
        # 清理参数，防止代码注入
        # cookie/header 参数允许包含 ; (分号是 Cookie 的正常分隔符)
        ALLOW_SEMICOLON = {"cookie", "headers", "user_agent"}
        safe_params = {}
        for key, value in params.items():
            if key.lower() in ALLOW_SEMICOLON:
                # 只禁止最危险的命令注入字符，允许分号
                str_val = str(value)
                if re.search(r'[`$]', str_val):
                    raise ValueError(f"参数包含危险字符，拒绝执行: {str_val[:50]}")
                safe_params[key] = str_val
            else:
                safe_params[key] = self._sanitize_param(value)

        # 替换参数
        code = skill.code
        for key, value in safe_params.items():
            code = code.replace(f"{{{{{key}}}}}", str(value))

        # 注入 SkillContext（序列化为 JSON 字符串，用 json.loads 解析）
        # 不直接展开为 Python 字面量，避免 JSON true/false/null 与 Python 不兼容
        # Skill code 中可通过 globals().get("__skill_context__", {}) 读取
        ctx_prefix = ""
        if context is not None:
            ctx_json = json.dumps(
                json.dumps(context.to_dict(), ensure_ascii=False),
                ensure_ascii=False,
            )
            ctx_prefix = f"import json as _json; __skill_context__ = _json.loads({ctx_json})\n\n"

        full_code = ctx_prefix + code

        # 写入临时文件到系统 temp 目录（远离项目目录，避免触发 uvicorn 热重载）
        import tempfile
        _py_drive = os.path.splitdrive(sys.executable)[0]
        _tmp_base = os.environ.get("TEMP", os.environ.get("TMP", tempfile.gettempdir()))
        _tmp_drive = os.path.splitdrive(_tmp_base)[0]
        if _py_drive and _tmp_drive and _py_drive.lower() != _tmp_drive.lower():
            # 驱动器不同时，在 Python 所在驱动器根目录下建 clawai_tmp
            _skill_tmp = _py_drive + "\\clawai_tmp"
        else:
            _skill_tmp = _tmp_base
        # 确保目录路径使用正斜杠（Windows 兼容性）
        _skill_tmp = _skill_tmp.replace('/', '\\')
        os.makedirs(_skill_tmp, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8', dir=_skill_tmp) as f:
            f.write('# -*- coding: utf-8 -*-\n')
            # 注入 logging，避免 skill code 中 logger.debug/info 报 NameError
            f.write('import logging as _logging; logger = _logging.getLogger("skill")\n')
            f.write(full_code)
            temp_path = f.name

        try:
            # 用户自定义技能（author != "ClawAI"）给更长超时，内置技能保持 30s
            exec_timeout = 120 if getattr(skill, 'author', 'ClawAI') != 'ClawAI' else 30
            # Windows: 强制正斜杠路径，避免 subprocess 传参时反斜杠被解析为转义字符
            safe_temp_path = temp_path.replace('\\', '/')
            result = subprocess.run(
                [sys.executable, safe_temp_path],
                shell=False,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=exec_timeout
            )
            return result.stdout + result.stderr
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass
    
    def _execute_bash(self, skill: Skill, params: Dict[str, Any], context: Optional["SkillContext"] = None) -> str:
        """执行 Bash 脚本（安全模式：参数转义 + shell=False）"""
        # 清理参数，防止命令注入
        safe_params = {}
        for key, value in params.items():
            safe_params[key] = self._sanitize_param(value)

        # 替换参数到模板
        cmd = skill.command_template
        for key, value in safe_params.items():
            cmd = cmd.replace(f"{{{{{key}}}}}", str(value))

        # 使用 shlex 分割命令为列表，避免 shell=True
        cmd_list = shlex.split(cmd)

        # 将 context 基本信息注入环境变量，供 Bash script 读取
        env = os.environ.copy()
        if context is not None:
            env["SKILL_SESSION_ID"] = context.session_id
            env["SKILL_TARGET"] = context.target
            env["SKILL_PHASE"] = context.phase

        result = subprocess.run(
            cmd_list,
            shell=False,
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )
        return result.stdout + result.stderr
    
    def _execute_curl(self, skill: Skill, params: Dict[str, Any], context: Optional["SkillContext"] = None) -> str:
        """执行 curl 命令（安全模式：参数转义 + shell=False）"""
        # 清理参数，防止命令注入
        safe_params = {}
        for key, value in params.items():
            safe_params[key] = self._sanitize_param(value)

        # 替换参数到模板
        cmd = skill.command_template
        for key, value in safe_params.items():
            cmd = cmd.replace(f"{{{{{key}}}}}", str(value))

        # 使用 shlex 分割命令为列表，避免 shell=True
        cmd_list = shlex.split(cmd)

        # 将 context 基本信息注入环境变量
        env = os.environ.copy()
        if context is not None:
            env["SKILL_SESSION_ID"] = context.session_id
            env["SKILL_TARGET"] = context.target
            env["SKILL_PHASE"] = context.phase

        result = subprocess.run(
            cmd_list,
            shell=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )
        return result.stdout
    
    def _execute_builtin(self, skill: Skill, params: Dict[str, Any], context: Optional["SkillContext"] = None) -> str:
        """执行内置检测逻辑"""
        target = params.get("target", "")
        
        if skill.id == "sqli_basic":
            return self._builtin_sqli_basic(target, params)
        elif skill.id == "xss_reflected":
            return self._builtin_xss_reflected(target, params)
        elif skill.id == "auth_bruteforce":
            return self._builtin_auth_bruteforce(target, params)
        elif skill.id == "vuln_quick_scan":
            return self._builtin_quick_scan(target, params)
        elif skill.id == "vuln_deep_scan":
            return self._builtin_deep_scan(target, params)
        elif skill.id == "waf_detection":
            return self._builtin_waf_detection(target, params)
        else:
            return "内置检测完成"
    
    def _builtin_sqli_basic(self, target: str, params: Dict[str, Any]) -> str:
        """内置 SQL 注入检测"""
        import urllib.request
        import urllib.parse
        
        payloads = [
            "' OR '1'='1",
            "' OR '1'='1'--",
            "1' AND '1'='1",
            "1 UNION SELECT NULL--",
            "' AND 1=1--",
        ]
        
        results = []
        param_name = params.get("param", "id")
        
        for payload in payloads:
            try:
                url = f"{target}?{param_name}={urllib.parse.quote(payload)}"
                req = urllib.request.Request(url)
                response = urllib.request.urlopen(req, timeout=10)
                content = response.read().decode('utf-8', errors='ignore')
                
                # 检测 SQL 错误
                sql_errors = [
                    "SQL syntax", "mysql_fetch", "ORA-", "PostgreSQL",
                    "sqlite_", "ODBC", "Microsoft SQL", "SQLSTATE"
                ]
                
                for error in sql_errors:
                    if error.lower() in content.lower():
                        results.append(f"PAYLOAD_HIT: {payload} -> {error}")
                        break
            except Exception as e:
                results.append(f"ERROR: {payload} -> {str(e)[:50]}")
        
        return "\n".join(results) if results else "无 SQL 注入迹象"
    
    def _builtin_xss_reflected(self, target: str, params: Dict[str, Any]) -> str:
        """内置 XSS 检测"""
        import urllib.request
        import urllib.parse
        
        payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "'\"><script>alert('XSS')</script>",
            "javascript:alert('XSS')",
        ]
        
        results = []
        param_name = params.get("param", "q")
        
        for payload in payloads:
            try:
                url = f"{target}?{param_name}={urllib.parse.quote(payload)}"
                req = urllib.request.Request(url)
                response = urllib.request.urlopen(req, timeout=10)
                content = response.read().decode('utf-8', errors='ignore')
                
                if payload in content or "alert" in content:
                    results.append(f"XSS_FOUND: {payload}")
            except Exception as e:
                pass
        
        return "\n".join(results) if results else "未检测到反射型 XSS"
    
    def _builtin_auth_bruteforce(self, target: str, params: Dict[str, Any]) -> str:
        """内置认证暴力破解"""
        # 常见凭据
        credentials = [
            ("admin", "admin"),
            ("admin", "password"),
            ("admin", "123456"),
            ("root", "root"),
            ("admin", "admin123"),
        ]
        
        results = []
        
        for username, password in credentials:
            # 这里简化处理，实际需要根据具体表单调整
            results.append(f"尝试: {username}:{password}")
        
        return "\n".join(results) + "\n建议使用 hydra 进行完整暴力破解"
    
    def _builtin_quick_scan(self, target: str, params: Dict[str, Any]) -> str:
        """内置快速扫描"""
        try:
            from ..vuln_detector import quick_scan
            result = quick_scan(target)
            
            output = f"=== 快速扫描结果 ===\n"
            output += f"目标: {target}\n"
            output += f"发现漏洞: {result['total_vulnerabilities']}\n"
            
            if result.get('waf_info', {}).get('has_waf'):
                wafs = result['waf_info'].get('detected_wafs', [])
                output += f"WAF检测: {', '.join([w['name'] for w in wafs])}\n"
            
            output += "\n漏洞详情:\n"
            for vuln in result.get('vulnerabilities', []):
                output += f"  [{vuln['severity'].upper()}] {vuln['title']}\n"
                output += f"    类型: {vuln['type']}\n"
                output += f"    CVSS: {vuln['cvss_score']}\n"
            
            return output
        except Exception as e:
            return f"快速扫描失败: {str(e)}"
    
    def _builtin_deep_scan(self, target: str, params: Dict[str, Any]) -> str:
        """内置深度扫描"""
        try:
            from ..vuln_detector import deep_scan
            result = deep_scan(target)
            
            output = f"=== 深度扫描结果 ===\n"
            output += f"目标: {target}\n"
            output += f"发现漏洞: {result['total_vulnerabilities']}\n"
            
            summary = result.get('summary', {})
            output += f"\n严重性分布:\n"
            output += f"  Critical: {summary.get('critical', 0)}\n"
            output += f"  High: {summary.get('high', 0)}\n"
            output += f"  Medium: {summary.get('medium', 0)}\n"
            output += f"  Low: {summary.get('low', 0)}\n"
            
            output += "\n漏洞详情:\n"
            for vuln in result.get('vulnerabilities', []):
                output += f"\n[{vuln['severity'].upper()}] {vuln['title']}\n"
                output += f"  类型: {vuln['type']}\n"
                output += f"  参数: {vuln.get('parameter', 'N/A')}\n"
                output += f"  CVSS: {vuln['cvss_score']}\n"
                output += f"  已验证: {'是' if vuln.get('verified') else '否'}\n"
                output += f"  修复建议: {vuln.get('remediation', 'N/A')}\n"
            
            return output
        except Exception as e:
            return f"深度扫描失败: {str(e)}"
    
    def _builtin_waf_detection(self, target: str, params: Dict[str, Any]) -> str:
        """内置WAF检测"""
        try:
            from ..vuln_detector import WAFDetector
            import urllib.request
            
            req = urllib.request.Request(target)
            response = urllib.request.urlopen(req, timeout=10)
            headers = dict(response.headers)
            body = response.read().decode('utf-8', errors='ignore')
            
            result = WAFDetector.detect(target, headers, body)
            
            output = f"=== WAF 检测结果 ===\n"
            output += f"目标: {target}\n"
            
            if result.get('has_waf'):
                output += f"检测到WAF: 是\n"
                for waf in result.get('detected_wafs', []):
                    output += f"\nWAF类型: {waf['name']}\n"
                    output += f"置信度: {waf['confidence']:.0%}\n"
                    output += f"拦截状态码: {waf.get('block_codes', [])}\n"
            else:
                output += f"检测到WAF: 否\n"
            
            return output
        except Exception as e:
            return f"WAF检测失败: {str(e)}"
    
    def _detect_vulnerability(self, skill: Skill, output: str) -> bool:
        """从输出检测漏洞是否存在"""
        # 根据技能类型设置不同的检测规则
        positive_indicators = {
            SkillType.POC: ["vulnerable", "found", "exploitable", "PAYLOAD_HIT"],
            SkillType.EXPLOIT: ["success", "shell", "access", "extracted"],
            SkillType.SCANNER: ["found", "detected", "open"],
        }
        
        indicators = positive_indicators.get(skill.type, ["found", "success"])
        
        output_lower = output.lower()
        for indicator in indicators:
            if indicator.lower() in output_lower:
                return True
        
        return False
    
    def _extract_evidence(self, skill: Skill, output: str) -> str:
        """提取漏洞证据"""
        # 提取关键行
        lines = output.split('\n')
        evidence_lines = []
        
        for line in lines:
            if any(kw in line.lower() for kw in ['payload', 'found', 'vulnerable', 'error', 'success']):
                evidence_lines.append(line.strip())
        
        return "\n".join(evidence_lines[:5]) if evidence_lines else output[:500]
