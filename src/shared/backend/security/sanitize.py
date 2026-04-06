"""
安全工具模块 - 提供安全的命令执行、路径验证和敏感信息过滤功能
"""

import subprocess
import os
import re
from typing import List, Tuple, Optional, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """安全相关异常"""
    pass


def safe_execute(
    cmd: List[str],
    timeout: int = 30,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
    input_data: Optional[str] = None
) -> Tuple[int, str, str]:
    """
    安全的命令执行函数

    参数:
        cmd: 命令参数列表，禁止使用字符串格式
        timeout: 执行超时时间（秒）
        cwd: 工作目录
        env: 环境变量
        input_data: 标准输入数据

    返回:
        (返回码, 标准输出, 标准错误)

    异常:
        TimeoutError: 执行超时
        SecurityError: 安全违规（如shell=True）
        subprocess.SubprocessError: 其他子进程错误
    """
    # 安全检查
    if not isinstance(cmd, list):
        raise SecurityError(f"命令必须是列表格式，禁止字符串: {cmd}")

    if any(';' in arg or '&' in arg or '|' in arg or '$' in arg for arg in cmd):
        logger.warning(f"命令中包含潜在危险字符: {cmd}")

    # 记录命令（脱敏后）
    safe_cmd = filter_sensitive_data(' '.join(cmd))
    logger.debug(f"执行命令: {safe_cmd}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
            input=input_data,
            shell=False,  # 关键：禁用shell执行
            encoding='utf-8',
            errors='replace'
        )

        # 记录执行结果（脱敏后）
        if result.stdout:
            safe_stdout = filter_sensitive_data(result.stdout[:500])  # 只记录前500字符
            logger.debug(f"命令输出: {safe_stdout}")

        if result.stderr:
            safe_stderr = filter_sensitive_data(result.stderr[:500])
            logger.warning(f"命令错误: {safe_stderr}")

        return result.returncode, result.stdout, result.stderr

    except subprocess.TimeoutExpired as e:
        logger.error(f"命令执行超时 ({timeout}s): {safe_cmd}")
        raise TimeoutError(f"命令执行超时: {timeout}秒") from e

    except Exception as e:
        logger.error(f"命令执行失败: {safe_cmd}, 错误: {e}")
        raise


def validate_path(path: str, base_dir: str) -> str:
    """
    路径验证，防止目录遍历攻击

    参数:
        path: 要验证的路径
        base_dir: 基础目录，路径必须在此目录下

    返回:
        规范化后的绝对路径

    异常:
        SecurityError: 路径尝试遍历到基础目录外
    """
    try:
        # 转换为绝对路径
        if not os.path.isabs(base_dir):
            base_dir = os.path.abspath(base_dir)

        # 规范化路径
        normalized = os.path.normpath(os.path.join(base_dir, path))
        absolute_path = os.path.abspath(normalized)

        # 验证是否在基础目录内
        if not absolute_path.startswith(base_dir):
            logger.error(f"路径遍历尝试: path={path}, base_dir={base_dir}, normalized={absolute_path}")
            raise SecurityError(f"路径遍历尝试: {path}")

        return absolute_path

    except Exception as e:
        logger.error(f"路径验证失败: {path}, 错误: {e}")
        raise SecurityError(f"路径验证失败: {path}") from e


def filter_sensitive_data(text: str) -> str:
    """
    过滤敏感信息（API密钥、密码等）

    参数:
        text: 要过滤的文本

    返回:
        过滤后的文本
    """
    if not text:
        return text

    # 敏感信息模式
    patterns = [
        # API密钥模式
        (r'sk-[a-zA-Z0-9]{24,}', 'sk-***'),
        (r'[aA][pP][iI][_-]?[kK]e[yY]\s*[=:]\s*["\']?([^"\'\s]+)["\']?', 'api_key=***'),
        (r'[bB]earer\s+[a-zA-Z0-9._-]+', 'Bearer ***'),

        # 密码模式
        (r'[pP]assword\s*[=:]\s*["\']?([^"\'\s]+)["\']?', 'password=***'),
        (r'[pP]wd\s*[=:]\s*["\']?([^"\'\s]+)["\']?', 'pwd=***'),

        # JWT令牌
        (r'eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+', 'JWT_TOKEN'),

        # 私钥模式
        (r'-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----[\s\S]*?-----END \1 PRIVATE KEY-----', '***PRIVATE_KEY***'),

        # 数据库连接字符串
        (r'postgres(ql)?://[^:@]+:[^@]+@', 'postgres://***:***@'),
        (r'mysql://[^:@]+:[^@]+@', 'mysql://***:***@'),
        (r'redis://[^:@]+:[^@]+@', 'redis://***:***@'),
    ]

    filtered = text
    for pattern, replacement in patterns:
        try:
            filtered = re.sub(pattern, replacement, filtered, flags=re.IGNORECASE)
        except Exception as e:
            logger.warning(f"正则表达式匹配失败: {pattern}, 错误: {e}")
            continue

    return filtered


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除危险字符

    参数:
        filename: 原始文件名

    返回:
        安全的文件名
    """
    # 移除危险字符
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ';', '&', '$', '`']
    safe_name = filename
    for char in dangerous_chars:
        safe_name = safe_name.replace(char, '_')

    # 限制长度
    if len(safe_name) > 255:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:250 - len(ext)] + ext

    return safe_name


def validate_url(url: str) -> bool:
    """
    验证URL是否安全

    参数:
        url: 要验证的URL

    返回:
        是否安全
    """
    # 简单URL验证
    if not url or not isinstance(url, str):
        return False

    # 检查危险协议
    dangerous_protocols = ['file://', 'gopher://', 'jar://', 'ldap://', 'mailto:']
    if any(url.lower().startswith(proto) for proto in dangerous_protocols):
        return False

    # 检查本地文件访问
    if url.lower().startswith('file://'):
        return False

    # 基本URL格式验证：必须包含 :// 且协议为 http 或 https
    # 注意：允许无协议（如 example.com）但需要谨慎
    # 为了安全，我们要求明确协议
    if "://" not in url:
        return False

    # 提取协议
    protocol = url.split("://")[0].lower()
    safe_protocols = ['http', 'https', 'ftp', 'ftps', 'ws', 'wss']
    if protocol not in safe_protocols:
        return False

    # 检查内网地址（可选，根据需求调整）
    # 这里可以添加更复杂的内网地址检测

    return True


class SafeCommandBuilder:
    """安全命令构建器"""

    @staticmethod
    def build_nmap(target: str, options: List[str] = None) -> List[str]:
        """构建安全的nmap命令"""
        if options is None:
            options = ['-sT', '-sV', '-sC']

        # 验证目标
        if not target or ';' in target or '&' in target or '|' in target:
            raise SecurityError(f"无效的目标地址: {target}")

        cmd = ['nmap'] + options + [target]
        return cmd

    @staticmethod
    def build_sqlmap(url: str, options: List[str] = None) -> List[str]:
        """构建安全的sqlmap命令"""
        if options is None:
            options = ['--batch', '--random-agent']

        # 验证URL
        if not validate_url(url):
            raise SecurityError(f"无效的URL: {url}")

        cmd = ['sqlmap', '-u', url] + options
        return cmd


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 测试安全执行
    try:
        returncode, stdout, stderr = safe_execute(['echo', 'hello world'])
        print(f"执行成功: {returncode}, 输出: {stdout}")
    except Exception as e:
        print(f"执行失败: {e}")

    # 测试路径验证
    try:
        safe_path = validate_path('../test.txt', '/home/user/project')
        print(f"安全路径: {safe_path}")
    except SecurityError as e:
        print(f"路径不安全: {e}")

    # 测试敏感信息过滤
    text = "api_key='sk-abc123def456' password='secret'"
    filtered = filter_sensitive_data(text)
    print(f"过滤后: {filtered}")